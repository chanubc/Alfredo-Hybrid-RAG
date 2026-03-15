"""Phase B: version marker for morpheme tokenization tsvector rebuild.

Revision ID: phase_b_0006
Revises: phase3_0005
Create Date: 2026-03-15

NOTE: This migration contains no schema changes (DDL).
The tsv column and GIN index were added in phase3_0005.

Data backfill (rebuilding tsvectors with kiwipiepy) is handled by a
separate script to avoid blocking app startup:

    python scripts/backfill_morpheme_tsvectors.py

On fresh installations there are no existing chunks, so backfill is
unnecessary — new chunks are tokenized at insert time via
chunk_repository.save_chunks().
"""

from __future__ import annotations

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "phase_b_0006"
down_revision: Union[str, None] = "phase3_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass  # Data backfill handled by scripts/backfill_morpheme_tsvectors.py


def downgrade() -> None:
    pass  # No schema changes to revert
