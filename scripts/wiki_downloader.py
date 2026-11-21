#!/usr/bin/env python3
"""
Simple MediaWiki content downloader.
Works with any MediaWiki-based wiki by changing BASE_URL and API_ENDPOINT.
"""

import argparse
import re
from pathlib import Path

import requests

# Tolkien Gateway
BASE_URL = "https://tolkiengateway.net"
API_ENDPOINT = f"{BASE_URL}/w/api.php"


def _strip_html(html: str) -> str:
    """Minimal HTML tag removal to get readable plain text from parsed output."""
    # Remove <style> and <script> blocks entirely
    text = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)
    # Remove [edit] / [modifier] links
    text = re.sub(r"\[(?:edit|modifier)\]", "", text)
    # Replace <br>, closing block tags with newlines
    text = re.sub(r"<br\s*/?>|</(?:p|div|li|tr|h[1-6])>", "\n", text)
    # Replace </td> and </th> with tab (for tables)
    text = re.sub(r"</(?:td|th)>", "\t", text)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common HTML entities
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#039;", "'")
        .replace("&nbsp;", " ")
    )
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_page(title: str) -> dict:
    """Fetch a page via action=parse (works on all MediaWiki sites)."""
    params = {
        "action": "parse",
        "page": title,
        "prop": "text|wikitext",
        "format": "json",
    }
    resp = requests.get(API_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        return {"title": title, "html": "", "wikitext": ""}
    return {
        "title": data["parse"]["title"],
        "html": data["parse"]["text"]["*"],
        "wikitext": data["parse"]["wikitext"]["*"],
    }


def get_page(title: str, fmt: str = "text") -> dict:
    """Fetch a single wiki page by title.

    Args:
        title: Page title (e.g. "Pikachu", "Goku").
        fmt: "text" for plain text, "html" for parsed HTML, "wikitext" for raw markup.
    """
    if fmt == "html":
        parsed = _parse_page(title)
        return {"title": parsed["title"], "content": parsed["html"], "format": "html"}
    if fmt == "wikitext":
        parsed = _parse_page(title)
        return {"title": parsed["title"], "content": parsed["wikitext"], "format": "wikitext"}
    # Plain text: try extracts first, fall back to parse + strip
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "format": "json",
    }
    resp = requests.get(API_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    content = page.get("extract", "")
    # Fallback: if extracts returned nothing, use action=parse and strip HTML
    if not content.strip():
        parsed = _parse_page(title)
        content = _strip_html(parsed["html"])
        return {"title": parsed["title"], "content": content, "format": "text"}

    return {
        "title": page.get("title", title),
        "content": content,
        "format": "text",
    }


def search_pages(query: str, limit: int = 10) -> list[dict]:
    """Search for pages matching a query string."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
    }
    resp = requests.get(API_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["query"]["search"]


def get_category_members(category: str, limit: int = 50) -> list[str]:
    """List page titles in a category (without 'Category:' prefix)."""
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": limit,
        "format": "json",
    }
    resp = requests.get(API_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    return [member["title"] for member in resp.json()["query"]["categorymembers"]]


def save(content: str, filepath: str) -> None:
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    Path(filepath).write_text(content, encoding="utf-8")
    print(f"Saved → {filepath}  ({len(content):,} chars)")


def main():
    parser = argparse.ArgumentParser(description="Download content from a MediaWiki")
    sub = parser.add_subparsers(dest="command", required=True)

    # page
    page_parser = sub.add_parser("page", help="Download a single page")
    page_parser.add_argument("title", help="Page title, e.g. 'Pikachu'")
    page_parser.add_argument("--format", choices=["text", "html", "wikitext"], default="text")
    page_parser.add_argument("-o", "--output", help="Save to file instead of printing")

    # search
    search_parser = sub.add_parser("search", help="Search for pages")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", "--limit", type=int, default=10)

    # category
    category_parser = sub.add_parser("category", help="List pages in a category")
    category_parser.add_argument("name", help="Category name (without 'Category:' prefix)")
    category_parser.add_argument("-n", "--limit", type=int, default=50)

    # bulk
    bulk_parser = sub.add_parser("bulk", help="Download multiple pages (one file each)")
    bulk_parser.add_argument("titles", nargs="+", help="Page titles")
    bulk_parser.add_argument("--format", choices=["text", "html", "wikitext"], default="text")
    bulk_parser.add_argument("-d", "--dir", default="wiki_pages", help="Output directory")

    args = parser.parse_args()
    if args.command == "page":
        result = get_page(args.title, args.format)
        if args.output:
            save(result["content"], args.output)
        else:
            print(result["content"])

    elif args.command == "search":
        results = search_pages(args.query, args.limit)
        for result in results:
            print(f"  {result['title']:30s}  (id={result['pageid']})")
    elif args.command == "category":
        titles = get_category_members(args.name, args.limit)
        for title in titles:
            print(f"  {title}")

    elif args.command == "bulk":
        extension = {"text": ".txt", "html": ".html", "wikitext": ".wiki"}[args.format]
        for title in args.titles:
            result = get_page(title, args.format)
            slug = title.replace(" ", "_").replace("/", "_")
            save(result["content"], f"{args.dir}/{slug}{extension}")


if __name__ == "__main__":
    main()
