"""
WebWeaver - 爬虫集成测试 / Crawler Integration Tests
=====================================================
测试爬虫引擎的集成功能。
Tests for crawler engine integration functionality.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from webweaver.crawler import Crawler, CrawlResult
from webweaver.config import CrawlerConfig
from webweaver.extractor import ExtractionRule
from webweaver.fetcher import FetchResponse
from webweaver.middleware import (
    UserAgentMiddleware,
    RetryMiddleware,
    FilterMiddleware,
    LoggingMiddleware,
)
from webweaver.pipeline import PrintPipeline, JsonFilePipeline, DataCleaningPipeline
from webweaver.ratelimit import RateLimiter
from webweaver.state import CrawlState


class TestCrawlResult(unittest.TestCase):
    """CrawlResult测试类 / CrawlResult test class."""

    def test_success_result(self) -> None:
        """测试成功结果 / Test success result."""
        result = CrawlResult(
            url="https://example.com",
            success=True,
            elapsed=1.5,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.elapsed, 1.5)

    def test_error_result(self) -> None:
        """测试错误结果 / Test error result."""
        result = CrawlResult(
            url="https://example.com",
            success=False,
            error="Connection timeout",
            elapsed=30.0,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Connection timeout")

    def test_to_dict(self) -> None:
        """测试转字典 / Test to dict."""
        result = CrawlResult(
            url="https://example.com",
            success=True,
            elapsed=1.0,
        )
        d = result.to_dict()
        self.assertEqual(d["url"], "https://example.com")
        self.assertTrue(d["success"])
        self.assertIn("elapsed", d)

    def test_repr(self) -> None:
        """测试repr / Test repr."""
        result = CrawlResult(url="https://example.com", success=True)
        r = repr(result)
        self.assertIn("example.com", r)
        self.assertIn("OK", r)


class TestCrawlState(unittest.TestCase):
    """CrawlState测试类 / CrawlState test class."""

    def test_mark_and_check_visited(self) -> None:
        """测试标记和检查已访问 / Test mark and check visited."""
        state = CrawlState()
        self.assertFalse(state.is_visited("https://example.com"))
        state.mark_visited("https://example.com")
        self.assertTrue(state.is_visited("https://example.com"))

    def test_pending_urls(self) -> None:
        """测试待爬取URL / Test pending URLs."""
        state = CrawlState()
        state.add_pending("https://example.com/1")
        state.add_pending("https://example.com/2")
        self.assertTrue(state.has_pending())
        self.assertEqual(len(state.pending_urls), 2)

    def test_get_next_pending(self) -> None:
        """测试获取下一个待爬取 / Test getting next pending."""
        state = CrawlState()
        state.add_pending("https://example.com/1")
        state.add_pending("https://example.com/2")

        url = state.get_next_pending()
        self.assertEqual(url, "https://example.com/1")
        self.assertEqual(len(state.pending_urls), 1)

    def test_dedup_pending(self) -> None:
        """测试待爬取去重 / Test pending deduplication."""
        state = CrawlState()
        state.add_pending("https://example.com/1")
        state.add_pending("https://example.com/1")  # 重复 / duplicate
        self.assertEqual(len(state.pending_urls), 1)

    def test_error_recording(self) -> None:
        """测试错误记录 / Test error recording."""
        state = CrawlState()
        state.record_error("https://example.com", "timeout")
        self.assertEqual(len(state.error_urls), 1)
        self.assertEqual(state.error_urls["https://example.com"], "timeout")

    def test_extracted_data(self) -> None:
        """测试提取数据记录 / Test extracted data recording."""
        state = CrawlState()
        state.add_extracted_data({"title": "Test"})
        state.add_extracted_data({"title": "Test2"})
        self.assertEqual(len(state.extracted_data), 2)

    def test_save_and_load(self) -> None:
        """测试保存和加载 / Test save and load."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            state = CrawlState(state_file=filepath)
            state.mark_visited("https://example.com")
            state.add_pending("https://example.com/2")
            state.add_extracted_data({"title": "Test"})
            state.save()

            new_state = CrawlState(state_file=filepath)
            loaded = new_state.load()
            self.assertTrue(loaded)
            self.assertTrue(new_state.is_visited("https://example.com"))
            self.assertEqual(len(new_state.extracted_data), 1)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_clear(self) -> None:
        """测试清空 / Test clear."""
        state = CrawlState()
        state.mark_visited("https://example.com")
        state.add_pending("https://example.com/2")
        state.clear()
        self.assertFalse(state.is_visited("https://example.com"))
        self.assertFalse(state.has_pending())

    def test_get_stats(self) -> None:
        """测试获取统计 / Test getting stats."""
        state = CrawlState()
        state.mark_visited("https://example.com")
        stats = state.get_stats()
        self.assertEqual(stats["visited_count"], 1)


