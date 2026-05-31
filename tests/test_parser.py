"""
WebWeaver - 解析器测试 / Parser Tests
======================================
测试HTML/JSON解析器的各项功能。
Tests for HTML/JSON parser functionality.
"""

import json
import unittest
from webweaver.parser import Parser, ParsedDocument, Element, _HTMLTreeBuilder


class TestElement(unittest.TestCase):
    """Element测试类 / Element test class."""

    def test_init(self) -> None:
        """测试元素初始化 / Test element initialization."""
        elem = Element(tag="div", attrs={"class": "test", "id": "myid"})
        self.assertEqual(elem.tag, "div")
        self.assertEqual(elem.id, "myid")
        self.assertEqual(elem.classes, ["test"])

    def test_tag_lowercase(self) -> None:
        """测试标签名小写化 / Test tag name lowercasing."""
        elem = Element(tag="DIV")
        self.assertEqual(elem.tag, "div")

    def test_get_attr(self) -> None:
        """测试获取属性 / Test getting attribute."""
        elem = Element(tag="a", attrs={"href": "https://example.com"})
        self.assertEqual(elem.get_attr("href"), "https://example.com")
        self.assertEqual(elem.get_attr("nonexistent"), "")
        self.assertEqual(elem.get_attr("nonexistent", "default"), "default")

    def test_get_text_simple(self) -> None:
        """测试简单文本获取 / Test simple text retrieval."""
        elem = Element(tag="p")
        elem.text = "Hello World"
        self.assertEqual(elem.get_text(), "Hello World")

    def test_get_text_with_children(self) -> None:
        """测试含子元素的文本获取 / Test text retrieval with children."""
        parent = Element(tag="div")
        parent.text = "Hello "
        child = Element(tag="span")
        child.text = "World"
        parent.children.append(child)
        self.assertEqual(parent.get_text(), "Hello World")

    def test_find(self) -> None:
        """测试元素查找 / Test element finding."""
        root = Element(tag="div")
        child = Element(tag="p", attrs={"class": "content"})
        root.children.append(child)

        found = root.find("p")
        self.assertIsNotNone(found)
        self.assertEqual(found.tag, "p")

        not_found = root.find("a")
        self.assertIsNone(not_found)

    def test_find_all(self) -> None:
        """测试查找所有元素 / Test finding all elements."""
        root = Element(tag="div")
        p1 = Element(tag="p")
        p2 = Element(tag="p")
        root.children.append(p1)
        root.children.append(p2)

        found = root.find_all("p")
        self.assertEqual(len(found), 2)

    def test_find_with_attrs(self) -> None:
        """测试带属性的查找 / Test finding with attributes."""
        root = Element(tag="div")
        p1 = Element(tag="p", attrs={"class": "a"})
        p2 = Element(tag="p", attrs={"class": "b"})
        root.children.append(p1)
        root.children.append(p2)

        found = root.find("p", {"class": "a"})
        self.assertIsNotNone(found)
        self.assertEqual(found.classes, ["a"])

    def test_to_dict(self) -> None:
        """测试转换为字典 / Test conversion to dict."""
        elem = Element(tag="div", attrs={"id": "test"})
        elem.text = "hello"
        d = elem.to_dict()
        self.assertEqual(d["tag"], "div")
        self.assertEqual(d["attrs"]["id"], "test")
        self.assertEqual(d["text"], "hello")

    def test_repr(self) -> None:
        """测试repr / Test repr."""
        elem = Element(tag="div", attrs={"id": "test"})
        r = repr(elem)
        self.assertIn("div", r)
        self.assertIn("test", r)


