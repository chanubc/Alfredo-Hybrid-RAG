# Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 대시보드 UX 개선 — 불필요한 탭/사이드바 제거, 트렌드 탭 시각화 강화, 홈 탭 정리

**Architecture:**
- 탭 구조: 🏠 홈 | 📈 트렌드 | 🔍 탐색 (보관함 제거, 탐색 맨 우측)
- 사이드바 제거 → `advanced` 파라미터 전체 제거
- 트렌드 탭: Drift Radar + Reactivation Debugger + PCA Knowledge Universe 항상 표시
- 홈 탭: 오늘 추천글 → 탐색 탭으로 이동, 링크 버튼 → 하이퍼링크

**Tech Stack:** Streamlit, Plotly, Pandas, scikit-learn (PCA)

---

## Chunk 1: 레이아웃 리팩토링 (app.py + home_tab.py)

### Task 1: app.py — 사이드바 제거 + 탭 재배치

**Files:**
- Modify: `dashboard/app.py`

현재 탭 순서: 홈 | 탐색 | 트렌드 | 보관함
변경 후 탭 순서: 홈 | 트렌드 | 탐색

- [ ] **Step 1: `app.py` 수정**

  `library_tab` import 제거, 사이드바 블록 제거, 탭 3개로 재배치:

  ```python
  from dashboard.tabs import discover_tab, home_tab, trends_tab

  # 사이드바 블록 전체 삭제 (with st.sidebar: 블록)

  st.title("📊 나의 지식 대시보드")

  tab1, tab2, tab3 = st.tabs(["🏠 홈", "📈 트렌드", "🔍 탐색"])

  with tab1:
      home_tab.render(client)

  with tab2:
      trends_tab.render()

  with tab3:
      discover_tab.render(client)
  ```

- [ ] **Step 2: 커밋**

  ```bash
  git add dashboard/app.py
  git commit -m "#N [refactor]: remove sidebar and reorganize tabs"
  ```

---

### Task 2: home_tab.py — 추천글 섹션 제거 + 링크 하이퍼링크 + advanced 제거

**Files:**
- Modify: `dashboard/tabs/home_tab.py`

현재:
- `render(client, advanced)` 시그니처
- 오늘 읽으면 좋은 글 섹션 (top3 카드)
- `_render_recommendation_card`에서 `st.link_button("🔗", url)` 사용
- Advanced drift expander

변경 후:
- `render(client)` 시그니처 (advanced 제거)
- 오늘 추천글 섹션 제거 (→ discover_tab으로 이동)
- Advanced expander 제거
- `reactivation` API 호출 제거 (홈에서 더 이상 불필요)

- [ ] **Step 1: `home_tab.py` 수정**

  ```python
  # import에서 cached_get_reactivation 제거
  from dashboard.api_client import (
      DashboardAPIClient,
      cached_get_drift,
      cached_get_graph_view,
      cached_get_stats,
  )

  def render(client: DashboardAPIClient) -> None:
      jwt_token: str = st.session_state["jwt_token"]
      with st.spinner("로딩 중..."):
          try:
              stats = cached_get_stats(jwt_token)
              drift = cached_get_drift(jwt_token)
              graph = cached_get_graph_view(jwt_token)
          except Exception as e:
              logger.error(f"Home tab data load failed: {e}")
              st.error(f"데이터 로딩 실패: {e}")
              return

      tvd = drift.get("tvd", 0.0)
      delta = drift.get("delta", {})
      analysis_text = _drift_to_text(tvd, delta)
      st.info(f"🧠 **나의 관심사 분석** — {analysis_text}")

      st.subheader("🕸 지식 그래프")
      st.caption("카테고리와 저장한 링크 관계를 시각화합니다. 읽음 처리는 텔레그램에서만 가능합니다.")
      _render_graph_view(graph)

      st.divider()

      st.subheader("📊 이번 주 요약")
      col1, col2 = st.columns(2)
      with col1:
          st.metric("이번 주 저장", f"{stats.get('this_week_count', 0)}개")
          st.metric("전체 저장", f"{stats.get('total', 0)}개")
      with col2:
          read_ratio = stats.get("read_ratio", 0)
          st.metric("읽음률", f"{read_ratio:.0%}")
          top_cat = stats.get("top_category") or "-"
          st.metric("최다 카테고리", top_cat)
  ```

  `_render_recommendation_card` 함수 전체 삭제 (더 이상 사용 안 함)

