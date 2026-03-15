"""Phase B: Kiwipiepy morpheme tokenization accuracy tests.

TDD criterion: before-after search accuracy improvement via morpheme tokenization.

WHY THESE TESTS EXIST:
  Phase A problem (still present):
    plainto_tsquery('simple', '채용공고를')  →  tsquery '채용공고를' (single token)
    to_tsvector('simple', '채용 공고 안내')  →  '공고' | '안내' | '채용' (3 tokens)
    '채용공고를' ∉ {'채용', '공고', '안내'}  →  sparse_score = 0  (NO MATCH)

  Phase B goal:
    morpheme_tokenize('채용공고를')          →  '채용 공고'  (Kiwi splits compound + strips particle)
    plainto_tsquery('simple', '채용 공고')  →  '채용' & '공고'
    '채용' ∈ tsvector AND '공고' ∈ tsvector →  sparse_score > 0  (MATCH ✓)

Each test documents a concrete before/after accuracy difference.
"""

import pytest

from app.infrastructure.rag.korean_utils import morpheme_tokenize


# ---------------------------------------------------------------------------
# Unit tests: morpheme_tokenize behaviour
# ---------------------------------------------------------------------------

def test_morpheme_tokenize_splits_compound_word():
    """'채용공고' (compound) → tokens contain '채용' and '공고' separately.

    Before (simple dict FTS): '채용공고' is a single unsplit token.
    After  (Kiwi):            split into nouns '채용' and '공고'.
    """
    result = morpheme_tokenize("채용공고")
    tokens = result.split()
    assert "채용" in tokens, f"'채용' not found in {tokens}"
    assert "공고" in tokens, f"'공고' not found in {tokens}"


def test_morpheme_tokenize_strips_particle_from_compound():
    """'채용공고를' (compound + particle) → contains '채용' and '공고', NOT '채용공고를'.

    Phase A handled this at keyword-matching layer.
    Phase B handles it at the FTS layer (no compound token in tsvector/tsquery).
    """
    result = morpheme_tokenize("채용공고를")
    tokens = result.split()
    assert "채용" in tokens, f"'채용' not found in {tokens}"
    assert "공고" in tokens, f"'공고' not found in {tokens}"
    # The particle-attached raw form should NOT appear as a token
    assert "채용공고를" not in tokens, "'채용공고를' should be decomposed, not kept as-is"


def test_morpheme_tokenize_simple_noun():
    """'증권에서' → '증권' (particle stripped, no split needed)."""
    result = morpheme_tokenize("증권에서")
    tokens = result.split()
    assert "증권" in tokens, f"'증권' not found in {tokens}"
    assert "증권에서" not in tokens, "particle 'ㅇ에서' should be stripped"


def test_morpheme_tokenize_preserves_english():
    """'AI 개발자를' → contains 'AI' and '개발자'.

    English tokens (tag=SL) and Korean nouns must both be preserved.
    """
    result = morpheme_tokenize("AI 개발자를")
    tokens = result.split()
    assert "AI" in tokens or "ai" in tokens.lower().split(), \
        f"'AI' not found in {tokens}"
    assert "개발자" in tokens, f"'개발자' not found in {tokens}"


def test_morpheme_tokenize_returns_string():
    """Return type is always str (space-joined tokens)."""
    assert isinstance(morpheme_tokenize("채용공고"), str)
    assert isinstance(morpheme_tokenize(""), str)


def test_morpheme_tokenize_empty_input():
    """Empty/whitespace input → empty string (no crash)."""
    assert morpheme_tokenize("") == ""
    assert morpheme_tokenize("   ") == ""


def test_morpheme_tokenize_mixed_korean_english():
    """'Python 백엔드 개발자를' → contains 'Python', '백엔드', '개발자'."""
    result = morpheme_tokenize("Python 백엔드 개발자를")
    tokens = result.split()
    assert "Python" in tokens or "python" in [t.lower() for t in tokens]
    assert "개발자" in tokens, f"'개발자' not found in {tokens}"


# ---------------------------------------------------------------------------
# Before-After FTS accuracy: simulated sparse_score improvement
# ---------------------------------------------------------------------------

