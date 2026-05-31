"""
WebWeaver - 核心爬虫引擎 / Core Crawler Engine
===============================================
整合所有组件，提供完整的爬虫功能，包括单页爬取、多页爬取、
深度爬取、断点续爬等。
Integrates all components to provide complete crawling functionality,
including single-page crawl, multi-page crawl, depth crawl, and
checkpoint resume.
"""

import time
from typing import Any, Callable, Dict, List, Optional
from .config import CrawlerConfig
from .exceptions import FetchError, ParseError
from .extractor import Extractor, ExtractionRule
from .fetcher import Fetcher, FetchResponse
from .middleware import BaseMiddleware
from .parser import Parser, ParsedDocument
from .pipeline import BasePipeline, PipelineManager
from .ratelimit import RateLimiter
from .selector import Selector
from .state import CrawlState
from .utils import (
    extract_links, get_domain, is_same_domain, is_valid_url, normalize_url
)


class CrawlResult:
    """爬取结果 / Crawl result.

    封装单次爬取的结果，包括URL、响应、解析后的文档和提取的数据。
    Encapsulates a single crawl result including URL, response,
    parsed document, and extracted data.

    Attributes:
        url: 请求的URL / Requested URL
        response: HTTP响应 / HTTP response
        document: 解析后的文档 / Parsed document
        data: 提取的数据 / Extracted data
        links: 发现的链接 / Discovered links
        success: 是否成功 / Whether successful
        error: 错误信息 / Error message
        elapsed: 耗时（秒）/ Elapsed time in seconds
    """

    def __init__(
        self,
        url: str = "",
        response: Optional[FetchResponse] = None,
        document: Optional[ParsedDocument] = None,
        data: Optional[Dict[str, Any]] = None,
        links: Optional[List[str]] = None,
        success: bool = True,
        error: str = "",
        elapsed: float = 0.0,
    ) -> None:
        """初始化爬取结果 / Initialize crawl result.

        Args:
            url: 请求的URL / Requested URL
            response: HTTP响应 / HTTP response
            document: 解析后的文档 / Parsed document
            data: 提取的数据 / Extracted data
            links: 发现的链接 / Discovered links
            success: 是否成功 / Whether successful
            error: 错误信息 / Error message
            elapsed: 耗时 / Elapsed time
        """
        self.url: str = url
        self.response: Optional[FetchResponse] = response
        self.document: Optional[ParsedDocument] = document
        self.data: Optional[Dict[str, Any]] = data
        self.links: List[str] = links or []
        self.success: bool = success
        self.error: str = error
        self.elapsed: float = elapsed

    def to_dict(self) -> Dict[str, Any]:
        """将结果转换为字典 / Convert result to dictionary.

        Returns:
            结果的字典表示 / Dictionary representation of result
        """
        return {
            "url": self.url,
            "success": self.success,
            "error": self.error,
            "elapsed": round(self.elapsed, 3),
            "status_code": self.response.status_code if self.response else 0,
            "title": self.document.title if self.document else "",
            "links_count": len(self.links),
            "data": self.data,
        }

    def __repr__(self) -> str:
        """返回结果的字符串表示 / Return string representation."""
        status = "OK" if self.success else "ERROR"
        return (
            f"CrawlResult(url='{self.url}', status={status}, "
            f"elapsed={self.elapsed:.2f}s)"
        )


