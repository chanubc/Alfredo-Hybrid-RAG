# Phase B: Morpheme FTS Before/After 정확도

## 📌 개요

Phase B는 **PostgreSQL FTS(Sparse) 레이어**에 kiwipiepy 형태소 분석을 적용합니다.

- **대상**: `chunks.tsv` (tsvector) 생성 + FTS 쿼리
- **핵심**: INSERT 시 `morpheme_tokenize(content)`, QUERY 시 `morpheme_tokenize(query)` — 양방향 동일 토크나이저
- **Phase A와의 차이**: Phase A는 Python keyword rescoring 레이어, Phase B는 DB FTS 레이어

---

## 개선 단계

| 단계 | FTS 레이어 | Keyword 레이어 | 설명 |
|------|-----------|--------------|------|
| **Pre-Phase A** | raw query | raw token 매칭 | 조사/복합어 모두 실패 |
| **Phase A** | raw query (0점) | morpheme 변형 + `_token_matches` | keyword만 복구 |
| **Phase B** | morpheme FTS | morpheme 변형 + `_token_matches` | FTS까지 복구 |

---

## 🔴 Phase A 잔존 문제

```
사용자 쿼리: "채용공고를"

plainto_tsquery('simple', '채용공고를') → tsquery: '채용공고를' (단일 토큰)
to_tsvector('simple', '채용 공고 안내') → '공고' | '안내' | '채용'

'채용공고를' ∉ {'채용', '공고', '안내'} → sparse_score = 0  ❌
→ Phase A가 keyword overlap으로 일부 복구했지만 FTS 레이어는 여전히 0
```

---

## 📊 실측 벤치마크 결과

> **측정 환경**: 라이브 DB (2,614 chunks), `scripts/benchmark_fts_accuracy.py`
> **Ground truth**: 쿼리 어근이 chunk content에 포함된 chunks
> **지표**: FTS+Keyword 통합 MRR (combined rank)

### 쿼리별 MRR 상세 (FTS / Keyword / Combined)

| 쿼리 | 형태소 | 관련 | FTS Pre-A | FTS Ph-A | FTS Ph-B | KW Pre-A | KW Ph-A | KW Ph-B | **Combined Pre-A** | **Combined Ph-A** | **Combined Ph-B** |
|------|--------|:---:|:---------:|:--------:|:--------:|:--------:|:-------:|:-------:|:------------------:|:-----------------:|:-----------------:|
| `채용공고를` | `채용 공고` | 114 | 0 | 0 | 1.0 | 0 | 1.0 | 1.0 | 0 | 1.0 | **1.0** |
| `개발자채용` | `개발자 채용` | 160 | 0 | 0 | 1.0 | 0 | 1.0 | 1.0 | 0 | 1.0 | **1.0** |
| `입사지원서` | `입사 지원서` | 173 | 0 | 0 | 1.0 | 0 | 1.0 | 1.0 | 0 | 1.0 | **1.0** |
| `백엔드에서` | `백 엔드`* | 4 | 0 | 0 | 1.0 | 0 | 0 | 0 | 0 | 0 | **1.0** |
| `증권에서` | `증권` | 17 | 0 | 0 | 1.0 | 0 | 1.0 | 1.0 | 0 | 1.0 | **1.0** |
| `스타트업에서의` | `스타트업` | 5 | 0 | 0 | 1.0 | 0 | 0 | 0 | 0 | 0 | **1.0** |
| `머신러닝으로` | `머신 러닝`* | 9 | 0 | 0 | 1.0 | 0 | 0 | 0 | 0 | 0 | **1.0** |
| `AI채용` | `AI 채용` | 1,481 | 0 | 0 | 1.0 | 0 | 1.0 | 1.0 | 0 | 1.0 | **1.0** |
| `Python백엔드` | `Python 백 엔드`* | 148 | 0 | 0 | 0 | 0 | 1.0 | 1.0 | 0 | 1.0 | **1.0** |
| `LLM활용` | `LLM 활용` | 142 | 0 | 0 | 1.0 | 0 | 1.0 | 1.0 | 0 | 1.0 | **1.0** |

> \* kiwipiepy가 외래어를 음절 분리 (예: `백엔드` → `백 엔드`). FTS 실패지만 keyword가 커버.

---

### 종합 지표 (FTS + Keyword Combined)

| 지표 | Pre-Phase A | Phase A | Phase B | A → B | Pre → B |
|------|:-----------:|:-------:|:-------:|:-----:|:-------:|
| **P@5** | 0.0000 | 0.5200 | **0.9000** | **+73%** | ∞ |
| **MRR** | 0.0000 | 0.7000 | **1.0000** | **+43%** | ∞ |
| **NDCG@5** | 0.0000 | 0.5562 | **0.9316** | **+67%** | ∞ |
| **Top-1 정확도** | 0/10 (0%) | 7/10 (70%) | **10/10 (100%)** | **+43%** | ∞ |

---

## 분석

### Pre-Phase A → Phase A (keyword rescoring 효과)
- FTS는 여전히 0 — DB 레이어 무변경
- keyword overlap이 morpheme 변형 덕에 0 → 0.52~0.70 확보
- **`백엔드에서`, `스타트업에서의`, `머신러닝으로`** 3개는 keyword도 실패 → 여전히 0

### Phase A → Phase B (FTS 복구 효과)
- FTS가 morpheme query를 통해 실질적 signal 제공
- keyword가 실패했던 3개 쿼리(`백엔드에서` 등)도 FTS가 커버
- **10/10 쿼리 Top-1 정확도 100%** 달성

### `Python백엔드` — 레이어 보완 사례
- FTS: `Python 백 엔드`로 분리 → 매칭 실패
- Keyword: `Python`, `백엔드` 각각 매칭 성공 → Combined 커버
- Phase B에서 FTS와 Keyword가 상호 보완하여 정확도 유지

---

## 🔧 구현 위치

```
app/infrastructure/rag/
  └── korean_utils.py
      └── morpheme_tokenize(text) → str

app/infrastructure/repository/
  └── chunk_repository.py
      ├── save_chunks: to_tsvector('simple', morpheme_tokenize(content))
      └── search_similar: plainto_tsquery('simple', morpheme_tokenize(query_text))

scripts/
  ├── backfill_morpheme_tsvectors.py   # 기존 chunks 1회 백필 (완료: 2,614건)
  └── benchmark_fts_accuracy.py        # 3단계 정확도 벤치마크
```

---

## 🧪 재측정

```bash
python scripts/benchmark_fts_accuracy.py --user-id <TELEGRAM_ID>
```

---

## 📚 관련 문서

- [Phase A: Korean Morpheme Handling](./korean-morpheme-handling.md)
- [Korean Morpheme Plan](./../.omc/plans/korean-morpheme-hybrid-search.md)
