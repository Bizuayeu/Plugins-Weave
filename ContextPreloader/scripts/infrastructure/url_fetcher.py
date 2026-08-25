"""URL fetching and HTML text extraction."""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML, stripping tags and script/style blocks."""

    SKIP_TAGS = {"script", "style", "head"}

    def __init__(self) -> None:
        super().__init__()
        self._result: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag.lower() in ("p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"):
            self._result.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._result.append(data)

    def get_text(self) -> str:
        text = "".join(self._result)
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)


def strip_html(html: str) -> str:
    """Strip HTML tags and return clean text."""
    if not html:
        return ""
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    return extractor.get_text()


def fetch_url(url: str, timeout: int) -> tuple[str, str]:
    """Fetch a URL and return content.

    Returns:
        (content, content_type) where:
        - For text/html: content = stripped text, content_type = "text/html"
        - For text/plain: content = raw text, content_type = "text/plain"
        - For non-text: content = "", content_type = actual type
        - On error: content = error message, content_type = ""
    """
    try:
        req = Request(url, headers={"User-Agent": "ContextPreloader/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            content_type = resp.getheader("Content-Type", "").split(";")[0].strip()

            if content_type.startswith("text/"):
                raw = resp.read()
                text = raw.decode("utf-8", errors="replace")
                if "html" in content_type:
                    return strip_html(text), content_type
                return text, content_type
            else:
                return "", content_type

    except HTTPError as e:
        return f"HTTP Error {e.code}: {e.reason}", ""
    except TimeoutError:
        return "Error: Connection timed out", ""
    except URLError as e:
        return f"URL Error: {e.reason}", ""
    except Exception as e:
        return f"Error: {e}", ""
