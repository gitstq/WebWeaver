"""
WebWeaver - CSS选择器风格元素提取器 / CSS Selector Style Element Extractor
===========================================================================
提供CSS选择器风格的元素查找功能，支持常见的选择器语法。
Provides CSS selector style element finding functionality,
supporting common selector syntax.
"""

import re
from typing import Dict, List, Optional, Union
from .parser import Element
from .exceptions import SelectorError


class SelectorList:
    """选择器结果列表 / Selector result list.

    封装选择器匹配的元素列表，提供链式调用接口。
    Encapsulates a list of elements matched by a selector,
    providing a chainable interface.

    Attributes:
        elements: 匹配的元素列表 / Matched element list
    """

    def __init__(self, elements: Optional[List[Element]] = None) -> None:
        """初始化选择器列表 / Initialize selector list.

        Args:
            elements: 元素列表 / Element list
        """
        self.elements: List[Element] = elements or []

    def css(self, query: str) -> "SelectorList":
        """在结果中进一步使用CSS选择器筛选 / Further filter results with CSS selector.

        Args:
            query: CSS选择器 / CSS selector

        Returns:
            新的选择器结果列表 / New selector result list
        """
        results: List[Element] = []
        for elem in self.elements:
            matched = _match_css(elem, query)
            results.extend(matched)
        return SelectorList(results)

    def text(self, separator: str = " ", strip: bool = True) -> str:
        """获取所有元素的文本内容 / Get text content of all elements.

        Args:
            separator: 文本连接符 / Text separator
            strip: 是否去除首尾空白 / Whether to strip whitespace

        Returns:
            合并后的文本 / Merged text
        """
        texts: List[str] = []
        for elem in self.elements:
            t = elem.get_text(separator=separator, strip=strip)
            if t:
                texts.append(t)
        return separator.join(texts)

    def attr(self, name: str) -> List[str]:
        """获取所有元素的指定属性 / Get specified attribute of all elements.

        Args:
            name: 属性名 / Attribute name

        Returns:
            属性值列表 / Attribute value list
        """
        return [elem.get_attr(name) for elem in self.elements]

    def attrs(self, name: str) -> List[str]:
        """获取所有元素的指定属性（同attr）/ Get specified attribute of all elements (same as attr).

        Args:
            name: 属性名 / Attribute name

        Returns:
            属性值列表 / Attribute value list
        """
        return self.attr(name)

    def first(self) -> Optional[Element]:
        """获取第一个元素 / Get first element.

        Returns:
            第一个元素或None / First element or None
        """
        return self.elements[0] if self.elements else None

    def last(self) -> Optional[Element]:
        """获取最后一个元素 / Get last element.

        Returns:
            最后一个元素或None / Last element or None
        """
        return self.elements[-1] if self.elements else None

    def get(self, index: int = 0, default: Optional[Element] = None) -> Optional[Element]:
        """按索引获取元素 / Get element by index.

        Args:
            index: 索引 / Index
            default: 默认值 / Default value

        Returns:
            指定索引的元素 / Element at specified index
        """
        try:
            return self.elements[index]
        except IndexError:
            return default

    def all(self) -> List[Element]:
        """获取所有元素 / Get all elements.

        Returns:
            所有元素列表 / All elements list
        """
        return self.elements

    def filter(self, predicate) -> "SelectorList":
        """使用自定义函数过滤元素 / Filter elements with custom function.

        Args:
            predicate: 过滤函数，接受Element返回bool / Filter function

        Returns:
            过滤后的选择器列表 / Filtered selector list
        """
        return SelectorList([e for e in self.elements if predicate(e)])

    def __len__(self) -> int:
        """返回元素数量 / Return element count."""
        return len(self.elements)

    def __bool__(self) -> bool:
        """是否有元素 / Whether has elements."""
        return len(self.elements) > 0

    def __iter__(self):
        """迭代元素 / Iterate elements."""
        return iter(self.elements)

    def __getitem__(self, index: int) -> Element:
        """按索引获取元素 / Get element by index."""
        return self.elements[index]

    def __repr__(self) -> str:
        """返回字符串表示 / Return string representation."""
        return f"SelectorList(count={len(self.elements)})"


