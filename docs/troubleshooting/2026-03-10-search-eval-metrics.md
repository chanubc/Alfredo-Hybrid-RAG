# 검색 성능 정량 평가 (Before / After)

## 문제상황

한국어 Hybrid Search 개선 작업(PR #69) 후 검색 품질이 향상됐다고 주장할 수 있었지만,
구체적인 수치 근거가 없었다.

기존에는 A/B 비교 인프라나 평가 데이터셋이 없었기 때문에
"개선됐다"는 주장을 정량적으로 뒷받침할 수 없었다.

---

## 해결방안

오프라인 평가 스크립트(`scripts/eval_retriever.py`)를 작성해
Before (Dense-only) vs After (Keyword Rescoring) 방식을 동일한 후보군에 적용하고
표준 검색 지표로 비교했다.

**평가 설계:**
- 10개 쿼리 × 5개 후보 케이스 (한국어 도메인 다양화: 금융, 개발, AI, 인프라 등)
- 각 케이스에 정답 link_id(ground truth) 명시
- Before: `dense_score` 내림차순 정렬만 적용
- After: `_rescore_with_keywords()` 적용 (recall_k 확대 + keyword overlap 재점수화)

**측정 지표:**
- **P@5** (Precision at 5): 상위 5개 결과 중 정답 비율
- **MRR** (Mean Reciprocal Rank): 첫 정답이 몇 번째에 등장하는지의 역수 평균
- **NDCG@5**: 정답 순위에 log 가중치를 적용한 품질 지표

---

## 성과

10개 케이스 기준 결과:

| 지표 | Before (Dense-only) | After (Keyword Rescoring) | 개선율 |
|------|---------------------|--------------------------|--------|
| **P@5** | 0.2600 | 0.2600 | 0% |
| **MRR** | 0.3333 | 0.9500 | **+185%** |
| **NDCG@5** | 0.5084 | 0.9390 | **+85%** |
| **1위 정확도** | 1/10 (10%) | 9/10 (90%) | **+800%** |

**해석:**
- P@5가 동일한 이유: Before에서도 정답은 5위 안에 존재했음. 문제는 순위였음.
- MRR +185%: 사용자가 첫 번째 결과에서 정답을 만날 확률이 33% → 95%로 상승.
- 1위 개선 9/10: keyword overlap이 dense score만으로는 상위권에 오르지 못했던 정답 문서를 1위로 복구.

**1위에 오르지 못한 케이스 (1건):**
- 쿼리: "스타트업 투자 시리즈A" / content_source=`og` (keyword_weight=0.1로 낮음)
- og 소스는 keyword 가중치가 낮아 dense score가 높은 비관련 문서를 이기지 못함
- 한계이자 의도된 설계: og는 메타 정보만 있어 keyword 신뢰도가 낮으므로 가중치를 낮게 유지

---

## 평가 실행 방법

```bash
# mock 데이터로 실행
python scripts/eval_retriever.py

# 실제 DB 연결 (DATABASE_URL, OPENAI_API_KEY 환경변수 필요)
python scripts/eval_retriever.py --real --user {telegram_user_id}
```

실제 DB 평가 시 `scripts/eval_retriever.py` 내 `REAL_EVAL_QUERIES` 리스트에
쿼리와 정답 URL을 채워넣으면 동일한 지표를 실데이터 기준으로 측정할 수 있다.

---

## 추가 개선 (2026-03-11)

### 문제상황

- 같은 링크의 여러 chunk가 검색 결과에 중복 등장 (link_id dedupe 없음)
- "하나 증권 공고" 같이 띄어쓰기로 입력 시 DB 키워드 "하나증권"과 exact match 실패 → keyword scoring 무효화
- "공고" 검색 시 "채용공고" 키워드와 매칭 실패 (exact set intersection 한계)

### 해결방안

1. **link_id dedupe** (`_dedupe_by_link`): 동일 링크의 청크 중 최고 점수만 유지
2. **query variant 생성** (`_build_query_variants`): 원문 + 공백제거본 + bi-gram 결합으로 변형 생성
3. **substring keyword 매칭** (`_token_matches`): query token이 keyword 안에 포함되는 방향만 허용 (역방향 제외로 false positive 방지)

### 성과 (14개 케이스 기준 — 기존 10개 + 신규 4개)

| 지표 | Dense-only | PR#68 | Today | PR#68↑ | Today 추가↑ | 누적↑ |
|------|------|------|------|------|------|------|
| **MRR** | 0.2952 | 0.7357 | **0.9286** | +149% | +26% | **+214%** |
| **NDCG@5** | 0.4737 | 0.7813 | **0.9415** | +65% | +21% | **+99%** |
| **신규 케이스 1위** | 0/4 | 0/4 | **4/4** | — | **+100%** | — |

**실서비스 검증 ("하나증권 공고" 쿼리):**
- Before: 챗GPT 자소서 1위 (오답), 하나증권 공개채용 5위, 동일 링크 중복 등장
- After: **하나증권 2026 신입사원 공개채용 1위 (60%)**, 중복 결과 제거
