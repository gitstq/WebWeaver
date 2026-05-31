"""
WebWeaver - 管道处理系统 / Pipeline Processing System
=====================================================
定义数据处理的管道系统，支持数据清洗、存储和通知等功能。
Defines a pipeline processing system for data, supporting cleaning,
storage, and notification.
"""

import csv
import io
import json
import os
import time
from typing import Any, Dict, List, Optional


class BasePipeline:
    """管道处理器基类 / Pipeline processor base class.

    所有管道处理器必须继承此类并实现process方法。
    All pipeline processors must inherit this class and implement the process method.

    Attributes:
        name: 管道名称 / Pipeline name
    """

    def __init__(self, name: str = "") -> None:
        """初始化管道 / Initialize pipeline.

        Args:
            name: 管道名称 / Pipeline name
        """
        self.name: str = name or self.__class__.__name__
        self._item_count: int = 0
        self._error_count: int = 0

    def process(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理数据项 / Process data item.

        Args:
            item: 待处理的数据字典 / Data dictionary to process

        Returns:
            处理后的数据字典，返回None表示丢弃该项 /
            Processed data dict, return None to drop the item
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.process() 必须被实现 / "
            f"{self.__class__.__name__}.process() must be implemented"
        )

    def open(self) -> None:
        """打开管道（在处理开始前调用）/ Open pipeline (called before processing).

        子类可重写此方法进行初始化操作。
        Subclasses can override this method for initialization.
        """
        self._item_count = 0
        self._error_count = 0

    def close(self) -> None:
        """关闭管道（在处理结束后调用）/ Close pipeline (called after processing).

        子类可重写此方法进行清理操作。
        Subclasses can override this method for cleanup.
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """获取管道统计信息 / Get pipeline statistics.

        Returns:
            统计信息字典 / Statistics dictionary
        """
        return {
            "name": self.name,
            "item_count": self._item_count,
            "error_count": self._error_count,
        }

    def __repr__(self) -> str:
        """返回管道的字符串表示 / Return string representation."""
        return f"Pipeline(name='{self.name}', items={self._item_count})"


class PrintPipeline(BasePipeline):
    """打印输出管道 / Print output pipeline.

    将提取的数据打印到标准输出。
    Prints extracted data to standard output.

    Attributes:
        prefix: 打印前缀 / Print prefix
        max_length: 文本最大显示长度 / Max text display length
    """

    def __init__(self, prefix: str = "[WebWeaver]", max_length: int = 200) -> None:
        """初始化打印管道 / Initialize print pipeline.

        Args:
            prefix: 打印前缀 / Print prefix
            max_length: 文本最大长度 / Max text length
        """
        super().__init__(name="PrintPipeline")
        self.prefix: str = prefix
        self.max_length: int = max_length

    def process(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """打印数据项 / Print data item.

        Args:
            item: 数据字典 / Data dictionary

        Returns:
            原始数据 / Original data
        """
        self._item_count += 1

        # 截断长文本 / Truncate long text
        display_item: Dict[str, Any] = {}
        for key, value in item.items():
            if isinstance(value, str) and len(value) > self.max_length:
                display_item[key] = value[:self.max_length] + "..."
            else:
                display_item[key] = value

        try:
            output = json.dumps(display_item, ensure_ascii=False, indent=2)
            print(f"{self.prefix} #{self._item_count}: {output}")
        except (TypeError, ValueError):
            print(f"{self.prefix} #{self._item_count}: {display_item}")

        return item


class JsonFilePipeline(BasePipeline):
    """JSON文件存储管道 / JSON file storage pipeline.

    将提取的数据保存为JSON文件。
    Saves extracted data as JSON file.

    Attributes:
        filepath: 输出文件路径 / Output file path
        items: 已收集的数据项 / Collected data items
        indent: JSON缩进 / JSON indent
    """

    def __init__(self, filepath: str = "output.json", indent: int = 2) -> None:
        """初始化JSON文件管道 / Initialize JSON file pipeline.

        Args:
            filepath: 输出文件路径 / Output file path
            indent: JSON缩进 / JSON indent
        """
        super().__init__(name="JsonFilePipeline")
        self.filepath: str = filepath
        self.items: List[Dict[str, Any]] = []
        self.indent: int = indent

    def open(self) -> None:
        """打开管道，初始化数据列表 / Open pipeline, initialize data list."""
        super().open()
        self.items = []

    def process(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """收集数据项 / Collect data item.

        Args:
            item: 数据字典 / Data dictionary

        Returns:
            原始数据 / Original data
        """
        self._item_count += 1
        self.items.append(item)
        return item

    def close(self) -> None:
        """关闭管道，将数据写入文件 / Close pipeline, write data to file."""
        if self.items:
            directory = os.path.dirname(self.filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, indent=self.indent)


class CsvPipeline(BasePipeline):
    """CSV文件存储管道 / CSV file storage pipeline.

    将提取的数据保存为CSV文件。
    Saves extracted data as CSV file.

    Attributes:
        filepath: 输出文件路径 / Output file path
        fieldnames: 列名列表 / Column name list
        items: 已收集的数据项 / Collected data items
    """

    def __init__(
        self,
        filepath: str = "output.csv",
        fieldnames: Optional[List[str]] = None,
    ) -> None:
        """初始化CSV管道 / Initialize CSV pipeline.

        Args:
            filepath: 输出文件路径 / Output file path
            fieldnames: 列名列表（自动检测）/ Column names (auto-detect)
        """
        super().__init__(name="CsvPipeline")
        self.filepath: str = filepath
        self.fieldnames: Optional[List[str]] = fieldnames
        self.items: List[Dict[str, Any]] = []
        self._writer: Optional[csv.DictWriter] = None
        self._file: Optional[io.TextIOWrapper] = None

    def open(self) -> None:
        """打开管道，准备CSV文件 / Open pipeline, prepare CSV file."""
        super().open()
        self.items = []

        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def process(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """收集数据项 / Collect data item.

        Args:
            item: 数据字典 / Data dictionary

        Returns:
            原始数据 / Original data
        """
        self._item_count += 1

        # 将非字符串值转换为字符串 / Convert non-string values to strings
        csv_item: Dict[str, str] = {}
        for key, value in item.items():
            if isinstance(value, (list, dict)):
                csv_item[key] = json.dumps(value, ensure_ascii=False)
            else:
                csv_item[key] = str(value) if value is not None else ""

        self.items.append(csv_item)

        # 自动检测列名（在close时最终确定）/ Auto-detect fieldnames (finalized at close)
        if self.fieldnames is None:
            all_keys: set = set()
            for i in self.items:
                all_keys.update(i.keys())
            self.fieldnames = sorted(all_keys)

        return item

    def close(self) -> None:
        """关闭管道，将数据写入CSV文件 / Close pipeline, write data to CSV file."""
        if not self.items:
            return

        # 最终确定列名（收集所有items的所有keys）/ Finalize fieldnames (collect all keys from all items)
        if self.fieldnames is None:
            all_keys: set = set()
            for i in self.items:
                all_keys.update(i.keys())
            self.fieldnames = sorted(all_keys)
        else:
            # 确保fieldnames包含所有items中的所有key / Ensure fieldnames contains all keys from all items
            all_keys: set = set(self.fieldnames)
            for i in self.items:
                all_keys.update(i.keys())
            self.fieldnames = sorted(all_keys)

        try:
            with open(self.filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                for item in self.items:
                    # 确保所有字段都存在 / Ensure all fields exist
                    row = {k: item.get(k, "") for k in self.fieldnames}
                    writer.writerow(row)
        except (IOError, csv.Error) as e:
            self._error_count += 1


class DataCleaningPipeline(BasePipeline):
    """数据清洗管道 / Data cleaning pipeline.

    清洗提取的数据，包括去除空白、标准化格式等。
    Cleans extracted data, including removing whitespace, normalizing formats, etc.

    Attributes:
        strip_strings: 是否去除字符串首尾空白 / Whether to strip strings
        remove_empty: 是否移除空值字段 / Whether to remove empty fields
        remove_none: 是否移除None值字段 / Whether to remove None fields
        max_string_length: 字符串最大长度（0表示不限制）/ Max string length (0=no limit)
    """

    def __init__(
        self,
        strip_strings: bool = True,
        remove_empty: bool = True,
        remove_none: bool = True,
        max_string_length: int = 0,
    ) -> None:
        """初始化清洗管道 / Initialize cleaning pipeline.

        Args:
            strip_strings: 是否去除空白 / Whether to strip whitespace
            remove_empty: 是否移除空值 / Whether to remove empty values
            remove_none: 是否移除None / Whether to remove None
            max_string_length: 字符串最大长度 / Max string length
        """
        super().__init__(name="DataCleaningPipeline")
        self.strip_strings: bool = strip_strings
        self.remove_empty: bool = remove_empty
        self.remove_none: bool = remove_none
        self.max_string_length: int = max_string_length

    def process(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """清洗数据项 / Clean data item.

        Args:
            item: 数据字典 / Data dictionary

        Returns:
            清洗后的数据 / Cleaned data
        """
        self._item_count += 1
        cleaned: Dict[str, Any] = {}

        for key, value in item.items():
            # 处理字符串 / Handle strings
            if isinstance(value, str):
                if self.strip_strings:
                    value = value.strip()
                if self.max_string_length and len(value) > self.max_string_length:
                    value = value[:self.max_string_length]

            # 过滤空值 / Filter empty values
            if self.remove_empty and value == "":
                continue
            if self.remove_none and value is None:
                continue

            cleaned[key] = value

        return cleaned if cleaned else None


class DeduplicationPipeline(BasePipeline):
    """去重管道 / Deduplication pipeline.

        根据指定字段对数据进行去重。
        Deduplicates data based on specified fields.

    Attributes:
        key_fields: 用于去重的字段列表 / Fields for deduplication
        seen_keys: 已见过的键集合 / Seen key set
    """

    def __init__(self, key_fields: Optional[List[str]] = None) -> None:
        """初始化去重管道 / Initialize deduplication pipeline.

        Args:
            key_fields: 用于去重的字段 / Fields for deduplication
        """
        super().__init__(name="DeduplicationPipeline")
        self.key_fields: List[str] = key_fields or []
        self.seen_keys: set = set()

    def open(self) -> None:
        """打开管道，重置已见键 / Open pipeline, reset seen keys."""
        super().open()
        self.seen_keys.clear()

    def process(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检查并去重 / Check and deduplicate.

        Args:
            item: 数据字典 / Data dictionary

        Returns:
            数据或None（重复项）/ Data or None (duplicate)
        """
        self._item_count += 1

        if not self.key_fields:
            return item

        # 构建去重键 / Build dedup key
        key_parts: List[str] = []
        for field in self.key_fields:
            value = item.get(field, "")
            key_parts.append(str(value))
        dedup_key = "|".join(key_parts)

        if dedup_key in self.seen_keys:
            return None

        self.seen_keys.add(dedup_key)
        return item