- [ ] **Step 2: 커밋**

  ```bash
  git add dashboard/tabs/home_tab.py
  git commit -m "#N [refactor]: remove recommendation section and advanced toggle from home tab"
  ```

---

## Chunk 2: 탐색 탭 — 오늘의 추천글 섹션 추가

### Task 3: discover_tab.py — 오늘 읽으면 좋은 글 섹션 추가 + 카드 하이퍼링크

**Files:**
- Modify: `dashboard/tabs/discover_tab.py`

추가할 섹션:
- 탭 상단에 "🔥 오늘 읽으면 좋은 글" 섹션 (reactivation top3)
- 링크 버튼 → 하이퍼링크 (`st.markdown(f"**[{title}]({url})**")`)

- [ ] **Step 1: import 추가 및 섹션 추가**

  ```python
  # import 추가
  from dashboard.api_client import DashboardAPIClient, cached_get_reactivation
  ```

  `render()` 함수 상단에 추가:

  ```python
  # ── 오늘 읽으면 좋은 글 ───────────────────────────────────────
  st.subheader("🔥 오늘 읽으면 좋은 글")
  st.caption("최근 관심사 기반으로 오래 묵혀둔 글을 추천합니다")

  jwt_token: str = st.session_state["jwt_token"]
  with st.spinner("추천 로딩 중..."):
      try:
          reactivation = cached_get_reactivation(jwt_token)
      except Exception as e:
          logger.error(f"Reactivation load failed: {e}")
          st.error(f"로딩 실패: {e}")
          reactivation = {}

  top3 = reactivation.get("items", [])[:3]
  if not top3:
      st.info("재활성화 후보가 없습니다. 링크를 더 저장하거나 3일 후에 다시 확인하세요.")
  else:
      for link in top3:
          _render_recommendation_card(link)

  st.divider()
  ```

- [ ] **Step 2: `_render_recommendation_card` 함수 추가**

  ```python
  def _render_recommendation_card(link: dict) -> None:
      with st.container(border=True):
          url = link.get("url")
          title = link.get("title", "제목 없음")
          cat = link.get("category", "")
          summary = link.get("summary", "")
          similarity = link.get("similarity", 0)
          recency = link.get("recency", 0)

          if similarity * 0.6 >= recency * 0.4:
              reason = "✨ 최근 관심사와 유사한 글"
          else:
              reason = "🕐 오랫동안 읽지 않은 글"

          if url:
              st.markdown(f"**[{title}]({url})**")
          else:
              st.markdown(f"**{title}**")
          st.caption(f"{cat}  ·  {reason}")
          if summary:
              st.write(summary[:120] + ("..." if len(summary) > 120 else ""))
  ```

- [ ] **Step 3: 기존 카드 함수 하이퍼링크로 변경**

  `_render_result_card` 수정:
  ```python
  def _render_result_card(r: dict) -> None:
      with st.container(border=True):
          url = r.get("url")
          title = r.get("title", "제목 없음")
          if url:
              st.markdown(f"**[{title}]({url})**")
          else:
              st.markdown(f"**{title}**")
          st.caption(r.get("category", ""))
          chunk = r.get("chunk_content", "")
          if chunk:
              st.write(chunk[:150] + ("..." if len(chunk) > 150 else ""))
  ```

  `_render_forgotten_card` 수정:
  ```python
  def _render_forgotten_card(item: dict) -> None:
      with st.container(border=True):
          url = item.get("url")
          title = item.get("title", "제목 없음")
          if url:
              st.markdown(f"**[{title}]({url})**")
          else:
              st.markdown(f"**{title}**")
          created = item.get("created_at", "")[:10]
          st.caption(f"{item.get('category', '')}  ·  저장일 {created}")
          summary = item.get("summary", "")
          if summary:
              st.write(summary[:120] + ("..." if len(summary) > 120 else ""))
  ```

