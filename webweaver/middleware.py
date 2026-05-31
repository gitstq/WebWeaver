"""
WebWeaver - 中间件模块 / Middleware Module
==========================================
定义中间件基类和内置中间件，用于在请求前后执行自定义逻辑。
Defines middleware base class and built-in middlewares for executing
custom logic before and after requests.
"""

import random
import re
import time
from typing import Any, Dict, List, Optional
from .config import CrawlerConfig
from .fetcher import FetchResponse


class BaseMiddleware:
    """中间件基类 / Middleware base class.

    所有中间件必须继承此类并实现相应方法。
    All middlewares must inherit this class and implement corresponding methods.

    中间件执行顺序：
    Middleware execution order:
    - process_request: 请求发送前 / Before request is sent
    - process_response: 响应接收后 / After response is received
    - process_error: 请求出错时 / When request errors
    """

    def __init__(self, name: str = "") -> None:
        """初始化中间件 / Initialize middleware.

        Args:
            name: 中间件名称 / Middleware name
        """
        self.name: str = name or self.__class__.__name__

    def process_request(
        self, url: str, headers: Dict[str, str], **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """处理请求（发送前）/ Process request (before sending).

        可以修改请求参数，返回None表示继续，返回字典表示修改参数。
        Can modify request parameters. Return None to continue,
        return dict to modify parameters.

        Args:
            url: 请求URL / Request URL
            headers: 请求头 / Request headers
            **kwargs: 其他请求参数 / Other request parameters

        Returns:
            修改后的参数字典或None / Modified parameter dict or None
        """
        return None

    def process_response(
        self, response: FetchResponse, **kwargs: Any
    ) -> Optional[FetchResponse]:
        """处理响应（接收后）/ Process response (after receiving).

        可以修改响应对象，返回None表示继续，返回FetchResponse表示替换。
        Can modify response object. Return None to continue,
        return FetchResponse to replace.

        Args:
            response: HTTP响应 / HTTP response
            **kwargs: 其他参数 / Other parameters

        Returns:
            修改后的响应或None / Modified response or None
        """
        return None

    def process_error(
        self, url: str, error: Exception, **kwargs: Any
    ) -> Optional[bool]:
        """处理错误 / Process error.

        返回True表示错误已处理（不重试），False表示继续处理。
        Return True if error is handled (no retry), False to continue.

        Args:
            url: 请求URL / Request URL
            error: 异常对象 / Exception object
            **kwargs: 其他参数 / Other parameters

        Returns:
            True表示已处理 / True means handled
        """
        return None

    def __repr__(self) -> str:
        """返回中间件的字符串表示 / Return string representation."""
        return f"Middleware(name='{self.name}')"


class UserAgentMiddleware(BaseMiddleware):
    """User-Agent轮换中间件 / User-Agent rotation middleware.

    自动为每个请求设置随机User-Agent。
    Automatically sets a random User-Agent for each request.

    Attributes:
        user_agents: User-Agent列表 / User-Agent list
    """

    def __init__(self, user_agents: Optional[List[str]] = None) -> None:
        """初始化User-Agent中间件 / Initialize User-Agent middleware.

        Args:
            user_agents: 自定义User-Agent列表 / Custom User-Agent list
        """
        super().__init__(name="UserAgentMiddleware")
        self.user_agents: List[str] = user_agents or CrawlerConfig.DEFAULT_USER_AGENTS

    def process_request(
        self, url: str, headers: Dict[str, str], **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """为请求设置随机User-Agent / Set random User-Agent for request.

        Args:
            url: 请求URL / Request URL
            headers: 请求头 / Request headers
            **kwargs: 其他参数 / Other parameters

        Returns:
            更新后的请求头 / Updated headers
        """
        headers["User-Agent"] = random.choice(self.user_agents)
        return {"headers": headers}


class RetryMiddleware(BaseMiddleware):
    """重试中间件 / Retry middleware.

    根据响应状态码决定是否重试请求。
    Determines whether to retry request based on response status code.

    Attributes:
        max_retries: 最大重试次数 / Maximum retry count
        retry_codes: 需要重试的状态码 / Status codes to retry
        retry_delay: 重试延迟 / Retry delay
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_codes: Optional[List[int]] = None,
        retry_delay: float = 1.0,
    ) -> None:
        """初始化重试中间件 / Initialize retry middleware.

        Args:
            max_retries: 最大重试次数 / Maximum retry count
            retry_codes: 需要重试的状态码 / Status codes to retry
            retry_delay: 重试延迟 / Retry delay
        """
        super().__init__(name="RetryMiddleware")
        self.max_retries: int = max_retries
        self.retry_codes: List[int] = retry_codes or [429, 500, 502, 503, 504]
        self.retry_delay: float = retry_delay
        self._retry_counts: Dict[str, int] = {}

    def process_request(
        self, url: str, headers: Dict[str, str], **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """检查重试次数 / Check retry count.

        Args:
            url: 请求URL / Request URL
            headers: 请求头 / Request headers
            **kwargs: 其他参数 / Other parameters

        Returns:
            None或中止标记 / None or abort marker
        """
        count = self._retry_counts.get(url, 0)
        if count >= self.max_retries:
            return {"abort": True}

        if count > 0:
            delay = self.retry_delay * (2 ** (count - 1))
            time.sleep(delay)

        return None

    def process_response(
        self, response: FetchResponse, **kwargs: Any
    ) -> Optional[FetchResponse]:
        """检查响应是否需要重试 / Check if response needs retry.

        Args:
            response: HTTP响应 / HTTP response
            **kwargs: 其他参数 / Other parameters

        Returns:
            None或替换的响应 / None or replacement response
        """
        url = kwargs.get("url", response.url)
        if response.status_code in self.retry_codes:
            self._retry_counts[url] = self._retry_counts.get(url, 0) + 1
        else:
            self._retry_counts.pop(url, None)

        return None

    def process_error(
        self, url: str, error: Exception, **kwargs: Any
    ) -> Optional[bool]:
        """处理请求错误 / Handle request error.

        Args:
            url: 请求URL / Request URL
            error: 异常 / Exception
            **kwargs: 其他参数 / Other parameters

        Returns:
            False表示可以重试 / False means can retry
        """
        self._retry_counts[url] = self._retry_counts.get(url, 0) + 1
        if self._retry_counts[url] >= self.max_retries:
            return True
        return False


class FilterMiddleware(BaseMiddleware):
    """URL过滤中间件 / URL filter middleware.

    根据规则过滤不需要爬取的URL。
    Filters URLs that don't need to be crawled based on rules.

    Attributes:
        allowed_domains: 允许的域名列表 / Allowed domain list
        denied_patterns: 拒绝的URL模式 / Denied URL patterns
        allowed_extensions: 允许的文件扩展名 / Allowed file extensions
    """

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        denied_patterns: Optional[List[str]] = None,
        allowed_extensions: Optional[List[str]] = None,
    ) -> None:
        """初始化过滤中间件 / Initialize filter middleware.

        Args:
            allowed_domains: 允许的域名 / Allowed domains
            denied_patterns: 拒绝的模式 / Denied patterns
            allowed_extensions: 允许的扩展名 / Allowed extensions
        """
        super().__init__(name="FilterMiddleware")
        self.allowed_domains: List[str] = allowed_domains or []
        self.denied_patterns: List[str] = denied_patterns or []
        self.allowed_extensions: List[str] = allowed_extensions or [
            ".html", ".htm", ".php", ".asp", ".aspx", ".jsp",
            "",  # 无扩展名的URL
        ]

    def process_request(
        self, url: str, headers: Dict[str, str], **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """检查URL是否应该被过滤 / Check if URL should be filtered.

        Args:
            url: 请求URL / Request URL
            headers: 请求头 / Request headers
            **kwargs: 其他参数 / Other parameters

        Returns:
            中止标记（如果URL被过滤）/ Abort marker (if URL is filtered)
        """
        from urllib.parse import urlparse
        from .utils import is_valid_url

        if not is_valid_url(url):
            return {"abort": True}

        parsed = urlparse(url)
        domain = parsed.netloc.split(":")[0]

        # 检查域名白名单 / Check domain whitelist
        if self.allowed_domains:
            domain_allowed = any(
                domain == d or domain.endswith("." + d)
                for d in self.allowed_domains
            )
            if not domain_allowed:
                return {"abort": True}

        # 检查拒绝模式 / Check denied patterns
        for pattern in self.denied_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return {"abort": True}

        # 检查文件扩展名 / Check file extension
        path = parsed.path.lower()
        has_valid_ext = any(
            path.endswith(ext) or not ext
            for ext in self.allowed_extensions
        )
        if not has_valid_ext and path.find(".") != -1:
            return {"abort": True}

        return None


class LoggingMiddleware(BaseMiddleware):
    """日志记录中间件 / Logging middleware.

    记录请求和响应的基本信息。
    Logs basic information about requests and responses.

    Attributes:
        log_level: 日志级别 / Log level
        log_entries: 日志条目列表 / Log entry list
    """

    LOG_LEVELS: Dict[str, int] = {
        "debug": 0,
        "info": 1,
        "warning": 2,
        "error": 3,
    }

    def __init__(self, log_level: str = "info") -> None:
        """初始化日志中间件 / Initialize logging middleware.

        Args:
            log_level: 日志级别 / Log level
        """
        super().__init__(name="LoggingMiddleware")
        self.log_level: str = log_level
        self.log_entries: List[Dict[str, Any]] = []

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        """记录日志 / Log message.

        Args:
            level: 日志级别 / Log level
            message: 日志消息 / Log message
            **kwargs: 额外数据 / Extra data
        """
        if self.LOG_LEVELS.get(level, 0) >= self.LOG_LEVELS.get(self.log_level, 1):
            entry = {
                "level": level,
                "message": message,
                "timestamp": time.time(),
                **kwargs,
            }
            self.log_entries.append(entry)

    def process_request(
        self, url: str, headers: Dict[str, str], **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """记录请求信息 / Log request info.

        Args:
            url: 请求URL / Request URL
            headers: 请求头 / Request headers
            **kwargs: 其他参数 / Other parameters

        Returns:
            None
        """
        self._log("info", f"请求 / Request: {url}")
        return None

    def process_response(
        self, response: FetchResponse, **kwargs: Any
    ) -> Optional[FetchResponse]:
        """记录响应信息 / Log response info.

        Args:
            response: HTTP响应 / HTTP response
            **kwargs: 其他参数 / Other parameters

        Returns:
            None
        """
        level = "info" if response.ok else "warning"
        self._log(
            level,
            f"响应 / Response: {response.url} -> {response.status_code}",
            status_code=response.status_code,
            content_length=response.content_length,
            elapsed=response.elapsed,
        )
        return None

    def process_error(
        self, url: str, error: Exception, **kwargs: Any
    ) -> Optional[bool]:
        """记录错误信息 / Log error info.

        Args:
            url: 请求URL / Request URL
            error: 异常 / Exception
            **kwargs: 其他参数 / Other parameters

        Returns:
            None
        """
        self._log(
            "error",
            f"错误 / Error: {url} - {str(error)}",
            error_type=type(error).__name__,
        )
        return None

    def get_logs(self) -> List[Dict[str, Any]]:
        """获取所有日志条目 / Get all log entries.

        Returns:
            日志条目列表 / Log entry list
        """
        return self.log_entries.copy()

    def clear_logs(self) -> None:
        """清除日志 / Clear logs."""
        self.log_entries.clear()
