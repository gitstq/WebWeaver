"""
WebWeaver - 管道测试 / Pipeline Tests
======================================
测试管道处理系统的各项功能。
Tests for pipeline processing system functionality.
"""

import json
import os
import tempfile
import unittest
from webweaver.pipeline import (
    BasePipeline,
    PipelineManager,
    PrintPipeline,
    JsonFilePipeline,
    CsvPipeline,
    DataCleaningPipeline,
    DeduplicationPipeline,
)


class TestPrintPipeline(unittest.TestCase):
    """PrintPipeline测试类 / PrintPipeline test class."""

    def test_process(self) -> None:
        """测试数据处理 / Test data processing."""
        pipeline = PrintPipeline()
        item = {"key": "value", "number": 42}
        result = pipeline.process(item)
        self.assertEqual(result, item)
        self.assertEqual(pipeline._item_count, 1)

    def test_process_with_long_text(self) -> None:
        """测试长文本截断 / Test long text truncation."""
        pipeline = PrintPipeline(max_length=10)
        long_text = "a" * 100
        item = {"text": long_text}
        result = pipeline.process(item)
        # 长文本应被截断 / Long text should be truncated
        self.assertIsNotNone(result)


class TestJsonFilePipeline(unittest.TestCase):
    """JsonFilePipeline测试类 / JsonFilePipeline test class."""

    def test_save_and_verify(self) -> None:
        """测试JSON保存 / Test JSON saving."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            pipeline = JsonFilePipeline(filepath=filepath)
            pipeline.open()

            pipeline.process({"name": "Alice", "age": 30})
            pipeline.process({"name": "Bob", "age": 25})

            pipeline.close()

            # 验证文件内容 / Verify file content
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["name"], "Alice")
            self.assertEqual(data[1]["name"], "Bob")
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_empty_data(self) -> None:
        """测试空数据 / Test empty data."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            filepath = f.name

        try:
            pipeline = JsonFilePipeline(filepath=filepath)
            pipeline.open()
            pipeline.close()
            # 空数据不应创建文件内容 / Empty data should not create file content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


class TestCsvPipeline(unittest.TestCase):
    """CsvPipeline测试类 / CsvPipeline test class."""

    def test_save_and_verify(self) -> None:
        """测试CSV保存 / Test CSV saving."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            filepath = f.name

        try:
            pipeline = CsvPipeline(filepath=filepath)
            pipeline.open()

            pipeline.process({"name": "Alice", "age": 30})
            pipeline.process({"name": "Bob", "age": 25})

            pipeline.close()

            # 验证CSV文件 / Verify CSV file
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
            lines = content.strip().split("\n")
            self.assertEqual(len(lines), 3)  # header + 2 rows
            self.assertIn("Alice", lines[1])
            self.assertIn("Bob", lines[2])
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_auto_fieldnames(self) -> None:
        """测试自动列名检测 / Test auto fieldname detection."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            filepath = f.name

        try:
            pipeline = CsvPipeline(filepath=filepath)
            pipeline.open()

            pipeline.process({"a": 1, "b": 2})
            pipeline.process({"b": 3, "c": 4})

            pipeline.close()

            with open(filepath, "r", encoding="utf-8-sig") as f:
                reader = f.read()
            self.assertIn("a", reader)
            self.assertIn("b", reader)
            self.assertIn("c", reader)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


class TestDataCleaningPipeline(unittest.TestCase):
    """DataCleaningPipeline测试类 / DataCleaningPipeline test class."""

    def test_strip_strings(self) -> None:
        """测试字符串去空白 / Test string stripping."""
        pipeline = DataCleaningPipeline(strip_strings=True)
        item = {"name": "  hello  ", "value": 42}
        result = pipeline.process(item)
        self.assertEqual(result["name"], "hello")
        self.assertEqual(result["value"], 42)

    def test_remove_empty(self) -> None:
        """测试移除空值 / Test removing empty values."""
        pipeline = DataCleaningPipeline(remove_empty=True)
        item = {"name": "hello", "empty": "", "value": 42}
        result = pipeline.process(item)
        self.assertNotIn("empty", result)
        self.assertIn("name", result)

    def test_remove_none(self) -> None:
        """测试移除None / Test removing None."""
        pipeline = DataCleaningPipeline(remove_none=True)
        item = {"name": "hello", "none_val": None, "value": 42}
        result = pipeline.process(item)
        self.assertNotIn("none_val", result)

    def test_max_string_length(self) -> None:
        """测试字符串最大长度 / Test max string length."""
        pipeline = DataCleaningPipeline(max_string_length=10)
        item = {"text": "a" * 100}
        result = pipeline.process(item)
        self.assertEqual(len(result["text"]), 10)

    def test_all_empty_returns_none(self) -> None:
        """测试全空返回None / Test all empty returns None."""
        pipeline = DataCleaningPipeline(remove_empty=True, remove_none=True)
        item = {"empty": "", "none": None}
        result = pipeline.process(item)
        self.assertIsNone(result)