- [ ] **Step 4: 커밋**

  ```bash
  git add dashboard/tabs/discover_tab.py
  git commit -m "#N [feat]: add recommendation section and hyperlink cards to discover tab"
  ```

---

## Chunk 3: 트렌드 탭 전면 개선

### Task 4: trends_tab.py — 3개 시각화 추가 + advanced 제거

**Files:**
- Modify: `dashboard/tabs/trends_tab.py`

변경 사항:
- `render(advanced)` → `render()` (advanced 파라미터 제거)
- Drift Radar 항상 표시 (Advanced 조건 제거)
- Reactivation Debugger 새 섹션 추가
- PCA Knowledge Universe 항상 표시 (Advanced 조건 제거)
- 기존 통계 섹션 (월별 추이, 카테고리 분포, 키워드, 읽기 습관) 유지

**새 탭 구조:**
1. 📈 Interest Drift (Radar Chart)
2. 🔁 Reactivation Debugger (DataFrame 랭킹)
3. 🌌 Knowledge Universe (PCA Scatter)
4. 📅 월별 저장 추이 (기존)
5. 🗂 카테고리 분포 (기존)
6. 🔑 나의 관심 키워드 (기존)
7. 📖 읽기 습관 (기존)

- [ ] **Step 1: import 및 시그니처 변경**

  ```python
  """📈 트렌드 탭 — 관심사 시각화 + 소비 패턴."""
  import pandas as pd
  import plotly.express as px
  import plotly.graph_objects as go
  import streamlit as st

  from dashboard.api_client import (
      cached_get_drift,
      cached_get_embeddings,
      cached_get_reactivation,
      cached_get_stats,
  )
  from dashboard.logger import logger


  def render() -> None:
      jwt_token: str = st.session_state["jwt_token"]
      with st.spinner("데이터 로딩 중..."):
          try:
              stats = cached_get_stats(jwt_token)
              drift = cached_get_drift(jwt_token)
              embeddings = cached_get_embeddings(jwt_token)
              reactivation = cached_get_reactivation(jwt_token)
          except Exception as e:
              logger.error(f"Trends tab data load failed: {e}")
              st.error(f"데이터 로딩 실패: {e}")
              return
  ```

- [ ] **Step 2: Interest Drift Radar 섹션 (항상 표시)**

  ```python
  # ── Interest Drift ────────────────────────────────────────────
  st.subheader("📈 Interest Drift — 관심사 변화")
  st.caption("최근 7일 vs 7~30일 전 카테고리 분포 비교")

  current_dist = drift.get("current_distribution", {})
  past_dist = drift.get("past_distribution", {})
  tvd = drift.get("tvd", 0)
  delta = drift.get("delta", {})
  all_cats = sorted(set(list(current_dist.keys()) + list(past_dist.keys())))

  if all_cats:
      stability_label = "급격한 변화" if tvd > 0.3 else "서서히 이동 중" if tvd > 0.1 else "안정적"
      st.metric("TVD (관심사 변화량)", f"{tvd:.3f}", help="0에 가까울수록 안정, 0.3 이상이면 급변")
      st.caption(f"현재 상태: **{stability_label}**")

      fig_radar = go.Figure()
      fig_radar.add_trace(go.Scatterpolar(
          r=[current_dist.get(c, 0) for c in all_cats] + [current_dist.get(all_cats[0], 0)],
          theta=all_cats + [all_cats[0]],
          fill="toself", name="최근 7일", line_color="royalblue",
      ))
      fig_radar.add_trace(go.Scatterpolar(
          r=[past_dist.get(c, 0) for c in all_cats] + [past_dist.get(all_cats[0], 0)],
          theta=all_cats + [all_cats[0]],
          fill="toself", name="7~30일 전", opacity=0.5, line_color="tomato",
      ))
      fig_radar.update_layout(
          polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
          height=380,
          margin=dict(t=40, b=20),
      )
      st.plotly_chart(fig_radar, use_container_width=True)

      if delta:
          df_delta = pd.DataFrame([
              {"카테고리": k, "변화량": round(v, 3), "방향": "▲ 증가" if v > 0 else "▼ 감소"}
              for k, v in sorted(delta.items(), key=lambda x: x[1], reverse=True)
              if abs(v) > 0.01
          ])
          if not df_delta.empty:
              st.dataframe(df_delta, use_container_width=True, hide_index=True)
  else:
      st.info("분석할 데이터가 부족합니다. 링크를 더 저장해주세요.")

  st.divider()
  ```

