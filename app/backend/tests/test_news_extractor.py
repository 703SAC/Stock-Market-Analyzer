"""기사 본문 추출기 테스트 (Phase 3). 네트워크 없이 주입형 fetch/extract로 검증."""

from services.news.extractor import ArticleExtractor


def test_extract_with_injected_functions():
    ext = ArticleExtractor(
        fetch_fn=lambda url: "<html>...</html>",
        extract_fn=lambda html: "  본문 텍스트  ",
    )
    assert ext.extract("https://x/1") == "본문 텍스트"


def test_empty_url_returns_none():
    ext = ArticleExtractor(fetch_fn=lambda url: "x", extract_fn=lambda h: "y")
    assert ext.extract("") is None


def test_fetch_none_returns_none():
    ext = ArticleExtractor(fetch_fn=lambda url: None, extract_fn=lambda h: "y")
    assert ext.extract("https://x/1") is None


def test_exception_is_swallowed():
    def boom(url):
        raise RuntimeError("network down")

    ext = ArticleExtractor(fetch_fn=boom, extract_fn=lambda h: "y")
    assert ext.extract("https://x/1") is None


def test_max_chars_truncation():
    ext = ArticleExtractor(
        fetch_fn=lambda url: "h",
        extract_fn=lambda h: "가" * 100,
        max_chars=10,
    )
    assert len(ext.extract("https://x/1")) == 10


def test_missing_trafilatura_returns_none_without_injection():
    # fetch_fn 미주입 + trafilatura 미설치 환경이면 None (예외 비전파)
    ext = ArticleExtractor()
    ext._lazy_trafilatura = lambda: None  # 강제 미설치 상황
    assert ext.extract("https://x/1") is None