class Selector:
    """CSS选择器 / CSS selector.

    提供CSS选择器风格的元素查找功能。
    Provides CSS selector style element finding functionality.

    Attributes:
        root: 根元素 / Root element
    """

    def __init__(self, root: Element) -> None:
        """初始化选择器 / Initialize selector.

        Args:
            root: 根元素 / Root element
        """
        self.root: Element = root

    def css(self, query: str) -> SelectorList:
        """使用CSS选择器查找元素 / Find elements using CSS selector.

        支持的语法：
        Supported syntax:
        - 标签选择器: div, p, a / Tag selectors: div, p, a
        - ID选择器: #myid / ID selector: #myid
        - 类选择器: .myclass / Class selector: .myclass
        - 属性选择器: [href], [name=value] / Attribute selectors: [href], [name=value]
        - 组合选择器: div.class, div#id / Combined: div.class, div#id
        - 后代选择器: div p / Descendant: div p
        - 子选择器: div > p / Child: div > p

        Args:
            query: CSS选择器字符串 / CSS selector string

        Returns:
            匹配的元素列表 / Matched element list

        Raises:
            SelectorError: 选择器语法错误 / Selector syntax error
        """
        if not query or not isinstance(query, str):
            raise SelectorError(query, "选择器不能为空 / Selector cannot be empty")

        query = query.strip()
        matched = _match_css(self.root, query)
        return SelectorList(matched)

    def xpath(self, query: str) -> SelectorList:
        """使用简化的XPath查找元素 / Find elements using simplified XPath.

        支持的XPath语法（简化版）：
        Supported XPath syntax (simplified):
        - //tag: 查找所有tag元素 / Find all tag elements
        - //tag[@attr]: 查找有attr属性的tag / Find tag with attr attribute
        - //tag[@attr='value']: 查找attr=value的tag / Find tag with attr=value
        - //tag[text()='value']: 查找文本为value的tag / Find tag with text=value
        - /root/tag: 从根开始的路径 / Path from root

        Args:
            query: XPath表达式 / XPath expression

        Returns:
            匹配的元素列表 / Matched element list
        """
        if not query or not isinstance(query, str):
            raise SelectorError(query, "XPath表达式不能为空 / XPath expression cannot be empty")

        query = query.strip()
        matched = _match_xpath(self.root, query)
        return SelectorList(matched)

    def text(self) -> str:
        """获取根元素的文本内容 / Get root element's text content.

        Returns:
            文本内容 / Text content
        """
        return self.root.get_text()

    def attr(self, name: str) -> str:
        """获取根元素的属性 / Get root element's attribute.

        Args:
            name: 属性名 / Attribute name

        Returns:
            属性值 / Attribute value
        """
        return self.root.get_attr(name)

    def all(self) -> SelectorList:
        """获取所有子元素 / Get all child elements.

        Returns:
            所有子元素列表 / All child elements list
        """
        return SelectorList(self.root.children)

    def find(self, query: str) -> Optional[Element]:
        """查找第一个匹配的元素 / Find first matching element.

        Args:
            query: CSS选择器 / CSS selector

        Returns:
            第一个匹配元素或None / First matching element or None
        """
        result = self.css(query)
        return result.first()

    def find_all(self, query: str) -> List[Element]:
        """查找所有匹配的元素 / Find all matching elements.

        Args:
            query: CSS选择器 / CSS selector

        Returns:
            匹配元素列表 / Matching element list
        """
        return self.css(query).all()


def _parse_css_selector(query: str) -> List[Dict[str, str]]:
    """解析CSS选择器为条件列表 / Parse CSS selector to condition list.

    将CSS选择器字符串解析为结构化的条件列表。
    Parses CSS selector string into a structured condition list.

    Args:
        query: CSS选择器字符串 / CSS selector string

    Returns:
        条件字典列表 / Condition dictionary list
    """
    conditions: List[Dict[str, str]] = []

    # 分割后代选择器 / Split descendant selectors
    parts = query.split()

    for part in parts:
        cond: Dict[str, str] = {"tag": "", "id": "", "classes": [], "attrs": {}, "attr_ops": {}}

        # 解析属性选择器 / Parse attribute selectors
        attr_matches = re.findall(r'\[([^\]]+)\]', part)
        for attr_match in attr_matches:
            part = part.replace(f"[{attr_match}]", "")
            # 支持运算符: =, ^=, $=, *=, ~=, |=
            # Support operators: =, ^=, $=, *=, ~=, |=
            op_match = re.match(r'([^\s=^$*~|]+)\s*([\^$*~|]?=)\s*["\']?([^"\']*)["\']?', attr_match)
            if op_match:
                attr_name = op_match.group(1).strip()
                attr_op = op_match.group(2)
                attr_value = op_match.group(3)
                cond["attrs"][attr_name] = attr_value
                cond["attr_ops"][attr_name] = attr_op
            else:
                cond["attrs"][attr_match] = ""
                cond["attr_ops"][attr_match] = "exists"

        # 解析ID选择器 / Parse ID selector
        id_match = re.search(r'#([a-zA-Z0-9_-]+)', part)
        if id_match:
            cond["id"] = id_match.group(1)
            part = part.replace(f"#{id_match.group(1)}", "")

        # 解析类选择器 / Parse class selectors
        class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', part)
        if class_matches:
            cond["classes"] = class_matches
            for cls in class_matches:
                part = part.replace(f".{cls}", "")

        # 剩余部分为标签名 / Remaining part is tag name
        cond["tag"] = part.strip().lower()

        conditions.append(cond)

    return conditions


