"""Phase A/B FTS + Keyword 정확도 3단계 벤치마크.

Stage 1 (Pre-Phase A): raw query → FTS 0점, keyword overlap도 raw 토큰 매칭
Stage 2 (Phase A):     raw query → FTS 0점, keyword overlap은 morpheme 변형 적용
Stage 3 (Phase B):     morpheme FTS + keyword overlap (Phase A와 동일)

측정 레이어:
  - Sparse FTS: ts_rank via plainto_tsquery
  - Keyword overlap: links.keywords 컬럼 기반 Python-level 매칭

Ground truth: 쿼리 어근이 chunk content에 포함된 chunks

Usage:
    python scripts/benchmark_fts_accuracy.py --user-id <USER_ID>
    python scripts/benchmark_fts_accuracy.py --user-id <USER_ID> --top-k 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.rag.korean_utils import morpheme_tokenize
from app.infrastructure.rag.retriever import _build_query_variants, _token_matches

load_dotenv()

TOP_K = 5

TEST_QUERIES: list[tuple[str, list[str]]] = [
    ("채용공고를",      ["채용", "공고"]),
    ("개발자채용",      ["개발자", "채용"]),
    ("입사지원서",      ["입사", "지원"]),
    ("백엔드에서",      ["백엔드"]),
    ("증권에서",        ["증권"]),
    ("스타트업에서의",  ["스타트업"]),
    ("머신러닝으로",    ["머신러닝"]),
    ("AI채용",          ["AI", "채용"]),
    ("Python백엔드",    ["Python", "백엔드"]),
    ("LLM활용",         ["LLM"]),
]


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _precision_at_k(ranked_ids: list[int], relevant: set[int], k: int) -> float:
    hits = sum(1 for cid in ranked_ids[:k] if cid in relevant)
    return hits / k if k > 0 else 0.0

def _mrr(ranked_ids: list[int], relevant: set[int]) -> float:
    for rank, cid in enumerate(ranked_ids, start=1):
        if cid in relevant:
            return 1.0 / rank
    return 0.0

def _ndcg_at_k(ranked_ids: list[int], relevant: set[int], k: int) -> float:
    dcg = sum(1.0 / math.log2(r + 1) for r, cid in enumerate(ranked_ids[:k], 1) if cid in relevant)
    ideal = sum(1.0 / math.log2(r + 1) for r in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal > 0 else 0.0

def _top1(ranked_ids: list[int], relevant: set[int]) -> float:
    return 1.0 if ranked_ids and ranked_ids[0] in relevant else 0.0


# ---------------------------------------------------------------------------
# Keyword overlap helpers (Python-level, simulates rescoring layer)
# ---------------------------------------------------------------------------

def _parse_keywords(raw) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [k.lower() for k in parsed if isinstance(k, str) and k.strip()]
    except Exception:
        pass
    return []


def _keyword_overlap_pre_a(query: str, keywords: list[str], title: str) -> float:
    """Pre-Phase A: raw token split, exact/substring only (no morpheme)."""
    q_tokens = {t.lower() for t in query.split() if t}
    if not q_tokens:
        return 0.0
    matched = sum(
        1 for qt in q_tokens
        if any(qt == kw or (len(qt) >= 2 and qt in kw) for kw in keywords)
        or (len(qt) >= 2 and qt in title.lower())
    )
    return matched / len(q_tokens)


def _keyword_overlap_phase_a(query: str, keywords: list[str], title: str) -> float:
    """Phase A: morpheme query variants + _token_matches (compound split + particle strip)."""
    all_token_sets = [
        {t.lower() for t in v.split() if t}
        for v in _build_query_variants(query)
    ]
    best = 0.0
    for q_tokens in all_token_sets:
        if not q_tokens:
            continue
        matched = sum(
            1 for qt in q_tokens
            if any(_token_matches(qt, kw) for kw in keywords)
            or (len(qt) >= 2 and qt in title.lower())
        )
        overlap = matched / len(q_tokens)
        best = max(best, overlap)
    return best


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _get_relevant_ids(conn, user_id: int, root_terms: list[str]) -> set[int]:
    conditions = " OR ".join(f"LOWER(c.content) LIKE :t{i}" for i in range(len(root_terms)))
    params: dict = {"user_id": user_id}
    for i, t in enumerate(root_terms):
        params[f"t{i}"] = f"%{t.lower()}%"
    rows = (await conn.execute(
        sa.text(f"SELECT c.id FROM chunks c JOIN links l ON c.link_id=l.id WHERE l.user_id=:user_id AND ({conditions})"),
        params,
    )).fetchall()
    return {r.id for r in rows}


async def _fts_ranked_ids(conn, user_id: int, tsquery_text: str, top_k: int) -> list[int]:
    if not tsquery_text.strip():
        return []
    rows = (await conn.execute(
        sa.text("""
            SELECT c.id FROM chunks c JOIN links l ON c.link_id=l.id
            WHERE l.user_id=:user_id AND c.tsv IS NOT NULL
              AND c.tsv @@ plainto_tsquery('simple', :q)
            ORDER BY ts_rank(c.tsv, plainto_tsquery('simple', :q)) DESC
            LIMIT :k
        """),
        {"user_id": user_id, "q": tsquery_text, "top_k": top_k, "k": top_k},
    )).fetchall()
    return [r.id for r in rows]


async def _get_link_keywords_by_chunk_ids(conn, chunk_ids: list[int]) -> dict[int, tuple[list[str], str]]:
    """chunk_id → (keywords, title)"""
    if not chunk_ids:
        return {}
    rows = (await conn.execute(
        sa.text("""
            SELECT c.id AS chunk_id, l.keywords, COALESCE(l.title,'') AS title
            FROM chunks c JOIN links l ON c.link_id=l.id
            WHERE c.id = ANY(:ids)
        """),
        {"ids": list(chunk_ids)},
    )).fetchall()
    return {r.chunk_id: (_parse_keywords(r.keywords), r.title) for r in rows}


async def _keyword_ranked_ids(conn, user_id: int, query: str, top_k: int, stage: str) -> list[int]:
    """keyword overlap 기반 상위 chunk_ids 반환. stage: 'pre_a' | 'phase_a'"""
    rows = (await conn.execute(
        sa.text("""
            SELECT c.id AS chunk_id, l.keywords, COALESCE(l.title,'') AS title
            FROM chunks c JOIN links l ON c.link_id=l.id
            WHERE l.user_id=:user_id AND l.keywords IS NOT NULL
        """),
        {"user_id": user_id},
    )).fetchall()

    scored = []
    for r in rows:
        kws = _parse_keywords(r.keywords)
        if stage == "pre_a":
            score = _keyword_overlap_pre_a(query, kws, r.title)
        else:  # phase_a and phase_b are same for keyword layer
            score = _keyword_overlap_phase_a(query, kws, r.title)
        if score > 0:
            scored.append((r.chunk_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in scored[:top_k]]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_benchmark(user_id: int, top_k: int) -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("DATABASE_URL not set")

    url = make_url(database_url).set(drivername="postgresql+asyncpg")
    engine = create_async_engine(url)

    results = []
    try:
        async with engine.connect() as conn:
            for query, roots in TEST_QUERIES:
                relevant = await _get_relevant_ids(conn, user_id, roots)
                if not relevant:
                    print(f"  [SKIP] '{query}' — DB에 관련 chunks 없음")
                    continue

                morpheme_q = morpheme_tokenize(query)

                # FTS scores
                fts_raw   = await _fts_ranked_ids(conn, user_id, query,      top_k)
                fts_morph = await _fts_ranked_ids(conn, user_id, morpheme_q,  top_k)

                # Keyword overlap scores
                kw_pre_a  = await _keyword_ranked_ids(conn, user_id, query, top_k, "pre_a")
                kw_phase_a = await _keyword_ranked_ids(conn, user_id, query, top_k, "phase_a")

                results.append({
                    "query":       query,
                    "morpheme":    morpheme_q,
                    "n_relevant":  len(relevant),
                    "relevant":    relevant,
                    # Stage 1: Pre-Phase A (raw FTS + raw keyword)
                    "pre_a_fts":   fts_raw,
                    "pre_a_kw":    kw_pre_a,
                    # Stage 2: Phase A (raw FTS + morpheme keyword)
                    "a_fts":       fts_raw,
                    "a_kw":        kw_phase_a,
                    # Stage 3: Phase B (morpheme FTS + morpheme keyword)
                    "b_fts":       fts_morph,
                    "b_kw":        kw_phase_a,
                })
    finally:
        await engine.dispose()

    if not results:
        print("측정 가능한 쿼리 없음.")
        return

    _print_report(results, top_k)


def _metrics(ranked: list[int], relevant: set[int], k: int) -> tuple[float, float, float, float]:
    return (
        _precision_at_k(ranked, relevant, k),
        _mrr(ranked, relevant),
        _ndcg_at_k(ranked, relevant, k),
        _top1(ranked, relevant),
    )


def _print_report(results: list[dict], top_k: int) -> None:
    stages = ["Pre-A", "Phase A", "Phase B"]
    metric_names = [f"P@{top_k}", "MRR", f"NDCG@{top_k}", "Top-1"]

    # Aggregate per stage
    agg: dict[str, list[list[float]]] = {s: [[] for _ in metric_names] for s in stages}

    print("\n" + "=" * 100)
    print(f"{'쿼리':<16} {'형태소':<18} {'관련':>4}  "
          f"{'--- FTS ---':^18}  {'-- Keyword --':^18}  {'--- FTS+KW ---':^18}")
    print(f"{'':16} {'':18} {'':4}  "
          f"{'Pre-A':>6} {'Ph-A':>6} {'Ph-B':>6}  "
          f"{'Pre-A':>6} {'Ph-A':>6} {'Ph-B':>6}  "
          f"{'Pre-A':>6} {'Ph-A':>6} {'Ph-B':>6}")
    print("-" * 100)

    for r in results:
        rel = r["relevant"]

        # FTS-only metrics (MRR as representative)
        fts_pre_a = _mrr(r["pre_a_fts"], rel)
        fts_a     = _mrr(r["a_fts"],     rel)
        fts_b     = _mrr(r["b_fts"],     rel)

        # Keyword-only metrics (MRR)
        kw_pre_a  = _mrr(r["pre_a_kw"],  rel)
        kw_a      = _mrr(r["a_kw"],      rel)
        kw_b      = _mrr(r["b_kw"],      rel)  # same as a_kw

        # Combined: union of FTS + keyword hits (best rank)
        def combined_rank(fts_ids, kw_ids, relevant):
            seen = {}
            for rank, cid in enumerate(fts_ids + [c for c in kw_ids if c not in fts_ids], 1):
                if cid not in seen:
                    seen[cid] = rank
            ranked = sorted(seen.keys(), key=lambda c: seen[c])
            return _mrr(ranked, relevant)

        comb_pre_a = combined_rank(r["pre_a_fts"], r["pre_a_kw"], rel)
        comb_a     = combined_rank(r["a_fts"],     r["a_kw"],     rel)
        comb_b     = combined_rank(r["b_fts"],     r["b_kw"],     rel)

        print(
            f"{r['query']:<16} {r['morpheme']:<18} {r['n_relevant']:>4}  "
            f"{fts_pre_a:>6.3f} {fts_a:>6.3f} {fts_b:>6.3f}  "
            f"{kw_pre_a:>6.3f} {kw_a:>6.3f} {kw_b:>6.3f}  "
            f"{comb_pre_a:>6.3f} {comb_a:>6.3f} {comb_b:>6.3f}"
        )

    print("=" * 100)

    # Summary table per metric
    print(f"\n{'지표':12} {'Pre-Phase A':>12} {'Phase A':>10} {'Phase B':>10}  {'A→B':>8} {'Pre→B':>8}")
    print("-" * 60)

    metric_labels = [f"P@{top_k}", "MRR", f"NDCG@{top_k}", "Top-1 정확도"]
    for mi, label in enumerate(metric_labels):
        pre_vals, a_vals, b_vals = [], [], []
        for r in results:
            rel = r["relevant"]
            pre_p, pre_m, pre_n, pre_t = _metrics(r["pre_a_fts"] + [c for c in r["pre_a_kw"] if c not in r["pre_a_fts"]], rel, top_k)
            a_p,   a_m,   a_n,   a_t   = _metrics(r["a_fts"]     + [c for c in r["a_kw"]     if c not in r["a_fts"]],     rel, top_k)
            b_p,   b_m,   b_n,   b_t   = _metrics(r["b_fts"]     + [c for c in r["b_kw"]     if c not in r["b_fts"]],     rel, top_k)
            vals_all = [(pre_p, a_p, b_p), (pre_m, a_m, b_m), (pre_n, a_n, b_n), (pre_t, a_t, b_t)]
            pre_vals.append(vals_all[mi][0])
            a_vals.append(vals_all[mi][1])
            b_vals.append(vals_all[mi][2])

        n = len(results)
        pre_avg = sum(pre_vals) / n
        a_avg   = sum(a_vals)   / n
        b_avg   = sum(b_vals)   / n

        def diff(before, after):
            if before == 0:
                return f"{'∞' if after > 0 else '0%':>8}"
            return f"{(after - before) / before * 100:>+7.0f}%"

        print(f"{label:<12} {pre_avg:>12.4f} {a_avg:>10.4f} {b_avg:>10.4f}  {diff(a_avg, b_avg)} {diff(pre_avg, b_avg)}")

    print(f"\n측정 쿼리 수: {len(results)} / {len(TEST_QUERIES)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--top-k",  type=int, default=TOP_K)
    args = parser.parse_args()
    asyncio.run(run_benchmark(args.user_id, args.top_k))
