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