- [ ] **Step 3: Reactivation Debugger 섹션**

  ```python
  # ── Reactivation Debugger ─────────────────────────────────────
  st.subheader("🔁 Reactivation Debugger — 추천 알고리즘 투명성")
  st.caption("Score = (유사도 × 0.6) + (시간 감쇠 × 0.4) 공식으로 오늘의 추천 순위를 계산합니다")

  items = reactivation.get("items", [])
  if items:
      df_rank = pd.DataFrame([
          {
              "순위": idx + 1,
              "제목": item.get("title", "")[:40],
              "카테고리": item.get("category", ""),
              "유사도": round(item.get("similarity", 0), 3),
              "시간감쇠": round(item.get("recency", 0), 3),
              "최종점수": round(item.get("score", 0), 3),
          }
          for idx, item in enumerate(items[:15])
      ])
      st.dataframe(
          df_rank,
          use_container_width=True,
          hide_index=True,
          column_config={
              "최종점수": st.column_config.ProgressColumn("최종점수", min_value=0, max_value=1),
              "유사도": st.column_config.ProgressColumn("유사도", min_value=0, max_value=1),
              "시간감쇠": st.column_config.ProgressColumn("시간감쇠", min_value=0, max_value=1),
          }
      )
      st.caption(f"총 {reactivation.get('total', 0)}개 후보 중 상위 15개 표시")
  else:
      st.info("재활성화 후보가 없습니다. 링크를 더 저장하거나 3일 후에 다시 확인하세요.")

  st.divider()
  ```

- [ ] **Step 4: Knowledge Universe (PCA Scatter) 섹션**

  ```python
  # ── Knowledge Universe ────────────────────────────────────────
  st.subheader("🌌 Knowledge Universe — 나의 지식 공간")
  pca_items = embeddings.get("items", [])
  explained = embeddings.get("explained_variance")

  if pca_items:
      caption_text = f"저장한 링크 {len(pca_items)}개를 2D 벡터 공간에 시각화"
      if explained:
          caption_text += f"  ·  설명 분산 {explained:.1%}"
      st.caption(caption_text)

      df_pca = pd.DataFrame(pca_items)
      fig_pca = px.scatter(
          df_pca, x="x", y="y",
          color="category",
          hover_name="title",
          hover_data={"x": False, "y": False},
          labels={"category": "카테고리"},
      )
      fig_pca.update_traces(marker=dict(size=8, opacity=0.75))
      fig_pca.update_layout(
          height=480,
          margin=dict(t=10, b=10),
          xaxis=dict(visible=False),
          yaxis=dict(visible=False),
      )
      st.plotly_chart(fig_pca, use_container_width=True)
  else:
      st.info("임베딩 데이터가 3개 이상이어야 Knowledge Universe 시각화가 가능합니다.")

  st.divider()
  ```

- [ ] **Step 5: 기존 통계 섹션 유지 (시그니처만 변경)**

  기존 코드에서 `if advanced:` 블록만 제거하고 나머지 통계 섹션 유지

- [ ] **Step 6: 커밋**

  ```bash
  git add dashboard/tabs/trends_tab.py
  git commit -m "#N [feat]: redesign trends tab with drift radar, reactivation debugger, and knowledge universe"
  ```

---

## 완료 확인

- [ ] `dashboard/app.py`: 탭 3개 (홈|트렌드|탐색), 사이드바 없음
- [ ] `dashboard/tabs/home_tab.py`: `render(client)` 시그니처, 추천글 섹션 없음
- [ ] `dashboard/tabs/discover_tab.py`: 상단에 오늘 추천글 섹션, 하이퍼링크 카드
- [ ] `dashboard/tabs/trends_tab.py`: `render()` 시그니처, 3개 시각화 항상 표시
- [ ] `dashboard/tabs/library_tab.py`: 파일 잔존 (import만 제거, 파일 삭제 선택 사항)
- [ ] `streamlit run dashboard/app.py` 실행 후 UI 확인
