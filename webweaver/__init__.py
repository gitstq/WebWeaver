"""
WebWeaver - 轻量级自适应Web爬虫引擎 / Lightweight Adaptive Web Crawler Engine
===========================================================================
零外部依赖，仅使用Python标准库。
Zero external dependencies, using only Python standard library.

快速开始 / Quick Start:
    from webweaver import Crawler, CrawlerConfig

    # 创建爬虫 / Create crawler
    crawler = Crawler()

    # 爬取单个页面 / Crawl a single page
    result = crawler.start("https://example.com")
    print(result.document.title)

    # 使用提取规则 / Use extraction rules
    from webweaver import ExtractionRule
    crawler.add_extraction_rule(ExtractionRule(
        name="title",
        selector_type="css",
        selector="title",
    ))
    result = crawler.start("https://example.com")
    print(result.data)
"""

__version__ = "1.0.0"
__author__ = "WebWeaver Team"
__license__ = "MIT"

# 导出核心类 / Export core classes
from .config import CrawlerConfig
from .crawler import Crawler, CrawlResult
from .exceptions import (
    WebWeaverError,
    FetchError,
    ParseError,
    SelectorError,
    ExtractionError,
    PipelineError,
    RateLimitError,
    StateError,
    ConfigError,
    TimeoutError,
    RobotParserError,
)
from .extractor import Extractor, ExtractionRule
from .fetcher import Fetcher, FetchResponse
from .middleware import (
    BaseMiddleware,
    UserAgentMiddleware,
    RetryMiddleware,
    FilterMiddleware,
    LoggingMiddleware,
)
from .parser import Parser, ParsedDocument, Element
from .pipeline import (
    BasePipeline,
    PipelineManager,
    PrintPipeline,
    JsonFilePipeline,
    CsvPipeline,
    DataCleaningPipeline,
    DeduplicationPipeline,
)
from .ratelimit import RateLimiter
from .selector import Selector, SelectorList
from .state import CrawlState
from .utils import (
    normalize_url,
    is_valid_url,
    get_domain,
    get_base_url,
    is_same_domain,
    extract_links,
    detect_encoding,
    clean_text,
    safe_filename,
)

__all__ = [
    # 版本信息 / Version info
    "__version__",
    "__author__",
    "__license__",
    # 核心类 / Core classes
    "Crawler",
    "CrawlerConfig",
    "CrawlResult",
    # 请求器 / Fetcher
    "Fetcher",
    "FetchResponse",
    # 解析器 / Parser
    "Parser",
    "ParsedDocument",
    "Element",
    # 选择器 / Selector
    "Selector",
    "SelectorList",
    # 提取器 / Extractor
    "Extractor",
    "ExtractionRule",
    # 管道 / Pipeline
    "BasePipeline",
    "PipelineManager",
    "PrintPipeline",
    "JsonFilePipeline",
    "CsvPipeline",
    "DataCleaningPipeline",
    "DeduplicationPipeline",
    # 中间件 / Middleware
    "BaseMiddleware",
    "UserAgentMiddleware",
    "RetryMiddleware",
    "FilterMiddleware",
    "LoggingMiddleware",
    # 速率限制 / Rate limiter
    "RateLimiter",
    # 状态管理 / State management
    "CrawlState",
    # 异常 / Exceptions
    "WebWeaverError",
    "FetchError",
    "ParseError",
    "SelectorError",
    "ExtractionError",
    "PipelineError",
    "RateLimitError",
    "StateError",
    "ConfigError",
    "TimeoutError",
    "RobotParserError",
    # 工具函数 / Utilities
    "normalize_url",
    "is_valid_url",
    "get_domain",
    "get_base_url",
    "is_same_domain",
    "extract_links",
    "detect_encoding",
    "clean_text",
    "safe_filename",
]