def _element_matches_condition(element: Element, condition: Dict[str, str]) -> bool:
    """检查元素是否匹配单个条件 / Check if element matches a single condition.

    Args:
        element: 待检查的元素 / Element to check
        condition: 匹配条件 / Match condition

    Returns:
        是否匹配 / Whether matched
    """
    # 标签匹配 / Tag match
    tag = condition.get("tag", "")
    if tag and element.tag != tag:
        return False

    # ID匹配 / ID match
    elem_id = condition.get("id", "")
    if elem_id and element.id != elem_id:
        return False

    # 类匹配 / Class match
    required_classes = condition.get("classes", [])
    if required_classes:
        elem_classes = set(element.classes)
        for cls in required_classes:
            if cls not in elem_classes:
                return False

    # 属性匹配 / Attribute match
    required_attrs = condition.get("attrs", {})
    attr_ops = condition.get("attr_ops", {})
    if required_attrs:
        for attr_name, attr_value in required_attrs.items():
            elem_value = element.attrs.get(attr_name, "")
            op = attr_ops.get(attr_name, "=")

            if op == "exists":
                # 仅检查属性是否存在 / Only check if attribute exists
                if attr_name not in element.attrs:
                    return False
            elif op == "^=":
                # 前缀匹配 / Prefix match
                if not elem_value.startswith(attr_value):
                    return False
            elif op == "$=":
                # 后缀匹配 / Suffix match
                if not elem_value.endswith(attr_value):
                    return False
            elif op == "*=":
                # 包含匹配 / Contains match
                if attr_value not in elem_value:
                    return False
            elif op == "~=":
                # 空格分隔的词匹配 / Space-separated word match
                if attr_value not in elem_value.split():
                    return False
            elif op == "|=":
                # 前缀或精确匹配 / Prefix or exact match
                if not (elem_value == attr_value or elem_value.startswith(attr_value + "-")):
                    return False
            else:
                # 精确匹配（默认）/ Exact match (default)
                if attr_value:
                    if elem_value != attr_value:
                        return False
                else:
                    if attr_name not in element.attrs:
                        return False

    return True


def _match_css(root: Element, query: str) -> List[Element]:
    """使用CSS选择器在元素树中查找 / Find elements in tree using CSS selector.

    Args:
        root: 根元素 / Root element
        query: CSS选择器 / CSS selector

    Returns:
        匹配的元素列表 / Matched element list
    """
    conditions = _parse_css_selector(query)

    if not conditions:
        return []

    # 处理单层选择器 / Handle single-level selector
    if len(conditions) == 1:
        return _find_matching_elements(root, conditions[0])

    # 处理多层选择器（后代选择器）/ Handle multi-level selectors (descendant)
    return _find_descendant_match(root, conditions, 0)


def _find_matching_elements(root: Element, condition: Dict[str, str]) -> List[Element]:
    """在元素树中递归查找匹配条件的元素 / Recursively find matching elements.

    Args:
        root: 根元素 / Root element
        condition: 匹配条件 / Match condition

    Returns:
        匹配的元素列表 / Matched element list
    """
    results: List[Element] = []

    # 检查当前元素（跳过根节点）/ Check current element (skip root node)
    if root.tag != "__root__" and _element_matches_condition(root, condition):
        results.append(root)

    # 递归检查子元素 / Recursively check children
    for child in root.children:
        results.extend(_find_matching_elements(child, condition))

    return results