class TestRateLimiter(unittest.TestCase):
    """RateLimiter测试类 / RateLimiter test class."""

    def test_init(self) -> None:
        """测试初始化 / Test initialization."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        self.assertIsNotNone(limiter)

    def test_acquire_no_wait(self) -> None:
        """测试无需等待 / Test no wait needed."""
        limiter = RateLimiter(max_requests=100, window_seconds=60, min_delay=0)
        wait_time = limiter.acquire()
        self.assertEqual(wait_time, 0.0)

    def test_record_success(self) -> None:
        """测试记录成功 / Test recording success."""
        limiter = RateLimiter()
        limiter.record_request(True, 200)
        stats = limiter.get_stats()
        self.assertEqual(stats["error_count"], 0)
        self.assertEqual(stats["requests_in_window"], 1)

    def test_record_error(self) -> None:
        """测试记录错误 / Test recording error."""
        limiter = RateLimiter()
        limiter.record_request(False, 500)
        stats = limiter.get_stats()
        self.assertEqual(stats["error_count"], 1)

    def test_record_429(self) -> None:
        """测试429状态码处理 / Test 429 status code handling."""
        limiter = RateLimiter(min_delay=0.5)
        initial_delay = limiter._current_delay
        limiter.record_request(False, 429)
        # 429应导致延迟增加 / 429 should increase delay
        self.assertGreater(limiter._current_delay, initial_delay)

    def test_reset(self) -> None:
        """测试重置 / Test reset."""
        limiter = RateLimiter()
        limiter.record_request(False, 500)
        limiter.reset()
        stats = limiter.get_stats()
        self.assertEqual(stats["error_count"], 0)
        self.assertEqual(stats["requests_in_window"], 0)

    def test_get_stats(self) -> None:
        """测试获取统计 / Test getting stats."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        stats = limiter.get_stats()
        self.assertEqual(stats["max_requests"], 10)
        self.assertEqual(stats["window_seconds"], 60)


