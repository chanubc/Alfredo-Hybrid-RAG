"""Phase B FTS 정확도 벤치마크.

Before (Phase A): raw query → plainto_tsquery('simple', raw_query)
After  (Phase B): morpheme_tokenize(query) → plainto_tsquery('simple', morpheme_query)

Ground truth: 쿼리 어근(root terms)이 chunk content에 포함된 chunks
Metrics: P@5, MRR, NDCG@5, Top-1 Accuracy

Usage:
    python scripts/benchmark_fts_accuracy.py --user-id <USER_ID>
    python scripts/benchmark_fts_accuracy.py --user-id <USER_ID> --top-k 10
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.rag.korean_utils import morpheme_tokenize

load_dotenv()

TOP_K = 5

# (query, root_terms_for_ground_truth)
# Ground truth: chunk.content에 root_terms 중 하나 이상 포함
TEST_QUERIES: list[tuple[str, list[str]]] = [
    # 복합어 + 조사 (Phase B 핵심)
    ("채용공고를",      ["채용", "공고"]),
    ("개발자채용",      ["개발자", "채용"]),
    ("입사지원서",      ["입사", "지원"]),
    # 단순 조사
    ("백엔드에서",      ["백엔드"]),
    ("증권에서",        ["증권"]),
    ("스타트업에서의",  ["스타트업"]),
    ("머신러닝으로",    ["머신러닝"]),
    # 한영 혼합
    ("AI채용",          ["AI", "채용"]),
    ("Python백엔드",    ["Python", "백엔드"]),
    ("LLM활용",         ["LLM"]),
]


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _precision_at_k(ranked_ids: list[int], relevant_ids: set[int], k: int) -> float:
    top_k = ranked_ids[:k]
    hits = sum(1 for cid in top_k if cid in relevant_ids)
    return hits / k if k > 0 else 0.0


def _mrr(ranked_ids: list[int], relevant_ids: set[int]) -> float:
    for rank, cid in enumerate(ranked_ids, start=1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0


def _ndcg_at_k(ranked_ids: list[int], relevant_ids: set[int], k: int) -> float:
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, cid in enumerate(ranked_ids[:k], start=1)
        if cid in relevant_ids
    )
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


def _top1_accuracy(ranked_ids: list[int], relevant_ids: set[int]) -> float:
    return 1.0 if ranked_ids and ranked_ids[0] in relevant_ids else 0.0


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _get_relevant_ids(conn, user_id: int, root_terms: list[str]) -> set[int]:
    """root_terms 중 하나라도 content에 포함된 chunk ids."""
    conditions = " OR ".join(
        f"LOWER(c.content) LIKE :term_{i}" for i in range(len(root_terms))
    )
    params: dict = {"user_id": user_id}
    for i, term in enumerate(root_terms):
        params[f"term_{i}"] = f"%{term.lower()}%"

    rows = (await conn.execute(
        sa.text(f"""
            SELECT c.id FROM chunks c
            JOIN links l ON c.link_id = l.id
            WHERE l.user_id = :user_id AND ({conditions})
        """),
        params,
    )).fetchall()
    return {row.id for row in rows}


async def _fts_ranked_ids(conn, user_id: int, tsquery_text: str, top_k: int) -> list[int]:
    """FTS 쿼리 결과를 ts_rank DESC로 반환. 매칭 없으면 []."""
    if not tsquery_text.strip():
        return []
    rows = (await conn.execute(
        sa.text("""
            SELECT c.id
            FROM chunks c
            JOIN links l ON c.link_id = l.id
            WHERE l.user_id = :user_id
              AND c.tsv IS NOT NULL
              AND c.tsv @@ plainto_tsquery('simple', :q)
            ORDER BY ts_rank(c.tsv, plainto_tsquery('simple', :q)) DESC
            LIMIT :top_k
        """),
        {"user_id": user_id, "q": tsquery_text, "top_k": top_k},
    )).fetchall()
    return [row.id for row in rows]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_benchmark(user_id: int, top_k: int) -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    url = make_url(database_url).set(drivername="postgresql+asyncpg")
    engine = create_async_engine(url)

    results = []

    try:
        async with engine.connect() as conn:
            for query, root_terms in TEST_QUERIES:
                relevant_ids = await _get_relevant_ids(conn, user_id, root_terms)
                if not relevant_ids:
                    print(f"  [SKIP] '{query}' — DB에 관련 chunks 없음 (root: {root_terms})")
                    continue

                # Before: raw query
                before_ids = await _fts_ranked_ids(conn, user_id, query, top_k)
                # After: morpheme_tokenize
                morpheme_query = morpheme_tokenize(query)
                after_ids = await _fts_ranked_ids(conn, user_id, morpheme_query, top_k)

                results.append({
                    "query":       query,
                    "morpheme":    morpheme_query,
                    "n_relevant":  len(relevant_ids),
                    "before_ids":  before_ids,
                    "after_ids":   after_ids,
                    "relevant":    relevant_ids,
                })
    finally:
        await engine.dispose()

    if not results:
        print("측정 가능한 쿼리가 없습니다. DB에 관련 내용이 없거나 user_id가 잘못됐습니다.")
        return

    _print_report(results, top_k)


def _print_report(results: list[dict], top_k: int) -> None:
    before_p, after_p = [], []
    before_mrr, after_mrr = [], []
    before_ndcg, after_ndcg = [], []
    before_t1, after_t1 = [], []

    header = f"{'쿼리':<18} {'형태소':<18} {'관련':<4} " \
             f"{'P@5 B':>6} {'P@5 A':>6} " \
             f"{'MRR B':>6} {'MRR A':>6} " \
             f"{'NDCG B':>7} {'NDCG A':>7} " \
             f"{'1위 B':>5} {'1위 A':>5}"
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))

    for r in results:
        rel = r["relevant"]
        bp = _precision_at_k(r["before_ids"], rel, top_k)
        ap = _precision_at_k(r["after_ids"],  rel, top_k)
        bm = _mrr(r["before_ids"], rel)
        am = _mrr(r["after_ids"],  rel)
        bn = _ndcg_at_k(r["before_ids"], rel, top_k)
        an = _ndcg_at_k(r["after_ids"],  rel, top_k)
        bt = _top1_accuracy(r["before_ids"], rel)
        at = _top1_accuracy(r["after_ids"],  rel)

        before_p.append(bp);  after_p.append(ap)
        before_mrr.append(bm); after_mrr.append(am)
        before_ndcg.append(bn); after_ndcg.append(an)
        before_t1.append(bt);  after_t1.append(at)

        print(
            f"{r['query']:<18} {r['morpheme']:<18} {r['n_relevant']:<4} "
            f"{bp:>6.4f} {ap:>6.4f} "
            f"{bm:>6.4f} {am:>6.4f} "
            f"{bn:>7.4f} {an:>7.4f} "
            f"{bt:>5.0f} {at:>5.0f}"
        )

    n = len(results)
    avg = lambda lst: sum(lst) / n

    def pct(b, a):
        return f"+{(a-b)/b*100:.0f}%" if b > 0 else ("∞" if a > 0 else "0%")

    print("=" * len(header))
    bp_avg = avg(before_p);  ap_avg = avg(after_p)
    bm_avg = avg(before_mrr); am_avg = avg(after_mrr)
    bn_avg = avg(before_ndcg); an_avg = avg(after_ndcg)
    bt_avg = avg(before_t1);  at_avg = avg(after_t1)

    print(f"\n{'지표':<12} {'Before':>8} {'After':>8} {'향상':>8}")
    print("-" * 40)
    print(f"{'P@5':<12} {bp_avg:>8.4f} {ap_avg:>8.4f} {pct(bp_avg, ap_avg):>8}")
    print(f"{'MRR':<12} {bm_avg:>8.4f} {am_avg:>8.4f} {pct(bm_avg, am_avg):>8}")
    print(f"{'NDCG@5':<12} {bn_avg:>8.4f} {an_avg:>8.4f} {pct(bn_avg, an_avg):>8}")
    print(f"{'1위 정확도':<12} {bt_avg:>8.4f} {at_avg:>8.4f} {pct(bt_avg, at_avg):>8}")
    print(f"\n측정 쿼리 수: {n} / {len(TEST_QUERIES)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase B FTS accuracy benchmark")
    parser.add_argument("--user-id", type=int, required=True, help="테스트할 user_id (telegram_id)")
    parser.add_argument("--top-k",  type=int, default=TOP_K, help="검색 결과 수 (기본 5)")
    args = parser.parse_args()
    asyncio.run(run_benchmark(args.user_id, args.top_k))
