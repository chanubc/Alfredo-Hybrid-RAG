"""📈 트렌드 탭 — 소비 패턴 시각화."""
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.api_client import cached_get_stats
from dashboard.logger import logger


def render() -> None:
    jwt_token: str = st.session_state["jwt_token"]
    with st.spinner("통계 로딩 중..."):
        try:
            stats = cached_get_stats(jwt_token)
        except Exception as e:
            logger.error(f"Trends tab data load failed: {e}")
            st.error(f"데이터 로딩 실패: {e}")
            return

    # ── 월별 저장 추이 ────────────────────────────────────────────
    st.subheader("📅 월별 저장 추이")
    monthly = stats.get("monthly_series", [])
    if monthly:
        df_monthly = pd.DataFrame(monthly)
        fig = px.line(
            df_monthly, x="month", y="count",
            markers=True, labels={"month": "월", "count": "저장 수"},
        )
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("아직 데이터가 부족합니다.")

    st.divider()

    # ── 카테고리 분포 ─────────────────────────────────────────────
    st.subheader("🗂 카테고리 분포")
    cat_dist = stats.get("category_dist", [])
    if cat_dist:
        df_cat = pd.DataFrame(cat_dist)
        fig2 = px.bar(
            df_cat, x="category", y="count",
            labels={"category": "카테고리", "count": "링크 수"},
            color="category",
        )
        fig2.update_layout(height=280, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("아직 데이터가 부족합니다.")

    st.divider()

    # ── 상위 키워드 ───────────────────────────────────────────────
    st.subheader("🔑 나의 관심 키워드 Top 20")
    keywords = stats.get("top_keywords", [])
    if keywords:
        df_kw = pd.DataFrame(keywords[:20])
        fig3 = px.bar(
            df_kw, x="count", y="keyword",
            orientation="h",
            labels={"keyword": "", "count": "빈도"},
        )
        fig3.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("키워드 데이터가 없습니다.")

    st.divider()

    # ── 읽기 습관 ─────────────────────────────────────────────────
    st.subheader("📖 읽기 습관")
    col1, col2 = st.columns(2)
    with col1:
        total = stats.get("total", 0)
        unread = stats.get("unread_count", 0)
        st.metric("전체 저장", f"{total}개")
        st.metric("미열람", f"{unread}개")
    with col2:
        read_ratio = stats.get("read_ratio", 0)
        this_month = stats.get("this_month_count", 0)
        st.metric("읽음률", f"{read_ratio:.0%}")
        st.metric("이번 달 저장", f"{this_month}개")

