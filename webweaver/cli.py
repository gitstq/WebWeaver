"""
WebWeaver - 命令行接口 / Command Line Interface
================================================
提供webweaver命令行工具，支持fetch、crawl和extract子命令。
Provides the webweaver CLI tool supporting fetch, crawl, and extract subcommands.
"""

import argparse
import json
import sys
from typing import List, Optional


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器 / Create CLI argument parser.

    Returns:
        ArgumentParser实例 / ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="webweaver",
        description="WebWeaver - 轻量级自适应Web爬虫引擎 / "
                    "Lightweight Adaptive Web Crawler Engine",
        epilog="示例 / Examples:\n"
               "  webweaver fetch https://example.com\n"
               "  webweaver crawl https://example.com --depth 2 --output json\n"
               "  webweaver extract https://example.com --rules rules.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="可用命令 / Available commands",
    )

    # fetch 子命令 / fetch subcommand
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="获取单个URL的内容 / Fetch content from a single URL",
    )
    fetch_parser.add_argument(
        "url",
        help="目标URL / Target URL",
    )
    fetch_parser.add_argument(
        "--method", "-m",
        default="GET",
        choices=["GET", "POST", "PUT", "DELETE", "HEAD"],
        help="HTTP方法 / HTTP method (default: GET)",
    )
    fetch_parser.add_argument(
        "--output", "-o",
        default="text",
        choices=["text", "json", "headers"],
        help="输出格式 / Output format (default: text)",
    )
    fetch_parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=30.0,
        help="超时时间（秒）/ Timeout in seconds (default: 30)",
    )
    fetch_parser.add_argument(
        "--output-file", "-f",
        default="",
        help="输出文件路径 / Output file path",
    )

    # crawl 子命令 / crawl subcommand
    crawl_parser = subparsers.add_parser(
        "crawl",
        help="爬取网页内容 / Crawl web content",
    )
    crawl_parser.add_argument(
        "url",
        help="起始URL / Starting URL",
    )
    crawl_parser.add_argument(
        "--depth", "-d",
        type=int,
        default=1,
        help="爬取深度 / Crawl depth (default: 1)",
    )
    crawl_parser.add_argument(
        "--output", "-o",
        default="json",
        choices=["json", "csv", "text"],
        help="输出格式 / Output format (default: json)",
    )
    crawl_parser.add_argument(
        "--output-file", "-f",
        default="",
        help="输出文件路径 / Output file path",
    )
    crawl_parser.add_argument(
        "--same-domain",
        action="store_true",
        default=True,
        help="限制同域名 / Limit to same domain (default: True)",
    )
    crawl_parser.add_argument(
        "--no-same-domain",
        action="store_true",
        help="不限制域名 / Don't limit domain",
    )
    crawl_parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=30.0,
        help="超时时间（秒）/ Timeout in seconds (default: 30)",
    )
    crawl_parser.add_argument(
        "--max-urls",
        type=int,
        default=50,
        help="最大爬取URL数 / Max URLs to crawl (default: 50)",
    )
    crawl_parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="请求间隔（秒）/ Request delay in seconds (default: 1.0)",
    )
    crawl_parser.add_argument(
        "--resume",
        action="store_true",
        help="从断点恢复 / Resume from checkpoint",
    )

    # extract 子命令 / extract subcommand
    extract_parser = subparsers.add_parser(
        "extract",
        help="使用规则提取数据 / Extract data using rules",
    )
    extract_parser.add_argument(
        "url",
        help="目标URL / Target URL",
    )
    extract_parser.add_argument(
        "--rules", "-r",
        required=True,
        help="提取规则JSON文件路径 / Extraction rules JSON file path",
    )
    extract_parser.add_argument(
        "--output", "-o",
        default="json",
        choices=["json", "csv", "text"],
        help="输出格式 / Output format (default: json)",
    )
    extract_parser.add_argument(
        "--output-file", "-f",
        default="",
        help="输出文件路径 / Output file path",
    )

    return parser


def cmd_fetch(args: argparse.Namespace) -> int:
    """执行fetch命令 / Execute fetch command.

    Args:
        args: 命令行参数 / Command line arguments

    Returns:
        退出码 / Exit code
    """
    from .config import CrawlerConfig
    from .fetcher import Fetcher

    config = CrawlerConfig(timeout=args.timeout)
    fetcher = Fetcher(config)

    try:
        response = fetcher.fetch(args.url, method=args.method)

        if args.output == "json":
            output = json.dumps(response.to_dict(), ensure_ascii=False, indent=2)
        elif args.output == "headers":
            output = json.dumps(response.headers, ensure_ascii=False, indent=2)
        else:
            output = response.text

        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"已保存到 / Saved to: {args.output_file}")
        else:
            print(output)

        return 0

    except Exception as e:
        print(f"错误 / Error: {e}", file=sys.stderr)
        return 1


