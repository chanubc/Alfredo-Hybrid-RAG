import pytest
from app.utils.url import normalize_url


def test_strips_xmt_and_slof():
    url = "https://www.threads.com/@user/post/ABC?xmt=SESSION1&slof=1"
    assert normalize_url(url) == "https://www.threads.com/@user/post/ABC"


def test_strips_utm_params():
    url = "https://example.com/article?utm_source=twitter&utm_medium=social"
    assert normalize_url(url) == "https://example.com/article"


def test_strips_fbclid_preserves_content_param():
    url = "https://example.com/page?fbclid=ABC123&id=42"
    result = normalize_url(url)
    assert "id=42" in result
    assert "fbclid" not in result


def test_preserves_youtube_v_param():
    url = "https://www.youtube.com/watch?v=VIDEO_ID&utm_source=share"
    result = normalize_url(url)
    assert "v=VIDEO_ID" in result
    assert "utm_source" not in result


def test_preserves_naver_blog_params():
    url = "https://blog.naver.com/post?blogId=test&logNo=123"
    result = normalize_url(url)
    assert "blogId=test" in result
    assert "logNo=123" in result


def test_no_params_unchanged():
    url = "https://example.com/article"
    assert normalize_url(url) == "https://example.com/article"


def test_strips_fragment():
    url = "https://example.com/article#section-1"
    assert normalize_url(url) == "https://example.com/article"


def test_strips_fragment_and_tracking():
    url = "https://example.com/post?utm_source=email#top"
    assert normalize_url(url) == "https://example.com/post"


def test_mixed_tracking_and_content_params():
    url = "https://example.com/search?q=python&utm_campaign=promo&page=2"
    result = normalize_url(url)
    assert "q=python" in result
    assert "page=2" in result
    assert "utm_campaign" not in result


# ── HOST_RULES 기반 도메인별 처리 ─────────────────────────────────────────────

def test_twitter_t_and_s_stripped():
    url = "https://twitter.com/user/status/123?t=ABCDEF&s=20"
    result = normalize_url(url)
    assert "t=" not in result
    assert "s=" not in result


def test_x_com_t_and_s_stripped():
    url = "https://x.com/user/status/456?t=ABCDEF&s=20&lang=ko"
    result = normalize_url(url)
    assert "t=" not in result
    assert "s=" not in result
    assert "lang=ko" in result


def test_youtube_t_timestamp_preserved():
    """YouTube ?t=90s는 콘텐츠 시작 위치이므로 보존되어야 한다."""
    url = "https://www.youtube.com/watch?v=VIDEO_ID&t=90s"
    result = normalize_url(url)
    assert "v=VIDEO_ID" in result
    assert "t=90s" in result


def test_general_site_source_preserved():
    """일반 사이트 ?source=feed는 전역 제거 대상이 아니므로 보존되어야 한다."""
    url = "https://example.com/article?source=feed&id=42"
    result = normalize_url(url)
    assert "source=feed" in result
    assert "id=42" in result


def test_hash_router_fragment_preserved():
    """SPA hash-router(#/path) fragment는 실제 라우트이므로 보존되어야 한다."""
    url = "https://app.example.com/#/post/123"
    result = normalize_url(url)
    assert "#/post/123" in result


def test_plain_anchor_fragment_stripped():
    """일반 앵커(#section-1) fragment는 제거되어야 한다."""
    url = "https://example.com/article#section-1"
    result = normalize_url(url)
    assert "#" not in result