class TestHTMLTreeBuilder(unittest.TestCase):
    """HTML树构建器测试类 / HTML tree builder test class."""

    def test_simple_html(self) -> None:
        """测试简单HTML解析 / Test simple HTML parsing."""
        builder = _HTMLTreeBuilder()
        builder.feed("<html><body><p>Hello</p></body></html>")
        builder.close()

        p_elements = builder.root.find_all("p")
        self.assertEqual(len(p_elements), 1)
        self.assertEqual(p_elements[0].get_text(), "Hello")

    def test_nested_elements(self) -> None:
        """测试嵌套元素解析 / Test nested element parsing."""
        builder = _HTMLTreeBuilder()
        builder.feed("<div><p><span>text</span></p></div>")
        builder.close()

        divs = builder.root.find_all("div")
        self.assertEqual(len(divs), 1)
        spans = divs[0].find_all("span")
        self.assertEqual(len(spans), 1)

    def test_attributes(self) -> None:
        """测试属性解析 / Test attribute parsing."""
        builder = _HTMLTreeBuilder()
        builder.feed('<a href="https://example.com" class="link">Link</a>')
        builder.close()

        a_elements = builder.root.find_all("a")
        self.assertEqual(len(a_elements), 1)
        self.assertEqual(a_elements[0].get_attr("href"), "https://example.com")
        self.assertEqual(a_elements[0].classes, ["link"])

    def test_void_elements(self) -> None:
        """测试自闭合标签 / Test void elements."""
        builder = _HTMLTreeBuilder()
        builder.feed('<div><img src="test.jpg"><br></div>')
        builder.close()

        imgs = builder.root.find_all("img")
        self.assertEqual(len(imgs), 1)
        brs = builder.root.find_all("br")
        self.assertEqual(len(brs), 1)

    def test_script_tag(self) -> None:
        """测试script标签 / Test script tag."""
        builder = _HTMLTreeBuilder()
        builder.feed('<script>var x = "<p>not a tag</p>";</script>')
        builder.close()

        scripts = builder.root.find_all("script")
        self.assertEqual(len(scripts), 1)
        self.assertIn("var x", scripts[0].text)

    def test_multiple_same_tags(self) -> None:
        """测试多个相同标签 / Test multiple same tags."""
        builder = _HTMLTreeBuilder()
        builder.feed('<ul><li>a</li><li>b</li><li>c</li></ul>')
        builder.close()

        lis = builder.root.find_all("li")
        self.assertEqual(len(lis), 3)
        texts = [li.get_text() for li in lis]
        self.assertEqual(texts, ["a", "b", "c"])

    def test_html_entities(self) -> None:
        """测试HTML实体 / Test HTML entities."""
        builder = _HTMLTreeBuilder()
        builder.feed("<p>Hello &amp; World &lt;3&gt;</p>")
        builder.close()

        p = builder.root.find("p")
        self.assertIsNotNone(p)
        text = p.get_text()
        self.assertIn("&", text)
        self.assertIn("<", text)

    def test_id_attribute(self) -> None:
        """测试ID属性 / Test ID attribute."""
        builder = _HTMLTreeBuilder()
        builder.feed('<div id="main"><p id="content">text</p></div>')
        builder.close()

        content = builder.root.find(attrs={"id": "content"})
        self.assertIsNotNone(content)
        self.assertEqual(content.get_text(), "text")