def cmd_crawl(args: argparse.Namespace) -> int:
    """执行crawl命令 / Execute crawl command.

    Args:
        args: 命令行参数 / Command line arguments

    Returns:
        退出码 / Exit code
    """
    from .config import CrawlerConfig
    from .crawler import Crawler
    from .pipeline import JsonFilePipeline, CsvPipeline, PrintPipeline

    same_domain = args.same_domain and not args.no_same_domain

    config = CrawlerConfig(
        timeout=args.timeout,
        delay_range=(args.delay * 0.5, args.delay * 1.5),
        auto_save_state=args.resume,
    )

    crawler = Crawler(config)

    # 设置输出管道 / Set output pipeline
    if args.output == "json":
        output_file = args.output_file or "crawl_results.json"
        crawler.add_pipeline(JsonFilePipeline(output_file))
    elif args.output == "csv":
        output_file = args.output_file or "crawl_results.csv"
        crawler.add_pipeline(CsvPipeline(output_file))
    else:
        crawler.add_pipeline(PrintPipeline())

    # 加载断点状态 / Load checkpoint state
    if args.resume:
        crawler.load_state()
        print("已加载断点状态 / Loaded checkpoint state")

    try:
        if args.depth <= 1:
            # 单页爬取 / Single page crawl
            result = crawler.start(args.url)
            results = [result]
        else:
            # 递归爬取 / Recursive crawl
            results = crawler.crawl_recursive(
                args.url,
                max_depth=args.depth,
                same_domain=same_domain,
            )

        # 打印统计信息 / Print statistics
        stats = crawler.get_stats()
        print(f"\n爬取完成 / Crawl completed:")
        print(f"  总请求数 / Total requests: {stats['total_requests']}")
        print(f"  成功数 / Successes: {stats['total_success']}")
        print(f"  错误数 / Errors: {stats['total_errors']}")
        print(f"  发现链接 / Links found: {stats['total_links']}")
        print(f"  耗时 / Elapsed: {stats['elapsed']}s")

        return 0

    except KeyboardInterrupt:
        print("\n爬取已中断 / Crawl interrupted")
        crawler.save_state()
        print("状态已保存，可用 --resume 恢复 / State saved, use --resume to restore")
        return 130

    except Exception as e:
        print(f"错误 / Error: {e}", file=sys.stderr)
        return 1


def cmd_extract(args: argparse.Namespace) -> int:
    """执行extract命令 / Execute extract command.

    Args:
        args: 命令行参数 / Command line arguments

    Returns:
        退出码 / Exit code
    """
    from .config import CrawlerConfig
    from .crawler import Crawler
    from .extractor import Extractor
    from .pipeline import JsonFilePipeline, CsvPipeline, PrintPipeline

    # 加载提取规则 / Load extraction rules
    try:
        extractor = Extractor.from_rules_file(args.rules)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"规则文件加载失败 / Failed to load rules file: {e}", file=sys.stderr)
        return 1

    config = CrawlerConfig(timeout=30.0)
    crawler = Crawler(config)
    crawler.set_extractor(extractor)

    # 设置输出管道 / Set output pipeline
    if args.output == "json":
        output_file = args.output_file or "extract_results.json"
        crawler.add_pipeline(JsonFilePipeline(output_file))
    elif args.output == "csv":
        output_file = args.output_file or "extract_results.csv"
        crawler.add_pipeline(CsvPipeline(output_file))
    else:
        crawler.add_pipeline(PrintPipeline())

    try:
        result = crawler.start(args.url)

        if result.success and result.data:
            if not args.output_file and args.output == "text":
                print(json.dumps(result.data, ensure_ascii=False, indent=2))
            else:
                print(f"数据提取完成 / Data extraction completed")
        elif result.error:
            print(f"提取失败 / Extraction failed: {result.error}", file=sys.stderr)
            return 1

        return 0

    except Exception as e:
        print(f"错误 / Error: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """主入口函数 / Main entry function.

    Args:
        argv: 命令行参数列表 / Command line argument list

    Returns:
        退出码 / Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "fetch":
        return cmd_fetch(args)
    elif args.command == "crawl":
        return cmd_crawl(args)
    elif args.command == "extract":
        return cmd_extract(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
