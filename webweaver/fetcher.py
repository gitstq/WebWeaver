"""
WebWeaver - HTTP请求器 / HTTP Fetcher
======================================
基于Python标准库urllib实现自适应HTTP请求，内置反检测机制。
Implements adaptive HTTP requests based on Python's standard library urllib,
with built-in anti-detection mechanisms.
"""

import gzip
import io
import json
import random
import socket
import ssl
import time
import urllib.request
import urllib.error
import urllib.parse
from http.client import HTTPResponse
from typing import Any, Dict, List, Optional, Tuple, Union
from .config import CrawlerConfig
from .exceptions import FetchError, TimeoutError
from .ratelimit import RateLimiter
from .utils import detect_encoding


class FetchResponse:
    """HTTP响应封装 / HTTP response wrapper.

    封装urllib的HTTP响应，提供便捷的访问接口。
    Wraps urllib's HTTP response with convenient access interfaces.

    Attributes:
        url: 最终URL（可能经过重定向）/ Final URL (may have been redirected)
        status_code: HTTP状态码 / HTTP status code
        headers: 响应头字典 / Response header dictionary
        body: 响应体字节 / Response body bytes
        text: 解码后的文本 / Decoded text
        encoding: 检测到的编码 / Detected encoding
        elapsed: 请求耗时（秒）/ Request elapsed time in seconds
        history: 重定向历史 / Redirect history
    """

    def __init__(
        self,
        url: str = "",
        status_code: int = 0,
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b"",
        encoding: str = "utf-8",
        elapsed: float = 0.0,
        history: Optional[List[str]] = None,
    ) -> None:
        """初始化HTTP响应 / Initialize HTTP response.

        Args:
            url: 最终URL / Final URL
            status_code: HTTP状态码 / HTTP status code
            headers: 响应头 / Response headers
            body: 响应体 / Response body
            encoding: 编码 / Encoding
            elapsed: 耗时 / Elapsed time
            history: 重定向历史 / Redirect history
        """
        self.url: str = url
        self.status_code: int = status_code
        self.headers: Dict[str, str] = headers or {}
        self.body: bytes = body
        self.encoding: str = encoding
        self.elapsed: float = elapsed
        self.history: List[str] = history or []

    @property
    def text(self) -> str:
        """获取解码后的文本内容 / Get decoded text content.

        Returns:
            解码后的文本 / Decoded text
        """
        if not self.body:
            return ""
        try:
            return self.body.decode(self.encoding)
        except (UnicodeDecodeError, LookupError):
            # 尝试其他编码 / Try other encodings
            for enc in ("utf-8", "gb18030", "latin-1", "iso-8859-1"):
                try:
                    return self.body.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            return self.body.decode("utf-8", errors="replace")

    @property
    def ok(self) -> bool:
        """检查响应是否成功 / Check if response is successful.

        Returns:
            状态码是否在200-399范围内 / Whether status code is in 200-399 range
        """
        return 200 <= self.status_code < 400

    @property
    def content_type(self) -> str:
        """获取Content-Type / Get Content-Type.

        Returns:
            Content-Type值 / Content-Type value
        """
        return self.headers.get("Content-Type", "")

    def json(self) -> Any:
        """将响应体解析为JSON / Parse response body as JSON.

        Returns:
            解析后的Python对象 / Parsed Python object
        """
        return json.loads(self.text)

    @property
    def content_length(self) -> int:
        """获取内容长度 / Get content length.

        Returns:
            内容字节数 / Content byte count
        """
        return len(self.body)

    def to_dict(self) -> Dict[str, Any]:
        """将响应转换为字典 / Convert response to dictionary.

        Returns:
            响应的字典表示 / Dictionary representation of response
        """
        return {
            "url": self.url,
            "status_code": self.status_code,
            "headers": self.headers,
            "content_length": self.content_length,
            "encoding": self.encoding,
            "elapsed": round(self.elapsed, 3),
            "ok": self.ok,
        }

    def __repr__(self) -> str:
        """返回响应的字符串表示 / Return string representation."""
        return (
            f"FetchResponse(url='{self.url}', status={self.status_code}, "
            f"size={self.content_length}, elapsed={self.elapsed:.2f}s)"
        )


