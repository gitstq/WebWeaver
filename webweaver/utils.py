"""
WebWeaver - 工具函数模块 / Utility Functions Module
=====================================================
提供URL处理、编码检测、文本清洗等通用工具函数。
Provides common utility functions for URL handling, encoding detection,
text cleaning, etc.
"""

import re
import html
import urllib.parse
from typing import Dict, List, Optional, Tuple
from urllib.parse import (
    urlparse, urljoin, urlunparse, parse_qs, urlencode,
    quote, unquote
)


def normalize_url(url: str, base_url: str = "") -> str:
    """标准化URL / Normalize URL.

    将URL转换为标准格式，处理相对路径、片段标识符等。
    Converts URL to standard format, handling relative paths, fragments, etc.

    Args:
        url: 待标准化的URL / URL to normalize
        base_url: 基础URL，用于解析相对路径 / Base URL for resolving relative paths

    Returns:
        标准化后的绝对URL / Normalized absolute URL
    """
    url = url.strip()

    # 移除首尾空白 / Strip whitespace
    if not url:
        return url

    # 如果是相对URL且提供了base_url，则合并 / If relative URL with base_url, join
    if base_url and not url.startswith(("http://", "https://", "//")):
        url = urljoin(base_url, url)

    # 处理协议相对URL (//example.com) / Handle protocol-relative URLs
    if url.startswith("//"):
        url = "https:" + url

    parsed = urlparse(url)

    # 确保有scheme / Ensure scheme exists
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")

    # 移除片段标识符 / Remove fragment identifier
    parsed = parsed._replace(fragment="")

    # 标准化路径 / Normalize path
    path = parsed.path
    if not path:
        path = "/"

    # 移除末尾斜杠（根路径除外） / Remove trailing slash (except root)
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    parsed = parsed._replace(path=path)

    return urlunparse(parsed)


def is_valid_url(url: str) -> bool:
    """检查URL是否有效 / Check if URL is valid.

    Args:
        url: 待检查的URL / URL to check

    Returns:
        URL是否有效 / Whether URL is valid
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    if not url:
        return False

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    if not parsed.netloc:
        return False

    # 检查域名格式 / Check domain format
    domain = parsed.netloc.split(":")[0]
    if not domain or "." not in domain:
        return False

    return True


def get_domain(url: str) -> str:
    """提取URL的域名 / Extract domain from URL.

    Args:
        url: 目标URL / Target URL

    Returns:
        域名字符串 / Domain string
    """
    parsed = urlparse(url)
    return parsed.netloc.split(":")[0]


def get_base_url(url: str) -> str:
    """获取URL的基础部分（协议+域名） / Get base part of URL (scheme + domain).

    Args:
        url: 目标URL / Target URL

    Returns:
        基础URL / Base URL
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_same_domain(url1: str, url2: str) -> bool:
    """检查两个URL是否属于同一域名 / Check if two URLs belong to the same domain.

    Args:
        url1: 第一个URL / First URL
        url2: 第二个URL / Second URL

    Returns:
        是否同域名 / Whether same domain
    """
    return get_domain(url1).lower() == get_domain(url2).lower()


