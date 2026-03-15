"""Phase B: Rebuild chunk tsvectors with kiwipiepy morpheme tokenization.

Revision ID: phase_b_0006
Revises: phase3_0005
Create Date: 2026-03-15

WHY THIS MIGRATION EXISTS:
  Phase A stored tsvectors using to_tsvector('simple', raw_content).
  Korean compound words like '채용공고' became single unsplit tokens,
  so FTS queries for '채용' or '공고' produced sparse_score ≈ 0.

  Phase B uses kiwipiepy to pre-split compound words into morphemes before
  passing to PostgreSQL.  This migration backfills all existing chunks so
  their tsv column reflects morpheme-split tokens.

  EFFECT:
    Before: to_tsvector('simple', '채용공고 안내') → {'채용공고', '안내'}
    After:  to_tsvector('simple', '채용 공고 안내') → {'채용', '공고', '안내'}
    Queries for '채용' or '공고' now hit the GIN index → sparse_score > 0.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "phase_b_0006"
down_revision: Union[str, None] = "phase3_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _morpheme_tokenize(text: str) -> str:
    """Inline tokenizer for migration — avoids circular import with app code."""
    try:
        from kiwipiepy import Kiwi  # type: ignore[import]
        kiwi = Kiwi()
        tokens = kiwi.tokenize(text)
        return " ".join(
            t.form for t in tokens
            if t.tag.startswith(("NN", "VV", "SL", "XR"))
        )
    except Exception:
        # Fallback: return text as-is if kiwipiepy unavailable during migration
        return text


def upgrade() -> None:
    """Rebuild all existing chunk tsvectors with morpheme tokenization.

    Processes chunks in batches of 500 to avoid memory/lock issues on large tables.
    Each chunk's content is tokenized via kiwipiepy; the resulting morpheme string
    is passed to to_tsvector('simple', ...) in PostgreSQL.
    """
    conn = op.get_bind()

    # Count total chunks for progress awareness
    count_result = conn.execute(sa.text("SELECT COUNT(*) FROM chunks"))
    total = count_result.scalar() or 0

    if total == 0:
        return  # No chunks to backfill

    batch_size = 500
    offset = 0
    updated = 0

    while offset < total:
        rows = conn.execute(
            sa.text("SELECT id, content FROM chunks ORDER BY id LIMIT :lim OFFSET :off"),
            {"lim": batch_size, "off": offset},
        ).fetchall()

        if not rows:
            break

        for row in rows:
            morpheme_content = _morpheme_tokenize(row.content or "")
            conn.execute(
                sa.text(
                    "UPDATE chunks SET tsv = to_tsvector('simple', :mc) WHERE id = :id"
                ),
                {"mc": morpheme_content, "id": row.id},
            )
            updated += 1

        offset += batch_size

    # Rebuild GIN index statistics after bulk update
    conn.execute(sa.text("ANALYZE chunks"))


def downgrade() -> None:
    """Revert tsvectors to raw content (Phase A behaviour)."""
    conn = op.get_bind()

    batch_size = 500
    offset = 0

    count_result = conn.execute(sa.text("SELECT COUNT(*) FROM chunks"))
    total = count_result.scalar() or 0

    while offset < total:
        rows = conn.execute(
            sa.text("SELECT id, content FROM chunks ORDER BY id LIMIT :lim OFFSET :off"),
            {"lim": batch_size, "off": offset},
        ).fetchall()

        if not rows:
            break

        for row in rows:
            conn.execute(
                sa.text(
                    "UPDATE chunks SET tsv = to_tsvector('simple', :c) WHERE id = :id"
                ),
                {"c": row.content or "", "id": row.id},
            )

        offset += batch_size

    conn.execute(sa.text("ANALYZE chunks"))
