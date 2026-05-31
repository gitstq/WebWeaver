"""
WebWeaver - HTML/JSON解析器 / HTML/JSON Parser
==============================================
基于Python标准库html.parser实现零外部依赖的HTML解析。
Implements zero-external-dependency HTML parsing based on Python's
standard library html.parser.
"""

import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from .exceptions import ParseError


class Element:
    """HTML元素节点 / HTML element node.

    表示解析后的HTML元素，包含标签名、属性、子元素和文本内容。
    Represents a parsed HTML element with tag name, attributes,
    child elements, and text content.

    Attributes:
        tag: 标签名（小写）/ Tag name (lowercase)
        attrs: 属性字典 / Attribute dictionary
        children: 子元素列表 / Child element list
        text: 直接文本内容 / Direct text content
        parent: 父元素 / Parent element
        raw_html: 原始HTML / Raw HTML
    """

    def __init__(
        self,
        tag: str = "",
        attrs: Optional[Dict[str, str]] = None,
        parent: Optional["Element"] = None,
    ) -> None:
        """初始化HTML元素 / Initialize HTML element.

        Args:
            tag: 标签名 / Tag name
            attrs: 属性字典 / Attribute dictionary
            parent: 父元素 / Parent element
        """
        self.tag: str = tag.lower() if tag else ""
        self.attrs: Dict[str, str] = attrs or {}
        self.children: List["Element"] = []
        self.text: str = ""
        self.parent: Optional["Element"] = parent
        self.raw_html: str = ""

    @property
    def id(self) -> str:
        """获取元素的id属性 / Get element's id attribute.

        Returns:
            id属性值 / id attribute value
        """
        return self.attrs.get("id", "")

    @property
    def classes(self) -> List[str]:
        """获取元素的class列表 / Get element's class list.

        Returns:
            class属性值拆分后的列表 / Split class attribute values
        """
        class_str = self.attrs.get("class", "")
        return class_str.split() if class_str else []

    def get_attr(self, name: str, default: str = "") -> str:
        """获取属性值 / Get attribute value.

        Args:
            name: 属性名 / Attribute name
            default: 默认值 / Default value

        Returns:
            属性值 / Attribute value
        """
        return self.attrs.get(name, default)

    def get_text(self, separator: str = " ", strip: bool = True) -> str:
        """递归获取元素及其所有子元素的文本内容 / Recursively get text content.

        Args:
            separator: 文本连接符 / Text separator
            strip: 是否去除首尾空白 / Whether to strip whitespace

        Returns:
            合并后的文本内容 / Merged text content
        """
        texts: List[str] = []

        if self.text:
            texts.append(self.text.strip() if strip else self.text)

        for child in self.children:
            child_text = child.get_text(separator=separator, strip=strip)
            if child_text:
                texts.append(child_text)

        result = separator.join(texts)
        if strip:
            # 合并多余的分隔符 / Merge extra separators
            parts = result.split(separator)
            result = separator.join(p for p in parts if p)
        return result

    def find(self, tag: str = "", attrs: Optional[Dict[str, str]] = None) -> Optional["Element"]:
        """在子元素中查找第一个匹配的元素 / Find first matching element in children.

        Args:
            tag: 标签名（空字符串匹配任意标签）/ Tag name (empty matches any)
            attrs: 属性过滤条件 / Attribute filter conditions

        Returns:
            匹配的元素或None / Matching element or None
        """
        for child in self.children:
            if child._matches(tag, attrs):
                return child
            result = child.find(tag, attrs)
            if result:
                return result
        return None

    def find_all(
        self, tag: str = "", attrs: Optional[Dict[str, str]] = None
    ) -> List["Element"]:
        """在子元素中查找所有匹配的元素 / Find all matching elements in children.

        Args:
            tag: 标签名（空字符串匹配任意标签）/ Tag name (empty matches any)
            attrs: 属性过滤条件 / Attribute filter conditions

        Returns:
            匹配的元素列表 / List of matching elements
        """
        results: List["Element"] = []
        for child in self.children:
            if child._matches(tag, attrs):
                results.append(child)
            results.extend(child.find_all(tag, attrs))
        return results

    def _matches(self, tag: str = "", attrs: Optional[Dict[str, str]] = None) -> bool:
        """检查元素是否匹配给定的标签和属性 / Check if element matches given tag and attrs.

        Args:
            tag: 标签名 / Tag name
            attrs: 属性条件 / Attribute conditions

        Returns:
            是否匹配 / Whether matched
        """
        if tag and self.tag != tag.lower():
            return False
        if attrs:
            for key, value in attrs.items():
                elem_value = self.attrs.get(key, "")
                if value and elem_value != value:
                    return False
                elif not value and key not in self.attrs:
                    return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """将元素转换为字典 / Convert element to dictionary.

        Returns:
            元素的字典表示 / Dictionary representation of element
        """
        result: Dict[str, Any] = {
            "tag": self.tag,
            "attrs": self.attrs,
        }
        if self.text:
            result["text"] = self.text
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        return result

    def __repr__(self) -> str:
        """返回元素的字符串表示 / Return string representation."""
        attrs_str = ""
        if self.attrs:
            attrs_str = " " + " ".join(
                f'{k}="{v}"' for k, v in self.attrs.items()
            )
        return f"<{self.tag}{attrs_str}>"


