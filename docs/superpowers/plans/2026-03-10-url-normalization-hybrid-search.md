# URL 정규화 & Hybrid Search 개선 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 트래킹 파라미터로 인한 URL 중복 저장 버그를 제거하고, 한국어에서 미동작하는 FTS sparse 컴포넌트를 LLM 키워드 기반 매칭으로 교체한다.

**Architecture:** URL 저장 진입부에서 트래킹 파라미터를 제거한 정규화 URL을 사용하고, Hybrid Search의 sparse 컴포넌트를 `plainto_tsquery('simple')` 대신 Python 레벨 keyword overlap 스코어링으로 대체한다. SQL에 `d.dense_score`와 `l.content_source` 컬럼을 추가 반환해 Python에서 재스코어링한다.

**Tech Stack:** Python 3.11+, SQLAlchemy (asyncpg), FastAPI, pytest + pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-03-10-url-normalization-hybrid-search-design.md`

---

## File Map

| 파일 | 변경 종류 | 역할 |
|---|---|---|
| `app/utils/url.py` | **신규** | `normalize_url()` — 트래킹 파라미터 제거 |
| `app/application/usecases/save_link_usecase.py` | **수정** | `execute()` 진입부에 `normalize_url()` 1줄 추가 |
| `app/infrastructure/repository/chunk_repository.py` | **수정** | `search_similar()` SQL SELECT에 `d.dense_score`, `l.content_source` 추가 |
| `app/infrastructure/rag/retriever.py` | **수정** | `retrieve()` 에 keyword overlap 재스코어링 로직 추가 |
| `tests/test_url_utils.py` | **신규** | `normalize_url()` 단위 테스트 |
| `tests/test_retriever.py` | **신규** | keyword 스코어링 단위 테스트 |

---

## Chunk 1: URL 정규화

### Task 1: `normalize_url()` 유틸 구현

**Files:**
- Create: `app/utils/url.py`
- Create: `tests/test_url_utils.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_url_utils.py
import pytest
from app.utils.url import normalize_url


def test_strips_xmt_and_slof():
    url = "https://www.threads.com/@user/post/ABC?xmt=SESSION1&slof=1"
    assert normalize_url(url) == "https://www.threads.com/@user/post/ABC"


def test_strips_utm_params():
    url = "https://example.com/article?utm_source=twitter&utm_medium=social"
    assert normalize_url(url) == "https://example.com/article"


def test_strips_fbclid():
    url = "https://example.com/page?fbclid=ABC123&id=42"
    assert normalize_url(url) == "https://example.com/page?id=42"


def test_preserves_youtube_v_param():
    url = "https://www.youtube.com/watch?v=VIDEO_ID&utm_source=share"
    result = normalize_url(url)
    assert "v=VIDEO_ID" in result
    assert "utm_source" not in result


def test_preserves_naver_blog_params():
    url = "https://blog.naver.com/post?blogId=test&logNo=123"
    result = normalize_url(url)
    assert "blogId=test" in result
    assert "logNo=123" in result


def test_no_params_unchanged():
    url = "https://example.com/article"
    assert normalize_url(url) == "https://example.com/article"


def test_strips_fragment():
    url = "https://example.com/article#section-1"
    assert normalize_url(url) == "https://example.com/article"


def test_strips_fragment_and_tracking():
    url = "https://example.com/post?utm_source=email#top"
    assert normalize_url(url) == "https://example.com/post"


def test_mixed_tracking_and_content_params():
    url = "https://example.com/search?q=python&utm_campaign=promo&page=2"
    result = normalize_url(url)
    assert "q=python" in result
    assert "page=2" in result
    assert "utm_campaign" not in result
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_url_utils.py -v
```
Expected: `ImportError: cannot import name 'normalize_url'`

- [ ] **Step 3: `app/utils/url.py` 구현**

```python
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

TRACKING_PARAMS = frozenset({
    # 소셜/광고 트래킹
    "xmt", "slof", "igsh", "igshid", "fbclid",
    # UTM
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    # 기타
    "_ga", "_gl", "source", "mc_cid", "mc_eid",
    # 트위터/X
    "t", "s",
})
# ⚠️ "ref" 제외: Amazon 등 일부 사이트에서 콘텐츠 식별에 사용됨