class TestDeduplicationPipeline(unittest.TestCase):
    """DeduplicationPipeline测试类 / DeduplicationPipeline test class."""

    def test_dedup_single_field(self) -> None:
        """测试单字段去重 / Test single field deduplication."""
        pipeline = DeduplicationPipeline(key_fields=["id"])
        pipeline.open()

        r1 = pipeline.process({"id": "1", "name": "Alice"})
        r2 = pipeline.process({"id": "2", "name": "Bob"})
        r3 = pipeline.process({"id": "1", "name": "Alice2"})  # 重复 / duplicate

        self.assertIsNotNone(r1)
        self.assertIsNotNone(r2)
        self.assertIsNone(r3)

    def test_dedup_multiple_fields(self) -> None:
        """测试多字段去重 / Test multi-field deduplication."""
        pipeline = DeduplicationPipeline(key_fields=["first_name", "last_name"])
        pipeline.open()

        r1 = pipeline.process({"first_name": "Alice", "last_name": "Smith"})
        r2 = pipeline.process({"first_name": "Alice", "last_name": "Jones"})
        r3 = pipeline.process({"first_name": "Alice", "last_name": "Smith"})  # 重复 / duplicate

        self.assertIsNotNone(r1)
        self.assertIsNotNone(r2)
        self.assertIsNone(r3)

    def test_no_key_fields(self) -> None:
        """测试无键字段（不去重）/ Test no key fields (no dedup)."""
        pipeline = DeduplicationPipeline(key_fields=[])
        pipeline.open()

        r1 = pipeline.process({"id": "1"})
        r2 = pipeline.process({"id": "1"})
        self.assertIsNotNone(r1)
        self.assertIsNotNone(r2)

    def test_reset_on_open(self) -> None:
        """测试open重置 / Test open reset."""
        pipeline = DeduplicationPipeline(key_fields=["id"])
        pipeline.open()
        pipeline.process({"id": "1"})
        pipeline.open()  # 重置 / reset
        r = pipeline.process({"id": "1"})
        self.assertIsNotNone(r)


class TestPipelineManager(unittest.TestCase):
    """PipelineManager测试类 / PipelineManager test class."""

    def test_add_and_process(self) -> None:
        """测试添加和处理 / Test add and process."""
        manager = PipelineManager()
        manager.add_pipeline(DataCleaningPipeline(strip_strings=True))

        item = {"name": "  hello  "}
        result = manager.process(item)
        self.assertEqual(result["name"], "hello")

    def test_chain_pipelines(self) -> None:
        """测试管道链 / Test pipeline chain."""
        manager = PipelineManager()
        manager.add_pipeline(DataCleaningPipeline(strip_strings=True))
        manager.add_pipeline(DeduplicationPipeline(key_fields=["id"]))
        manager.open()

        r1 = manager.process({"id": "1", "name": "  Alice  "})
        r2 = manager.process({"id": "1", "name": "  Bob  "})  # 去重 / dedup

        self.assertIsNotNone(r1)
        self.assertEqual(r1["name"], "Alice")
        self.assertIsNone(r2)

    def test_remove_pipeline(self) -> None:
        """测试移除管道 / Test removing pipeline."""
        manager = PipelineManager()
        p1 = DataCleaningPipeline()
        p1.name = "cleaner"
        manager.add_pipeline(p1)

        self.assertTrue(manager.remove_pipeline("cleaner"))
        self.assertEqual(len(manager), 0)
        self.assertFalse(manager.remove_pipeline("nonexistent"))

    def test_open_close(self) -> None:
        """测试打开和关闭 / Test open and close."""
        manager = PipelineManager()
        manager.add_pipeline(PrintPipeline())
        manager.open()
        manager.close()
        # 不应抛出异常 / Should not raise exception

    def test_get_stats(self) -> None:
        """测试获取统计 / Test getting stats."""
        manager = PipelineManager()
        manager.add_pipeline(DataCleaningPipeline())
        stats = manager.get_stats()
        self.assertEqual(len(stats), 1)

    def test_process_none_stops_chain(self) -> None:
        """测试None停止管道链 / Test None stops pipeline chain."""
        manager = PipelineManager()
        manager.add_pipeline(DeduplicationPipeline(key_fields=["id"]))
        manager.add_pipeline(DataCleaningPipeline())
        manager.open()

        manager.process({"id": "1"})
        # 第二次相同id，去重返回None，后续管道不执行 / Second same id, dedup returns None
        result = manager.process({"id": "1"})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
