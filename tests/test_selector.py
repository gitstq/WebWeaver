"""
WebWeaver - 选择器测试 / Selector Tests
========================================
测试CSS选择器和XPath选择器的功能。
Tests for CSS selector and XPath selector functionality.
"""

import unittest
from webweaver.parser import Parser
from webweaver.selector import Selector, SelectorList, _parse_css_selector


class TestCSSParser(unittest.TestCase):
    """CSS选择器解析测试类 / CSS selector parsing test class."""

    def test_tag_selector(self) -> None:
        """测试标签选择器 / Test tag selector."""
        conditions = _parse_css_selector("div")
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0]["tag"], "div")

    def test_id_selector(self) -> None:
        """测试ID选择器 / Test ID selector."""
        conditions = _parse_css_selector("#myid")
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0]["id"], "myid")

    def test_class_selector(self) -> None:
        """测试类选择器 / Test class selector."""
        conditions = _parse_css_selector(".myclass")
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0]["classes"], ["myclass"])

    def test_combined_selector(self) -> None:
        """测试组合选择器 / Test combined selector."""
        conditions = _parse_css_selector("div.myclass#myid")
        self.assertEqual(conditions[0]["tag"], "div")
        self.assertEqual(conditions[0]["classes"], ["myclass"])
        self.assertEqual(conditions[0]["id"], "myid")

    def test_attribute_selector(self) -> None:
        """测试属性选择器 / Test attribute selector."""
        conditions = _parse_css_selector("[href]")
        self.assertEqual(len(conditions), 1)
        self.assertIn("href", conditions[0]["attrs"])

    def test_attribute_value_selector(self) -> None:
        """测试属性值选择器 / Test attribute value selector."""
        conditions = _parse_css_selector('[name="test"]')
        self.assertEqual(conditions[0]["attrs"]["name"], "test")

    def test_descendant_selector(self) -> None:
        """测试后代选择器 / Test descendant selector."""
        conditions = _parse_css_selector("div p")
        self.assertEqual(len(conditions), 2)
        self.assertEqual(conditions[0]["tag"], "div")
        self.assertEqual(conditions[1]["tag"], "p")

    def test_multiple_classes(self) -> None:
        """测试多类选择器 / Test multiple class selector."""
        conditions = _parse_css_selector(".class1.class2")
        self.assertEqual(conditions[0]["classes"], ["class1", "class2"])


class TestSelector(unittest.TestCase):
    """Selector测试类 / Selector test class."""

    def _create_selector(self, html: str) -> Selector:
        """创建选择器的辅助方法 / Helper to create selector."""
        parser = Parser()
        doc = parser.parse_html(html)
        return Selector(doc.root)

    def test_css_tag_selector(self) -> None:
        """测试CSS标签选择器 / Test CSS tag selector."""
        sel = self._create_selector(
            "<html><body><p>1</p><p>2</p><div>3</div></body></html>"
        )
        result = sel.css("p")
        self.assertEqual(len(result), 2)

    def test_css_id_selector(self) -> None:
        """测试CSS ID选择器 / Test CSS ID selector."""
        sel = self._create_selector(
            '<html><body><div id="main">content</div><div id="other">other</div></body></html>'
        )
        result = sel.css("#main")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.first().get_text(), "content")

    def test_css_class_selector(self) -> None:
        """测试CSS类选择器 / Test CSS class selector."""
        sel = self._create_selector(
            '<html><body><p class="highlight">A</p><p class="normal">B</p><p class="highlight">C</p></body></html>'
        )
        result = sel.css(".highlight")
        self.assertEqual(len(result), 2)

    def test_css_attribute_selector(self) -> None:
        """测试CSS属性选择器 / Test CSS attribute selector."""
        sel = self._create_selector(
            '<html><body><a href="https://example.com">Link</a><a href="/local">Local</a></body></html>'
        )
        result = sel.css('[href^="https"]')
        self.assertEqual(len(result), 1)

    def test_css_descendant_selector(self) -> None:
        """测试CSS后代选择器 / Test CSS descendant selector."""
        sel = self._create_selector(
            '<html><body><div><p>1</p></div><p>2</p></body></html>'
        )
        result = sel.css("div p")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.first().get_text(), "1")

    def test_css_combined_selector(self) -> None:
        """测试CSS组合选择器 / Test CSS combined selector."""
        sel = self._create_selector(
            '<html><body><p class="title">Title</p><p class="content">Content</p></body></html>'
        )
        result = sel.css("p.title")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.first().get_text(), "Title")

    def test_xpath_tag(self) -> None:
        """测试XPath标签查找 / Test XPath tag finding."""
        sel = self._create_selector(
            "<html><body><p>1</p><p>2</p></body></html>"
        )
        result = sel.xpath("//p")
        self.assertEqual(len(result), 2)

    def test_xpath_with_attribute(self) -> None:
        """测试XPath属性查找 / Test XPath attribute finding."""
        sel = self._create_selector(
            '<html><body><a href="https://example.com">Link</a></body></html>'
        )
        result = sel.xpath('//a[@href]')
        self.assertEqual(len(result), 1)

    def test_xpath_with_attribute_value(self) -> None:
        """测试XPath属性值查找 / Test XPath attribute value finding."""
        sel = self._create_selector(
            '<html><body><div class="main">content</div><div class="side">side</div></body></html>'
        )
        result = sel.xpath('//div[@class="main"]')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.first().get_text(), "content")

    def test_find(self) -> None:
        """测试find方法 / Test find method."""
        sel = self._create_selector(
            '<html><body><div id="test">content</div></body></html>'
        )
        elem = sel.find("#test")
        self.assertIsNotNone(elem)
        self.assertEqual(elem.get_text(), "content")

    def test_find_all(self) -> None:
        """测试find_all方法 / Test find_all method."""
        sel = self._create_selector(
            "<html><body><p>1</p><p>2</p><p>3</p></body></html>"
        )
        elems = sel.find_all("p")
        self.assertEqual(len(elems), 3)


