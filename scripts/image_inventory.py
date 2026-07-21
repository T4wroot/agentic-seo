#!/usr/bin/env python3
"""Inventory images for SEO, accessibility, and performance signals."""

from __future__ import annotations

import argparse
import json
import os
from urllib.parse import urlparse

from seo_common import fetch_url, load_html, parse_html


def inventory(source: str, fetch_images: bool = False, timeout: int = 15) -> dict:
    html, url, fetched = load_html(source, timeout=timeout)
    parsed = parse_html(html, url)
    rows = []
    issues = []
    for idx, img in enumerate(parsed["images"]):
        src = img.get("src") or ""
        ext = os.path.splitext(urlparse(src).path)[1].lower().lstrip(".")
        row = {
            "src": src,
            "alt": img.get("alt"),
            "has_alt": img.get("alt") is not None and img.get("alt") != "",
            "width": img.get("width"),
            "height": img.get("height"),
            "is_responsive_fill": bool(img.get("is_responsive_fill")),
            "loading": img.get("loading"),
            "srcset": bool(img.get("srcset")),
            "sizes": bool(img.get("sizes")),
            "format": ext,
            "likely_lcp_candidate": idx == 0 or img.get("fetchpriority") == "high" or img.get("loading") == "eager",
        }
        if not row["has_alt"]:
            issues.append({"severity": "warning", "message": "Image missing alt text", "url": src})
        if not row["is_responsive_fill"] and (not row["width"] or not row["height"]):
            issues.append({"severity": "info", "message": "Image missing explicit dimensions", "url": src})
        if row["likely_lcp_candidate"] and row["loading"] == "lazy":
            issues.append({"severity": "warning", "message": "Likely LCP image is lazy-loaded", "url": src})
        if fetch_images and src.startswith("http"):
            head = fetch_url(src, method="HEAD", timeout=timeout)
            row["status"] = head.get("status")
            row["content_length"] = head.get("headers", {}).get("content-length")
            row["content_type"] = head.get("headers", {}).get("content-type")
        rows.append(row)
    return {"url": url or source, "count": len(rows), "missing_alt": sum(1 for r in rows if not r["has_alt"]), "issues": issues, "images": rows, "fetch_error": fetched.get("error")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory images on a page")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--fetch-images", action="store_true")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = inventory(args.source, args.fetch_images, args.timeout)
    print(json.dumps(result, indent=2) if args.json else "\n".join(f"{'missing-alt' if not r['has_alt'] else 'ok'}\t{r['src']}" for r in result["images"]))


if __name__ == "__main__":
    main()
