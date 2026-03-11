import json

from app.domain.repositories.i_chunk_repository import IChunkRepository
from app.application.ports.ai_analysis_port import AIAnalysisPort

_KEYWORD_WEIGHT_JINA = 0.3
_KEYWORD_WEIGHT_OG = 0.1

_RECALL_MULTIPLIER = 5
_MIN_RECALL_K = 30
_MAX_RECALL_K = 100

_MIN_RESULT_SIMILARITY = 0.30
_RELATIVE_RESULT_RATIO = 0.50

_HIRING_INTENT_TERMS = frozenset({
    "공고", "채용", "채용공고", "공개채용", "공채", "신입", "신입사원", "인턴", "모집", "취업",
})
_HIRING_RESULT_TERMS = frozenset({
    "채용공고", "공개채용", "공채", "신입사원", "인턴", "모집",
})
_HIRING_CATEGORY_BOOST = 0.05
_HIRING_TERM_BOOST = 0.10


class HybridRetriever:
    """벡터 유사도 + LLM 키워드 기반 하이브리드 검색기."""

    def __init__(self, openai: AIAnalysisPort, chunk_repo: IChunkRepository) -> None:
        self._openai = openai
        self._chunk_repo = chunk_repo

    async def retrieve(self, user_id: int, query: str, top_k: int = 10) -> list[dict]:
        """Dense + LLM Keyword Overlap 하이브리드 검색.

        DB는 recall_k로 넓게 조회 후 keyword rescoring → intent boost → link_id dedupe
        → score cutoff → 최종 top_k 반환.
        """
        [embedding] = await self._openai.embed([query])
        recall_k = min(max(top_k * _RECALL_MULTIPLIER, _MIN_RECALL_K), _MAX_RECALL_K)
        results = await self._chunk_repo.search_similar(user_id, embedding, recall_k, query_text=query)
        rescored = _rescore_with_keywords(results, query)
        deduped = _dedupe_by_link(rescored)
        if _has_hiring_intent(query):
            boosted = _apply_intent_boosts(deduped, query)
            return _apply_score_cutoff(boosted)[:top_k]
        return deduped[:top_k]


def _build_query_variants(query: str) -> list[str]:
    """원문 + 공백제거본 + bi-gram 결합본으로 query 변형 생성.

    예: "하나 증권 공고" → ["하나 증권 공고", "하나증권공고", "하나증권 공고", "하나 증권공고"]
    """
    base = query.strip()
    variants = [base]

    compact = "".join(base.split())
    if compact and compact not in variants:
        variants.append(compact)

    tokens = base.split()
    for i in range(len(tokens) - 1):
        combined = tokens[i] + tokens[i + 1]
        variant = " ".join(tokens[:i] + [combined] + tokens[i + 2:])
        if variant not in variants:
            variants.append(variant)

    return variants


def _token_matches(query_token: str, keyword: str) -> bool:
    """부분 문자열 포함 여부. query_token이 keyword 안에 있는 방향만 허용.

    keyword in query_token 방향은 compact variant에서 과도한 boost를 유발하므로 제외.
    예: "공고" in "채용공고" → 허용 / "하나증권" in "하나증권공고" → 차단
    """
    q = query_token.lower()
    k = keyword.lower()
    if q == k:
        return True
    if len(q) >= 2 and q in k:
        return True
    return False


def _rescore_with_keywords(results: list[dict], query: str) -> list[dict]:
    """dense_score + keyword overlap으로 final_score 재산출 후 내림차순 정렬.

    query 변형(원문/공백제거/bi-gram)별 overlap 중 최댓값을 사용.
    """
    all_token_sets = [
        {t.lower() for t in v.split() if t}
        for v in _build_query_variants(query)
    ]
    if not any(all_token_sets):
        return results

    rescored = []
    for r in results:
        dense_score = r.get("dense_score", r.get("similarity", 0))
        keyword_weight = (
            _KEYWORD_WEIGHT_JINA if r.get("content_source") == "jina"
            else _KEYWORD_WEIGHT_OG
        )

        overlap = 0.0
        raw_keywords = r.get("keywords")
        if raw_keywords:
            try:
                parsed = json.loads(raw_keywords)
                if not isinstance(parsed, list):
                    parsed = []
                link_keywords = [k.lower() for k in parsed if isinstance(k, str) and k.strip()]
                best_overlap = 0.0
                for query_tokens in all_token_sets:
                    if not query_tokens:
                        continue
                    matched = sum(
                        1 for qt in query_tokens
                        if any(_token_matches(qt, kw) for kw in link_keywords)
                    )
                    variant_overlap = matched / len(query_tokens)
                    if variant_overlap > best_overlap:
                        best_overlap = variant_overlap
                overlap = best_overlap
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        final_score = dense_score * (1 - keyword_weight) + overlap * keyword_weight
        rescored.append({**r, "similarity": round(final_score, 4)})

    return sorted(rescored, key=lambda x: x["similarity"], reverse=True)


def _dedupe_by_link(results: list[dict]) -> list[dict]:
    """link_id 기준 중복 제거, 최고 점수 청크 유지."""
    best_by_link: dict[int, dict] = {}
    for r in results:
        link_id = r.get("link_id")
        if link_id is None:
            continue
        prev = best_by_link.get(link_id)
        if prev is None or r.get("similarity", 0) > prev.get("similarity", 0):
            best_by_link[link_id] = r
    return sorted(best_by_link.values(), key=lambda x: x.get("similarity", 0), reverse=True)


def _apply_intent_boosts(results: list[dict], query: str) -> list[dict]:
    """채용 의도 질의에서 Career/채용성 키워드 결과에 소폭 가산점 적용."""
    boosted = []
    for r in results:
        bonus = 0.0
        category = (r.get("category") or "").lower()
        if category == "career":
            bonus += _HIRING_CATEGORY_BOOST

        title = (r.get("title") or "").lower()
        hiring_match = any(term in title for term in _HIRING_RESULT_TERMS)

        raw_keywords = r.get("keywords")
        if raw_keywords and not hiring_match:
            try:
                parsed = json.loads(raw_keywords)
                if isinstance(parsed, list):
                    keywords = {k.lower() for k in parsed if isinstance(k, str) and k.strip()}
                    hiring_match = any(
                        any(_token_matches(term, kw) for kw in keywords)
                        for term in _HIRING_RESULT_TERMS
                    )
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        if hiring_match:
            bonus += _HIRING_TERM_BOOST

        boosted.append({**r, "similarity": round(r.get("similarity", 0) + bonus, 4)})

    return sorted(boosted, key=lambda x: x.get("similarity", 0), reverse=True)


def _apply_score_cutoff(results: list[dict]) -> list[dict]:
    """상위 결과와 점수 차이가 큰 tail noise를 제거."""
    if not results:
        return results

    top_score = results[0].get("similarity", 0)
    threshold = max(_MIN_RESULT_SIMILARITY, top_score * _RELATIVE_RESULT_RATIO)

    kept = [results[0]]
    for r in results[1:]:
        if r.get("similarity", 0) >= threshold:
            kept.append(r)
    return kept


def _has_hiring_intent(query: str) -> bool:
    query_tokens = {
        token.lower()
        for variant in _build_query_variants(query)
        for token in variant.split()
        if token
    }
    return bool(_HIRING_INTENT_TERMS & query_tokens)