class TestSelectorList(unittest.TestCase):
    """SelectorList测试类 / SelectorList test class."""

    def _create_selector_list(self, html: str, query: str) -> SelectorList:
        """创建选择器结果列表的辅助方法 / Helper to create selector list."""
        parser = Parser()
        doc = parser.parse_html(html)
        sel = Selector(doc.root)
        return sel.css(query)

    def test_first(self) -> None:
        """测试获取第一个元素 / Test getting first element."""
        result = self._create_selector_list(
            "<html><body><p>1</p><p>2</p></body></html>", "p"
        )
        first = result.first()
        self.assertIsNotNone(first)
        self.assertEqual(first.get_text(), "1")

    def test_last(self) -> None:
        """测试获取最后一个元素 / Test getting last element."""
        result = self._create_selector_list(
            "<html><body><p>1</p><p>2</p></body></html>", "p"
        )
        last = result.last()
        self.assertIsNotNone(last)
        self.assertEqual(last.get_text(), "2")

    def test_get(self) -> None:
        """测试按索引获取 / Test getting by index."""
        result = self._create_selector_list(
            "<html><body><p>1</p><p>2</p><p>3</p></body></html>", "p"
        )
        self.assertEqual(result.get(0).get_text(), "1")
        self.assertEqual(result.get(1).get_text(), "2")
        self.assertIsNone(result.get(10))

    def test_text(self) -> None:
        """测试文本获取 / Test text retrieval."""
        result = self._create_selector_list(
            "<html><body><p>Hello</p><p>World</p></body></html>", "p"
        )
        text = result.text()
        self.assertIn("Hello", text)
        self.assertIn("World", text)

    def test_attr(self) -> None:
        """测试属性获取 / Test attribute retrieval."""
        result = self._create_selector_list(
            '<html><body><a href="a.html">A</a><a href="b.html">B</a></body></html>',
            "a",
        )
        hrefs = result.attr("href")
        self.assertEqual(len(hrefs), 2)
        self.assertIn("a.html", hrefs)
        self.assertIn("b.html", hrefs)

    def test_len(self) -> None:
        """测试长度 / Test length."""
        result = self._create_selector_list(
            "<html><body><p>1</p><p>2</p></body></html>", "p"
        )
        self.assertEqual(len(result), 2)

    def test_bool(self) -> None:
        """测试布尔值 / Test boolean value."""
        result = self._create_selector_list(
            "<html><body><p>1</p></body></html>", "p"
        )
        self.assertTrue(result)

        empty_result = self._create_selector_list(
            "<html><body><p>1</p></body></html>", "a"
        )
        self.assertFalse(empty_result)

    def test_iteration(self) -> None:
        """测试迭代 / Test iteration."""
        result = self._create_selector_list(
            "<html><body><p>1</p><p>2</p></body></html>", "p"
        )
        count = 0
        for _ in result:
            count += 1
        self.assertEqual(count, 2)

    def test_filter(self) -> None:
        """测试过滤 / Test filtering."""
        result = self._create_selector_list(
            '<html><body><p class="a">1</p><p class="b">2</p><p class="a">3</p></body></html>',
            "p",
        )
        filtered = result.filter(lambda e: "a" in e.classes)
        self.assertEqual(len(filtered), 2)


if __name__ == "__main__":
    unittest.main()
