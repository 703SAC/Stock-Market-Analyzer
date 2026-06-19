"""기사 본문 추출기 (Trafilatura).

원칙: trafilatura는 선택적 의존성으로 지연 import 한다. 미설치/네트워크 실패 시
예외를 던지지 않고 None을 반환하여 파이프라인이 멈추지 않게 한다(가용성 우선).
테스트는 fetcher/extractor를 주입하여 네트워크 없이 검증한다.
"""

from __future__ import annotations

from typing import Callable


class ArticleExtractor:
    """URL → 본문 텍스트. fetch_fn/extract_fn 주입 가능(테스트/대체용)."""

    def __init__(
        self,
        fetch_fn: Callable[[str], str | None] | None = None,
        extract_fn: Callable[[str], str | None] | None = None,
        max_chars: int = 4000,
    ):
        self._fetch_fn = fetch_fn
        self._extract_fn = extract_fn
        self._max_chars = max_chars

    def _lazy_trafilatura(self):
        try:
            import trafilatura  # noqa: PLC0415

            return trafilatura
        except Exception:
            return None

    def extract(self, url: str) -> str | None:
        """본문 추출. 실패 시 None(예외 비전파)."""
        if not url:
            return None
        try:
            if self._fetch_fn is not None:
                downloaded = self._fetch_fn(url)
            else:
                tf = self._lazy_trafilatura()
                if tf is None:
                    return None
                downloaded = tf.fetch_url(url)
            if not downloaded:
                return None

            if self._extract_fn is not None:
                text = self._extract_fn(downloaded)
            else:
                tf = self._lazy_trafilatura()
                if tf is None:
                    return None
                text = tf.extract(downloaded, include_comments=False, include_tables=False)
            if not text:
                return None
            text = text.strip()
            return text[: self._max_chars] if self._max_chars else text
        except Exception:
            return None
