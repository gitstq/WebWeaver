<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License" />
  <img src="https://img.shields.io/badge/Version-v1.0.0-orange.svg" alt="Version 1.0.0" />
  <img src="https://img.shields.io/badge/Dependencies-0%20External-purple.svg" alt="Zero Dependencies" />
</p>

<h1 align="center">🕷️ WebWeaver</h1>

<p align="center">
  <b>轻量级自适应Web爬虫引擎</b><br/>
  <i>Lightweight Adaptive Web Crawler Engine</i>
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> ·
  <a href="#繁體中文">繁體中文</a> ·
  <a href="#english">English</a>
</p>

---

<a id="简体中文"></a>

## 🎉 项目介绍

**WebWeaver** 是一款纯 Python 实现的轻量级自适应 Web 爬虫引擎，专为简洁高效而设计。它完全依赖 Python 标准库，无需安装任何第三方包，即可完成从页面抓取、内容解析到数据提取的全流程工作。

无论你是想快速抓取单个页面的数据，还是需要构建一套完整的网站爬取方案，WebWeaver 都能以最少的代码量帮你搞定。

### 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                      WebWeaver 引擎                      │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Fetcher │  Parser  │ Selector │Extractor │  Pipeline   │
│  HTTP请求 │ HTML解析  │ CSS/XPath│ 数据提取  │  管道处理   │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│  Middleware · RateLimiter · State · Config · CLI         │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🧩 **零外部依赖** | 仅使用 Python 标准库，`pip install` 即装即用，无需操心依赖冲突 |
| 🧠 **自适应爬取** | 自动检测页面类型（HTML/JSON），智能选择解析策略 |
| 🛡️ **内置反检测** | User-Agent 轮换、随机延迟、请求头伪装，降低被封风险 |
| 🎯 **结构化数据提取** | 支持 CSS 选择器、XPath、正则表达式、JSON 路径四种提取方式 |
| 🔗 **管道式处理** | 内置 JSON/CSV/打印/清洗/去重管道，可自由组合、链式调用 |
| 💾 **断点续爬** | 自动保存爬取状态到本地文件，支持中断后恢复，不丢进度 |
| ⏱️ **智能速率限制** | 基于令牌桶算法，根据服务器响应动态调整请求频率 |
| 🖥️ **CLI 命令行接口** | 提供 `fetch`、`crawl`、`extract` 三个子命令，一行搞定常见任务 |

---

## 🚀 快速开始

### 📦 安装

```bash
# 从 GitHub 安装
pip install git+https://github.com/gitstq/WebWeaver.git

# 或克隆后本地安装
git clone https://github.com/gitstq/WebWeaver.git
cd WebWeaver
pip install .
```

> ⚙️ **环境要求**：Python 3.8 及以上版本，无需安装任何第三方依赖。

### 🐍 三行代码爬取网页

```python
from webweaver import Crawler

# 创建爬虫实例
crawler = Crawler()

# 爬取单个页面
result = crawler.start("https://example.com")
print(result.document.title)
print(result.document.text[:200])
```

### 🎯 使用提取规则

```python
from webweaver import Crawler, ExtractionRule

crawler = Crawler()

# 添加提取规则
crawler.add_extraction_rule(ExtractionRule(
    name="title",
    selector_type="css",
    selector="title",
))

# 爬取并提取数据
result = crawler.start("https://example.com")
print(result.data)
# 输出: {'title': 'Example Domain'}
```

### 🖥️ 命令行使用

```bash
# 获取页面内容
webweaver fetch https://example.com --output json

# 爬取网站（深度2层，输出CSV）
webweaver crawl https://example.com --depth 2 --output csv --output-file results.csv

# 使用提取规则文件
webweaver extract https://example.com --rules rules.json
```

---

## 📖 详细使用指南

### 1. API 用法

#### 单页爬取

```python
from webweaver import Crawler

crawler = Crawler()
result = crawler.start("https://example.com")

# 访问结果
print(f"URL: {result.url}")
print(f"状态: {'成功' if result.success else '失败'}")
print(f"耗时: {result.elapsed:.2f}s")
print(f"标题: {result.document.title}")
print(f"正文: {result.document.text[:200]}")
print(f"链接数: {len(result.links)}")
```

#### 批量爬取

```python
from webweaver import Crawler

crawler = Crawler()
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

results = crawler.crawl_many(urls)
for result in results:
    print(f"{result.url} -> {result.document.title}")
```

#### 递归爬取（深度优先）

```python
from webweaver import Crawler

crawler = Crawler()

# 从起始URL开始，最大深度3层，限制同域名
results = crawler.crawl_recursive(
    start_url="https://example.com",
    max_depth=3,
    same_domain=True,
)

print(f"共爬取 {len(results)} 个页面")
```

#### 链式调用

```python
from webweaver import Crawler, ExtractionRule
from webweaver import JsonFilePipeline, UserAgentMiddleware

crawler = (
    Crawler()
    .add_extraction_rule(ExtractionRule(
        name="title", selector_type="css", selector="title"
    ))
    .add_extraction_rule(ExtractionRule(
        name="description", selector_type="css", selector="meta[name=description]",
        attribute="content"
    ))
    .add_pipeline(JsonFilePipeline("output.json"))
    .add_middleware(UserAgentMiddleware())
    .on_result(lambda r: print(f"✅ {r.url}"))
)

result = crawler.start("https://example.com")
```

#### 结果回调

```python
from webweaver import Crawler

def on_crawl_result(result):
    if result.success:
        print(f"🎉 爬取成功: {result.url}")
        print(f"   标题: {result.document.title}")
    else:
        print(f"❌ 爬取失败: {result.url} - {result.error}")

crawler = Crawler()
crawler.on_result(on_crawl_result)
crawler.start("https://example.com")
```

---

### 2. 配置

`CrawlerConfig` 提供了丰富的配置选项：

```python
from webweaver import Crawler, CrawlerConfig

config = CrawlerConfig(
    timeout=30.0,              # 请求超时（秒）
    max_retries=3,             # 最大重试次数
    retry_delay=1.0,          # 重试延迟基数（秒）
    delay_range=(0.5, 2.0),   # 随机延迟范围（秒）
    max_depth=3,               # 最大爬取深度
    respect_robots_txt=True,   # 遵守 robots.txt
    follow_redirects=True,    # 跟随重定向
    max_redirects=5,           # 最大重定向次数
    encoding="utf-8",          # 默认编码
    auto_save_state=True,      # 自动保存状态
    state_save_interval=10,    # 状态保存间隔
)

crawler = Crawler(config)
```

#### 从文件加载配置

```python
from webweaver import CrawlerConfig

# 从 JSON 文件加载
config = CrawlerConfig.from_file("crawler_config.json")

# 保存配置到文件
config.save_to_file("crawler_config.json")
```

配置文件示例 (`crawler_config.json`)：

```json
{
  "timeout": 30.0,
  "max_retries": 3,
  "delay_range": [0.5, 2.0],
  "max_depth": 3,
  "respect_robots_txt": true,
  "follow_redirects": true,
  "encoding": "utf-8",
  "auto_save_state": true,
  "state_save_interval": 10,
  "proxies": {
    "http": "http://proxy:8080",
    "https": "https://proxy:8080"
  }
}
```