class TestParsedDocument(unittest.TestCase):
    """ParsedDocument测试类 / ParsedDocument test class."""

    def _create_doc(self, html: str) -> ParsedDocument:
        """创建解析文档的辅助方法 / Helper to create parsed document."""
        builder = _HTMLTreeBuilder()
        builder.feed(html)
        builder.close()
        return ParsedDocument(root=builder.root, raw_html=html, content_type="html")

    def test_title_extraction(self) -> None:
        """测试标题提取 / Test title extraction."""
        doc = self._create_doc(
            "<html><head><title>Test Title</title></head><body></body></html>"
        )
        self.assertEqual(doc.title, "Test Title")

    def test_meta_extraction(self) -> None:
        """测试元信息提取 / Test meta extraction."""
        doc = self._create_doc(
            '<html><head>'
            '<meta name="description" content="A test page">'
            '<meta name="keywords" content="test,web">'
            '</head><body></body></html>'
        )
        self.assertEqual(doc.meta["description"], "A test page")
        self.assertEqual(doc.meta["keywords"], "test,web")

    def test_get_links(self) -> None:
        """测试链接提取 / Test link extraction."""
        doc = self._create_doc(
            '<html><body>'
            '<a href="https://example.com">Link 1</a>'
            '<a href="/page2">Link 2</a>'
            '</body></html>'
        )
        links = doc.get_links()
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0]["href"], "https://example.com")
        self.assertEqual(links[1]["href"], "/page2")

    def test_get_images(self) -> None:
        """测试图片提取 / Test image extraction."""
        doc = self._create_doc(
            '<html><body>'
            '<img src="image1.jpg" alt="Image 1">'
            '<img src="image2.png" alt="Image 2">'
            '</body></html>'
        )
        images = doc.get_images()
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0]["src"], "image1.jpg")
        self.assertEqual(images[1]["alt"], "Image 2")

    def test_to_dict(self) -> None:
        """测试转换为字典 / Test conversion to dict."""
        doc = self._create_doc("<html><head><title>Test</title></head><body></body></html>")
        d = doc.to_dict()
        self.assertEqual(d["title"], "Test")
        self.assertEqual(d["content_type"], "html")


class TestParser(unittest.TestCase):
    """Parser测试类 / Parser test class."""

    def setUp(self) -> None:
        """测试前准备 / Test setup."""
        self.parser = Parser()

    def test_parse_html(self) -> None:
        """测试HTML解析 / Test HTML parsing."""
        doc = self.parser.parse_html("<html><body><h1>Title</h1></body></html>")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.content_type, "html")

        h1 = doc.root.find("h1")
        self.assertIsNotNone(h1)
        self.assertEqual(h1.get_text(), "Title")

    def test_parse_html_empty(self) -> None:
        """测试空HTML解析 / Test empty HTML parsing."""
        from webweaver.exceptions import ParseError
        with self.assertRaises(ParseError):
            self.parser.parse_html("")

    def test_parse_json(self) -> None:
        """测试JSON解析 / Test JSON parsing."""
        data = self.parser.parse_json('{"name": "test", "value": 42}')
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["value"], 42)

    def test_parse_json_array(self) -> None:
        """测试JSON数组解析 / Test JSON array parsing."""
        data = self.parser.parse_json('[1, 2, 3]')
        self.assertEqual(data, [1, 2, 3])

    def test_parse_json_invalid(self) -> None:
        """测试无效JSON解析 / Test invalid JSON parsing."""
        from webweaver.exceptions import ParseError
        with self.assertRaises(ParseError):
            self.parser.parse_json("not json")

    def test_detect_content_type_html(self) -> None:
        """测试HTML类型检测 / Test HTML type detection."""
        self.assertEqual(
            self.parser.detect_content_type("<html><body>test</body></html>"),
            "html",
        )

    def test_detect_content_type_json(self) -> None:
        """测试JSON类型检测 / Test JSON type detection."""
        self.assertEqual(
            self.parser.detect_content_type('{"key": "value"}'),
            "json",
        )

    def test_detect_content_type_text(self) -> None:
        """测试纯文本类型检测 / Test plain text type detection."""
        self.assertEqual(
            self.parser.detect_content_type("just plain text"),
            "text",
        )

    def test_detect_content_type_empty(self) -> None:
        """测试空内容类型检测 / Test empty content type detection."""
        self.assertEqual(self.parser.detect_content_type(""), "text")

    def test_auto_parse_html(self) -> None:
        """测试自动解析HTML / Test auto-parse HTML."""
        doc = self.parser.auto_parse("<html><body><p>test</p></body></html>")
        self.assertEqual(doc.content_type, "html")

    def test_auto_parse_json(self) -> None:
        """测试自动解析JSON / Test auto-parse JSON."""
        doc = self.parser.auto_parse('{"key": "value"}')
        self.assertEqual(doc.content_type, "json")


if __name__ == "__main__":
    unittest.main()
