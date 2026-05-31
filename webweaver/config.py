"""
WebWeaver - 配置管理模块 / Configuration Management Module
===========================================================
管理爬虫引擎的全局配置，包括请求参数、速率限制、解析选项等。
Manages global configuration for the crawler engine, including request parameters,
rate limits, parsing options, etc.
"""

import json
import os
from typing import Any, Dict, List, Optional


class CrawlerConfig:
    """爬虫配置类 / Crawler configuration class.

    管理WebWeaver爬虫引擎的所有可配置参数。
    Manages all configurable parameters for the WebWeaver crawler engine.

    Attributes:
        user_agents: 可用的User-Agent列表 / List of available User-Agents
        timeout: 请求超时时间（秒） / Request timeout in seconds
        max_retries: 最大重试次数 / Maximum retry attempts
        retry_delay: 重试延迟基数（秒） / Base retry delay in seconds
        delay_range: 随机延迟范围（秒） / Random delay range in seconds
        max_depth: 最大爬取深度 / Maximum crawl depth
        respect_robots_txt: 是否遵守robots.txt / Whether to respect robots.txt
        follow_redirects: 是否跟随重定向 / Whether to follow redirects
        max_redirects: 最大重定向次数 / Maximum redirect count
        encoding: 默认编码 / Default encoding
        state_file: 断点续爬状态文件路径 / Checkpoint state file path
        auto_save_state: 是否自动保存状态 / Whether to auto-save state
        state_save_interval: 状态保存间隔 / State save interval
        concurrent_requests: 并发请求数 / Concurrent request count
        headers: 默认请求头 / Default request headers
        proxies: 代理配置 / Proxy configuration
        pipelines: 管道处理器名称列表 / Pipeline processor name list
        middlewares: 中间件名称列表 / Middleware name list
    """

    # 默认User-Agent列表 / Default User-Agent list
    DEFAULT_USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 "
        "Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 "
        "Firefox/121.0",
    ]

    def __init__(self, **kwargs: Any) -> None:
        """初始化爬虫配置 / Initialize crawler configuration.

        Args:
            **kwargs: 配置参数，可覆盖默认值 / Configuration parameters to override defaults
        """
        # User-Agent配置 / User-Agent configuration
        self.user_agents: List[str] = kwargs.get(
            "user_agents", self.DEFAULT_USER_AGENTS.copy()
        )

        # 请求配置 / Request configuration
        self.timeout: float = kwargs.get("timeout", 30.0)
        self.max_retries: int = kwargs.get("max_retries", 3)
        self.retry_delay: float = kwargs.get("retry_delay", 1.0)
        self.delay_range: tuple = kwargs.get("delay_range", (0.5, 2.0))
        self.follow_redirects: bool = kwargs.get("follow_redirects", True)
        self.max_redirects: int = kwargs.get("max_redirects", 5)
        self.encoding: str = kwargs.get("encoding", "utf-8")

        # 爬取配置 / Crawl configuration
        self.max_depth: int = kwargs.get("max_depth", 3)
        self.respect_robots_txt: bool = kwargs.get("respect_robots_txt", True)
        self.concurrent_requests: int = kwargs.get("concurrent_requests", 1)

        # 状态管理配置 / State management configuration
        self.state_file: str = kwargs.get("state_file", ".webweaver_state.json")
        self.auto_save_state: bool = kwargs.get("auto_save_state", True)
        self.state_save_interval: int = kwargs.get("state_save_interval", 10)

        # 代理配置 / Proxy configuration
        self.proxies: Dict[str, str] = kwargs.get("proxies", {})

        # 默认请求头 / Default request headers
        self.headers: Dict[str, str] = kwargs.get("headers", {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

        # 管道和中间件 / Pipelines and middlewares
        self.pipelines: List[str] = kwargs.get("pipelines", [])
        self.middlewares: List[str] = kwargs.get("middlewares", [])

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典 / Convert configuration to dictionary.

        Returns:
            包含所有配置项的字典 / Dictionary containing all configuration items
        """
        return {
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "delay_range": list(self.delay_range),
            "max_depth": self.max_depth,
            "respect_robots_txt": self.respect_robots_txt,
            "follow_redirects": self.follow_redirects,
            "max_redirects": self.max_redirects,
            "encoding": self.encoding,
            "state_file": self.state_file,
            "auto_save_state": self.auto_save_state,
            "state_save_interval": self.state_save_interval,
            "concurrent_requests": self.concurrent_requests,
            "headers": self.headers,
            "proxies": self.proxies,
            "pipelines": self.pipelines,
            "middlewares": self.middlewares,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrawlerConfig":
        """从字典创建配置 / Create configuration from dictionary.

        Args:
            data: 配置字典 / Configuration dictionary

        Returns:
            CrawlerConfig实例 / CrawlerConfig instance
        """
        return cls(**data)

    @classmethod
    def from_file(cls, filepath: str) -> "CrawlerConfig":
        """从JSON文件加载配置 / Load configuration from JSON file.

        Args:
            filepath: 配置文件路径 / Configuration file path

        Returns:
            CrawlerConfig实例 / CrawlerConfig instance
        """
        if not os.path.exists(filepath):
            return cls()

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_to_file(self, filepath: str) -> None:
        """将配置保存到JSON文件 / Save configuration to JSON file.

        Args:
            filepath: 保存路径 / Save path
        """
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def __repr__(self) -> str:
        """返回配置的字符串表示 / Return string representation of config."""
        return (
            f"CrawlerConfig(timeout={self.timeout}, max_retries={self.max_retries}, "
            f"max_depth={self.max_depth}, concurrent={self.concurrent_requests})"
        )
