#!/usr/bin/env python3
"""Generate an llms.txt draft from site metadata and priority URLs."""

from __future__ import annotations

import argparse
import json
from urllib.parse import urlparse

from seo_common import fetch_url, normalize_url, parse_html, read_urls


def page_title(url: str, timeout: int) -> tuple[str, str]:
    fetched = fetch_url(url, timeout=timeout, max_bytes=1_000_000)
    if fetched.get("text") and "html" in fetched.get("headers", {}).get("content-type", ""):
        html = parse_html(fetched["text"], fetched.get("url") or url)
        return html.get("title") or urlparse(url).path.strip("/") or url, html.get("meta_description") or ""
    return urlparse(url).path.strip("/") or url, ""


def generate(site: str, urls: list[str], title: str | None = None, description: str | None = None, timeout: int = 15, fetch_titles: bool = False) -> dict:
    site = normalize_url(site)
    if not title or not description:
        fetched = fetch_url(site, timeout=timeout, max_bytes=1_000_000)
        if fetched.get("text"):
            html = parse_html(fetched["text"], fetched.get("url") or site)
            title = title or html.get("title") or urlparse(site).netloc
            description = description or html.get("meta_description") or f"Official information and priority pages for {urlparse(site).netloc}."
    title = title or urlparse(site).netloc
    description = description or f"Official information and priority pages for {urlparse(site).netloc}."

    links = []
    for url in urls:
        label, desc = page_title(url, timeout) if fetch_titles else (urlparse(url).path.strip("/") or "Home", "")
        links.append({"title": label, "url": normalize_url(url, site), "description": desc})

    lines = [f"# {title}", "", f"> {description}", "", "## Priority pages"]
    for link in links:
        suffix = f": {link['description']}" if link["description"] else ""
        lines.append(f"- [{link['title']}]({link['url']}){suffix}")
    lines.extend(["", "## Notes", "- Use these URLs as the preferred starting points for understanding this site."])
    text = "\n".join(lines) + "\n"
    return {"site": site, "count": len(links), "llms_txt": text, "links": links}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a draft llms.txt")
    parser.add_argument("site")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--url-file")
    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--fetch-titles", action="store_true")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    urls = read_urls(args.urls, args.url_file) or [args.site]
    result = generate(args.site, urls, args.title, args.description, args.timeout, args.fetch_titles)
    print(json.dumps(result, indent=2) if args.json else result["llms_txt"])


if __name__ == "__main__":
    main()
