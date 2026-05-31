"""
WebWeaver - 自定义异常模块 / Custom Exception Module
=====================================================
定义WebWeaver爬虫框架中所有自定义异常类。
Defines all custom exception classes for the WebWeaver crawler framework.
"""


class WebWeaverError(Exception):
    """WebWeaver基础异常类 / Base exception class for WebWeaver.

    所有WebWeaver自定义异常的基类，便于统一捕获和处理。
    Base class for all WebWeaver custom exceptions for unified catching and handling.
    """

    def __init__(self, message: str = "", *args, **kwargs):
        """初始化异常 / Initialize exception.

        Args:
            message: 异常描述信息 / Exception description message
            *args: 额外位置参数 / Additional positional arguments
            **kwargs: 额外关键字参数 / Additional keyword arguments
        """
        self.message = message
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        """返回异常的字符串表示 / Return string representation of exception."""
        return self.message or super().__str__()


class FetchError(WebWeaverError):
    """HTTP请求异常 / HTTP request exception.

    当HTTP请求失败时抛出，包括网络错误、超时、连接拒绝等情况。
    Raised when an HTTP request fails, including network errors, timeouts,
    connection refused, etc.
    """

    def __init__(self, url: str, status_code: int = 0,
                 reason: str = "", message: str = ""):
        """初始化请求异常 / Initialize fetch exception.

        Args:
            url: 请求的目标URL / Target URL of the request
            status_code: HTTP状态码，0表示无状态码 / HTTP status code, 0 means no code
            reason: 失败原因描述 / Failure reason description
            message: 自定义消息 / Custom message
        """
        self.url = url
        self.status_code = status_code
        self.reason = reason
        if not message:
            if status_code:
                message = f"请求失败 / Fetch failed: {url} (状态码/status_code={status_code}, 原因/reason={reason})"
            else:
                message = f"请求失败 / Fetch failed: {url} (原因/reason={reason})"
        super().__init__(message)


class ParseError(WebWeaverError):
    """解析异常 / Parsing exception.

    当HTML或JSON解析失败时抛出。
    Raised when HTML or JSON parsing fails.
    """

    def __init__(self, content_type: str = "", message: str = ""):
        """初始化解析异常 / Initialize parse exception.

        Args:
            content_type: 内容类型（html/json） / Content type (html/json)
            message: 自定义消息 / Custom message
        """
        self.content_type = content_type
        if not message:
            message = f"{content_type} 解析失败 / {content_type} parsing failed"
        super().__init__(message)


class SelectorError(WebWeaverError):
    """选择器异常 / Selector exception.

    当CSS/XPath选择器语法错误或匹配失败时抛出。
    Raised when CSS/XPath selector syntax is invalid or matching fails.
    """

    def __init__(self, query: str = "", message: str = ""):
        """初始化选择器异常 / Initialize selector exception.

        Args:
            query: 导致异常的选择器表达式 / Selector expression that caused the error
            message: 自定义消息 / Custom message
        """
        self.query = query
        if not message:
            message = f"选择器错误 / Selector error: '{query}'"
        super().__init__(message)


class ExtractionError(WebWeaverError):
    """数据提取异常 / Data extraction exception.

    当数据提取规则执行失败时抛出。
    Raised when data extraction rules fail to execute.
    """

    def __init__(self, rule_name: str = "", message: str = ""):
        """初始化提取异常 / Initialize extraction exception.

        Args:
            rule_name: 导致异常的规则名称 / Rule name that caused the error
            message: 自定义消息 / Custom message
        """
        self.rule_name = rule_name
        if not message:
            message = f"提取规则 '{rule_name}' 执行失败 / Extraction rule '{rule_name}' failed"
        super().__init__(message)


class PipelineError(WebWeaverError):
    """管道处理异常 / Pipeline processing exception.

    当管道处理器执行失败时抛出。
    Raised when a pipeline processor fails to execute.
    """

    def __init__(self, pipeline_name: str = "", message: str = ""):
        """初始化管道异常 / Initialize pipeline exception.

        Args:
            pipeline_name: 导致异常的管道名称 / Pipeline name that caused the error
            message: 自定义消息 / Custom message
        """
        self.pipeline_name = pipeline_name
        if not message:
            message = f"管道 '{pipeline_name}' 处理失败 / Pipeline '{pipeline_name}' processing failed"
        super().__init__(message)


class RateLimitError(WebWeaverError):
    """速率限制异常 / Rate limit exception.

    当请求频率超过限制时抛出。
    Raised when request frequency exceeds the limit.
    """

    def __init__(self, message: str = "请求频率超过限制 / Request rate exceeded limit"):
        """初始化速率限制异常 / Initialize rate limit exception.

        Args:
            message: 自定义消息 / Custom message
        """
        super().__init__(message)


class StateError(WebWeaverError):
    """状态管理异常 / State management exception.

    当断点续爬状态保存或恢复失败时抛出。
    Raised when checkpoint state save or restore fails.
    """

    def __init__(self, message: str = "状态管理错误 / State management error"):
        """初始化状态异常 / Initialize state exception.

        Args:
            message: 自定义消息 / Custom message
        """
        super().__init__(message)


class ConfigError(WebWeaverError):
    """配置异常 / Configuration exception.

    当配置无效或缺失时抛出。
    Raised when configuration is invalid or missing.
    """

    def __init__(self, key: str = "", message: str = ""):
        """初始化配置异常 / Initialize config exception.

        Args:
            key: 导致异常的配置键 / Configuration key that caused the error
            message: 自定义消息 / Custom message
        """
        self.key = key
        if not message:
            message = f"配置错误 '{key}' / Configuration error '{key}'"
        super().__init__(message)


class TimeoutError(WebWeaverError):
    """超时异常 / Timeout exception.

    当请求或操作超时时抛出。
    Raised when a request or operation times out.
    """

    def __init__(self, url: str = "", timeout: float = 0.0, message: str = ""):
        """初始化超时异常 / Initialize timeout exception.

        Args:
            url: 超时的URL / URL that timed out
            timeout: 超时时间（秒） / Timeout duration (seconds)
            message: 自定义消息 / Custom message
        """
        self.url = url
        self.timeout = timeout
        if not message:
            message = f"请求超时 / Request timed out: {url} (超时/timeout={timeout}s)"
        super().__init__(message)


class RobotParserError(WebWeaverError):
    """robots.txt解析异常 / robots.txt parsing exception.

    当robots.txt文件解析失败时抛出。
    Raised when robots.txt file parsing fails.
    """

    def __init__(self, url: str = "", message: str = ""):
        """初始化robots解析异常 / Initialize robots parser exception.

        Args:
            url: robots.txt的URL / URL of robots.txt
            message: 自定义消息 / Custom message
        """
        self.url = url
        if not message:
            message = f"robots.txt 解析失败 / robots.txt parsing failed: {url}"
        super().__init__(message)