class PipelineManager:
    """管道管理器 / Pipeline manager.

    管理多个管道处理器的执行顺序和生命周期。
    Manages execution order and lifecycle of multiple pipeline processors.

    Attributes:
        pipelines: 管道列表 / Pipeline list
    """

    def __init__(self) -> None:
        """初始化管道管理器 / Initialize pipeline manager."""
        self.pipelines: List[BasePipeline] = []

    def add_pipeline(self, pipeline: BasePipeline) -> "PipelineManager":
        """添加管道处理器 / Add pipeline processor.

        Args:
            pipeline: 管道处理器 / Pipeline processor

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.pipelines.append(pipeline)
        return self

    def remove_pipeline(self, name: str) -> bool:
        """移除管道处理器 / Remove pipeline processor.

        Args:
            name: 管道名称 / Pipeline name

        Returns:
            是否成功移除 / Whether successfully removed
        """
        for i, pipeline in enumerate(self.pipelines):
            if pipeline.name == name:
                self.pipelines.pop(i)
                return True
        return False

    def open(self) -> None:
        """打开所有管道 / Open all pipelines."""
        for pipeline in self.pipelines:
            pipeline.open()

    def close(self) -> None:
        """关闭所有管道 / Close all pipelines."""
        for pipeline in self.pipelines:
            try:
                pipeline.close()
            except Exception:
                pass

    def process(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通过所有管道处理数据项 / Process data item through all pipelines.

        Args:
            item: 数据字典 / Data dictionary

        Returns:
            处理后的数据或None（被丢弃）/ Processed data or None (dropped)
        """
        current = item
        for pipeline in self.pipelines:
            if current is None:
                return None
            try:
                current = pipeline.process(current)
            except Exception as e:
                pipeline._error_count += 1
                continue
        return current

    def get_stats(self) -> List[Dict[str, Any]]:
        """获取所有管道的统计信息 / Get stats for all pipelines.

        Returns:
            统计信息列表 / Statistics list
        """
        return [pipeline.get_stats() for pipeline in self.pipelines]

    def __len__(self) -> int:
        """返回管道数量 / Return pipeline count."""
        return len(self.pipelines)

    def __repr__(self) -> str:
        """返回管道管理器的字符串表示 / Return string representation."""
        names = [p.name for p in self.pipelines]
        return f"PipelineManager(pipelines={names})"
