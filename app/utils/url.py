from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 모든 도메인에서 제거할 트래킹 파라미터
_GLOBAL_TRACKING_PARAMS = frozenset({
    # UTM
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    # 광고/소셜 트래킹
    "fbclid", "igsh", "igshid", "xmt", "slof",
    # 분석 도구
    "_ga", "_gl", "mc_cid", "mc_eid",
})

# 도메인별 추가 제거 파라미터
_HOST_RULES: dict[str, frozenset[str]] = {
    "twitter.com": frozenset({"t", "s"}),
    "x.com": frozenset({"t", "s"}),
}


def normalize_url(url: str) -> str:
    """트래킹 파라미터를 제거하고 fragment를 처리한 정규화 URL 반환.

    - 전역 트래킹 파라미터(utm_*, fbclid 등) 제거
    - 도메인별 파라미터(twitter/x의 t, s) 제거
    - hash-router fragment(#/로 시작) 보존
    - 일반 앵커 fragment(#section 등) 제거
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")

    # 도메인별 제거 대상 파라미터 결합
    drop_params = _GLOBAL_TRACKING_PARAMS | _HOST_RULES.get(host, frozenset())

    filtered = {
        k: v
        for k, v in parse_qs(parsed.query, keep_blank_values=True).items()
        if k.lower() not in drop_params
    }
    clean_query = urlencode(filtered, doseq=True)

    # hash-router(#/...)는 실제 라우트이므로 보존, 일반 앵커는 제거
    fragment = parsed.fragment if parsed.fragment.startswith("/") else ""

    return urlunparse(parsed._replace(query=clean_query, fragment=fragment))