class _HTMLTreeBuilder(HTMLParser):
    """HTML树构建器 / HTML tree builder.

    内部使用的HTML解析器，将HTML构建为元素树。
    Internal HTML parser that builds an element tree from HTML.
    """

    # 自闭合标签 / Self-closing tags
    VOID_ELEMENTS: set = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    # 原始内容标签（不解析子元素）/ Raw content tags (don't parse children)
    RAW_TEXT_ELEMENTS: set = {"script", "style", "textarea"}

    def __init__(self) -> None:
        """初始化HTML树构建器 / Initialize HTML tree builder."""
        super().__init__(convert_charrefs=False)
        self.root: Element = Element(tag="__root__")
        self._current: Element = self.root
        self._raw_text: str = ""
        self._in_raw_tag: bool = False
        self._raw_tag: str = ""

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        """处理开始标签 / Handle start tag.

        Args:
            tag: 标签名 / Tag name
            attrs: 属性列表 / Attribute list
        """
        tag_lower = tag.lower()
        attrs_dict = {k: (v or "") for k, v in attrs}

        element = Element(tag=tag_lower, attrs=attrs_dict, parent=self._current)
        self._current.children.append(element)

        if tag_lower in self.RAW_TEXT_ELEMENTS:
            self._in_raw_tag = True
            self._raw_tag = tag_lower
            self._raw_text = ""
            self._current = element
        elif tag_lower not in self.VOID_ELEMENTS:
            self._current = element

    def handle_endtag(self, tag: str) -> None:
        """处理结束标签 / Handle end tag.

        Args:
            tag: 标签名 / Tag name
        """
        tag_lower = tag.lower()

        if self._in_raw_tag and tag_lower == self._raw_tag:
            self._in_raw_tag = False
            self._raw_tag = ""
            if self._current.text:
                self._current.text += self._raw_text
            else:
                self._current.text = self._raw_text
            self._raw_text = ""

        if self._current.parent:
            self._current = self._current.parent

    def handle_data(self, data: str) -> None:
        """处理文本数据 / Handle text data.

        Args:
            data: 文本内容 / Text content
        """
        if self._in_raw_tag:
            self._raw_text += data
        else:
            if self._current.text:
                self._current.text += data
            else:
                self._current.text = data

    def handle_entityref(self, name: str) -> None:
        """处理HTML实体引用 / Handle HTML entity reference.

        Args:
            name: 实体名称 / Entity name
        """
        import html
        char = html.unescape(f"&{name};")
        if self._in_raw_tag:
            self._raw_text += char
        else:
            self._current.text = (self._current.text or "") + char

    def handle_charref(self, name: str) -> None:
        """处理字符引用 / Handle character reference.

        Args:
            name: 字符引用名称 / Character reference name
        """
        import html
        char = html.unescape(f"&#{name};")
        if self._in_raw_tag:
            self._raw_text += char
        else:
            self._current.text = (self._current.text or "") + char

    def handle_comment(self, data: str) -> None:
        """处理HTML注释（忽略）/ Handle HTML comments (ignored).

        Args:
            data: 注释内容 / Comment content
        """
        pass

    def error(self, message: str) -> None:
        """处理解析错误 / Handle parse error.

        Args:
            message: 错误消息 / Error message
        """
        pass


