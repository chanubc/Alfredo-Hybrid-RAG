# Non-Kiwi BM25-style sparse recall path

## Why this exists

Kiwi rollback restored the pre-PR95 `simple`-FTS pipeline, but that also removed the
extra Korean morpheme recall we had briefly relied on. Dense recall + keyword/title
rescoring still handles many cases, yet lexical intent-heavy queries such as
`채용공고 링크` can under-rank the right link when the dense candidate set is noisy.

This patch adds a **non-Kiwi sparse recall path** that keeps the existing
`chunks.tsv` index and does not introduce a new dependency.

## Design

1. `HybridRetriever.retrieve()` still fetches the dense hybrid chunk path and OG path.
2. In parallel, it now also calls `ChunkRepository.search_sparse_candidates()`.
3. That path:
   - reuses `_build_query_variants(query)`
   - queries the existing `chunks.tsv` index with those variants
   - ranks chunk hits with `ts_rank_cd(..., 32)`
   - returns the top lexical candidates for the normal Python rescoring/dedupe flow

So the retrieval stack is now:

- dense + FTS hybrid chunk path
- **non-Kiwi BM25-style lexical recall path**
- OG summary embedding path
- keyword/title overlap rescoring
- link-level dedupe + score cutoff

## Why this is safe

- No new dependency
- No schema migration
- No Kiwi-specific tokenization
- Uses the existing `chunks.tsv` index, so the extra recall path stays index-backed
- Runs in parallel with the other DB paths to limit latency regression

## Expected effect

- Better recall for lexical Korean queries where the right document is present in `chunks.tsv`
- Better ranking for exact-intent queries like `채용공고 링크`
- Existing particle/substring keyword logic still handles compound/attached-token cases

## Verification checklist

Run:

```bash
pytest tests/test_chunk_repository_fts.py tests/test_retriever.py
pytest tests/test_retriever_quality.py
```

Look for:

- sparse lexical SQL shape coverage
- retriever regression for the new BM25-style path
- no ranking regression for the existing OG/dense scenarios
