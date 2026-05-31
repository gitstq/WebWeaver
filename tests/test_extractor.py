"""
WebWeaver - 提取器测试 / Extractor Tests
=========================================
测试数据提取引擎的各项功能。
Tests for data extraction engine functionality.
"""

import json
import unittest
from webweaver.parser import Parser
from webweaver.extractor import Extractor, ExtractionRule


class TestExtractionRule(unittest.TestCase):
    """ExtractionRule测试类 / ExtractionRule test class."""

    def test_init(self) -> None:
        """测试规则初始化 / Test rule initialization."""
        rule = ExtractionRule(
            name="title",
            selector_type="css",
            selector="title",
        )
        self.assertEqual(rule.name, "title")
        self.assertEqual(rule.selector_type, "css")
        self.assertEqual(rule.selector, "title")

    def test_to_dict(self) -> None:
        """测试规则转字典 / Test rule to dict."""
        rule = ExtractionRule(
            name="test",
            selector_type="css",
            selector="div",
            attribute="class",
            default="N/A",
        )
        d = rule.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["selector_type"], "css")
        self.assertEqual(d["default"], "N/A")

    def test_from_dict(self) -> None:
        """测试从字典创建规则 / Test creating rule from dict."""
        data = {
            "name": "test",
            "selector_type": "xpath",
            "selector": "//div",
            "multiple": True,
        }
        rule = ExtractionRule.from_dict(data)
        self.assertEqual(rule.name, "test")
        self.assertEqual(rule.selector_type, "xpath")
        self.assertTrue(rule.multiple)


class TestExtractor(unittest.TestCase):
    """Extractor测试类 / Extractor test class."""

    def setUp(self) -> None:
        """测试前准备 / Test setup."""
        self.parser = Parser()
        self.extractor = Extractor()

    def test_extract_css_text(self) -> None:
        """测试CSS文本提取 / Test CSS text extraction."""
        html = '<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="title",
            selector_type="css",
            selector="title",
        ))
        self.extractor.add_rule(ExtractionRule(
            name="content",
            selector_type="css",
            selector="p",
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["title"], "Test Page")
        self.assertEqual(result["content"], "Hello World")

    def test_extract_css_attribute(self) -> None:
        """测试CSS属性提取 / Test CSS attribute extraction."""
        html = '<html><body><a href="https://example.com">Link</a></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="link_href",
            selector_type="css",
            selector="a",
            attribute="href",
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["link_href"], "https://example.com")

    def test_extract_css_multiple(self) -> None:
        """测试CSS多值提取 / Test CSS multiple value extraction."""
        html = '<html><body><li>A</li><li>B</li><li>C</li></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="items",
            selector_type="css",
            selector="li",
            multiple=True,
        ))

        result = self.extractor.extract(doc)
        self.assertIn("A", result["items"])
        self.assertIn("B", result["items"])

    def test_extract_regex(self) -> None:
        """测试正则提取 / Test regex extraction."""
        html = '<html><body><p>Price: $99.99</p></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="price",
            selector_type="regex",
            selector=r'\$(\d+\.\d+)',
            regex_group=1,
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["price"], "99.99")

    def test_extract_with_default(self) -> None:
        """测试默认值 / Test default value."""
        html = '<html><body><p>content</p></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="nonexistent",
            selector_type="css",
            selector=".nonexistent",
            default="default_value",
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["nonexistent"], "default_value")

    def test_extract_with_transform(self) -> None:
        """测试转换函数 / Test transform function."""
        html = '<html><body><p>  Hello World  </p></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="text",
            selector_type="css",
            selector="p",
            transform="strip",
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["text"], "Hello World")

    def test_extract_with_regex_postprocess(self) -> None:
        """测试正则后处理 / Test regex post-processing."""
        html = '<html><body><p>Found 42 items</p></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="text",
            selector_type="css",
            selector="p",
            regex=r'(\d+)',
            regex_group=0,
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["text"], "42")

    def test_extract_meta(self) -> None:
        """测试meta提取 / Test meta extraction."""
        html = (
            '<html><head>'
            '<meta name="description" content="A test page">'
            '</head><body></body></html>'
        )
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="description",
            selector_type="meta",
            selector="description",
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["description"], "A test page")

    def test_extract_title_type(self) -> None:
        """测试title类型提取 / Test title type extraction."""
        html = '<html><head><title>My Title</title></head><body></body></html>'
        doc = self.parser.parse_html(html)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="page_title",
            selector_type="title",
        ))

        result = self.extractor.extract(doc)
        self.assertEqual(result["page_title"], "My Title")

    def test_builtin_transforms(self) -> None:
        """测试内置转换函数 / Test built-in transform functions."""
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["upper"]("hello"), "HELLO")
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["lower"]("HELLO"), "hello")
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["strip"]("  hi  "), "hi")
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["int"]("42"), 42)
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["float"]("3.14"), 3.14)
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["bool"]("yes"), True)
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["first"](["a", "b"]), "a")
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["last"](["a", "b"]), "b")
        self.assertEqual(Extractor.BUILTIN_TRANSFORMS["len"]([1, 2, 3]), 3)

    def test_register_custom_transform(self) -> None:
        """测试注册自定义转换函数 / Test registering custom transform."""
        extractor = Extractor()
        extractor.register_transform("double", lambda x: x * 2 if isinstance(x, (int, float)) else x)

        self.assertIn("double", extractor.transforms)
        self.assertEqual(extractor.transforms["double"](5), 10)

    def test_extract_batch(self) -> None:
        """测试批量提取 / Test batch extraction."""
        html1 = '<html><head><title>Page 1</title></head><body></body></html>'
        html2 = '<html><head><title>Page 2</title></head><body></body></html>'

        doc1 = self.parser.parse_html(html1)
        doc2 = self.parser.parse_html(html2)

        self.extractor.clear_rules()
        self.extractor.add_rule(ExtractionRule(
            name="title",
            selector_type="css",
            selector="title",
        ))

        results = self.extractor.extract_batch([doc1, doc2])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Page 1")
        self.assertEqual(results[1]["title"], "Page 2")

    def test_chain_add_rules(self) -> None:
        """测试链式添加规则 / Test chain adding rules."""
        extractor = Extractor()
        extractor.add_rule(ExtractionRule(name="a", selector_type="title"))
        extractor.add_rule(ExtractionRule(name="b", selector_type="title"))
        self.assertEqual(len(extractor.rules), 2)


if __name__ == "__main__":
    unittest.main()
