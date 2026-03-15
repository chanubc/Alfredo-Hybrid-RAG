"""Korean language utilities for morpheme tokenization."""

from __future__ import annotations

_kiwi_instance = None


def _kiwi():
    """Return the shared Kiwi instance (lazy-init on first call)."""
    global _kiwi_instance
    if _kiwi_instance is None:
        from kiwipiepy import Kiwi  # type: ignore[import]
        _kiwi_instance = Kiwi()
    return _kiwi_instance


def morpheme_tokenize(text: str) -> str:
    """Tokenize Korean text into meaningful morphemes for FTS.

    Extracts nouns (NN*), verbs (VV*), and foreign words (SL) via kiwipiepy,
    returning them space-joined so PostgreSQL 'simple' dictionary can index each
    morpheme independently.

    Compound words are split and particles stripped automatically:
        morpheme_tokenize("채용공고를")       → "채용 공고"
        morpheme_tokenize("증권에서")         → "증권"
        morpheme_tokenize("AI 개발자를 채용") → "AI 개발자 채용"
        morpheme_tokenize("")                 → ""
    """
    if not text or not text.strip():
        return ""

    try:
        tokens = _kiwi().tokenize(text)
        meaningful = [
            t.form
            for t in tokens
            if t.tag.startswith(("NN", "VV", "SL", "XR"))
        ]
        return " ".join(meaningful)
    except Exception:
        # Fallback to whitespace split so FTS/keyword paths keep working
        # even if kiwipiepy is unavailable or raises unexpectedly.
        return " ".join(text.split())