def normalize_url(url: str) -> str:
    """트래킹 파라미터와 fragment를 제거한 정규화 URL 반환."""
    parsed = urlparse(url)
    filtered = {
        k: v
        for k, v in parse_qs(parsed.query, keep_blank_values=True).items()
        if k.lower() not in TRACKING_PARAMS
    }
    clean_query = urlencode(filtered, doseq=True)
    return urlunparse(parsed._replace(query=clean_query, fragment=""))
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_url_utils.py -v
```
Expected: 9개 PASS

- [ ] **Step 5: 커밋**

```bash
git add app/utils/url.py tests/test_url_utils.py
git commit -m "#66 [feat] : normalize_url 유틸 구현 (트래킹 파라미터 제거)"
```

---

### Task 2: `save_link_usecase.py` 에 URL 정규화 통합

**Files:**
- Modify: `app/application/usecases/save_link_usecase.py:37`
- Modify: `tests/test_save_link_usecase.py`

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/test_save_link_usecase.py`에 아래 테스트를 추가한다.

```python
@pytest.mark.asyncio
async def test_url_normalized_before_duplicate_check(save_link_usecase, save_link_dependencies):
    """트래킹 파라미터가 제거된 URL로 중복 체크가 수행되어야 한다."""
    link_repo = save_link_dependencies["link_repo"]
    link_repo.exists_by_user_and_url.return_value = True

    dirty_url = "https://www.threads.com/@user/post/ABC?xmt=SESSION1&slof=1"
    clean_url = "https://www.threads.com/@user/post/ABC"

    await save_link_usecase.execute(telegram_id=111, url=dirty_url, memo=None)

    link_repo.exists_by_user_and_url.assert_called_once_with(111, clean_url)


@pytest.mark.asyncio
async def test_url_without_tracking_params_unchanged(save_link_usecase, save_link_dependencies):
    """트래킹 파라미터 없는 URL은 그대로 중복 체크에 사용된다."""
    link_repo = save_link_dependencies["link_repo"]
    link_repo.exists_by_user_and_url.return_value = True

    url = "https://example.com/article?id=42"
    await save_link_usecase.execute(telegram_id=111, url=url, memo=None)

    link_repo.exists_by_user_and_url.assert_called_once_with(111, url)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_save_link_usecase.py::test_url_normalized_before_duplicate_check -v
```
Expected: FAIL — `exists_by_user_and_url` called with dirty URL, not clean URL

- [ ] **Step 3: `save_link_usecase.py` 수정**

`execute()` 메서드 첫 줄에 import와 normalize 추가.

```python
# 파일 상단 import에 추가:
from app.utils.url import normalize_url

# execute() 메서드:
async def execute(self, telegram_id: int, url: str, memo: str | None = None) -> None:
    url = normalize_url(url)   # ← 이 줄만 추가
    try:
        if await self._link_repo.exists_by_user_and_url(telegram_id, url):
        ...
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_save_link_usecase.py -v
```
Expected: 전체 PASS (기존 테스트 포함)

- [ ] **Step 5: 커밋**

```bash
git add app/application/usecases/save_link_usecase.py tests/test_save_link_usecase.py
git commit -m "#66 [feat] : save_link_usecase URL 정규화 통합"
```

---

## Chunk 2: Hybrid Search 개선 (FTS → Keyword 매칭)

### Task 3: `chunk_repository.py` SQL에 `dense_score`, `content_source` 추가

**Files:**
- Modify: `app/infrastructure/repository/chunk_repository.py:55-93`

> SQL은 기존 구조를 유지하고 SELECT 항목만 추가.
> - `dense_score`: `dense` CTE 안에서 `l.content_source`와 함께 추가 (outer query에서 중복 JOIN 불필요)
> - 최종 SELECT: `d.dense_score`, `d.content_source` 참조

- [ ] **Step 1: `search_similar()` Hybrid SQL 수정 (query_text 있는 경우)**

`chunk_repository.py` hybrid SQL을 아래와 같이 수정한다. `dense` CTE에 두 컬럼을 추가하고 outer SELECT에서 `d.`로 참조.