class TestCrawler(unittest.TestCase):
    """Crawler测试类 / Crawler test class."""

    def setUp(self) -> None:
        """测试前准备 / Test setup."""
        self.config = CrawlerConfig(
            timeout=5.0,
            delay_range=(0.0, 0.0),
            auto_save_state=False,
        )
        self.crawler = Crawler(self.config)

    def test_init(self) -> None:
        """测试初始化 / Test initialization."""
        self.assertIsNotNone(self.crawler.config)
        self.assertIsNotNone(self.crawler.fetcher)
        self.assertIsNotNone(self.crawler.parser)
        self.assertIsNotNone(self.crawler.extractor)
        self.assertIsNotNone(self.crawler.state)

    def test_add_pipeline(self) -> None:
        """测试添加管道 / Test adding pipeline."""
        pipeline = PrintPipeline()
        self.crawler.add_pipeline(pipeline)
        self.assertEqual(len(self.crawler.pipeline_manager), 1)

    def test_add_middleware(self) -> None:
        """测试添加中间件 / Test adding middleware."""
        middleware = UserAgentMiddleware()
        self.crawler.add_middleware(middleware)
        self.assertEqual(len(self.crawler.middlewares), 1)

    def test_add_extraction_rule(self) -> None:
        """测试添加提取规则 / Test adding extraction rule."""
        rule = ExtractionRule(name="title", selector_type="css", selector="title")
        self.crawler.add_extraction_rule(rule)
        self.assertEqual(len(self.crawler.extractor.rules), 1)

    def test_chain_methods(self) -> None:
        """测试链式调用 / Test method chaining."""
        crawler = Crawler()
        result = (
            crawler
            .add_pipeline(PrintPipeline())
            .add_middleware(UserAgentMiddleware())
            .add_extraction_rule(
                ExtractionRule(name="title", selector_type="title")
            )
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(crawler.pipeline_manager), 1)
        self.assertEqual(len(crawler.middlewares), 1)

    def test_get_stats(self) -> None:
        """测试获取统计 / Test getting stats."""
        stats = self.crawler.get_stats()
        self.assertIn("total_requests", stats)
        self.assertIn("total_success", stats)
        self.assertIn("total_errors", stats)

    def test_repr(self) -> None:
        """测试repr / Test repr."""
        r = repr(self.crawler)
        self.assertIn("Crawler", r)


class TestMiddleware(unittest.TestCase):
    """中间件测试类 / Middleware test class."""

    def test_user_agent_middleware(self) -> None:
        """测试User-Agent中间件 / Test User-Agent middleware."""
        mw = UserAgentMiddleware()
        headers = {}
        result = mw.process_request("https://example.com", headers)
        self.assertIsNotNone(result)
        self.assertIn("User-Agent", result["headers"])

    def test_retry_middleware_process_error(self) -> None:
        """测试重试中间件错误处理 / Test retry middleware error handling."""
        mw = RetryMiddleware(max_retries=3)
        # 第一次错误应返回False（可重试）/ First error should return False (can retry)
        result = mw.process_error("https://example.com", Exception("timeout"))
        self.assertFalse(result)

    def test_retry_middleware_max_retries(self) -> None:
        """测试重试中间件最大重试 / Test retry middleware max retries."""
        mw = RetryMiddleware(max_retries=2)
        mw.process_error("https://example.com", Exception("timeout"))
        mw.process_error("https://example.com", Exception("timeout"))
        # 第三次应返回True（不再重试）/ Third should return True (no more retries)
        result = mw.process_error("https://example.com", Exception("timeout"))
        self.assertTrue(result)

    def test_filter_middleware(self) -> None:
        """测试过滤中间件 / Test filter middleware."""
        mw = FilterMiddleware(allowed_domains=["example.com"])

        # 允许的域名 / Allowed domain
        result = mw.process_request("https://example.com/page", {})
        self.assertIsNone(result)  # None表示不拦截 / None means not blocked

        # 不允许的域名 / Disallowed domain
        result = mw.process_request("https://other.com/page", {})
        self.assertIsNotNone(result)
        self.assertTrue(result.get("abort"))

    def test_logging_middleware(self) -> None:
        """测试日志中间件 / Test logging middleware."""
        mw = LoggingMiddleware()
        mw.process_request("https://example.com", {})

        resp = FetchResponse(url="https://example.com", status_code=200, body=b"test")
        mw.process_response(resp)

        mw.process_error("https://example.com", Exception("error"))

        logs = mw.get_logs()
        self.assertEqual(len(logs), 3)

    def test_logging_middleware_clear(self) -> None:
        """测试日志中间件清除 / Test logging middleware clear."""
        mw = LoggingMiddleware()
        mw.process_request("https://example.com", {})
        mw.clear_logs()
        self.assertEqual(len(mw.get_logs()), 0)


if __name__ == "__main__":
    unittest.main()
