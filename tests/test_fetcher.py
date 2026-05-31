"""
WebWeaver - 请求器测试 / Fetcher Tests
======================================
测试HTTP请求器的各项功能。
Tests for HTTP fetcher functionality.
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from webweaver.fetcher import Fetcher, FetchResponse
from webweaver.config import CrawlerConfig


class TestFetchResponse(unittest.TestCase):
    """FetchResponse测试类 / FetchResponse test class."""

    def test_init_default(self) -> None:
        """测试默认初始化 / Test default initialization."""
        resp = FetchResponse()
        self.assertEqual(resp.url, "")
        self.assertEqual(resp.status_code, 0)
        self.assertEqual(resp.body, b"")
        self.assertFalse(resp.ok)

    def test_init_with_params(self) -> None:
        """测试带参数初始化 / Test initialization with parameters."""
        resp = FetchResponse(
            url="https://example.com",
            status_code=200,
            body=b"<html>test</html>",
            headers={"Content-Type": "text/html"},
        )
        self.assertEqual(resp.url, "https://example.com")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.content_type, "text/html")

    def test_text_property(self) -> None:
        """测试text属性 / Test text property."""
        resp = FetchResponse(body=b"hello world")
        self.assertEqual(resp.text, "hello world")

    def test_text_property_empty(self) -> None:
        """测试空body的text属性 / Test text property with empty body."""
        resp = FetchResponse(body=b"")
        self.assertEqual(resp.text, "")

    def test_ok_property(self) -> None:
        """测试ok属性 / Test ok property."""
        resp_200 = FetchResponse(status_code=200)
        self.assertTrue(resp_200.ok)

        resp_301 = FetchResponse(status_code=301)
        self.assertTrue(resp_301.ok)

        resp_404 = FetchResponse(status_code=404)
        self.assertFalse(resp_404.ok)

        resp_500 = FetchResponse(status_code=500)
        self.assertFalse(resp_500.ok)

    def test_content_length(self) -> None:
        """测试content_length属性 / Test content_length property."""
        resp = FetchResponse(body=b"hello")
        self.assertEqual(resp.content_length, 5)

    def test_to_dict(self) -> None:
        """测试to_dict方法 / Test to_dict method."""
        resp = FetchResponse(
            url="https://example.com",
            status_code=200,
            body=b"test",
        )
        d = resp.to_dict()
        self.assertEqual(d["url"], "https://example.com")
        self.assertEqual(d["status_code"], 200)
        self.assertTrue(d["ok"])
        self.assertIn("elapsed", d)

    def test_repr(self) -> None:
        """测试repr / Test repr."""
        resp = FetchResponse(url="https://example.com", status_code=200, body=b"test")
        r = repr(resp)
        self.assertIn("example.com", r)
        self.assertIn("200", r)


class TestFetcher(unittest.TestCase):
    """Fetcher测试类 / Fetcher test class."""

    def setUp(self) -> None:
        """测试前准备 / Test setup."""
        self.config = CrawlerConfig(
            timeout=5.0,
            delay_range=(0.0, 0.0),  # 测试时无延迟 / No delay during tests
        )
        self.fetcher = Fetcher(self.config)

    def test_init(self) -> None:
        """测试初始化 / Test initialization."""
        self.assertIsNotNone(self.fetcher.config)
        self.assertIsNotNone(self.fetcher.rate_limiter)
        self.assertIsNotNone(self.fetcher._ssl_context)

    def test_get_random_user_agent(self) -> None:
        """测试随机User-Agent / Test random User-Agent."""
        ua = self.fetcher._get_random_user_agent()
        self.assertIsInstance(ua, str)
        self.assertTrue(len(ua) > 0)
        self.assertIn("Mozilla", ua)

    def test_build_headers(self) -> None:
        """测试构建请求头 / Test building headers."""
        headers = self.fetcher._build_headers()
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept", headers)
        self.assertIn("Accept-Language", headers)

    def test_build_headers_with_extra(self) -> None:
        """测试构建请求头（含额外头）/ Test building headers with extra."""
        headers = self.fetcher._build_headers({"X-Custom": "value"})
        self.assertEqual(headers["X-Custom"], "value")
        self.assertIn("User-Agent", headers)

    def test_decompress_body_gzip(self) -> None:
        """测试gzip解压 / Test gzip decompression."""
        import gzip
        original = b"hello world"
        compressed = gzip.compress(original)
        result = self.fetcher._decompress_body(compressed, "gzip")
        self.assertEqual(result, original)

    def test_decompress_body_none(self) -> None:
        """测试无压缩 / Test no compression."""
        data = b"hello world"
        result = self.fetcher._decompress_body(data, "")
        self.assertEqual(result, data)

    def test_detect_page_type_static(self) -> None:
        """测试静态页面检测 / Test static page detection."""
        resp = FetchResponse(
            body=b"<html><head><title>Test</title></head>"
                 b"<body><p>Hello World</p></body></html>" * 10,
            status_code=200,
        )
        page_type = self.fetcher.detect_page_type(resp)
        self.assertEqual(page_type, "static")

    def test_detect_page_type_dynamic(self) -> None:
        """测试动态页面检测 / Test dynamic page detection."""
        resp = FetchResponse(
            body=b'<html><div id="__next">React App</div></html>',
            status_code=200,
        )
        page_type = self.fetcher.detect_page_type(resp)
        self.assertEqual(page_type, "dynamic")

    def test_detect_page_type_spa_vue(self) -> None:
        """测试Vue SPA检测 / Test Vue SPA detection."""
        resp = FetchResponse(
            body=b'<html><div id="app"></div><script>window.__INITIAL_STATE__={}</script></html>',
            status_code=200,
        )
        page_type = self.fetcher.detect_page_type(resp)
        self.assertEqual(page_type, "dynamic")

    def test_detect_page_type_unknown(self) -> None:
        """测试未知页面类型 / Test unknown page type."""
        resp = FetchResponse(
            body=b"short",
            status_code=200,
        )
        page_type = self.fetcher.detect_page_type(resp)
        self.assertEqual(page_type, "unknown")


if __name__ == "__main__":
    unittest.main()
