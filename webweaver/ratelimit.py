"""
WebWeaver - 智能速率限制器 / Intelligent Rate Limiter
======================================================
提供自适应速率控制，避免因请求过快被封禁。
Provides adaptive rate control to avoid being blocked due to excessive requests.
"""

import time
import random
from collections import deque
from typing import Optional


class RateLimiter:
    """智能速率限制器 / Intelligent rate limiter.

    基于令牌桶算法实现自适应速率控制，根据服务器响应动态调整请求速率。
    Implements adaptive rate control based on token bucket algorithm,
    dynamically adjusting request rate based on server responses.

    Attributes:
        max_requests: 时间窗口内最大请求数 / Max requests per time window
        window_seconds: 时间窗口大小（秒） / Time window size in seconds
        min_delay: 最小请求间隔（秒） / Minimum request interval in seconds
        max_delay: 最大请求间隔（秒） / Maximum request interval in seconds
        backoff_factor: 退避因子 / Backoff factor
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: float = 60.0,
        min_delay: float = 0.5,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
    ) -> None:
        """初始化速率限制器 / Initialize rate limiter.

        Args:
            max_requests: 时间窗口内最大请求数 / Max requests per time window
            window_seconds: 时间窗口大小（秒） / Time window size in seconds
            min_delay: 最小请求间隔（秒） / Minimum request interval in seconds
            max_delay: 最大请求间隔（秒） / Maximum request interval in seconds
            backoff_factor: 退避因子 / Backoff factor
        """
        self.max_requests: int = max_requests
        self.window_seconds: float = window_seconds
        self.min_delay: float = min_delay
        self.max_delay: float = max_delay
        self.backoff_factor: float = backoff_factor

        # 请求时间戳记录 / Request timestamp records
        self._timestamps: deque = deque()

        # 当前延迟 / Current delay
        self._current_delay: float = min_delay

        # 连续错误计数 / Consecutive error count
        self._error_count: int = 0

        # 上次请求时间 / Last request time
        self._last_request_time: float = 0.0

    def acquire(self) -> float:
        """获取请求许可，返回需要等待的时间 / Acquire request permission.

        计算当前是否需要等待，并返回等待时间。
        Calculates whether waiting is needed and returns wait time.

        Returns:
            需要等待的秒数（0表示可以立即请求）/ Seconds to wait (0 means can request immediately)
        """
        now = time.time()

        # 清理过期的时间戳 / Clean up expired timestamps
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        # 检查是否超过速率限制 / Check if rate limit exceeded
        if len(self._timestamps) >= self.max_requests:
            oldest = self._timestamps[0]
            wait_time = oldest + self.window_seconds - now
            if wait_time > 0:
                return wait_time

        # 计算最小间隔等待 / Calculate minimum interval wait
        elapsed = now - self._last_request_time
        if elapsed < self._current_delay:
            return self._current_delay - elapsed

        return 0.0

    def wait(self) -> None:
        """等待直到可以发送请求 / Wait until a request can be sent.

        阻塞当前线程直到速率限制允许发送请求。
        Blocks current thread until rate limit allows sending a request.
        """
        wait_time = self.acquire()
        if wait_time > 0:
            # 添加少量随机抖动 / Add small random jitter
            jitter = random.uniform(0, min(wait_time * 0.1, 0.5))
            time.sleep(wait_time + jitter)

    def record_request(self, success: bool = True, status_code: int = 200) -> None:
        """记录请求结果 / Record request result.

        根据请求结果调整速率限制参数。
        Adjusts rate limit parameters based on request result.

        Args:
            success: 请求是否成功 / Whether request succeeded
            status_code: HTTP状态码 / HTTP status code
        """
        now = time.time()
        self._timestamps.append(now)
        self._last_request_time = now

        if success and 200 <= status_code < 400:
            # 请求成功，逐步恢复速率 / Request succeeded, gradually restore rate
            self._error_count = 0
            self._current_delay = max(
                self.min_delay,
                self._current_delay / self.backoff_factor
            )
        else:
            # 请求失败，增加延迟 / Request failed, increase delay
            self._error_count += 1
            self._current_delay = min(
                self.max_delay,
                self._current_delay * self.backoff_factor
            )

            # 429状态码特殊处理（被限流） / Special handling for 429 (rate limited)
            if status_code == 429:
                self._current_delay = min(
                    self.max_delay,
                    self._current_delay * 2
                )

    def get_stats(self) -> dict:
        """获取速率限制器统计信息 / Get rate limiter statistics.

        Returns:
            包含统计信息的字典 / Dictionary with statistics
        """
        now = time.time()
        cutoff = now - self.window_seconds
        recent_count = sum(1 for t in self._timestamps if t >= cutoff)

        return {
            "current_delay": round(self._current_delay, 3),
            "error_count": self._error_count,
            "requests_in_window": recent_count,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
        }

    def reset(self) -> None:
        """重置速率限制器 / Reset rate limiter.

        清除所有状态，恢复到初始配置。
        Clears all state, restores to initial configuration.
        """
        self._timestamps.clear()
        self._current_delay = self.min_delay
        self._error_count = 0
        self._last_request_time = 0.0
