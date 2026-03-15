"""Backfill chunk tsvectors with kiwipiepy morpheme tokenization.

One-time script to rebuild existing chunks' tsv column using morpheme-split tokens.
New chunks are tokenized at insert time, so this only needs to run once on
servers that had chunks before Phase B was deployed.

Usage:
    python scripts/backfill_morpheme_tsvectors.py

Safe to run multiple times (idempotent).
"""

from __future__ import annotations

import os
import sys

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from dotenv import load_dotenv

load_dotenv()

_BATCH_SIZE = 500


def _make_kiwi():
    try:
        from kiwipiepy import Kiwi  # type: ignore[import]
    except ImportError:
        raise ImportError("kiwipiepy is required. Run: pip install kiwipiepy")
    return Kiwi()


def _tokenize(kiwi, text: str) -> str:
    tokens = kiwi.tokenize(text)
    return " ".join(
        t.form for t in tokens
        if t.tag.startswith(("NN", "VV", "SL", "XR"))
    )


def main() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    # asyncpg URL → sync psycopg2-compatible URL
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    engine = sa.create_engine(sync_url)
    kiwi = _make_kiwi()

    with engine.connect() as conn:
        total = conn.execute(sa.text("SELECT COUNT(*) FROM chunks")).scalar() or 0
        if total == 0:
            print("No chunks to backfill.")
            return

        print(f"Backfilling {total} chunks...")
        last_id = 0
        updated = 0

        while True:
            rows = conn.execute(
                sa.text(
                    "SELECT id, content FROM chunks "
                    "WHERE id > :last_id ORDER BY id LIMIT :lim"
                ),
                {"last_id": last_id, "lim": _BATCH_SIZE},
            ).fetchall()

            if not rows:
                break

            params = [
                {"mc": _tokenize(kiwi, row.content or ""), "id": row.id}
                for row in rows
            ]
            conn.execute(
                sa.text("UPDATE chunks SET tsv = to_tsvector('simple', :mc) WHERE id = :id"),
                params,
            )
            conn.commit()

            updated += len(rows)
            last_id = rows[-1].id
            print(f"  {updated}/{total} done...")

        conn.execute(sa.text("ANALYZE chunks"))
        conn.commit()

    print(f"Done. {updated} chunks updated.")


if __name__ == "__main__":
    main()
