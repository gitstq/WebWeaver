"""
WebWeaver - 断点续爬状态管理 / Checkpoint Resume State Management
===================================================================
管理爬取状态，支持中断恢复和断点续爬。
Manages crawl state, supporting interrupt recovery and checkpoint resume.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Set


class CrawlState:
    """爬取状态管理器 / Crawl state manager.

    跟踪已访问的URL、待爬取的URL队列、提取的数据等，
    支持将状态持久化到文件以实现断点续爬。
    Tracks visited URLs, pending URL queue, extracted data, etc.,
    supports persisting state to file for checkpoint resume.

    Attributes:
        state_file: 状态文件路径 / State file path
        visited_urls: 已访问URL集合 / Visited URL set
        pending_urls: 待爬取URL列表 / Pending URL list
        extracted_data: 已提取的数据列表 / Extracted data list
        error_urls: 出错的URL列表 / Error URL list
        metadata: 元数据信息 / Metadata information
    """

    def __init__(self, state_file: str = ".webweaver_state.json") -> None:
        """初始化状态管理器 / Initialize state manager.

        Args:
            state_file: 状态文件路径 / State file path
        """
        self.state_file: str = state_file
        self.visited_urls: Set[str] = set()
        self.pending_urls: List[str] = []
        self.extracted_data: List[Dict[str, Any]] = []
        self.error_urls: Dict[str, str] = {}  # url -> error_message
        self.metadata: Dict[str, Any] = {
            "created_at": time.time(),
            "updated_at": time.time(),
            "total_crawled": 0,
            "total_errors": 0,
        }

    def mark_visited(self, url: str) -> None:
        """标记URL为已访问 / Mark URL as visited.

        Args:
            url: 已访问的URL / Visited URL
        """
        self.visited_urls.add(url)
        self.metadata["total_crawled"] = len(self.visited_urls)
        self.metadata["updated_at"] = time.time()

    def is_visited(self, url: str) -> bool:
        """检查URL是否已访问 / Check if URL has been visited.

        Args:
            url: 待检查的URL / URL to check

        Returns:
            是否已访问 / Whether visited
        """
        return url in self.visited_urls

    def add_pending(self, url: str) -> None:
        """添加待爬取URL / Add pending URL.

        Args:
            url: 待爬取的URL / URL to crawl
        """
        if url not in self.visited_urls and url not in self.pending_urls:
            self.pending_urls.append(url)
            self.metadata["updated_at"] = time.time()

    def add_pending_batch(self, urls: List[str]) -> None:
        """批量添加待爬取URL / Batch add pending URLs.

        Args:
            urls: 待爬取的URL列表 / List of URLs to crawl
        """
        for url in urls:
            self.add_pending(url)

    def get_next_pending(self) -> Optional[str]:
        """获取下一个待爬取URL / Get next pending URL.

        Returns:
            下一个待爬取URL，无则返回None / Next pending URL, None if empty
        """
        if self.pending_urls:
            url = self.pending_urls.pop(0)
            self.metadata["updated_at"] = time.time()
            return url
        return None

    def record_error(self, url: str, error_message: str) -> None:
        """记录爬取错误 / Record crawl error.

        Args:
            url: 出错的URL / Error URL
            error_message: 错误信息 / Error message
        """
        self.error_urls[url] = error_message
        self.metadata["total_errors"] = len(self.error_urls)
        self.metadata["updated_at"] = time.time()

    def add_extracted_data(self, data: Dict[str, Any]) -> None:
        """添加提取的数据 / Add extracted data.

        Args:
            data: 提取的数据字典 / Extracted data dictionary
        """
        self.extracted_data.append(data)
        self.metadata["updated_at"] = time.time()

    def add_extracted_data_batch(self, data_list: List[Dict[str, Any]]) -> None:
        """批量添加提取的数据 / Batch add extracted data.

        Args:
            data_list: 数据字典列表 / List of data dictionaries
        """
        self.extracted_data.extend(data_list)
        self.metadata["updated_at"] = time.time()

    def save(self, filepath: Optional[str] = None) -> None:
        """保存状态到文件 / Save state to file.

        Args:
            filepath: 保存路径，默认使用state_file / Save path, defaults to state_file
        """
        filepath = filepath or self.state_file

        state_dict = {
            "visited_urls": list(self.visited_urls),
            "pending_urls": self.pending_urls,
            "extracted_data": self.extracted_data,
            "error_urls": self.error_urls,
            "metadata": self.metadata,
        }

        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=2)

    def load(self, filepath: Optional[str] = None) -> bool:
        """从文件加载状态 / Load state from file.

        Args:
            filepath: 文件路径，默认使用state_file / File path, defaults to state_file

        Returns:
            是否成功加载 / Whether successfully loaded
        """
        filepath = filepath or self.state_file

        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state_dict = json.load(f)

            self.visited_urls = set(state_dict.get("visited_urls", []))
            self.pending_urls = state_dict.get("pending_urls", [])
            self.extracted_data = state_dict.get("extracted_data", [])
            self.error_urls = state_dict.get("error_urls", {})
            self.metadata = state_dict.get("metadata", self.metadata)

            return True
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return False

    def clear(self) -> None:
        """清空所有状态 / Clear all state.

        重置所有状态数据，但不删除状态文件。
        Resets all state data but does not delete the state file.
        """
        self.visited_urls.clear()
        self.pending_urls.clear()
        self.extracted_data.clear()
        self.error_urls.clear()
        self.metadata = {
            "created_at": time.time(),
            "updated_at": time.time(),
            "total_crawled": 0,
            "total_errors": 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取状态统计信息 / Get state statistics.

        Returns:
            统计信息字典 / Statistics dictionary
        """
        return {
            "visited_count": len(self.visited_urls),
            "pending_count": len(self.pending_urls),
            "extracted_count": len(self.extracted_data),
            "error_count": len(self.error_urls),
            "total_crawled": self.metadata.get("total_crawled", 0),
            "total_errors": self.metadata.get("total_errors", 0),
            "created_at": self.metadata.get("created_at", 0),
            "updated_at": self.metadata.get("updated_at", 0),
        }

    def has_pending(self) -> bool:
        """检查是否有待爬取的URL / Check if there are pending URLs.

        Returns:
            是否有待爬取URL / Whether there are pending URLs
        """
        return len(self.pending_urls) > 0

    def __repr__(self) -> str:
        """返回状态管理器的字符串表示 / Return string representation."""
        return (
            f"CrawlState(visited={len(self.visited_urls)}, "
            f"pending={len(self.pending_urls)}, "
            f"extracted={len(self.extracted_data)}, "
            f"errors={len(self.error_urls)})"
        )