class Fetcher:
    """HTTP请求器 / HTTP fetcher.

    基于urllib实现自适应HTTP请求，内置反检测机制。
    Implements adaptive HTTP requests based on urllib with built-in anti-detection.

    Attributes:
        config: 爬虫配置 / Crawler configuration
        rate_limiter: 速率限制器 / Rate limiter
    """

    def __init__(self, config: Optional[CrawlerConfig] = None) -> None:
        """初始化请求器 / Initialize fetcher.

        Args:
            config: 爬虫配置 / Crawler configuration
        """
        self.config: CrawlerConfig = config or CrawlerConfig()
        self.rate_limiter: RateLimiter = RateLimiter(
            max_requests=self.config.concurrent_requests * 5,
            window_seconds=60.0,
            min_delay=self.config.delay_range[0],
            max_delay=self.config.delay_range[1] * 5,
        )

        # 创建SSL上下文 / Create SSL context
        self._ssl_context: ssl.SSLContext = self._create_ssl_context()

    def _create_ssl_context(self) -> ssl.SSLContext:
        """创建SSL上下文 / Create SSL context.

        Returns:
            SSL上下文对象 / SSL context object
        """
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx
        except Exception:
            return ssl._create_unverified_context()

    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent / Get random User-Agent.

        Returns:
            随机选择的User-Agent字符串 / Randomly selected User-Agent string
        """
        return random.choice(self.config.user_agents)

    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """构建请求头 / Build request headers.

        合并默认请求头和自定义请求头，自动添加User-Agent。
        Merges default and custom headers, automatically adds User-Agent.

        Args:
            extra_headers: 额外请求头 / Extra headers

        Returns:
            合并后的请求头 / Merged headers
        """
        headers = self.config.headers.copy()
        headers["User-Agent"] = self._get_random_user_agent()

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _decompress_body(self, data: bytes, encoding: str = "") -> bytes:
        """解压缩响应体 / Decompress response body.

        Args:
            data: 原始数据 / Raw data
            encoding: 内容编码 / Content encoding

        Returns:
            解压后的数据 / Decompressed data
        """
        encoding = encoding.lower()
        if encoding == "gzip":
            try:
                return gzip.decompress(data)
            except Exception:
                return data
        elif encoding == "deflate":
            try:
                import zlib
                return zlib.decompress(data)
            except Exception:
                return data
        elif encoding == "br":
            try:
                import zlib
                return zlib.decompress(data, zlib.MAX_WBITS | 16)
            except Exception:
                return data
        return data

    def fetch(
        self,
        url: str,
        method: str = "GET",
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        follow_redirects: Optional[bool] = None,
        max_redirects: Optional[int] = None,
    ) -> FetchResponse:
        """发送HTTP请求 / Send HTTP request.

        Args:
            url: 目标URL / Target URL
            method: HTTP方法 / HTTP method
            data: 请求体数据 / Request body data
            headers: 额外请求头 / Extra headers
            timeout: 超时时间 / Timeout
            follow_redirects: 是否跟随重定向 / Whether to follow redirects
            max_redirects: 最大重定向次数 / Maximum redirect count

        Returns:
            HTTP响应对象 / HTTP response object

        Raises:
            FetchError: 请求失败 / Request failed
            TimeoutError: 请求超时 / Request timed out
        """
        timeout = timeout or self.config.timeout
        follow_redirects = (
            follow_redirects if follow_redirects is not None
            else self.config.follow_redirects
        )
        max_redirects = (
            max_redirects if max_redirects is not None
            else self.config.max_redirects
        )

        # 速率限制等待 / Rate limit wait
        self.rate_limiter.wait()

        # 随机延迟 / Random delay
        delay = random.uniform(*self.config.delay_range)
        time.sleep(delay)

        request_headers = self._build_headers(headers)
        history: List[str] = [url]
        start_time = time.time()

        for attempt in range(self.config.max_retries):
            try:
                current_url = url if not history or len(history) <= 1 else history[-1]

                # 准备请求数据 / Prepare request data
                req_data = data
                if data and isinstance(data, str):
                    req_data = data.encode("utf-8")

                # 创建请求对象 / Create request object
                req = urllib.request.Request(
                    current_url,
                    data=req_data,
                    headers=request_headers,
                    method=method.upper(),
                )

                # 设置超时的socket / Set socket timeout
                socket.setdefaulttimeout(timeout)

                # 发送请求 / Send request
                response = urllib.request.urlopen(
                    req,
                    timeout=timeout,
                    context=self._ssl_context,
                )

                # 读取响应 / Read response
                response_body = response.read()

                # 处理重定向 / Handle redirects
                if follow_redirects and response.status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location", "")
                    if location and len(history) < max_redirects:
                        history.append(location)
                        current_url = location
                        continue

                # 解压缩 / Decompress
                content_encoding = response.headers.get("Content-Encoding", "")
                response_body = self._decompress_body(response_body, content_encoding)

                # 检测编码 / Detect encoding
                content_type = response.headers.get("Content-Type", "")
                encoding = self.config.encoding
                charset_match = __import__("re").search(
                    r"charset=([^\s;]+)", content_type, re.IGNORECASE
                )
                if charset_match:
                    encoding = charset_match.group(1).strip()

                # 构建响应头字典 / Build response header dictionary
                resp_headers = {}
                for key, value in response.headers.items():
                    resp_headers[key] = value

                elapsed = time.time() - start_time

                fetch_resp = FetchResponse(
                    url=current_url,
                    status_code=response.status,
                    headers=resp_headers,
                    body=response_body,
                    encoding=encoding,
                    elapsed=elapsed,
                    history=history[:-1],
                )

                # 记录成功请求 / Record successful request
                self.rate_limiter.record_request(True, response.status)

                return fetch_resp

            except urllib.error.HTTPError as e:
                elapsed = time.time() - start_time
                self.rate_limiter.record_request(False, e.code)

                # 读取错误响应体 / Read error response body
                error_body = b""
                try:
                    error_body = e.read()
                except Exception:
                    pass

                resp_headers = {}
                try:
                    for key, value in e.headers.items():
                        resp_headers[key] = value
                except Exception:
                    pass

                # 4xx错误不重试 / Don't retry 4xx errors (except 429)
                if 400 <= e.code < 500 and e.code != 429:
                    raise FetchError(
                        url=url,
                        status_code=e.code,
                        reason=str(e.reason),
                    )

                # 等待后重试 / Wait and retry
                retry_delay = self.config.retry_delay * (attempt + 1)
                time.sleep(retry_delay)

            except urllib.error.URLError as e:
                elapsed = time.time() - start_time
                self.rate_limiter.record_request(False, 0)

                if "timed out" in str(e.reason).lower():
                    raise TimeoutError(url=url, timeout=timeout)

                # 网络错误，等待后重试 / Network error, wait and retry
                retry_delay = self.config.retry_delay * (attempt + 1)
                time.sleep(retry_delay)

            except socket.timeout:
                self.rate_limiter.record_request(False, 0)
                raise TimeoutError(url=url, timeout=timeout)

            except Exception as e:
                self.rate_limiter.record_request(False, 0)
                raise FetchError(url=url, reason=str(e))

        # 所有重试都失败 / All retries failed
        raise FetchError(
            url=url,
            reason=f"超过最大重试次数 {self.config.max_retries} / "
                   f"Exceeded max retries {self.config.max_retries}",
        )

    def fetch_many(
        self, urls: List[str], method: str = "GET", **kwargs: Any
    ) -> List[FetchResponse]:
        """批量发送HTTP请求 / Batch send HTTP requests.

        Args:
            urls: URL列表 / URL list
            method: HTTP方法 / HTTP method
            **kwargs: 额外参数 / Extra parameters

        Returns:
            响应列表 / Response list
        """
        results: List[FetchResponse] = []
        for url in urls:
            try:
                resp = self.fetch(url, method=method, **kwargs)
                results.append(resp)
            except (FetchError, TimeoutError) as e:
                # 创建错误响应 / Create error response
                results.append(FetchResponse(
                    url=url,
                    status_code=0,
                    headers={},
                    body=b"",
                ))
        return results

    def detect_page_type(self, response: FetchResponse) -> str:
        """检测页面类型 / Detect page type.

        根据响应内容判断页面是静态还是动态渲染。
        Determines if page is static or dynamically rendered based on response.

        Args:
            response: HTTP响应 / HTTP response

        Returns:
            页面类型（'static', 'dynamic', 'unknown'）/ Page type
        """
        text = response.text[:5000].lower()

        # 检测SPA框架特征 / Detect SPA framework characteristics
        spa_indicators = [
            "react", "vue", "angular", "next.js", "nuxt",
            "__next", "_nuxt", "ng-app", "v-app",
            "window.__initial_state", "window.__data",
            "application/json",
        ]
        for indicator in spa_indicators:
            if indicator in text:
                return "dynamic"

        # 检测是否需要JavaScript渲染 / Detect if JavaScript rendering is needed
        js_required_indicators = [
            "noscript", "javascript:void(0)",
            "document.getelementbyid",
            "please enable javascript",
            "需要启用javascript",
        ]
        for indicator in js_required_indicators:
            if indicator in text:
                return "dynamic"

        # 检查是否有实际内容 / Check if there's actual content
        if len(response.body) > 500:
            return "static"

        return "unknown"