class Crawler:
    """WebWeaver核心爬虫引擎 / WebWeaver core crawler engine.

    整合请求器、解析器、选择器、提取器、管道和中间件，
    提供完整的网页爬取功能。

    Integrates fetcher, parser, selector, extractor, pipelines, and middlewares
    to provide complete web crawling functionality.

    Attributes:
        config: 爬虫配置 / Crawler configuration
        fetcher: HTTP请求器 / HTTP fetcher
        parser: HTML/JSON解析器 / HTML/JSON parser
        extractor: 数据提取器 / Data extractor
        state: 爬取状态 / Crawl state
        pipeline_manager: 管道管理器 / Pipeline manager
        middlewares: 中间件列表 / Middleware list
    """

    def __init__(self, config: Optional[CrawlerConfig] = None) -> None:
        """初始化爬虫引擎 / Initialize crawler engine.

        Args:
            config: 爬虫配置 / Crawler configuration
        """
        self.config: CrawlerConfig = config or CrawlerConfig()
        self.fetcher: Fetcher = Fetcher(self.config)
        self.parser: Parser = Parser(self.config.encoding)
        self.extractor: Extractor = Extractor()
        self.state: CrawlState = CrawlState(self.config.state_file)
        self.pipeline_manager: PipelineManager = PipelineManager()
        self.middlewares: List[BaseMiddleware] = []
        self.rate_limiter: RateLimiter = self.fetcher.rate_limiter

        # 回调函数 / Callback function
        self._on_result: Optional[Callable[[CrawlResult], None]] = None

        # 是否正在运行 / Whether running
        self._running: bool = False

        # 爬取统计 / Crawl statistics
        self._stats: Dict[str, Any] = {
            "total_requests": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_links": 0,
            "start_time": 0.0,
            "end_time": 0.0,
        }

    def on_result(self, callback: Callable[[CrawlResult], None]) -> "Crawler":
        """设置结果回调函数 / Set result callback function.

        Args:
            callback: 回调函数 / Callback function

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self._on_result = callback
        return self

    def add_pipeline(self, pipeline: BasePipeline) -> "Crawler":
        """添加管道处理器 / Add pipeline processor.

        Args:
            pipeline: 管道处理器 / Pipeline processor

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.pipeline_manager.add_pipeline(pipeline)
        return self

    def add_middleware(self, middleware: BaseMiddleware) -> "Crawler":
        """添加中间件 / Add middleware.

        Args:
            middleware: 中间件 / Middleware

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.middlewares.append(middleware)
        return self

    def set_extractor(self, extractor: Extractor) -> "Crawler":
        """设置数据提取器 / Set data extractor.

        Args:
            extractor: 提取器 / Extractor

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.extractor = extractor
        return self

    def add_extraction_rule(self, rule: ExtractionRule) -> "Crawler":
        """添加提取规则 / Add extraction rule.

        Args:
            rule: 提取规则 / Extraction rule

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.extractor.add_rule(rule)
        return self

    def load_state(self) -> bool:
        """加载爬取状态 / Load crawl state.

        Returns:
            是否成功加载 / Whether successfully loaded
        """
        return self.state.load()

    def save_state(self) -> None:
        """保存爬取状态 / Save crawl state."""
        self.state.save()

    def clear_state(self) -> None:
        """清除爬取状态 / Clear crawl state."""
        self.state.clear()
        self.state.save()

    def start(
        self,
        url: str,
        callback: Optional[Callable[[CrawlResult], None]] = None,
        depth: int = 0,
        extract: bool = True,
    ) -> CrawlResult:
        """爬取单个URL / Crawl a single URL.

        Args:
            url: 目标URL / Target URL
            callback: 结果回调 / Result callback
            depth: 爬取深度 / Crawl depth
            extract: 是否提取数据 / Whether to extract data

        Returns:
            爬取结果 / Crawl result
        """
        if callback:
            self._on_result = callback

        self._stats["start_time"] = time.time()
        self._running = True

        result = self._crawl_url(url, depth, extract)

        self._stats["end_time"] = time.time()
        self._running = False

        # 自动保存状态 / Auto-save state
        if self.config.auto_save_state:
            self.save_state()

        return result

    def crawl_many(
        self,
        urls: List[str],
        callback: Optional[Callable[[CrawlResult], None]] = None,
        extract: bool = True,
    ) -> List[CrawlResult]:
        """批量爬取多个URL / Batch crawl multiple URLs.

        Args:
            urls: URL列表 / URL list
            callback: 结果回调 / Result callback
            extract: 是否提取数据 / Whether to extract data

        Returns:
            爬取结果列表 / Crawl result list
        """
        if callback:
            self._on_result = callback

        self._stats["start_time"] = time.time()
        self._running = True

        # 打开管道 / Open pipelines
        self.pipeline_manager.open()

        results: List[CrawlResult] = []
        for url in urls:
            if not self._running:
                break

            result = self._crawl_url(url, depth=0, extract=extract)
            results.append(result)

            # 触发回调 / Trigger callback
            if self._on_result:
                self._on_result(result)

        # 关闭管道 / Close pipelines
        self.pipeline_manager.close()

        self._stats["end_time"] = time.time()
        self._running = False

        # 自动保存状态 / Auto-save state
        if self.config.auto_save_state:
            self.save_state()

        return results

    def crawl_recursive(
        self,
        start_url: str,
        max_depth: int = 3,
        same_domain: bool = True,
        callback: Optional[Callable[[CrawlResult], None]] = None,
        extract: bool = True,
    ) -> List[CrawlResult]:
        """递归爬取（深度优先）/ Recursive crawl (depth-first).

        Args:
            start_url: 起始URL / Starting URL
            max_depth: 最大深度 / Maximum depth
            same_domain: 是否限制同域名 / Whether to limit to same domain
            callback: 结果回调 / Result callback
            extract: 是否提取数据 / Whether to extract data

        Returns:
            爬取结果列表 / Crawl result list
        """
        if callback:
            self._on_result = callback

        self._stats["start_time"] = time.time()
        self._running = True

        # 打开管道 / Open pipelines
        self.pipeline_manager.open()

        # 尝试加载已有状态 / Try to load existing state
        if self.config.auto_save_state:
            self.load_state()

        # 添加起始URL / Add starting URL
        start_url = normalize_url(start_url)
        self.state.add_pending(start_url)

        results: List[CrawlResult] = []
        base_domain = get_domain(start_url)
        crawl_count = 0

        while self.state.has_pending() and self._running:
            url = self.state.get_next_pending()
            if url is None:
                break

            # 检查域名限制 / Check domain restriction
            if same_domain and not is_same_domain(url, start_url):
                continue

            result = self._crawl_url(url, depth=0, extract=extract)
            results.append(result)

            # 触发回调 / Trigger callback
            if self._on_result:
                self._on_result(result)

            # 如果成功且发现了新链接，添加到待爬取队列 / If successful and found new links, add to queue
            if result.success and result.links:
                for link in result.links:
                    if not self.state.is_visited(link):
                        if not same_domain or is_same_domain(link, start_url):
                            self.state.add_pending(link)

            crawl_count += 1

            # 定期保存状态 / Periodically save state
            if self.config.auto_save_state and crawl_count % self.config.state_save_interval == 0:
                self.save_state()

        # 关闭管道 / Close pipelines
        self.pipeline_manager.close()

        self._stats["end_time"] = time.time()
        self._running = False

        # 保存最终状态 / Save final state
        if self.config.auto_save_state:
            self.save_state()

        return results

    def stop(self) -> None:
        """停止爬取 / Stop crawling."""
        self._running = False

    def _crawl_url(
        self, url: str, depth: int = 0, extract: bool = True
    ) -> CrawlResult:
        """爬取单个URL的内部实现 / Internal implementation of crawling a single URL.

        Args:
            url: 目标URL / Target URL
            depth: 当前深度 / Current depth
            extract: 是否提取数据 / Whether to extract data

        Returns:
            爬取结果 / Crawl result
        """
        start_time = time.time()
        url = normalize_url(url)

        # 标记为已访问 / Mark as visited
        self.state.mark_visited(url)
        self._stats["total_requests"] += 1

        # 执行中间件请求前处理 / Execute middleware pre-request processing
        headers = self.config.headers.copy()
        for middleware in self.middlewares:
            try:
                result = middleware.process_request(url, headers)
                if result and result.get("abort"):
                    return CrawlResult(
                        url=url,
                        success=False,
                        error="请求被中间件拦截 / Request blocked by middleware",
                        elapsed=time.time() - start_time,
                    )
                if result and "headers" in result:
                    headers = result["headers"]
            except Exception as e:
                continue

        # 发送HTTP请求 / Send HTTP request
        try:
            response = self.fetcher.fetch(url, headers=headers)
        except (FetchError, Exception) as e:
            self._stats["total_errors"] += 1
            self.state.record_error(url, str(e))

            # 执行中间件错误处理 / Execute middleware error handling
            for middleware in self.middlewares:
                try:
                    handled = middleware.process_error(url, e)
                    if handled:
                        break
                except Exception:
                    continue

            return CrawlResult(
                url=url,
                success=False,
                error=str(e),
                elapsed=time.time() - start_time,
            )

        # 执行中间件响应处理 / Execute middleware response processing
        for middleware in self.middlewares:
            try:
                modified = middleware.process_response(response, url=url)
                if modified:
                    response = modified
            except Exception:
                continue

        # 解析响应内容 / Parse response content
        document: Optional[ParsedDocument] = None
        try:
            document = self.parser.auto_parse(response.text)
        except ParseError as e:
            self._stats["total_errors"] += 1
            return CrawlResult(
                url=url,
                response=response,
                success=False,
                error=f"解析失败 / Parse failed: {e}",
                elapsed=time.time() - start_time,
            )

        # 提取数据 / Extract data
        data: Optional[Dict[str, Any]] = None
        if extract and self.extractor.rules:
            try:
                data = self.extractor.extract(document)
            except Exception as e:
                data = {"error": str(e)}

        # 通过管道处理数据 / Process data through pipelines
        if data:
            processed = self.pipeline_manager.process(data)
            if processed:
                data = processed
                self.state.add_extracted_data(data)

        # 提取链接 / Extract links
        links: List[str] = []
        if document and document.content_type == "html":
            links = extract_links(response.text, url)
            self._stats["total_links"] += len(links)

        elapsed = time.time() - start_time
        self._stats["total_success"] += 1

        return CrawlResult(
            url=url,
            response=response,
            document=document,
            data=data,
            links=links,
            success=True,
            elapsed=elapsed,
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取爬取统计信息 / Get crawl statistics.

        Returns:
            统计信息字典 / Statistics dictionary
        """
        elapsed = 0.0
        if self._stats["start_time"]:
            end = self._stats["end_time"] or time.time()
            elapsed = end - self._stats["start_time"]

        return {
            "total_requests": self._stats["total_requests"],
            "total_success": self._stats["total_success"],
            "total_errors": self._stats["total_errors"],
            "total_links": self._stats["total_links"],
            "elapsed": round(elapsed, 2),
            "state": self.state.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
            "pipelines": self.pipeline_manager.get_stats(),
        }

    def __repr__(self) -> str:
        """返回爬虫的字符串表示 / Return string representation."""
        return (
            f"Crawler(config={self.config}, "
            f"pipelines={len(self.pipeline_manager)}, "
            f"middlewares={len(self.middlewares)})"
        )
