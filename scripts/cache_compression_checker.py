#!/usr/bin/env python3
"""Check compression and caching headers for a page and optional assets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

try:
    from lib.safe_http import safe_request
except ImportError:
    from scripts.lib.safe_http import safe_request

from seo_common import BeautifulSoup, load_html, normalize_url, require_bs4


STATIC_EXTENSIONS = (".css", ".js", ".mjs", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg", ".woff2", ".woff")
TEXT_EXTENSIONS = (".html", ".css", ".js", ".mjs", ".json", ".xml", ".svg", ".txt")


def _load_source(source: str, timeout: int) -> tuple[str, str, dict]:
    path = Path(source)
    if path.is_file():
        return path.read_text(encoding="utf-8"), "", {"url": source, "status": None, "headers": {}, "error": None}
    return load_html(source, timeout=timeout)


def _is_url(value: str) -> bool:
    if Path(value).is_file():
        return False
    return urlparse(value).scheme in ("http", "https") or ("." in value and "/" not in value)


def _asset_urls(soup, page_url: str = "") -> list[str]:
    urls = []
    for tag in soup.find_all(["script", "link", "img"], src=True):
        value = tag.get("src")
        urls.append(normalize_url(value, page_url) if page_url and value else value)
    for tag in soup.find_all("link", href=True):
        rel = " ".join(tag.get("rel") or []).lower()
        if any(token in rel for token in ("stylesheet", "preload", "modulepreload", "icon")):
            value = tag.get("href")
            urls.append(normalize_url(value, page_url) if page_url and value else value)
    return [url for url in urls if url and url.startswith(("http://", "https://"))]


def _cache_max_age(cache_control: str | None) -> int | None:
    if not cache_control:
        return None
    match = re.search(r"(?:s-maxage|max-age)=(\d+)", cache_control)
    return int(match.group(1)) if match else None


def _check_url(url: str, timeout: int) -> dict:
    row = {
        "url": url,
        "status": None,
        "content_type": None,
        "content_encoding": None,
        "cache_control": None,
        "etag": None,
        "vary": None,
        "content_length": None,
        "issues": [],
        "error": None,
    }
    try:
        response = safe_request("HEAD", normalize_url(url), timeout=timeout, max_response_bytes=0)
    except Exception as exc:  # noqa: BLE001 - network and policy errors should be reported, not fatal
        row["error"] = str(exc)
        return row

    headers = {str(k).lower(): v for k, v in response.headers.items()}
    row.update({
        "status": response.status_code,
        "content_type": headers.get("content-type"),
        "content_encoding": headers.get("content-encoding"),
        "cache_control": headers.get("cache-control"),
        "etag": headers.get("etag"),
        "vary": headers.get("vary"),
    })
    length = headers.get("content-length")
    row["content_length"] = int(length) if length and length.isdigit() else None

    path = urlparse(url).path.lower()
    is_static = path.endswith(STATIC_EXTENSIONS)
    is_text = path.endswith(TEXT_EXTENSIONS) or (row["content_type"] and any(t in row["content_type"] for t in ("text/", "javascript", "json", "xml", "svg")))
    if is_text and row["content_encoding"] not in ("br", "gzip", "deflate"):
        row["issues"].append({"severity": "warning", "message": "Compressible response is not Brotli/gzip encoded"})
    max_age = _cache_max_age(row["cache_control"])
    if is_static and (max_age is None or max_age < 604800):
        row["issues"].append({"severity": "warning", "message": "Static asset cache lifetime is short or missing"})
    if is_static and row["cache_control"] and "immutable" not in row["cache_control"].lower() and max_age and max_age >= 2_592_000:
        row["issues"].append({"severity": "info", "message": "Long-lived static asset can use immutable"})
    if not row["etag"] and "last-modified" not in headers:
        row["issues"].append({"severity": "info", "message": "No validator header (ETag or Last-Modified)"})
    if row["content_encoding"] and row["vary"] and "accept-encoding" not in row["vary"].lower():
        row["issues"].append({"severity": "warning", "message": "Compressed response should vary on Accept-Encoding"})
    return row


def audit(source: str, include_assets: bool = False, timeout: int = 15, max_assets: int = 25) -> dict:
    if not _is_url(source):
        html, url, fetched = _load_source(source, timeout=timeout)
        require_bs4()
        soup = BeautifulSoup(html or "", "html.parser")
        return {
            "url": source,
            "resources_checked": 0,
            "issues": [{"severity": "info", "message": "Header checks require HTTP(S); local HTML was parsed for asset discovery only."}],
            "resources": [],
            "asset_count": len(_asset_urls(soup, url)),
            "fetch_error": fetched.get("error"),
        }

    html, url, fetched = _load_source(source, timeout=timeout)
    resources = [_check_url(url or source, timeout)]
    if include_assets and html:
        require_bs4()
        soup = BeautifulSoup(html or "", "html.parser")
        seen = {resources[0]["url"]}
        for asset in _asset_urls(soup, url):
            if asset in seen:
                continue
            seen.add(asset)
            resources.append(_check_url(asset, timeout))
            if len(resources) - 1 >= max_assets:
                break
    issues = []
    for row in resources:
        for item in row["issues"]:
            issues.append({**item, "url": row["url"]})
        if row["error"]:
            issues.append({"severity": "info", "message": "Could not fetch headers", "url": row["url"], "evidence": row["error"]})
    return {
        "url": url or source,
        "resources_checked": len(resources),
        "issues": issues,
        "resources": resources,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check cache and compression headers")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--include-assets", action="store_true", help="Also check linked CSS/JS/images/fonts")
    parser.add_argument("--max-assets", type=int, default=25)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()

    result = audit(args.source, args.include_assets, args.timeout, args.max_assets)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Resources checked: {result['resources_checked']}; issues: {len(result['issues'])}")


if __name__ == "__main__":
    main()