def extract_links(html_content: str, base_url: str = "") -> List[str]:
    """从HTML内容中提取所有链接 / Extract all links from HTML content.

    Args:
        html_content: HTML内容 / HTML content
        base_url: 基础URL，用于解析相对链接 / Base URL for resolving relative links

    Returns:
        去重后的URL列表 / Deduplicated URL list
    """
    links: List[str] = []

    # 匹配href属性 / Match href attributes
    href_pattern = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    for match in href_pattern.finditer(html_content):
        href = match.group(1).strip()
        if href and not href.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
            if base_url:
                href = urljoin(base_url, href)
            if is_valid_url(href):
                links.append(href)

    # 匹配src属性（图片等资源） / Match src attributes (images etc.)
    src_pattern = re.compile(r'src\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    for match in src_pattern.finditer(html_content):
        src = match.group(1).strip()
        if src and not src.startswith(("data:", "javascript:")):
            if base_url:
                src = urljoin(base_url, src)
            if is_valid_url(src):
                links.append(src)

    # 去重并保持顺序 / Deduplicate while preserving order
    seen: set = set()
    unique_links: List[str] = []
    for link in links:
        normalized = normalize_url(link)
        if normalized not in seen:
            seen.add(normalized)
            unique_links.append(normalized)

    return unique_links


def detect_encoding(raw_bytes: bytes) -> str:
    """检测字节数据的编码 / Detect encoding of byte data.

    通过分析BOM标记和meta标签来检测编码。
    Detects encoding by analyzing BOM markers and meta tags.

    Args:
        raw_bytes: 原始字节数据 / Raw byte data

    Returns:
        检测到的编码名称 / Detected encoding name
    """
    # 检查BOM标记 / Check BOM markers
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        return "utf-8-sig"
    if raw_bytes.startswith(b'\xff\xfe'):
        return "utf-16-le"
    if raw_bytes.startswith(b'\xfe\xff'):
        return "utf-16-be"

    # 尝试从meta标签检测 / Try to detect from meta tags
    try:
        text = raw_bytes[:4096].decode("ascii", errors="ignore")
        # 匹配 charset 声明 / Match charset declarations
        charset_patterns = [
            r'<meta[^>]+charset\s*=\s*["\']?([^"\';\s>]+)',
            r'<\?xml[^>]+encoding\s*=\s*["\']([^"\']+)',
        ]
        for pattern in charset_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                charset = match.group(1).strip().lower()
                # 标准化编码名称 / Normalize encoding names
                encoding_map = {
                    "utf8": "utf-8",
                    "gb2312": "gb18030",
                    "gbk": "gb18030",
                    "iso-8859-1": "latin-1",
                }
                return encoding_map.get(charset, charset)
    except Exception:
        pass

    return "utf-8"


def clean_text(text: str) -> str:
    """清洗文本内容 / Clean text content.

    移除多余的空白字符、HTML实体等。
    Removes excess whitespace, HTML entities, etc.

    Args:
        text: 待清洗的文本 / Text to clean

    Returns:
        清洗后的文本 / Cleaned text
    """
    if not text:
        return ""

    # 解码HTML实体 / Decode HTML entities
    text = html.unescape(text)

    # 替换多个空白为单个空格 / Replace multiple whitespace with single space
    text = re.sub(r'[\t\r\n]+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)

    # 移除零宽字符 / Remove zero-width characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)

    return text.strip()


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """截断文本 / Truncate text.

    Args:
        text: 原始文本 / Original text
        max_length: 最大长度 / Maximum length
        suffix: 截断后缀 / Truncation suffix

    Returns:
        截断后的文本 / Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_filename(text: str, max_length: int = 100) -> str:
    """将文本转换为安全的文件名 / Convert text to safe filename.

    Args:
        text: 原始文本 / Original text
        max_length: 最大长度 / Maximum length

    Returns:
        安全的文件名 / Safe filename
    """
    # 移除不安全字符 / Remove unsafe characters
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', text)
    text = re.sub(r'_+', '_', text)
    text = text.strip('._')

    if not text:
        text = "unnamed"

    return text[:max_length]


def parse_query_string(url: str) -> Dict[str, str]:
    """解析URL查询参数 / Parse URL query parameters.

    Args:
        url: 包含查询参数的URL / URL with query parameters

    Returns:
        查询参数字典 / Query parameter dictionary
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def build_query_string(params: Dict[str, str]) -> str:
    """构建查询字符串 / Build query string.

    Args:
        params: 参数字典 / Parameter dictionary

    Returns:
        查询字符串 / Query string
    """
    return urlencode(params)


def url_matches_pattern(url: str, pattern: str) -> bool:
    """检查URL是否匹配给定的模式 / Check if URL matches a given pattern.

    支持简单的通配符模式（*表示任意字符）。
    Supports simple wildcard patterns (* means any characters).

    Args:
        url: 目标URL / Target URL
        pattern: 匹配模式 / Match pattern

    Returns:
        是否匹配 / Whether matched
    """
    # 将通配符模式转换为正则表达式 / Convert wildcard pattern to regex
    regex_pattern = ""
    for char in pattern:
        if char == "*":
            regex_pattern += ".*"
        elif char in r"\^$.|?+()[]{}":
            regex_pattern += "\\" + char
        else:
            regex_pattern += char

    return bool(re.match(regex_pattern, url, re.IGNORECASE))


def merge_dicts(*dicts: Dict) -> Dict:
    """深度合并多个字典 / Deep merge multiple dictionaries.

    Args:
        *dicts: 待合并的字典 / Dictionaries to merge

    Returns:
        合并后的字典 / Merged dictionary
    """
    result: Dict = {}
    for d in dicts:
        if not isinstance(d, dict):
            continue
        for key, value in d.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
    return result