```sql
WITH dense AS (
    SELECT
        c.id AS chunk_id,
        l.id AS link_id,
        l.title,
        l.url,
        l.summary,
        l.category,
        l.keywords,
        l.content_source,                                       -- ← 추가
        c.content AS chunk_content,
        1 - (c.embedding <=> CAST(:emb AS vector)) AS dense_score
    FROM chunks c
    JOIN links l ON c.link_id = l.id
    WHERE l.user_id = :user_id
),
sparse AS (
    SELECT
        c.id AS chunk_id,
        ts_rank(c.tsv, plainto_tsquery('simple', :query_text)) AS sparse_score
    FROM chunks c
    JOIN links l ON c.link_id = l.id
    WHERE l.user_id = :user_id
      AND c.tsv IS NOT NULL
      AND c.tsv @@ plainto_tsquery('simple', :query_text)
)
SELECT
    d.link_id,
    d.title,
    d.url,
    d.summary,
    d.category,
    d.keywords,
    d.chunk_content,
    d.dense_score,                                              -- ← 추가
    d.content_source,                                           -- ← 추가
    (d.dense_score * 0.7 + COALESCE(s.sparse_score, 0) * 0.3) AS similarity
FROM dense d
LEFT JOIN sparse s ON d.chunk_id = s.chunk_id
ORDER BY similarity DESC
LIMIT :top_k
```

- [ ] **Step 1-b: Dense-only 폴백 SQL 수정 (query_text 없는 경우)**

`else` 분기의 dense-only SQL도 동일하게 수정한다.

```sql
SELECT
    l.id        AS link_id,
    l.title,
    l.url,
    l.summary,
    l.category,
    l.keywords,
    l.content_source,                                           -- ← 추가
    c.content   AS chunk_content,
    1 - (c.embedding <=> CAST(:emb AS vector)) AS dense_score, -- ← 추가
    1 - (c.embedding <=> CAST(:emb AS vector)) AS similarity
FROM chunks c
JOIN links l ON c.link_id = l.id
WHERE l.user_id = :user_id
ORDER BY c.embedding <=> CAST(:emb AS vector)
LIMIT :top_k
```

- [ ] **Step 2: 변경 사항이 기존 반환 구조를 깨지 않는지 확인**

```bash
pytest tests/ -v -k "not test_url"
```
Expected: 기존 테스트 전체 PASS (새 컬럼은 dict에 추가될 뿐 기존 키 제거 없음)

- [ ] **Step 3: 커밋**

```bash
git add app/infrastructure/repository/chunk_repository.py
git commit -m "#66 [refactor] : search_similar SQL에 dense_score, content_source 반환 추가"
```

---

### Task 4: `HybridRetriever` 에 keyword overlap 재스코어링 추가

**Files:**
- Modify: `app/infrastructure/rag/retriever.py`
- Create: `tests/test_retriever.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_retriever.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.rag.retriever import HybridRetriever


def make_retriever():
    openai = AsyncMock()
    openai.embed.return_value = [[0.1] * 5]
    chunk_repo = AsyncMock()
    return HybridRetriever(openai=openai, chunk_repo=chunk_repo), chunk_repo


@pytest.mark.asyncio
async def test_keyword_overlap_boosts_relevant_result():
    """키워드 매칭 결과가 dense-only 결과보다 높은 final_score를 받아야 한다."""
    retriever, chunk_repo = make_retriever()

    chunk_repo.search_similar.return_value = [
        {
            "link_id": 1, "title": "하나증권 AI 직무",
            "keywords": json.dumps(["하나증권", "AI직무", "채용공고", "금융", "취업"]),
            "dense_score": 0.65, "similarity": 0.455,
            "content_source": "jina",
            "url": "https://threads.com/abc", "summary": "...",
            "category": "Career", "chunk_content": "...",
        },
        {
            "link_id": 2, "title": "파이썬 로깅",
            "keywords": json.dumps(["Python", "로깅", "logging", "개발", "모범사례"]),
            "dense_score": 0.72, "similarity": 0.504,
            "content_source": "jina",
            "url": "https://wikidocs.net/abc", "summary": "...",
            "category": "Dev", "chunk_content": "...",
        },
    ]

    results = await retriever.retrieve(user_id=111, query="하나증권 관련 공고", top_k=5)

    # 하나증권 링크가 상위여야 함 (키워드 매칭 덕분에)
    assert results[0]["link_id"] == 1, "하나증권 링크가 1위여야 함"


@pytest.mark.asyncio
async def test_og_source_has_lower_keyword_weight():
    """content_source='og'인 경우 keyword_weight가 0.1로 낮아야 한다."""
    retriever, chunk_repo = make_retriever()

    chunk_repo.search_similar.return_value = [
        {
            "link_id": 1, "title": "테스트",
            "keywords": json.dumps(["하나증권", "채용"]),
            "dense_score": 0.5, "similarity": 0.35,
            "content_source": "og",
            "url": "https://example.com", "summary": "",
            "category": "Career", "chunk_content": "",
        },
    ]

    results = await retriever.retrieve(user_id=111, query="하나증권 채용", top_k=5)
    # og 가중치: 0.5 * 0.9 + 1.0 * 0.1 = 0.55
    assert abs(results[0]["similarity"] - 0.55) < 0.01


@pytest.mark.asyncio
async def test_no_keyword_match_uses_dense_only():
    """키워드 매칭 없으면 dense_score 기반으로만 정렬되어야 한다."""
    retriever, chunk_repo = make_retriever()

    chunk_repo.search_similar.return_value = [
        {
            "link_id": 1, "title": "A",
            "keywords": json.dumps(["alpha", "beta"]),
            "dense_score": 0.9, "similarity": 0.63,
            "content_source": "jina",
            "url": "https://a.com", "summary": "", "category": "AI", "chunk_content": "",
        },
        {
            "link_id": 2, "title": "B",
            "keywords": json.dumps(["gamma", "delta"]),
            "dense_score": 0.8, "similarity": 0.56,
            "content_source": "jina",
            "url": "https://b.com", "summary": "", "category": "AI", "chunk_content": "",
        },
    ]

    results = await retriever.retrieve(user_id=111, query="xyz 없는쿼리", top_k=5)
    # 키워드 매칭 없으면 dense 순서 유지
    assert results[0]["link_id"] == 1
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_retriever.py -v
```
Expected: FAIL — `HybridRetriever.retrieve()` 가 keyword 스코어링 없이 동작