def _find_descendant_match(
    root: Element, conditions: List[Dict[str, str]], index: int
) -> List[Element]:
    """查找匹配多层后代选择器的元素 / Find elements matching multi-level descendant selector.

    Args:
        root: 根元素 / Root element
        conditions: 条件列表 / Condition list
        index: 当前条件索引 / Current condition index

    Returns:
        匹配的元素列表 / Matched element list
    """
    if index >= len(conditions):
        return []

    condition = conditions[index]
    results: List[Element] = []

    # 在当前层级查找匹配当前条件的元素 / Find elements matching current condition
    matching = _find_matching_elements(root, condition)

    if index == len(conditions) - 1:
        # 最后一个条件，返回匹配结果 / Last condition, return matches
        return matching

    # 对每个匹配的元素，递归查找后续条件 / For each match, recursively find subsequent conditions
    for elem in matching:
        results.extend(_find_descendant_match(elem, conditions, index + 1))

    return results


def _match_xpath(root: Element, query: str) -> List[Element]:
    """使用简化XPath在元素树中查找 / Find elements in tree using simplified XPath.

    Args:
        root: 根元素 / Root element
        query: XPath表达式 / XPath expression

    Returns:
        匹配的元素列表 / Matched element list
    """
    results: List[Element] = []

    # 解析XPath / Parse XPath
    query = query.strip()

    # 处理 //tag 格式 / Handle //tag format
    if query.startswith("//"):
        xpath_part = query[2:]
        return _xpath_find_all(root, xpath_part)

    # 处理 /root/tag 格式 / Handle /root/tag format
    if query.startswith("/"):
        parts = query.strip("/").split("/")
        return _xpath_path_find(root, parts)

    return results


def _xpath_find_all(root: Element, xpath_part: str) -> List[Element]:
    """XPath // 查找 / XPath // find.

    Args:
        root: 根元素 / Root element
        xpath_part: XPath部分表达式 / XPath partial expression

    Returns:
        匹配的元素列表 / Matched element list
    """
    results: List[Element] = []

    # 解析标签和条件 / Parse tag and conditions
    tag = ""
    attr_conditions: Dict[str, str] = {}
    text_condition: Optional[str] = None

    # 提取属性条件 / Extract attribute conditions
    attr_matches = re.findall(r'\[@([^\]=]+)(?:=["\']([^"\']*)["\'])?\]', xpath_part)
    for attr_name, attr_value in attr_matches:
        attr_conditions[attr_name] = attr_value

    # 提取文本条件 / Extract text condition
    text_match = re.search(r'\[text\(\)\s*=\s*["\']([^"\']*)["\']\]', xpath_part)
    if text_match:
        text_condition = text_match.group(1)

    # 提取标签名 / Extract tag name
    tag = re.sub(r'\[.*?\]', '', xpath_part).strip()

    # 递归查找 / Recursively find
    def _search(elem: Element) -> None:
        if elem.tag != "__root__":
            if not tag or elem.tag == tag:
                # 检查属性条件 / Check attribute conditions
                attr_match = True
                for attr_name, attr_value in attr_conditions.items():
                    elem_val = elem.attrs.get(attr_name, "")
                    if attr_value and elem_val != attr_value:
                        attr_match = False
                        break
                    elif not attr_value and attr_name not in elem.attrs:
                        attr_match = False
                        break

                # 检查文本条件 / Check text condition
                text_match = True
                if text_condition is not None:
                    elem_text = elem.get_text().strip()
                    if elem_text != text_condition:
                        text_match = False

                if attr_match and text_match:
                    results.append(elem)

        for child in elem.children:
            _search(child)

    _search(root)
    return results


def _xpath_path_find(root: Element, parts: List[str]) -> List[Element]:
    """XPath路径查找 / XPath path find.

    Args:
        root: 根元素 / Root element
        parts: 路径部分列表 / Path part list

    Returns:
        匹配的元素列表 / Matched element list
    """
    if not parts:
        return []

    current_part = parts[0]
    remaining = parts[1:]

    # 查找当前层级的匹配元素 / Find matching elements at current level
    tag = re.sub(r'\[.*?\]', '', current_part).strip()
    matching: List[Element] = []

    for child in root.children:
        if not tag or child.tag == tag:
            matching.append(child)

    if not remaining:
        return matching

    # 继续查找下一层级 / Continue to next level
    results: List[Element] = []
    for elem in matching:
        results.extend(_xpath_path_find(elem, remaining))

    return results
