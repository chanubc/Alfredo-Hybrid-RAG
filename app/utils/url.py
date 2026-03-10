from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

TRACKING_PARAMS = frozenset({
    # 소셜/광고 트래킹
    "xmt", "slof", "igsh", "igshid", "fbclid",
    # UTM
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    # 기타
    "_ga", "_gl", "source", "mc_cid", "mc_eid",
    # 트위터/X
    "t", "s",
})
# ⚠️ "ref" 제외: Amazon 등 일부 사이트에서 콘텐츠 식별에 사용됨


def normalize_url(url: str) -> str:
    """트래킹 파라미터와 fragment를 제거한 정규화 URL 반환."""
    parsed = urlparse(url)
    filtered = {
        k: v
        for k, v in parse_qs(parsed.query, keep_blank_values=True).items()
        if k.lower() not in TRACKING_PARAMS
    }
    clean_query = urlencode(filtered, doseq=True)
    return urlunparse(parsed._replace(query=clean_query, fragment=""))