class ParsedDocument:
    """解析后的文档 / Parsed document.

    封装解析后的HTML文档，提供便捷的访问接口。
    Encapsulates a parsed HTML document with convenient access interfaces.

    Attributes:
        root: 文档根元素 / Document root element
        title: 文档标题 / Document title
        meta: 元信息字典 / Meta information dictionary
        raw_html: 原始HTML / Raw HTML
        content_type: 内容类型 / Content type
    """

    def __init__(
        self,
        root: Element,
        raw_html: str = "",
        content_type: str = "html",
    ) -> None:
        """初始化解析文档 / Initialize parsed document.

        Args:
            root: 文档根元素 / Document root element
            raw_html: 原始HTML内容 / Raw HTML content
            content_type: 内容类型 / Content type
        """
        self.root: Element = root
        self.raw_html: str = raw_html
        self.content_type: str = content_type
        self.title: str = self._extract_title()
        self.meta: Dict[str, str] = self._extract_meta()

    def _extract_title(self) -> str:
        """提取文档标题 / Extract document title.

        Returns:
            标题文本 / Title text
        """
        title_elem = self.root.find("title")
        if title_elem:
            return title_elem.get_text().strip()
        return ""

    def _extract_meta(self) -> Dict[str, str]:
        """提取文档元信息 / Extract document meta information.

        Returns:
            元信息字典 / Meta information dictionary
        """
        meta: Dict[str, str] = {}
        meta_elems = self.root.find_all("meta")
        for elem in meta_elems:
            name = elem.get_attr("name", elem.get_attr("property", ""))
            content = elem.get_attr("content", "")
            if name and content:
                meta[name] = content
        return meta

    def get_element_by_id(self, element_id: str) -> Optional[Element]:
        """通过ID查找元素 / Find element by ID.

        Args:
            element_id: 元素ID / Element ID

        Returns:
            匹配的元素或None / Matching element or None
        """
        return self.root.find(attrs={"id": element_id})

    def get_elements_by_tag(self, tag: str) -> List[Element]:
        """通过标签名查找所有元素 / Find all elements by tag name.

        Args:
            tag: 标签名 / Tag name

        Returns:
            匹配的元素列表 / List of matching elements
        """
        return self.root.find_all(tag=tag)

    def get_links(self) -> List[Dict[str, str]]:
        """提取所有链接 / Extract all links.

        Returns:
            链接信息列表，每项包含href和text / Link info list with href and text
        """
        links: List[Dict[str, str]] = []
        a_elements = self.root.find_all("a")
        for a in a_elements:
            href = a.get_attr("href", "")
            text = a.get_text().strip()
            if href:
                links.append({"href": href, "text": text})
        return links

    def get_images(self) -> List[Dict[str, str]]:
        """提取所有图片信息 / Extract all image information.

        Returns:
            图片信息列表 / Image info list
        """
        images: List[Dict[str, str]] = []
        img_elements = self.root.find_all("img")
        for img in img_elements:
            src = img.get_attr("src", "")
            alt = img.get_attr("alt", "")
            if src:
                images.append({"src": src, "alt": alt})
        return images

    def to_dict(self) -> Dict[str, Any]:
        """将文档转换为字典 / Convert document to dictionary.

        Returns:
            文档的字典表示 / Dictionary representation of document
        """
        return {
            "title": self.title,
            "meta": self.meta,
            "content_type": self.content_type,
            "root": self.root.to_dict(),
        }

    def __repr__(self) -> str:
        """返回文档的字符串表示 / Return string representation."""
        return f"ParsedDocument(title='{self.title}', type='{self.content_type}')"