- [ ] **Step 3: `retriever.py` 수정**

```python
import json
from app.domain.repositories.i_chunk_repository import IChunkRepository
from app.application.ports.ai_analysis_port import AIAnalysisPort

_KEYWORD_WEIGHT_JINA = 0.3
_KEYWORD_WEIGHT_OG   = 0.1


class HybridRetriever:
    """벡터 유사도 + LLM 키워드 기반 하이브리드 검색기."""

    def __init__(self, openai: AIAnalysisPort, chunk_repo: IChunkRepository) -> None:
        self._openai = openai
        self._chunk_repo = chunk_repo

    async def retrieve(self, user_id: int, query: str, top_k: int = 10) -> list[dict]:
        """Dense + LLM Keyword Overlap 하이브리드 검색."""
        [embedding] = await self._openai.embed([query])
        results = await self._chunk_repo.search_similar(user_id, embedding, top_k, query_text=query)
        return _rescore_with_keywords(results, query)


def _rescore_with_keywords(results: list[dict], query: str) -> list[dict]:
    """dense_score + keyword overlap으로 final_score 재산출 후 내림차순 정렬."""
    query_tokens = {t.lower() for t in query.split() if t}
    if not query_tokens:
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
                link_keywords = {k.lower() for k in json.loads(raw_keywords)}
                overlap = len(query_tokens & link_keywords) / len(query_tokens)
            except (json.JSONDecodeError, TypeError):
                pass

        final_score = dense_score * (1 - keyword_weight) + overlap * keyword_weight
        rescored.append({**r, "similarity": round(final_score, 4)})

    return sorted(rescored, key=lambda x: x["similarity"], reverse=True)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_retriever.py -v
```
Expected: 3개 PASS

- [ ] **Step 5: 전체 테스트 통과 확인**

```bash
pytest tests/ -v
```
Expected: 전체 PASS

- [ ] **Step 6: 커밋**

```bash
git add app/infrastructure/rag/retriever.py tests/test_retriever.py
git commit -m "#66 [feat] : HybridRetriever LLM 키워드 overlap 재스코어링 추가"
```

---

## 완료 체크리스트

- [ ] `normalize_url()` — 트래킹 파라미터 & fragment 제거, 콘텐츠 파라미터 보존
- [ ] `save_link_usecase` — URL 정규화 후 중복 체크 및 저장
- [ ] `chunk_repository` — `dense_score`, `content_source` SQL 반환
- [ ] `HybridRetriever` — keyword overlap 재스코어링 (jina: 0.3, og: 0.1)
- [ ] 전체 테스트 통과 (`pytest tests/ -v`)
