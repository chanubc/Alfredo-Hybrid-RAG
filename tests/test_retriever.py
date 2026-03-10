import json
import pytest
from unittest.mock import AsyncMock
from app.infrastructure.rag.retriever import HybridRetriever


def make_retriever():
    openai = AsyncMock()
    openai.embed.return_value = [[0.1] * 5]
    chunk_repo = AsyncMock()
    return HybridRetriever(openai=openai, chunk_repo=chunk_repo), chunk_repo


def _make_result(link_id, title, keywords, dense_score, content_source="jina"):
    return {
        "link_id": link_id,
        "title": title,
        "keywords": json.dumps(keywords),
        "dense_score": dense_score,
        "similarity": dense_score * 0.7,
        "content_source": content_source,
        "url": f"https://example.com/{link_id}",
        "summary": "",
        "category": "AI",
        "chunk_content": "",
    }


@pytest.mark.asyncio
async def test_keyword_overlap_boosts_relevant_result():
    """키워드 매칭 결과가 dense-only 결과보다 높은 final_score를 받아야 한다."""
    retriever, chunk_repo = make_retriever()
    chunk_repo.search_similar.return_value = [
        _make_result(1, "하나증권 AI 직무", ["하나증권", "AI직무", "채용공고", "금융", "취업"], dense_score=0.65),
        _make_result(2, "파이썬 로깅", ["Python", "로깅", "logging", "개발", "모범사례"], dense_score=0.72),
    ]

    results = await retriever.retrieve(user_id=111, query="하나증권 관련 공고", top_k=5)

    assert results[0]["link_id"] == 1, "하나증권 링크가 keyword 매칭으로 1위여야 함"


@pytest.mark.asyncio
async def test_og_source_has_lower_keyword_weight():
    """content_source='og'인 경우 keyword_weight가 0.1로 낮아야 한다."""
    retriever, chunk_repo = make_retriever()
    chunk_repo.search_similar.return_value = [
        _make_result(1, "테스트", ["하나증권", "채용"], dense_score=0.5, content_source="og"),
    ]

    results = await retriever.retrieve(user_id=111, query="하나증권 채용", top_k=5)

    # og 가중치: 0.5 * 0.9 + 1.0 * 0.1 = 0.55
    assert abs(results[0]["similarity"] - 0.55) < 0.01


@pytest.mark.asyncio
async def test_jina_source_has_higher_keyword_weight():
    """content_source='jina'인 경우 keyword_weight가 0.3이어야 한다."""
    retriever, chunk_repo = make_retriever()
    chunk_repo.search_similar.return_value = [
        _make_result(1, "테스트", ["하나증권", "채용"], dense_score=0.5, content_source="jina"),
    ]

    results = await retriever.retrieve(user_id=111, query="하나증권 채용", top_k=5)

    # jina 가중치: 0.5 * 0.7 + 1.0 * 0.3 = 0.65
    assert abs(results[0]["similarity"] - 0.65) < 0.01


@pytest.mark.asyncio
async def test_no_keyword_match_preserves_dense_order():
    """키워드 매칭 없으면 dense_score 기반 순서가 유지되어야 한다."""
    retriever, chunk_repo = make_retriever()
    chunk_repo.search_similar.return_value = [
        _make_result(1, "A", ["alpha", "beta"], dense_score=0.9),
        _make_result(2, "B", ["gamma", "delta"], dense_score=0.8),
    ]

    results = await retriever.retrieve(user_id=111, query="xyz없는쿼리", top_k=5)

    assert results[0]["link_id"] == 1
    assert results[1]["link_id"] == 2


@pytest.mark.asyncio
async def test_invalid_keywords_json_handled_gracefully():
    """keywords JSON 파싱 실패 시 keyword_score=0으로 처리해야 한다."""
    retriever, chunk_repo = make_retriever()
    chunk_repo.search_similar.return_value = [
        {**_make_result(1, "테스트", [], dense_score=0.8), "keywords": "INVALID_JSON"},
    ]

    results = await retriever.retrieve(user_id=111, query="테스트", top_k=5)

    assert len(results) == 1  # 에러 없이 결과 반환
