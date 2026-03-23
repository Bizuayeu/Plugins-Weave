"""T6+T7: HTML text extraction and URL fetching tests."""
import unittest
from http.client import HTTPResponse
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from scripts.infrastructure.url_fetcher import fetch_url, strip_html


class TestStripHtml(unittest.TestCase):
    """T6: HTML text extraction."""

    def test_strip_simple_tags(self):
        self.assertEqual(strip_html("<p>Hello</p>"), "Hello")

    def test_strip_nested_tags(self):
        result = strip_html("<div><b>Bold</b> text</div>")
        self.assertIn("Bold", result)
        self.assertIn("text", result)

    def test_strip_script_style(self):
        html = "<script>var x=1;</script><style>.a{}</style><p>Keep</p>"
        result = strip_html(html)
        self.assertIn("Keep", result)
        self.assertNotIn("var x", result)
        self.assertNotIn(".a{}", result)

    def test_decode_entities(self):
        result = strip_html("&amp; &lt; &gt;")
        self.assertIn("&", result)
        self.assertIn("<", result)
        self.assertIn(">", result)

    def test_preserve_whitespace(self):
        result = strip_html("<p>A</p><p>B</p>")
        self.assertIn("A", result)
        self.assertIn("B", result)

    def test_empty_html(self):
        self.assertEqual(strip_html(""), "")


def _mock_response(data: bytes, content_type: str = "text/html", status: int = 200):
    """Create a mock HTTP response."""
    resp = MagicMock()
    resp.read.return_value = data
    resp.getheader.return_value = content_type
    resp.status = status
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestFetchUrl(unittest.TestCase):
    """T7: URL fetching with mocked network."""

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_fetch_html_page(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            b"<html><body><p>Hello World</p></body></html>", "text/html"
        )
        content, ctype = fetch_url("https://example.com", 10)
        self.assertIn("Hello World", content)
        self.assertEqual(ctype, "text/html")

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_fetch_plain_text(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            b"Plain text content", "text/plain"
        )
        content, ctype = fetch_url("https://example.com/text", 10)
        self.assertEqual(content, "Plain text content")
        self.assertEqual(ctype, "text/plain")

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_fetch_non_text(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            b"%PDF-1.4", "application/pdf"
        )
        content, ctype = fetch_url("https://example.com/doc.pdf", 10)
        self.assertEqual(ctype, "application/pdf")
        self.assertEqual(content, "")

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_fetch_404(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            "https://example.com", 404, "Not Found", {}, None
        )
        content, ctype = fetch_url("https://example.com/missing", 10)
        self.assertIn("404", content)
        self.assertEqual(ctype, "")

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_fetch_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("Connection timed out")
        content, ctype = fetch_url("https://example.com/slow", 1)
        self.assertIn("timed out", content.lower())
        self.assertEqual(ctype, "")

    @patch("scripts.infrastructure.url_fetcher.urlopen")
    def test_fetch_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Connection refused")
        content, ctype = fetch_url("https://unreachable.example.com", 10)
        self.assertIn("error", content.lower())
        self.assertEqual(ctype, "")


if __name__ == "__main__":
    unittest.main()