---

### 3. 提取规则

`ExtractionRule` 支持多种选择器类型，满足各种数据提取需求：

#### CSS 选择器

```python
from webweaver import ExtractionRule

# 提取标题文本
ExtractionRule(name="title", selector_type="css", selector="h1")

# 提取链接属性
ExtractionRule(
    name="link", selector_type="css", selector="a.main-link",
    attribute="href"
)

# 提取多个元素
ExtractionRule(
    name="items", selector_type="css", selector="li.item",
    multiple=True
)
```

#### XPath

```python
ExtractionRule(
    name="price",
    selector_type="xpath",
    selector="//div[@class='price']/text()"
)
```

#### 正则表达式

```python
ExtractionRule(
    name="email",
    selector_type="regex",
    selector=r"[\w.+-]+@[\w-]+\.[\w.]+"
)
```

#### JSON 路径

```python
ExtractionRule(
    name="username",
    selector_type="json_path",
    selector="data.user.name"
)
```

#### Meta 标签

```python
ExtractionRule(
    name="description",
    selector_type="meta",
    selector="description"
)
```

#### 后处理与转换

```python
ExtractionRule(
    name="price",
    selector_type="css",
    selector=".price",
    regex=r"[\d.]+",           # 正则后处理：提取数字
    transform="float",        # 转换为浮点数
)
```

**内置转换函数**：`strip`、`lower`、`upper`、`title`、`int`、`float`、`bool`、`first`、`last`、`join`、`len`、`replace_spaces`、`remove_html`、`extract_number`

#### 从 JSON 文件加载规则

规则文件示例 (`rules.json`)：

```json
{
  "rules": [
    {
      "name": "title",
      "selector_type": "css",
      "selector": "h1",
      "default": "无标题"
    },
    {
      "name": "price",
      "selector_type": "css",
      "selector": ".price",
      "regex": "[\\d.]+",
      "transform": "float"
    },
    {
      "name": "description",
      "selector_type": "meta",
      "selector": "description"
    },
    {
      "name": "emails",
      "selector_type": "regex",
      "selector": "[\\w.+-]+@[\\w-]+\\.[\\w.]+",
      "multiple": true
    }
  ]
}
```

```python
from webweaver import Extractor

extractor = Extractor.from_rules_file("rules.json")
```

---

### 4. 管道

管道用于对提取的数据进行后处理，支持链式组合：

```python
from webweaver import (
    Crawler, ExtractionRule,
    JsonFilePipeline, CsvPipeline, PrintPipeline,
    DataCleaningPipeline, DeduplicationPipeline,
)

crawler = Crawler()

# 添加提取规则
crawler.add_extraction_rule(ExtractionRule(
    name="title", selector_type="css", selector="h1"
))

# 组合多个管道（按顺序执行）
crawler.add_pipeline(DataCleaningPipeline(
    strip_strings=True,       # 去除首尾空白
    remove_empty=True,       # 移除空值
    remove_none=True,        # 移除 None
))
crawler.add_pipeline(DeduplicationPipeline(
    key_fields=["title"]     # 按 title 字段去重
))
crawler.add_pipeline(JsonFilePipeline("results.json"))
crawler.add_pipeline(PrintPipeline())

result = crawler.start("https://example.com")
```

**内置管道一览**：

| 管道 | 说明 |
|------|------|
| `PrintPipeline` | 将数据打印到标准输出 |
| `JsonFilePipeline` | 将数据保存为 JSON 文件 |
| `CsvPipeline` | 将数据保存为 CSV 文件 |
| `DataCleaningPipeline` | 清洗数据（去空白、去空值等） |
| `DeduplicationPipeline` | 按指定字段去重 |

#### 自定义管道

```python
from webweaver import BasePipeline

class MyPipeline(BasePipeline):
    def process(self, item):
        # 自定义处理逻辑
        item["processed"] = True
        return item

    def open(self):
        print("管道已启动")

    def close(self):
        print("管道已关闭")

crawler.add_pipeline(MyPipeline())
```

---

### 5. 中间件

中间件可以在请求前后执行自定义逻辑，实现请求拦截、响应修改、错误处理等功能：

```python
from webweaver import (
    Crawler,
    UserAgentMiddleware,
    RetryMiddleware,
    FilterMiddleware,
    LoggingMiddleware,
)

crawler = Crawler()

# User-Agent 轮换
crawler.add_middleware(UserAgentMiddleware())

# 自动重试（针对 429/500/502/503/504）
crawler.add_middleware(RetryMiddleware(
    max_retries=3,
    retry_delay=1.0,
))

# URL 过滤
crawler.add_middleware(FilterMiddleware(
    allowed_domains=["example.com"],
    denied_patterns=[r"/login", r"/admin"],
    allowed_extensions=[".html", ".htm", ""],
))

# 日志记录
crawler.add_middleware(LoggingMiddleware(log_level="info"))
```

**内置中间件一览**：

| 中间件 | 说明 |
|--------|------|
| `UserAgentMiddleware` | 每次请求自动轮换 User-Agent |
| `RetryMiddleware` | 根据状态码自动重试，支持指数退避 |
| `FilterMiddleware` | 按域名、URL 模式、文件扩展名过滤 |
| `LoggingMiddleware` | 记录请求/响应/错误日志 |

#### 自定义中间件

```python
from webweaver import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    def process_request(self, url, headers, **kwargs):
        # 请求前处理
        headers["X-Custom-Header"] = "my-value"
        return {"headers": headers}

    def process_response(self, response, **kwargs):
        # 响应后处理
        return response

    def process_error(self, url, error, **kwargs):
        # 错误处理
        print(f"请求出错: {url} - {error}")
        return None

crawler.add_middleware(CustomMiddleware())
```

---

### 6. 断点续爬

WebWeaver 内置状态管理，支持中断恢复：

```python
from webweaver import Crawler

crawler = Crawler()

# 加载之前的爬取状态（如果存在）
crawler.load_state()

# 开始递归爬取
results = crawler.crawl_recursive(
    start_url="https://example.com",
    max_depth=5,
)

# 查看统计
stats = crawler.get_stats()
print(f"已访问: {stats['state']['visited_count']}")
print(f"待爬取: {stats['state']['pending_count']}")
```

```python
# 手动保存状态
crawler.save_state()

# 清除状态（重新开始）
crawler.clear_state()
```

CLI 中使用断点续爬：

```bash
# 正常爬取（自动保存状态）
webweaver crawl https://example.com --depth 3

# 中断后恢复爬取
webweaver crawl https://example.com --depth 3 --resume
```

---

### 7. 智能速率限制

基于令牌桶算法的自适应速率控制：

```python
from webweaver import Crawler, CrawlerConfig
from webweaver import RateLimiter

# 通过配置设置
config = CrawlerConfig(
    delay_range=(0.5, 2.0),  # 随机延迟范围
)
crawler = Crawler(config)

# 直接使用速率限制器
limiter = RateLimiter(
    max_requests=10,       # 时间窗口内最大请求数
    window_seconds=60.0,   # 时间窗口（秒）
    min_delay=0.5,         # 最小请求间隔
    max_delay=10.0,        # 最大请求间隔
    backoff_factor=2.0,    # 退避因子
)

# 速率限制器会根据服务器响应自动调整：
# - 请求成功 → 逐步恢复速率
# - 请求失败 → 自动增加延迟
# - 收到 429 → 延迟翻倍
```