class Parser:
    """HTML/JSON解析器 / HTML/JSON parser.

    提供HTML和JSON内容的解析功能，自动检测内容类型。
    Provides parsing functionality for HTML and JSON content,
    with automatic content type detection.

    Attributes:
        encoding: 默认编码 / Default encoding
    """

    def __init__(self, encoding: str = "utf-8") -> None:
        """初始化解析器 / Initialize parser.

        Args:
            encoding: 默认编码 / Default encoding
        """
        self.encoding: str = encoding

    def parse_html(self, html_content: str) -> ParsedDocument:
        """解析HTML内容 / Parse HTML content.

        Args:
            html_content: HTML字符串 / HTML string

        Returns:
            解析后的文档对象 / Parsed document object

        Raises:
            ParseError: 解析失败时抛出 / Raised when parsing fails
        """
        if not html_content or not isinstance(html_content, str):
            raise ParseError("html", "HTML内容为空或类型错误 / HTML content is empty or wrong type")

        try:
            builder = _HTMLTreeBuilder()
            builder.feed(html_content)
            builder.close()

            return ParsedDocument(
                root=builder.root,
                raw_html=html_content,
                content_type="html",
            )
        except Exception as e:
            raise ParseError("html", f"HTML解析失败 / HTML parsing failed: {e}")

    def parse_json(self, text: str) -> Any:
        """解析JSON内容 / Parse JSON content.

        Args:
            text: JSON字符串 / JSON string

        Returns:
            解析后的Python对象 / Parsed Python object

        Raises:
            ParseError: 解析失败时抛出 / Raised when parsing fails
        """
        if not text or not isinstance(text, str):
            raise ParseError("json", "JSON内容为空或类型错误 / JSON content is empty or wrong type")

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ParseError("json", f"JSON解析失败 / JSON parsing failed: {e}")

    def detect_content_type(self, text: str) -> str:
        """检测内容类型 / Detect content type.

        自动判断文本是HTML还是JSON。
        Automatically determines whether text is HTML or JSON.

        Args:
            text: 待检测的文本 / Text to detect

        Returns:
            内容类型（'html', 'json', 'text'）/ Content type
        """
        if not text:
            return "text"

        text_stripped = text.strip()

        # 检查JSON / Check JSON
        if text_stripped.startswith(("{", "[")):
            try:
                json.loads(text_stripped)
                return "json"
            except (json.JSONDecodeError, ValueError):
                pass

        # 检查HTML / Check HTML
        if re.search(r'<(!doctype|html|head|body|div|p|a|span)\b', text_stripped, re.IGNORECASE):
            return "html"

        # 检查是否包含HTML标签 / Check for HTML tags
        if re.search(r'<[a-zA-Z][^>]*>', text_stripped):
            return "html"

        return "text"

    def auto_parse(self, text: str) -> ParsedDocument:
        """自动检测并解析内容 / Auto-detect and parse content.

        Args:
            text: 待解析的文本 / Text to parse

        Returns:
            解析后的文档对象 / Parsed document object

        Raises:
            ParseError: 解析失败时抛出 / Raised when parsing fails
        """
        content_type = self.detect_content_type(text)

        if content_type == "html":
            return self.parse_html(text)
        elif content_type == "json":
            data = self.parse_json(text)
            # 将JSON数据包装为文档 / Wrap JSON data as document
            root = Element(tag="__json_root__")
            root.text = json.dumps(data, ensure_ascii=False)
            return ParsedDocument(
                root=root,
                raw_html=text,
                content_type="json",
            )
        else:
            # 纯文本包装为文档 / Wrap plain text as document
            root = Element(tag="__text_root__")
            root.text = text
            return ParsedDocument(
                root=root,
                raw_html=text,
                content_type="text",
            )