def test_fts_accuracy_before_after_compound_query():
    """BEFORE vs AFTER: compound word query matching stored tsvector tokens.

    Simulates what PostgreSQL does:
      Before:
        content_tsv_tokens  = to_tsvector('simple', '채용공고 안내') → {'채용공고', '안내'}
        query_tsv_tokens    = plainto_tsquery('simple', '채용공고를') → {'채용공고를'}
        intersection        = {} → sparse_score = 0

      After:
        content_tsv_tokens  = to_tsvector('simple', morpheme_tokenize('채용공고 안내'))
                            = to_tsvector('simple', '채용 공고 안내') → {'채용', '공고', '안내'}
        query_tsv_tokens    = plainto_tsquery('simple', morpheme_tokenize('채용공고를'))
                            = plainto_tsquery('simple', '채용 공고') → {'채용', '공고'}
        intersection        = {'채용', '공고'} → sparse_score > 0
    """
    content = "채용공고 안내"
    query = "채용공고를"

    # Simulate token sets (what PostgreSQL 'simple' dict produces)
    # BEFORE: raw tokens
    content_tokens_before = set(content.split())   # {'채용공고', '안내'}
    query_tokens_before = set(query.split())        # {'채용공고를'}
    match_before = bool(content_tokens_before & query_tokens_before)

    # AFTER: morpheme-tokenized tokens
    content_tokens_after = set(morpheme_tokenize(content).split())
    query_tokens_after = set(morpheme_tokenize(query).split())
    match_after = bool(content_tokens_after & query_tokens_after)

    # Core assertion: morpheme tokenization turns a NO-MATCH into a MATCH
    assert not match_before, (
        f"Before (raw): expected NO match, got intersection="
        f"{content_tokens_before & query_tokens_before}"
    )
    assert match_after, (
        f"After (morpheme): expected MATCH, got content={content_tokens_after} "
        f"vs query={query_tokens_after}"
    )


def test_fts_accuracy_before_after_particle_query():
    """BEFORE vs AFTER: particle-attached query vs stored noun tokens.

    Content stored as: '증권 거래 플랫폼'
    Query: '증권에서'

    Before: '증권에서' ∉ {'증권', '거래', '플랫폼'} → no FTS match
    After:  morpheme_tokenize('증권에서') → '증권'
            '증권' ∈ {'증권', '거래', '플랫폼'} → FTS match
    """
    content = "증권 거래 플랫폼"
    query = "증권에서"

    content_tokens_before = set(content.split())
    query_tokens_before = set(query.split())
    match_before = bool(content_tokens_before & query_tokens_before)

    content_tokens_after = set(morpheme_tokenize(content).split())
    query_tokens_after = set(morpheme_tokenize(query).split())
    match_after = bool(content_tokens_after & query_tokens_after)

    assert not match_before, (
        f"Before: expected no match, got {content_tokens_before & query_tokens_before}"
    )
    assert match_after, (
        f"After: expected match, got content={content_tokens_after} vs query={query_tokens_after}"
    )


def test_morpheme_tokenize_precision_not_degraded():
    """Unrelated content does NOT gain false FTS matches after morpheme tokenization.

    Query: '채용공고를'  (job posting)
    Unrelated content: '파이썬 비동기 프로그래밍'  (Python async)

    Both before and after morpheme tokenization, these should NOT match.
    This guards against precision degradation.
    """
    content = "파이썬 비동기 프로그래밍"
    query = "채용공고를"

    content_tokens = set(morpheme_tokenize(content).split())
    query_tokens = set(morpheme_tokenize(query).split())

    # No meaningful overlap expected
    overlap = content_tokens & query_tokens
    assert not overlap, (
        f"False positive: unrelated content matched query. "
        f"Overlap={overlap}, content={content_tokens}, query={query_tokens}"
    )


# ---------------------------------------------------------------------------
# Recall improvement: compound query now matches compound-split content
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,content,should_match", [
    # Compound word split improves recall
    ("채용공고를", "채용 공고 안내", True),
    ("입사지원서", "입사 지원 서류 안내", True),
    # Unrelated should still not match (precision preserved)
    ("채용공고를", "파이썬 비동기 프로그래밍", False),
    ("증권에서", "파이썬 asyncio 완전 정복", False),
])
def test_morpheme_tokenize_recall_precision_table(query, content, should_match):
    """Parametrized before-after accuracy: compound queries now match split content."""
    content_tokens = set(morpheme_tokenize(content).split())
    query_tokens = set(morpheme_tokenize(query).split())
    has_match = bool(content_tokens & query_tokens)
    assert has_match == should_match, (
        f"query={query!r} content={content!r}: "
        f"expected match={should_match}, got content_tokens={content_tokens}, "
        f"query_tokens={query_tokens}"
    )