---

### 8. CLI 命令行接口

WebWeaver 提供了三个子命令，覆盖常见使用场景：

#### `webweaver fetch` - 获取页面内容

```bash
# 获取页面纯文本
webweaver fetch https://example.com

# 输出为 JSON 格式
webweaver fetch https://example.com --output json

# 仅查看响应头
webweaver fetch https://example.com --output headers

# 保存到文件
webweaver fetch https://example.com --output json --output-file page.json

# 设置超时时间
webweaver fetch https://example.com --timeout 10

# 使用 POST 方法
webweaver fetch https://example.com --method POST
```

#### `webweaver crawl` - 爬取网站

```bash
# 单页爬取
webweaver crawl https://example.com

# 多层深度爬取
webweaver crawl https://example.com --depth 3

# 输出为 CSV
webweaver crawl https://example.com --depth 2 --output csv --output-file data.csv

# 不限制域名
webweaver crawl https://example.com --depth 2 --no-same-domain

# 设置最大URL数和延迟
webweaver crawl https://example.com --depth 3 --max-urls 100 --delay 1.5

# 断点续爬
webweaver crawl https://example.com --depth 3 --resume
```

#### `webweaver extract` - 提取数据

```bash
# 使用规则文件提取数据
webweaver extract https://example.com --rules rules.json

# 输出为 CSV
webweaver extract https://example.com --rules rules.json --output csv

# 保存到指定文件
webweaver extract https://example.com --rules rules.json --output json --output-file data.json
```

---

## 💡 设计思路与迭代规划

### 🎨 设计哲学

WebWeaver 的核心设计理念是 **"简单至上"**：

- **零依赖**：不引入任何第三方库，降低安装门槛和版本冲突风险
- **模块化**：每个组件（Fetcher、Parser、Selector、Extractor、Pipeline、Middleware）职责单一，可独立使用
- **可扩展**：通过管道和中间件机制，用户可以自由组合和扩展功能
- **渐进式**：从简单的单页抓取到复杂的递归爬取，API 设计层层递进

### 🗺️ 迭代规划

- [x] **v1.0.0** - 核心引擎发布：HTTP 请求、HTML 解析、CSS/XPath 选择器、数据提取、管道系统、中间件、断点续爬、CLI
- [ ] **v1.1.0** - 异步支持：基于 `asyncio` 的异步请求，提升并发性能
- [ ] **v1.2.0** - 插件系统：支持动态加载外部插件，扩展选择器和管道类型
- [ ] **v1.3.0** - 分布式爬取：支持多机协作，Redis 队列调度
- [ ] **v2.0.0** - 可视化监控：Web 仪表盘，实时查看爬取状态和统计数据

---

## 📦 安装与部署

### 系统要求

- Python 3.8+
- 无其他依赖

### 安装方式

```bash
# 方式一：从 PyPI 安装（推荐）
pip install webweaver

# 方式二：从 GitHub 安装最新版
pip install git+https://github.com/gitstq/WebWeaver.git

# 方式三：克隆后本地安装
git clone https://github.com/gitstq/WebWeaver.git
cd WebWeaver
pip install .
```

### 验证安装

```bash
# 验证 CLI
webweaver fetch https://example.com

# 验证 Python API
python -c "from webweaver import Crawler; print('安装成功！')"
```

### 项目结构

```
WebWeaver/
├── webweaver/              # 核心包
│   ├── __init__.py         # 包入口，导出所有公开API
│   ├── crawler.py          # 爬虫引擎
│   ├── fetcher.py          # HTTP 请求器
│   ├── parser.py           # HTML/JSON 解析器
│   ├── selector.py         # CSS/XPath 选择器
│   ├── extractor.py        # 数据提取引擎
│   ├── pipeline.py         # 管道处理系统
│   ├── middleware.py       # 中间件模块
│   ├── ratelimit.py        # 智能速率限制器
│   ├── state.py            # 断点续爬状态管理
│   ├── config.py           # 配置管理
│   ├── exceptions.py       # 异常定义
│   ├── utils.py            # 工具函数
│   └── cli.py              # 命令行接口
├── tests/                  # 测试用例
├── setup.py                # 安装配置
├── requirements.txt        # 依赖清单（空）
└── README.md               # 项目文档
```

---

## 🤝 贡献指南

我们欢迎并感谢所有形式的贡献！无论是提交 Bug 报告、改进文档，还是提交代码 PR，都是对项目的巨大支持。

### 参与流程

1. **Fork** 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交改动 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 **Pull Request**

### 开发规范

- 代码风格遵循 PEP 8
- 提交信息使用清晰的描述
- 新功能请附带相应的测试用例
- 文档与代码保持同步更新

### 提交 Issue

- 使用 GitHub Issues 提交 Bug 报告或功能建议
- 描述问题时请尽量包含复现步骤和环境信息

---

## 📄 开源协议

