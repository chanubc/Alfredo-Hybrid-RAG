"""Phase B: ChunkRepository FTS integration tests.

Verifies that save_chunks and search_similar use morpheme_tokenize so that
Korean compound words produce meaningful tsvector tokens instead of single
unsplit tokens.

RED tests: will FAIL until chunk_repository.py is updated to call morpheme_tokenize.
"""

from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest

from app.infrastructure.repository.chunk_repository import ChunkRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_repo() -> tuple[ChunkRepository, AsyncMock]:
    """Return a ChunkRepository with a mocked AsyncSession."""
    db = AsyncMock()
    db.execute = AsyncMock()
    repo = ChunkRepository(db)
    return repo, db


# ---------------------------------------------------------------------------
# save_chunks: tsvector must use morpheme_tokenize
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_chunks_passes_morpheme_content_to_tsvector():
    """save_chunks must pass morpheme_tokenize(content) to the tsvector column.

    Before Phase B:
      SQL param ':content' is used directly → to_tsvector('simple', '채용공고')
      '채용공고' stored as a single token → queries for '채용' or '공고' won't match.

    After Phase B:
      morpheme_tokenize('채용공고') → '채용 공고'
      SQL param ':morpheme_content' = '채용 공고'
      to_tsvector('simple', '채용 공고') → {'채용', '공고'} → queries match.
    """
    repo, db = make_repo()
    fake_embedding = [0.1] * 1536

    with patch(
        "app.infrastructure.repository.chunk_repository.morpheme_tokenize",
        return_value="채용 공고",
    ) as mock_mt:
        await repo.save_chunks(
            link_id=1,
            chunks=[("채용공고 안내문", fake_embedding)],
        )

    # morpheme_tokenize must be called with the chunk content
    mock_mt.assert_called_once_with("채용공고 안내문")

    # The params passed to db.execute must contain 'morpheme_content'
    execute_call = db.execute.call_args
    params_list = execute_call[0][1]  # positional args: (sql, params)
    assert isinstance(params_list, list) and len(params_list) == 1
    params = params_list[0]
    assert "morpheme_content" in params, (
        f"Expected 'morpheme_content' in SQL params, got: {list(params.keys())}"
    )
    assert params["morpheme_content"] == "채용 공고", (
        f"morpheme_content should be '채용 공고', got: {params['morpheme_content']}"
    )


@pytest.mark.asyncio
async def test_save_chunks_original_content_preserved():
    """save_chunks must still store original (un-tokenized) content in the content column.

    Morpheme tokenization is only for tsvector; the content column keeps original text
    so chunk_content can be returned to users verbatim.
    """
    repo, db = make_repo()
    fake_embedding = [0.1] * 1536
    original_content = "채용공고 상세 안내"

    with patch(
        "app.infrastructure.repository.chunk_repository.morpheme_tokenize",
        return_value="채용 공고 안내",
    ):
        await repo.save_chunks(
            link_id=1,
            chunks=[(original_content, fake_embedding)],
        )

    execute_call = db.execute.call_args
    params_list = execute_call[0][1]
    params = params_list[0]

    # Original content must be stored unchanged
    assert params["content"] == original_content, (
        f"content should be original '{original_content}', got: {params['content']}"
    )


# ---------------------------------------------------------------------------
# search_similar: FTS query must use morpheme_tokenize
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_similar_passes_morpheme_query_to_fts():
    """search_similar must pass morpheme_tokenize(query_text) to plainto_tsquery.

    Before Phase B:
      plainto_tsquery('simple', '채용공고를') → single token '채용공고를'
      Never matches tsvector {'채용', '공고'} → sparse_score = 0

    After Phase B:
      morpheme_tokenize('채용공고를') → '채용 공고'
      plainto_tsquery('simple', '채용 공고') → '채용' & '공고'
      Matches tsvector {'채용', '공고'} → sparse_score > 0
    """
    repo, db = make_repo()
    # Return a mock result
    mock_result = MagicMock()
    mock_result.mappings.return_value = []
    db.execute.return_value = mock_result

    query_text = "채용공고를"

    with patch(
        "app.infrastructure.repository.chunk_repository.morpheme_tokenize",
        return_value="채용 공고",
    ) as mock_mt:
        await repo.search_similar(
            user_id=1,
            query_embedding=[0.1] * 1536,
            top_k=5,
            query_text=query_text,
        )

    # morpheme_tokenize must be called with the raw query
    mock_mt.assert_called_once_with(query_text)

    # The SQL params must contain morpheme_query (not raw query_text)
    execute_call = db.execute.call_args
    params = execute_call[0][1]  # positional: (sql, params_dict)
    assert "morpheme_query" in params, (
        f"Expected 'morpheme_query' in SQL params, got: {list(params.keys())}"
    )
    assert params["morpheme_query"] == "채용 공고", (
        f"morpheme_query should be '채용 공고', got: {params.get('morpheme_query')}"
    )


@pytest.mark.asyncio
async def test_search_similar_dense_only_does_not_call_morpheme_tokenize():
    """When query_text is empty, dense-only path is used — morpheme_tokenize NOT called.

    Dense-only fallback must not break when kiwipiepy is unavailable or slow.
    """
    repo, db = make_repo()
    mock_result = MagicMock()
    mock_result.mappings.return_value = []
    db.execute.return_value = mock_result

    with patch(
        "app.infrastructure.repository.chunk_repository.morpheme_tokenize",
    ) as mock_mt:
        await repo.search_similar(
            user_id=1,
            query_embedding=[0.1] * 1536,
            top_k=5,
            query_text="",  # empty → dense-only path
        )

    mock_mt.assert_not_called()
