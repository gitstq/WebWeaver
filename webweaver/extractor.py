"""
WebWeaver - 数据提取引擎 / Data Extraction Engine
==================================================
提供结构化数据提取功能，支持CSS选择器、XPath、正则表达式和JSON路径提取。
Provides structured data extraction, supporting CSS selectors, XPath,
regular expressions, and JSON path extraction.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union
from .parser import ParsedDocument, Element
from .selector import Selector, SelectorList
from .exceptions import ExtractionError


class ExtractionRule:
    """数据提取规则 / Data extraction rule.

    定义如何从文档中提取特定数据字段。
    Defines how to extract a specific data field from a document.

    Attributes:
        name: 字段名称 / Field name
        selector_type: 选择器类型（css/xpath/regex/json_path）/
                       Selector type (css/xpath/regex/json_path)
        selector: 选择器表达式 / Selector expression
        attribute: 要提取的属性（空表示提取文本）/ Attribute to extract (empty for text)
        default: 默认值 / Default value
        multiple: 是否提取多个值 / Whether to extract multiple values
        regex: 正则表达式（用于后处理）/ Regex (for post-processing)
        regex_group: 正则捕获组 / Regex capture group
        transform: 转换函数名称 / Transform function name
    """

    def __init__(
        self,
        name: str,
        selector_type: str = "css",
        selector: str = "",
        attribute: str = "",
        default: Any = None,
        multiple: bool = False,
        regex: str = "",
        regex_group: int = 0,
        transform: str = "",
    ) -> None:
        """初始化提取规则 / Initialize extraction rule.

        Args:
            name: 字段名称 / Field name
            selector_type: 选择器类型 / Selector type
            selector: 选择器表达式 / Selector expression
            attribute: 属性名 / Attribute name
            default: 默认值 / Default value
            multiple: 是否提取多个值 / Whether to extract multiple values
            regex: 后处理正则表达式 / Post-processing regex
            regex_group: 正则捕获组索引 / Regex capture group index
            transform: 转换函数名 / Transform function name
        """
        self.name: str = name
        self.selector_type: str = selector_type.lower()
        self.selector: str = selector
        self.attribute: str = attribute
        self.default: Any = default
        self.multiple: bool = multiple
        self.regex: str = regex
        self.regex_group: int = regex_group
        self.transform: str = transform

    def to_dict(self) -> Dict[str, Any]:
        """将规则转换为字典 / Convert rule to dictionary.

        Returns:
            规则的字典表示 / Dictionary representation of rule
        """
        return {
            "name": self.name,
            "selector_type": self.selector_type,
            "selector": self.selector,
            "attribute": self.attribute,
            "default": self.default,
            "multiple": self.multiple,
            "regex": self.regex,
            "regex_group": self.regex_group,
            "transform": self.transform,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionRule":
        """从字典创建提取规则 / Create extraction rule from dictionary.

        Args:
            data: 规则字典 / Rule dictionary

        Returns:
            ExtractionRule实例 / ExtractionRule instance
        """
        return cls(**data)


class Extractor:
    """数据提取引擎 / Data extraction engine.

    根据提取规则从解析后的文档中提取结构化数据。
    Extracts structured data from parsed documents based on extraction rules.

    Attributes:
        rules: 提取规则列表 / Extraction rule list
        transforms: 注册的转换函数 / Registered transform functions
    """

    # 内置转换函数 / Built-in transform functions
    BUILTIN_TRANSFORMS: Dict[str, Any] = {
        "strip": lambda x: x.strip() if isinstance(x, str) else x,
        "lower": lambda x: x.lower() if isinstance(x, str) else x,
        "upper": lambda x: x.upper() if isinstance(x, str) else x,
        "title": lambda x: x.title() if isinstance(x, str) else x,
        "int": lambda x: int(x) if x else 0,
        "float": lambda x: float(x) if x else 0.0,
        "bool": lambda x: bool(x),
        "first": lambda x: x[0] if isinstance(x, list) and x else None,
        "last": lambda x: x[-1] if isinstance(x, list) and x else None,
        "join": lambda x: " ".join(x) if isinstance(x, list) else x,
        "len": lambda x: len(x) if x else 0,
        "replace_spaces": lambda x: re.sub(r'\s+', ' ', x).strip() if isinstance(x, str) else x,
        "remove_html": lambda x: re.sub(r'<[^>]+>', '', x).strip() if isinstance(x, str) else x,
        "extract_number": lambda x: re.sub(r'[^\d.-]', '', x).strip() if isinstance(x, str) else x,
    }

    def __init__(self) -> None:
        """初始化提取器 / Initialize extractor."""
        self.rules: List[ExtractionRule] = []
        self.transforms: Dict[str, Any] = self.BUILTIN_TRANSFORMS.copy()

    def add_rule(self, rule: ExtractionRule) -> "Extractor":
        """添加提取规则 / Add extraction rule.

        Args:
            rule: 提取规则 / Extraction rule

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.rules.append(rule)
        return self

    def add_rules(self, rules: List[ExtractionRule]) -> "Extractor":
        """批量添加提取规则 / Batch add extraction rules.

        Args:
            rules: 提取规则列表 / Extraction rule list

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.rules.extend(rules)
        return self

    def register_transform(self, name: str, func: Any) -> "Extractor":
        """注册自定义转换函数 / Register custom transform function.

        Args:
            name: 函数名称 / Function name
            func: 转换函数 / Transform function

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.transforms[name] = func
        return self

    def clear_rules(self) -> "Extractor":
        """清除所有提取规则 / Clear all extraction rules.

        Returns:
            self，支持链式调用 / self, for method chaining
        """
        self.rules.clear()
        return self

    def extract(self, doc: ParsedDocument) -> Dict[str, Any]:
        """从文档中提取数据 / Extract data from document.

        Args:
            doc: 解析后的文档 / Parsed document

        Returns:
            提取的数据字典 / Extracted data dictionary

        Raises:
            ExtractionError: 提取失败时抛出 / Raised when extraction fails
        """
        result: Dict[str, Any] = {}

        for rule in self.rules:
            try:
                value = self._apply_rule(doc, rule)
                result[rule.name] = value
            except Exception as e:
                if rule.default is not None:
                    result[rule.name] = rule.default
                else:
                    raise ExtractionError(
                        rule.name,
                        f"规则 '{rule.name}' 执行失败 / Rule '{rule.name}' failed: {e}",
                    )

        return result

    def _apply_rule(self, doc: ParsedDocument, rule: ExtractionRule) -> Any:
        """应用单个提取规则 / Apply a single extraction rule.

        Args:
            doc: 解析后的文档 / Parsed document
            rule: 提取规则 / Extraction rule

        Returns:
            提取的值 / Extracted value
        """
        if rule.selector_type == "css":
            value = self._extract_by_css(doc, rule)
        elif rule.selector_type == "xpath":
            value = self._extract_by_xpath(doc, rule)
        elif rule.selector_type == "regex":
            value = self._extract_by_regex(doc, rule)
        elif rule.selector_type == "json_path":
            value = self._extract_by_json_path(doc, rule)
        elif rule.selector_type == "meta":
            value = self._extract_by_meta(doc, rule)
        elif rule.selector_type == "title":
            value = doc.title
        elif rule.selector_type == "url":
            value = doc.raw_html  # URL通常在文档外部传入
        else:
            value = rule.default

        # 应用正则后处理 / Apply regex post-processing
        if rule.regex and value is not None:
            value = self._apply_regex(value, rule.regex, rule.regex_group)

        # 应用转换函数 / Apply transform function
        if rule.transform and rule.transform in self.transforms:
            try:
                value = self.transforms[rule.transform](value)
            except Exception:
                pass

        # 如果值为None，返回默认值 / If value is None, return default
        if value is None:
            value = rule.default

        return value

    def _extract_by_css(self, doc: ParsedDocument, rule: ExtractionRule) -> Any:
        """使用CSS选择器提取 / Extract using CSS selector.

        Args:
            doc: 解析后的文档 / Parsed document
            rule: 提取规则 / Extraction rule

        Returns:
            提取的值 / Extracted value
        """
        selector = Selector(doc.root)
        elements = selector.css(rule.selector)

        if not elements:
            return rule.default if not rule.multiple else []

        if rule.multiple:
            if rule.attribute:
                return elements.attr(rule.attribute)
            return elements.all_text if hasattr(elements, "all_text") else [
                elem.get_text() for elem in elements
            ]
        else:
            elem = elements.first()
            if elem is None:
                return rule.default
            if rule.attribute:
                return elem.get_attr(rule.attribute, rule.default)
            return elem.get_text()

    def _extract_by_xpath(self, doc: ParsedDocument, rule: ExtractionRule) -> Any:
        """使用XPath提取 / Extract using XPath.

        Args:
            doc: 解析后的文档 / Parsed document
            rule: 提取规则 / Extraction rule

        Returns:
            提取的值 / Extracted value
        """
        selector = Selector(doc.root)
        elements = selector.xpath(rule.selector)

        if not elements:
            return rule.default if not rule.multiple else []

        if rule.multiple:
            if rule.attribute:
                return [elem.get_attr(rule.attribute) for elem in elements]
            return [elem.get_text() for elem in elements]
        else:
            elem = elements.first()
            if elem is None:
                return rule.default
            if rule.attribute:
                return elem.get_attr(rule.attribute, rule.default)
            return elem.get_text()

    def _extract_by_regex(self, doc: ParsedDocument, rule: ExtractionRule) -> Any:
        """使用正则表达式提取 / Extract using regex.

        Args:
            doc: 解析后的文档 / Parsed document
            rule: 提取规则 / Extraction rule

        Returns:
            提取的值 / Extracted value
        """
        text = doc.raw_html
        if not text:
            return rule.default

        try:
            pattern = re.compile(rule.selector, re.DOTALL | re.IGNORECASE)
            matches = pattern.findall(text)

            if not matches:
                return rule.default if not rule.multiple else []

            if rule.multiple:
                return matches

            if isinstance(matches[0], tuple):
                return matches[0][rule.regex_group] if rule.regex_group < len(matches[0]) else matches[0][0]
            return matches[0]
        except re.error:
            return rule.default

    def _extract_by_json_path(self, doc: ParsedDocument, rule: ExtractionRule) -> Any:
        """使用JSON路径提取 / Extract using JSON path.

        支持简单的点号路径语法，如 data.items[0].name。
        Supports simple dot-notation path syntax, e.g. data.items[0].name.

        Args:
            doc: 解析后的文档 / Parsed document
            rule: 提取规则 / Extraction rule

        Returns:
            提取的值 / Extracted value
        """
        try:
            if doc.content_type == "json":
                data = json.loads(doc.root.text)
            else:
                # 尝试从页面中提取JSON数据 / Try to extract JSON from page
                json_match = re.search(
                    r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',
                    doc.raw_html,
                    re.DOTALL,
                )
                if json_match:
                    data = json.loads(json_match.group(1).strip())
                else:
                    return rule.default

            return self._resolve_json_path(data, rule.selector)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
            return rule.default

    def _resolve_json_path(self, data: Any, path: str) -> Any:
        """解析JSON路径 / Resolve JSON path.

        Args:
            data: JSON数据 / JSON data
            path: 点号分隔的路径 / Dot-separated path

        Returns:
            路径对应的值 / Value at path
        """
        if not path:
            return data

        current = data
        parts = path.split(".")

        for part in parts:
            if not part:
                continue

            # 处理数组索引 / Handle array index
            array_match = re.match(r'(\w+)\[(\d+)\]', part)
            if array_match:
                key = array_match.group(1)
                index = int(array_match.group(2))
                if isinstance(current, dict):
                    current = current.get(key, {})
                if isinstance(current, list) and index < len(current):
                    current = current[index]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

            if current is None:
                return None

        return current

    def _extract_by_meta(self, doc: ParsedDocument, rule: ExtractionRule) -> Any:
        """从meta标签提取 / Extract from meta tags.

        Args:
            doc: 解析后的文档 / Parsed document
            rule: 提取规则 / Extraction rule

        Returns:
            提取的值 / Extracted value
        """
        selector_name = rule.selector or rule.name
        return doc.meta.get(selector_name, rule.default)

    def _apply_regex(self, value: Any, pattern: str, group: int = 0) -> Any:
        """对值应用正则表达式 / Apply regex to value.

        Args:
            value: 输入值 / Input value
            pattern: 正则表达式 / Regex pattern
            group: 捕获组索引 / Capture group index

        Returns:
            匹配结果 / Match result
        """
        if value is None:
            return None

        text = str(value)
        try:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return match.group(group)
                except IndexError:
                    return match.group(0)
        except re.error:
            pass

        return value

    def extract_batch(self, docs: List[ParsedDocument]) -> List[Dict[str, Any]]:
        """批量提取数据 / Batch extract data.

        Args:
            docs: 文档列表 / Document list

        Returns:
            提取结果列表 / Extraction result list
        """
        results: List[Dict[str, Any]] = []
        for doc in docs:
            try:
                result = self.extract(doc)
                results.append(result)
            except ExtractionError:
                results.append({})
        return results

    @classmethod
    def from_rules_file(cls, filepath: str) -> "Extractor":
        """从JSON文件加载提取规则 / Load extraction rules from JSON file.

        Args:
            filepath: 规则文件路径 / Rules file path

        Returns:
            配置好的Extractor实例 / Configured Extractor instance
        """
        with open(filepath, "r", encoding="utf-8") as f:
            rules_data = json.load(f)

        extractor = cls()
        for rule_data in rules_data.get("rules", []):
            rule = ExtractionRule.from_dict(rule_data)
            extractor.add_rule(rule)

        return extractor