本项目基于 [MIT License](https://opensource.org/licenses/MIT) 开源。

```
MIT License

Copyright (c) 2024 WebWeaver Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<a id="繁體中文"></a>

## 🎉 專案介紹

**WebWeaver** 是一款純 Python 實作的輕量級自適應 Web 爬蟲引擎，專為簡潔高效而設計。它完全依賴 Python 標準庫，無需安裝任何第三方套件，即可完成從頁面抓取、內容解析到資料擷取的完整流程。

無論你是想快速抓取單一頁面的資料，還是需要建構一套完整的網站爬取方案，WebWeaver 都能以最少的程式碼量幫你搞定。

### 🏗️ 架構概覽

```
┌─────────────────────────────────────────────────────────┐
│                      WebWeaver 引擎                      │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Fetcher │  Parser  │ Selector │Extractor │  Pipeline   │
│ HTTP請求  │ HTML解析  │ CSS/XPath│ 資料擷取  │  管道處理   │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│  Middleware · RateLimiter · State · Config · CLI         │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ 核心特性

| 特性 | 說明 |
|------|------|
| 🧩 **零外部依賴** | 僅使用 Python 標準庫，`pip install` 即裝即用，無需擔心依賴衝突 |
| 🧠 **自適應爬取** | 自動偵測頁面類型（HTML/JSON），智慧選擇解析策略 |
| 🛡️ **內建反偵測** | User-Agent 輪換、隨機延遲、請求頭偽裝，降低被封風險 |
| 🎯 **結構化資料擷取** | 支援 CSS 選擇器、XPath、正規表示式、JSON 路徑四種擷取方式 |
| 🔗 **管道式處理** | 內建 JSON/CSV/列印/清洗/去重管道，可自由組合、鏈式呼叫 |
| 💾 **斷點續爬** | 自動儲存爬取狀態到本地檔案，支援中斷後恢復，不遺漏進度 |
| ⏱️ **智慧速率限制** | 基於權杖桶演算法，根據伺服器回應動態調整請求頻率 |
| 🖥️ **CLI 命令列介面** | 提供 `fetch`、`crawl`、`extract` 三個子命令，一行搞定常見任務 |

---

## 🚀 快速開始

### 📦 安裝

```bash
# 從 GitHub 安裝
pip install git+https://github.com/gitstq/WebWeaver.git

# 或複製後本地安裝
git clone https://github.com/gitstq/WebWeaver.git
cd WebWeaver
pip install .
```

> ⚙️ **環境需求**：Python 3.8 及以上版本，無需安裝任何第三方依賴。

### 🐍 三行程式碼爬取網頁

```python
from webweaver import Crawler

# 建立爬蟲實例
crawler = Crawler()

# 爬取單一頁面
result = crawler.start("https://example.com")
print(result.document.title)
print(result.document.text[:200])
```

### 🎯 使用擷取規則

```python
from webweaver import Crawler, ExtractionRule

crawler = Crawler()

# 新增擷取規則
crawler.add_extraction_rule(ExtractionRule(
    name="title",
    selector_type="css",
    selector="title",
))

# 爬取並擷取資料
result = crawler.start("https://example.com")
print(result.data)
# 輸出: {'title': 'Example Domain'}
```

### 🖥️ 命令列使用

```bash
# 取得頁面內容
webweaver fetch https://example.com --output json

# 爬取網站（深度2層，輸出CSV）
webweaver crawl https://example.com --depth 2 --output csv --output-file results.csv

# 使用擷取規則檔案
webweaver extract https://example.com --rules rules.json
```

---

## 📖 詳細使用指南

### 1. API 用法

#### 單頁爬取

```python
from webweaver import Crawler

crawler = Crawler()
result = crawler.start("https://example.com")

# 存取結果
print(f"URL: {result.url}")
print(f"狀態: {'成功' if result.success else '失敗'}")
print(f"耗時: {result.elapsed:.2f}s")
print(f"標題: {result.document.title}")
print(f"正文: {result.document.text[:200]}")
print(f"連結數: {len(result.links)}")
```

#### 批次爬取

```python
from webweaver import Crawler

crawler = Crawler()
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

results = crawler.crawl_many(urls)
for result in results:
    print(f"{result.url} -> {result.document.title}")
```

#### 遞迴爬取（深度優先）

```python
from webweaver import Crawler

crawler = Crawler()

# 從起始URL開始，最大深度3層，限制同網域
results = crawler.crawl_recursive(
    start_url="https://example.com",
    max_depth=3,
    same_domain=True,
)

print(f"共爬取 {len(results)} 個頁面")
```

#### 鏈式呼叫

```python
from webweaver import Crawler, ExtractionRule
from webweaver import JsonFilePipeline, UserAgentMiddleware

crawler = (
    Crawler()
    .add_extraction_rule(ExtractionRule(
        name="title", selector_type="css", selector="title"
    ))
    .add_extraction_rule(ExtractionRule(
        name="description", selector_type="css", selector="meta[name=description]",
        attribute="content"
    ))
    .add_pipeline(JsonFilePipeline("output.json"))
    .add_middleware(UserAgentMiddleware())
    .on_result(lambda r: print(f"✅ {r.url}"))
)

result = crawler.start("https://example.com")
```

#### 結果回呼

```python
from webweaver import Crawler

def on_crawl_result(result):
    if result.success:
        print(f"🎉 爬取成功: {result.url}")
        print(f"   標題: {result.document.title}")
    else:
        print(f"❌ 爬取失敗: {result.url} - {result.error}")

crawler = Crawler()
crawler.on_result(on_crawl_result)
crawler.start("https://example.com")
```

---

### 2. 組態

`CrawlerConfig` 提供了豐富的組態選項：

```python
from webweaver import Crawler, CrawlerConfig

config = CrawlerConfig(
    timeout=30.0,              # 請求逾時（秒）
    max_retries=3,             # 最大重試次數
    retry_delay=1.0,          # 重試延遲基數（秒）
    delay_range=(0.5, 2.0),   # 隨機延遲範圍（秒）
    max_depth=3,               # 最大爬取深度
    respect_robots_txt=True,   # 遵守 robots.txt
    follow_redirects=True,    # 跟隨重新導向
    max_redirects=5,           # 最大重新導向次數
    encoding="utf-8",          # 預設編碼
    auto_save_state=True,      # 自動儲存狀態
    state_save_interval=10,    # 狀態儲存間隔
)

crawler = Crawler(config)
```

#### 從檔案載入組態

```python
from webweaver import CrawlerConfig

# 從 JSON 檔案載入
config = CrawlerConfig.from_file("crawler_config.json")

# 儲存組態到檔案
config.save_to_file("crawler_config.json")
```

組態檔案範例 (`crawler_config.json`)：

```json
{
  "timeout": 30.0,
  "max_retries": 3,
  "delay_range": [0.5, 2.0],
  "max_depth": 3,
  "respect_robots_txt": true,
  "follow_redirects": true,
  "encoding": "utf-8",
  "auto_save_state": true,
  "state_save_interval": 10,
  "proxies": {
    "http": "http://proxy:8080",
    "https": "https://proxy:8080"
  }
}
```

---

### 3. 擷取規則

`ExtractionRule` 支援多種選擇器類型，滿足各種資料擷取需求：

#### CSS 選擇器

```python
from webweaver import ExtractionRule

# 擷取標題文字
ExtractionRule(name="title", selector_type="css", selector="h1")

# 擷取連結屬性
ExtractionRule(
    name="link", selector_type="css", selector="a.main-link",
    attribute="href"
)

# 擷取多個元素
ExtractionRule(
    name="items", selector_type="css", selector="li.item",
    multiple=True
)
```

#### XPath

```python
ExtractionRule(
    name="price",
    selector_type="xpath",
    selector="//div[@class='price']/text()"
)
```

#### 正規表示式

```python
ExtractionRule(
    name="email",
    selector_type="regex",
    selector=r"[\w.+-]+@[\w-]+\.[\w.]+"
)
```

#### JSON 路徑

```python
ExtractionRule(
    name="username",
    selector_type="json_path",
    selector="data.user.name"
)
```

#### Meta 標籤

```python
ExtractionRule(
    name="description",
    selector_type="meta",
    selector="description"
)
```

#### 後處理與轉換

```python
ExtractionRule(
    name="price",
    selector_type="css",
    selector=".price",
    regex=r"[\d.]+",           # 正規表示式後處理：擷取數字
    transform="float",        # 轉換為浮點數
)
```

**內建轉換函式**：`strip`、`lower`、`upper`、`title`、`int`、`float`、`bool`、`first`、`last`、`join`、`len`、`replace_spaces`、`remove_html`、`extract_number`

#### 從 JSON 檔案載入規則

規則檔案範例 (`rules.json`)：

```json
{
  "rules": [
    {
      "name": "title",
      "selector_type": "css",
      "selector": "h1",
      "default": "無標題"
    },
    {
      "name": "price",
      "selector_type": "css",
      "selector": ".price",
      "regex": "[\\d.]+",
      "transform": "float"
    },
    {
      "name": "description",
      "selector_type": "meta",
      "selector": "description"
    },
    {
      "name": "emails",
      "selector_type": "regex",
      "selector": "[\\w.+-]+@[\\w-]+\\.[\\w.]+",
      "multiple": true
    }
  ]
}
```

```python
from webweaver import Extractor

extractor = Extractor.from_rules_file("rules.json")
```

---

### 4. 管道

管道用於對擷取的資料進行後處理，支援鏈式組合：

```python
from webweaver import (
    Crawler, ExtractionRule,
    JsonFilePipeline, CsvPipeline, PrintPipeline,
    DataCleaningPipeline, DeduplicationPipeline,
)

crawler = Crawler()

# 新增擷取規則
crawler.add_extraction_rule(ExtractionRule(
    name="title", selector_type="css", selector="h1"
))

# 組合多個管道（依序執行）
crawler.add_pipeline(DataCleaningPipeline(
    strip_strings=True,       # 去除首尾空白
    remove_empty=True,       # 移除空值
    remove_none=True,        # 移除 None
))
crawler.add_pipeline(DeduplicationPipeline(
    key_fields=["title"]     # 按 title 欄位去重
))
crawler.add_pipeline(JsonFilePipeline("results.json"))
crawler.add_pipeline(PrintPipeline())

result = crawler.start("https://example.com")
```

**內建管道一覽**：

| 管道 | 說明 |
|------|------|
| `PrintPipeline` | 將資料列印到標準輸出 |
| `JsonFilePipeline` | 將資料儲存為 JSON 檔案 |
| `CsvPipeline` | 將資料儲存為 CSV 檔案 |
| `DataCleaningPipeline` | 清洗資料（去空白、去空值等） |
| `DeduplicationPipeline` | 按指定欄位去重 |

#### 自訂管道

```python
from webweaver import BasePipeline

class MyPipeline(BasePipeline):
    def process(self, item):
        # 自訂處理邏輯
        item["processed"] = True
        return item

    def open(self):
        print("管道已啟動")

    def close(self):
        print("管道已關閉")

crawler.add_pipeline(MyPipeline())
```

---

### 5. 中介軟體

中介軟體可以在請求前後執行自訂邏輯，實現請求攔截、回應修改、錯誤處理等功能：

```python
from webweaver import (
    Crawler,
    UserAgentMiddleware,
    RetryMiddleware,
    FilterMiddleware,
    LoggingMiddleware,
)

crawler = Crawler()

# User-Agent 輪換
crawler.add_middleware(UserAgentMiddleware())

# 自動重試（針對 429/500/502/503/504）
crawler.add_middleware(RetryMiddleware(
    max_retries=3,
    retry_delay=1.0,
))

# URL 過濾
crawler.add_middleware(FilterMiddleware(
    allowed_domains=["example.com"],
    denied_patterns=[r"/login", r"/admin"],
    allowed_extensions=[".html", ".htm", ""],
))

# 日誌記錄
crawler.add_middleware(LoggingMiddleware(log_level="info"))
```

**內建中介軟體一覽**：

| 中介軟體 | 說明 |
|----------|------|
| `UserAgentMiddleware` | 每次請求自動輪換 User-Agent |
| `RetryMiddleware` | 根據狀態碼自動重試，支援指數退避 |
| `FilterMiddleware` | 按網域、URL 模式、副檔名過濾 |
| `LoggingMiddleware` | 記錄請求/回應/錯誤日誌 |

#### 自訂中介軟體

```python
from webweaver import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    def process_request(self, url, headers, **kwargs):
        # 請求前處理
        headers["X-Custom-Header"] = "my-value"
        return {"headers": headers}

    def process_response(self, response, **kwargs):
        # 回應後處理
        return response

    def process_error(self, url, error, **kwargs):
        # 錯誤處理
        print(f"請求出錯: {url} - {error}")
        return None

crawler.add_middleware(CustomMiddleware())
```

---

### 6. 斷點續爬

WebWeaver 內建狀態管理，支援中斷恢復：

```python
from webweaver import Crawler

crawler = Crawler()

# 載入之前的爬取狀態（如果存在）
crawler.load_state()

# 開始遞迴爬取
results = crawler.crawl_recursive(
    start_url="https://example.com",
    max_depth=5,
)

# 查看統計
stats = crawler.get_stats()
print(f"已造訪: {stats['state']['visited_count']}")
print(f"待爬取: {stats['state']['pending_count']}")
```

```python
# 手動儲存狀態
crawler.save_state()

# 清除狀態（重新開始）
crawler.clear_state()
```

CLI 中使用斷點續爬：

```bash
# 正常爬取（自動儲存狀態）
webweaver crawl https://example.com --depth 3

# 中斷後恢復爬取
webweaver crawl https://example.com --depth 3 --resume
```

---

### 7. 智慧速率限制

基於權杖桶演算法的自適應速率控制：

```python
from webweaver import Crawler, CrawlerConfig
from webweaver import RateLimiter

# 透過組態設定
config = CrawlerConfig(
    delay_range=(0.5, 2.0),  # 隨機延遲範圍
)
crawler = Crawler(config)

# 直接使用速率限制器
limiter = RateLimiter(
    max_requests=10,       # 時間視窗內最大請求數
    window_seconds=60.0,   # 時間視窗（秒）
    min_delay=0.5,         # 最小請求間隔
    max_delay=10.0,        # 最大請求間隔
    backoff_factor=2.0,    # 退避因子
)

# 速率限制器會根據伺服器回應自動調整：
# - 請求成功 → 逐步恢復速率
# - 請求失敗 → 自動增加延遲
# - 收到 429 → 延遲加倍
```

---

### 8. CLI 命令列介面

WebWeaver 提供了三個子命令，涵蓋常見使用場景：

#### `webweaver fetch` - 取得頁面內容

```bash
# 取得頁面純文字
webweaver fetch https://example.com

# 輸出為 JSON 格式
webweaver fetch https://example.com --output json

# 僅查看回應頭
webweaver fetch https://example.com --output headers

# 儲存到檔案
webweaver fetch https://example.com --output json --output-file page.json

# 設定逾時時間
webweaver fetch https://example.com --timeout 10

# 使用 POST 方法
webweaver fetch https://example.com --method POST
```

#### `webweaver crawl` - 爬取網站

```bash
# 單頁爬取
webweaver crawl https://example.com

# 多層深度爬取
webweaver crawl https://example.com --depth 3

# 輸出為 CSV
webweaver crawl https://example.com --depth 2 --output csv --output-file data.csv

# 不限制網域
webweaver crawl https://example.com --depth 2 --no-same-domain

# 設定最大URL數和延遲
webweaver crawl https://example.com --depth 3 --max-urls 100 --delay 1.5

# 斷點續爬
webweaver crawl https://example.com --depth 3 --resume
```

#### `webweaver extract` - 擷取資料

```bash
# 使用規則檔案擷取資料
webweaver extract https://example.com --rules rules.json

# 輸出為 CSV
webweaver extract https://example.com --rules rules.json --output csv

# 儲存到指定檔案
webweaver extract https://example.com --rules rules.json --output json --output-file data.json
```

---

## 💡 設計思路與迭代規劃

### 🎨 設計哲學

WebWeaver 的核心設計理念是 **「簡單至上」**：

- **零依賴**：不引入任何第三方函式庫，降低安裝門檻和版本衝突風險
- **模組化**：每個元件（Fetcher、Parser、Selector、Extractor、Pipeline、Middleware）職責單一，可獨立使用
- **可擴展**：透過管道和中介軟體機制，使用者可以自由組合和擴展功能
- **漸進式**：從簡單的單頁抓取到複雜的遞迴爬取，API 設計層層遞進

### 🗺️ 迭代規劃

- [x] **v1.0.0** - 核心引擎發佈：HTTP 請求、HTML 解析、CSS/XPath 選擇器、資料擷取、管道系統、中介軟體、斷點續爬、CLI
- [ ] **v1.1.0** - 非同步支援：基於 `asyncio` 的非同步請求，提升並發效能
- [ ] **v1.2.0** - 外掛系統：支援動態載入外部外掛，擴展選擇器和管道類型
- [ ] **v1.3.0** - 分散式爬取：支援多機協作，Redis 佇列調度
- [ ] **v2.0.0** - 視覺化監控：Web 儀表板，即時查看爬取狀態和統計資料

---

## 📦 安裝與部署

### 系統需求

- Python 3.8+
- 無其他依賴

### 安裝方式

```bash
# 方式一：從 PyPI 安裝（推薦）
pip install webweaver

# 方式二：從 GitHub 安裝最新版
pip install git+https://github.com/gitstq/WebWeaver.git

# 方式三：複製後本地安裝
git clone https://github.com/gitstq/WebWeaver.git
cd WebWeaver
pip install .
```

### 驗證安裝

```bash
# 驗證 CLI
webweaver fetch https://example.com

# 驗證 Python API
python -c "from webweaver import Crawler; print('安裝成功！')"
```

### 專案結構

```
WebWeaver/
├── webweaver/              # 核心套件
│   ├── __init__.py         # 套件入口，匯出所有公開API
│   ├── crawler.py          # 爬蟲引擎
│   ├── fetcher.py          # HTTP 請求器
│   ├── parser.py           # HTML/JSON 解析器
│   ├── selector.py         # CSS/XPath 選擇器
│   ├── extractor.py        # 資料擷取引擎
│   ├── pipeline.py         # 管道處理系統
│   ├── middleware.py       # 中介軟體模組
│   ├── ratelimit.py        # 智慧速率限制器
│   ├── state.py            # 斷點續爬狀態管理
│   ├── config.py           # 組態管理
│   ├── exceptions.py       # 異常定義
│   ├── utils.py            # 工具函式
│   └── cli.py              # 命令列介面
├── tests/                  # 測試用例
├── setup.py                # 安裝組態
├── requirements.txt        # 依賴清單（空）
└── README.md               # 專案文件
```

---

## 🤝 貢獻指南

我們歡迎並感謝所有形式的貢獻！無論是提交 Bug 回報、改進文件，還是提交程式碼 PR，都是對專案的巨大支持。

### 參與流程

1. **Fork** 本儲存庫
2. 建立特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 **Pull Request**

### 開發規範

- 程式碼風格遵循 PEP 8
- 提交資訊使用清晰的描述
- 新功能請附帶對應的測試用例
- 文件與程式碼保持同步更新

### 提交 Issue

- 使用 GitHub Issues 提交 Bug 回報或功能建議
- 描述問題時請盡量包含重現步驟和環境資訊

---

## 📄 開源協議

本專案基於 [MIT License](https://opensource.org/licenses/MIT) 開源。

```
MIT License

Copyright (c) 2024 WebWeaver Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<a id="english"></a>

## 🎉 Introduction

**WebWeaver** is a lightweight, adaptive web crawler engine built entirely in Python. Designed with simplicity and efficiency in mind, it relies solely on the Python standard library -- no third-party packages required -- to handle the full workflow from page fetching and content parsing to structured data extraction.

Whether you need to quickly scrape a single page or build a complete site crawling solution, WebWeaver gets the job done with minimal code.

### 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      WebWeaver Engine                     │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Fetcher │  Parser  │ Selector │Extractor │  Pipeline   │
│ HTTP Req │ HTML Parse│CSS/XPath│Data Extr │ Pipe Proc   │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│  Middleware · RateLimiter · State · Config · CLI         │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🧩 **Zero External Dependencies** | Built exclusively on the Python standard library. Install and run with zero dependency conflicts |
| 🧠 **Adaptive Crawling** | Automatically detects page type (HTML/JSON) and selects the optimal parsing strategy |
| 🛡️ **Built-in Anti-Detection** | User-Agent rotation, random delays, and request header spoofing to reduce blocking risk |
| 🎯 **Structured Data Extraction** | Supports CSS selectors, XPath, regular expressions, and JSON path extraction |
| 🔗 **Pipeline Processing** | Built-in JSON/CSV/Print/Cleaning/Deduplication pipelines with composable, chainable API |
| 💾 **Checkpoint Resume** | Automatically persists crawl state to disk; resume from interruptions without losing progress |
| ⏱️ **Smart Rate Limiting** | Token bucket algorithm with dynamic rate adjustment based on server responses |
| 🖥️ **CLI Interface** | Three subcommands -- `fetch`, `crawl`, `extract` -- for common tasks right from the terminal |

---

## 🚀 Quick Start

### 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/gitstq/WebWeaver.git

# Or clone and install locally
git clone https://github.com/gitstq/WebWeaver.git
cd WebWeaver
pip install .
```

> ⚙️ **Requirements**: Python 3.8+. No third-party dependencies needed.

### 🐍 Crawl a Page in Three Lines

```python
from webweaver import Crawler

# Create a crawler instance
crawler = Crawler()

# Crawl a single page
result = crawler.start("https://example.com")
print(result.document.title)
print(result.document.text[:200])
```

### 🎯 Using Extraction Rules

```python
from webweaver import Crawler, ExtractionRule

crawler = Crawler()

# Add an extraction rule
crawler.add_extraction_rule(ExtractionRule(
    name="title",
    selector_type="css",
    selector="title",
))

# Crawl and extract data
result = crawler.start("https://example.com")
print(result.data)
# Output: {'title': 'Example Domain'}
```

### 🖥️ Command Line Usage

```bash
# Fetch page content
webweaver fetch https://example.com --output json

# Crawl a site (depth 2, output as CSV)
webweaver crawl https://example.com --depth 2 --output csv --output-file results.csv

# Extract data using a rules file
webweaver extract https://example.com --rules rules.json
```

---

## 📖 Detailed Guide

### 1. API Usage

#### Single Page Crawl

```python
from webweaver import Crawler

crawler = Crawler()
result = crawler.start("https://example.com")

# Access results
print(f"URL: {result.url}")
print(f"Status: {'OK' if result.success else 'FAILED'}")
print(f"Elapsed: {result.elapsed:.2f}s")
print(f"Title: {result.document.title}")
print(f"Body: {result.document.text[:200]}")
print(f"Links found: {len(result.links)}")
```

#### Batch Crawl

```python
from webweaver import Crawler

crawler = Crawler()
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

results = crawler.crawl_many(urls)
for result in results:
    print(f"{result.url} -> {result.document.title}")
```

#### Recursive Crawl (Depth-First)

```python
from webweaver import Crawler

crawler = Crawler()

# Start from a URL, max depth 3, same domain only
results = crawler.crawl_recursive(
    start_url="https://example.com",
    max_depth=3,
    same_domain=True,
)

print(f"Crawled {len(results)} pages in total")
```

#### Method Chaining

```python
from webweaver import Crawler, ExtractionRule
from webweaver import JsonFilePipeline, UserAgentMiddleware

crawler = (
    Crawler()
    .add_extraction_rule(ExtractionRule(
        name="title", selector_type="css", selector="title"
    ))
    .add_extraction_rule(ExtractionRule(
        name="description", selector_type="css", selector="meta[name=description]",
        attribute="content"
    ))
    .add_pipeline(JsonFilePipeline("output.json"))
    .add_middleware(UserAgentMiddleware())
    .on_result(lambda r: print(f"Done: {r.url}"))
)

result = crawler.start("https://example.com")
```

#### Result Callbacks

```python
from webweaver import Crawler

def on_crawl_result(result):
    if result.success:
        print(f"Success: {result.url}")
        print(f"  Title: {result.document.title}")
    else:
        print(f"Failed: {result.url} - {result.error}")

crawler = Crawler()
crawler.on_result(on_crawl_result)
crawler.start("https://example.com")
```

---

### 2. Configuration

`CrawlerConfig` offers a wide range of configuration options:

```python
from webweaver import Crawler, CrawlerConfig

config = CrawlerConfig(
    timeout=30.0,              # Request timeout (seconds)
    max_retries=3,             # Maximum retry attempts
    retry_delay=1.0,          # Base retry delay (seconds)
    delay_range=(0.5, 2.0),   # Random delay range (seconds)
    max_depth=3,               # Maximum crawl depth
    respect_robots_txt=True,   # Respect robots.txt
    follow_redirects=True,    # Follow redirects
    max_redirects=5,           # Maximum redirect count
    encoding="utf-8",          # Default encoding
    auto_save_state=True,      # Auto-save crawl state
    state_save_interval=10,    # State save interval
)

crawler = Crawler(config)
```

#### Loading Configuration from File

```python
from webweaver import CrawlerConfig

# Load from a JSON file
config = CrawlerConfig.from_file("crawler_config.json")

# Save configuration to file
config.save_to_file("crawler_config.json")
```

Example config file (`crawler_config.json`):

```json
{
  "timeout": 30.0,
  "max_retries": 3,
  "delay_range": [0.5, 2.0],
  "max_depth": 3,
  "respect_robots_txt": true,
  "follow_redirects": true,
  "encoding": "utf-8",
  "auto_save_state": true,
  "state_save_interval": 10,
  "proxies": {
    "http": "http://proxy:8080",
    "https": "https://proxy:8080"
  }
}
```

---

### 3. Extraction Rules

`ExtractionRule` supports multiple selector types for various data extraction needs:

#### CSS Selectors

```python
from webweaver import ExtractionRule

# Extract title text
ExtractionRule(name="title", selector_type="css", selector="h1")

# Extract link attribute
ExtractionRule(
    name="link", selector_type="css", selector="a.main-link",
    attribute="href"
)

# Extract multiple elements
ExtractionRule(
    name="items", selector_type="css", selector="li.item",
    multiple=True
)
```

#### XPath

```python
ExtractionRule(
    name="price",
    selector_type="xpath",
    selector="//div[@class='price']/text()"
)
```

#### Regular Expressions

```python
ExtractionRule(
    name="email",
    selector_type="regex",
    selector=r"[\w.+-]+@[\w-]+\.[\w.]+"
)
```

#### JSON Path

```python
ExtractionRule(
    name="username",
    selector_type="json_path",
    selector="data.user.name"
)
```

#### Meta Tags

```python
ExtractionRule(
    name="description",
    selector_type="meta",
    selector="description"
)
```

#### Post-Processing and Transforms

```python
ExtractionRule(
    name="price",
    selector_type="css",
    selector=".price",
    regex=r"[\d.]+",           # Regex post-processing: extract numbers
    transform="float",        # Convert to float
)
```

**Built-in transform functions**: `strip`, `lower`, `upper`, `title`, `int`, `float`, `bool`, `first`, `last`, `join`, `len`, `replace_spaces`, `remove_html`, `extract_number`

#### Loading Rules from a JSON File

Example rules file (`rules.json`):

```json
{
  "rules": [
    {
      "name": "title",
      "selector_type": "css",
      "selector": "h1",
      "default": "Untitled"
    },
    {
      "name": "price",
      "selector_type": "css",
      "selector": ".price",
      "regex": "[\\d.]+",
      "transform": "float"
    },
    {
      "name": "description",
      "selector_type": "meta",
      "selector": "description"
    },
    {
      "name": "emails",
      "selector_type": "regex",
      "selector": "[\\w.+-]+@[\\w-]+\\.[\\w.]+",
      "multiple": true
    }
  ]
}
```

```python
from webweaver import Extractor

extractor = Extractor.from_rules_file("rules.json")
```

---

### 4. Pipelines

Pipelines handle post-processing of extracted data and can be chained together:

```python
from webweaver import (
    Crawler, ExtractionRule,
    JsonFilePipeline, CsvPipeline, PrintPipeline,
    DataCleaningPipeline, DeduplicationPipeline,
)

crawler = Crawler()

# Add an extraction rule
crawler.add_extraction_rule(ExtractionRule(
    name="title", selector_type="css", selector="h1"
))

# Combine multiple pipelines (executed in order)
crawler.add_pipeline(DataCleaningPipeline(
    strip_strings=True,       # Strip leading/trailing whitespace
    remove_empty=True,       # Remove empty values
    remove_none=True,        # Remove None values
))
crawler.add_pipeline(DeduplicationPipeline(
    key_fields=["title"]     # Deduplicate by title field
))
crawler.add_pipeline(JsonFilePipeline("results.json"))
crawler.add_pipeline(PrintPipeline())

result = crawler.start("https://example.com")
```

**Built-in Pipelines**:

| Pipeline | Description |
|----------|-------------|
| `PrintPipeline` | Prints data to standard output |
| `JsonFilePipeline` | Saves data as a JSON file |
| `CsvPipeline` | Saves data as a CSV file |
| `DataCleaningPipeline` | Cleans data (strip whitespace, remove empty/None values) |
| `DeduplicationPipeline` | Deduplicates data by specified fields |

#### Custom Pipeline

```python
from webweaver import BasePipeline

class MyPipeline(BasePipeline):
    def process(self, item):
        # Custom processing logic
        item["processed"] = True
        return item

    def open(self):
        print("Pipeline opened")

    def close(self):
        print("Pipeline closed")

crawler.add_pipeline(MyPipeline())
```

---

### 5. Middleware

Middleware allows you to execute custom logic before and after requests, enabling request interception, response modification, and error handling:

```python
from webweaver import (
    Crawler,
    UserAgentMiddleware,
    RetryMiddleware,
    FilterMiddleware,
    LoggingMiddleware,
)

crawler = Crawler()

# User-Agent rotation
crawler.add_middleware(UserAgentMiddleware())

# Auto-retry (for 429/500/502/503/504)
crawler.add_middleware(RetryMiddleware(
    max_retries=3,
    retry_delay=1.0,
))

# URL filtering
crawler.add_middleware(FilterMiddleware(
    allowed_domains=["example.com"],
    denied_patterns=[r"/login", r"/admin"],
    allowed_extensions=[".html", ".htm", ""],
))

# Request/response logging
crawler.add_middleware(LoggingMiddleware(log_level="info"))
```

**Built-in Middleware**:

| Middleware | Description |
|-----------|-------------|
| `UserAgentMiddleware` | Automatically rotates User-Agent for each request |
| `RetryMiddleware` | Retries on specific status codes with exponential backoff |
| `FilterMiddleware` | Filters URLs by domain, pattern, and file extension |
| `LoggingMiddleware` | Logs request, response, and error information |

#### Custom Middleware

```python
from webweaver import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    def process_request(self, url, headers, **kwargs):
        # Pre-request processing
        headers["X-Custom-Header"] = "my-value"
        return {"headers": headers}

    def process_response(self, response, **kwargs):
        # Post-response processing
        return response

    def process_error(self, url, error, **kwargs):
        # Error handling
        print(f"Request error: {url} - {error}")
        return None

crawler.add_middleware(CustomMiddleware())
```

---

### 6. Checkpoint Resume

WebWeaver includes built-in state management for interrupt recovery:

```python
from webweaver import Crawler

crawler = Crawler()

# Load previous crawl state (if it exists)
crawler.load_state()

# Start recursive crawling
results = crawler.crawl_recursive(
    start_url="https://example.com",
    max_depth=5,
)

# View statistics
stats = crawler.get_stats()
print(f"Visited: {stats['state']['visited_count']}")
print(f"Pending: {stats['state']['pending_count']}")
```

```python
# Manually save state
crawler.save_state()

# Clear state (start fresh)
crawler.clear_state()
```

Using checkpoint resume from the CLI:

```bash
# Normal crawl (auto-saves state)
webweaver crawl https://example.com --depth 3

# Resume after interruption
webweaver crawl https://example.com --depth 3 --resume
```

---

### 7. Smart Rate Limiting

Adaptive rate control based on the token bucket algorithm:

```python
from webweaver import Crawler, CrawlerConfig
from webweaver import RateLimiter

# Configure via CrawlerConfig
config = CrawlerConfig(
    delay_range=(0.5, 2.0),  # Random delay range
)
crawler = Crawler(config)

# Use the rate limiter directly
limiter = RateLimiter(
    max_requests=10,       # Max requests per time window
    window_seconds=60.0,   # Time window (seconds)
    min_delay=0.5,         # Minimum request interval
    max_delay=10.0,        # Maximum request interval
    backoff_factor=2.0,    # Backoff factor
)

# The rate limiter dynamically adjusts based on server responses:
# - Successful request -> gradually restore rate
# - Failed request -> automatically increase delay
# - HTTP 429 received -> double the delay
```

---

### 8. CLI Reference

WebWeaver provides three subcommands covering common use cases:

#### `webweaver fetch` - Fetch Page Content

```bash
# Fetch page as plain text
webweaver fetch https://example.com

# Output as JSON
webweaver fetch https://example.com --output json

# View response headers only
webweaver fetch https://example.com --output headers

# Save to file
webweaver fetch https://example.com --output json --output-file page.json

# Set timeout
webweaver fetch https://example.com --timeout 10

# Use POST method
webweaver fetch https://example.com --method POST
```

#### `webweaver crawl` - Crawl a Website

```bash
# Single page crawl
webweaver crawl https://example.com

# Multi-depth crawl
webweaver crawl https://example.com --depth 3

# Output as CSV
webweaver crawl https://example.com --depth 2 --output csv --output-file data.csv

# No domain restriction
webweaver crawl https://example.com --depth 2 --no-same-domain

# Set max URLs and delay
webweaver crawl https://example.com --depth 3 --max-urls 100 --delay 1.5

# Resume from checkpoint
webweaver crawl https://example.com --depth 3 --resume
```

#### `webweaver extract` - Extract Data

```bash
# Extract data using a rules file
webweaver extract https://example.com --rules rules.json

# Output as CSV
webweaver extract https://example.com --rules rules.json --output csv

# Save to a specific file
webweaver extract https://example.com --rules rules.json --output json --output-file data.json
```

---

## 💡 Design Philosophy & Roadmap

### 🎨 Design Philosophy

WebWeaver is built on the principle of **"simplicity first"**:

- **Zero dependencies**: No third-party libraries, reducing installation friction and version conflict risks
- **Modular design**: Each component (Fetcher, Parser, Selector, Extractor, Pipeline, Middleware) has a single responsibility and can be used independently
- **Extensible**: The pipeline and middleware mechanisms allow users to freely compose and extend functionality
- **Progressive API**: From simple single-page fetching to complex recursive crawling, the API scales naturally

### 🗺️ Roadmap

- [x] **v1.0.0** - Core engine release: HTTP requests, HTML parsing, CSS/XPath selectors, data extraction, pipeline system, middleware, checkpoint resume, CLI
- [ ] **v1.1.0** - Async support: `asyncio`-based async requests for improved concurrency
- [ ] **v1.2.0** - Plugin system: Dynamic loading of external plugins for new selectors and pipeline types
- [ ] **v1.3.0** - Distributed crawling: Multi-machine coordination with Redis queue scheduling
- [ ] **v2.0.0** - Visual monitoring: Web dashboard for real-time crawl status and statistics

---

## 📦 Installation & Deployment

### System Requirements

- Python 3.8+
- No other dependencies

### Installation Methods

```bash
# Method 1: Install from PyPI (recommended)
pip install webweaver

# Method 2: Install latest from GitHub
pip install git+https://github.com/gitstq/WebWeaver.git

# Method 3: Clone and install locally
git clone https://github.com/gitstq/WebWeaver.git
cd WebWeaver
pip install .
```

### Verify Installation

```bash
# Verify CLI
webweaver fetch https://example.com

# Verify Python API
python -c "from webweaver import Crawler; print('Installation successful!')"
```

### Project Structure

```
WebWeaver/
├── webweaver/              # Core package
│   ├── __init__.py         # Package entry, exports all public APIs
│   ├── crawler.py          # Crawler engine
│   ├── fetcher.py          # HTTP fetcher
│   ├── parser.py           # HTML/JSON parser
│   ├── selector.py         # CSS/XPath selector
│   ├── extractor.py        # Data extraction engine
│   ├── pipeline.py         # Pipeline processing system
│   ├── middleware.py       # Middleware module
│   ├── ratelimit.py        # Smart rate limiter
│   ├── state.py            # Checkpoint resume state management
│   ├── config.py           # Configuration management
│   ├── exceptions.py       # Exception definitions
│   ├── utils.py            # Utility functions
│   └── cli.py              # Command line interface
├── tests/                  # Test cases
├── setup.py                # Installation configuration
├── requirements.txt        # Dependencies (empty)
└── README.md               # Project documentation
```

---

## 🤝 Contributing

We welcome and appreciate contributions of all kinds! Whether it's filing a bug report, improving documentation, or submitting a code PR, every contribution matters.

### How to Contribute

1. **Fork** this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

### Development Guidelines

- Follow PEP 8 code style
- Write clear, descriptive commit messages
- Include test cases for new features
- Keep documentation in sync with code changes

### Filing Issues

- Use GitHub Issues for bug reports or feature requests
- Include reproduction steps and environment details when describing a problem

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

```
MIT License

Copyright (c) 2024 WebWeaver Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```
