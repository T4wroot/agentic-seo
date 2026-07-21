#!/usr/bin/env python3
"""Audit image weight, responsive image usage, and likely LCP image risk."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from seo_common import fetch_url, load_html, parse_html


MODERN_FORMATS = {"avif", "webp"}
RASTER_FORMATS = {"jpg", "jpeg", "png", "gif"}


def _load_source(source: str, timeout: int) -> tuple[str, str, dict]:
    path = Path(source)
    if path.is_file():
        return path.read_text(encoding="utf-8"), "", {"url": source, "status": None, "headers": {}, "error": None}
    return load_html(source, timeout=timeout)


def _extension(src: str) -> str:
    return os.path.splitext(urlparse(src).path)[1].lower().lstrip(".")


def _local_size(src: str, html_source: str) -> int | None:
    if src.startswith(("http://", "https://", "data:")):
        return None
    base = Path(html_source).resolve().parent if Path(html_source).exists() else Path.cwd()
    candidate = (base / src.lstrip("/")).resolve()
    try:
        if candidate.is_file():
            return candidate.stat().st_size
    except OSError:
        return None
    return None


def audit(source: str, fetch_images: bool = False, timeout: int = 15) -> dict:
    html, url, fetched = _load_source(source, timeout=timeout)
    parsed = parse_html(html, url)
    images = []
    issues = []

    for index, img in enumerate(parsed["images"]):
        src = img.get("src") or ""
        ext = _extension(src)
        likely_lcp = index == 0 or img.get("fetchpriority") == "high" or img.get("loading") == "eager"
        row = {
            "src": src,
            "format": ext,
            "width": img.get("width"),
            "height": img.get("height"),
            "loading": img.get("loading"),
            "fetchpriority": img.get("fetchpriority"),
            "srcset": bool(img.get("srcset")),
            "sizes": bool(img.get("sizes")),
            "likely_lcp_candidate": likely_lcp,
            "status": None,
            "content_length": _local_size(src, source),
            "content_type": None,
        }
        if fetch_images and src.startswith(("http://", "https://")):
            head = fetch_url(src, method="HEAD", timeout=timeout)
            row["status"] = head.get("status")
            headers = head.get("headers", {})
            length = headers.get("content-length")
            row["content_length"] = int(length) if length and length.isdigit() else None
            row["content_type"] = headers.get("content-type")

        if likely_lcp and row["loading"] == "lazy":
            issues.append({"severity": "warning", "message": "Likely LCP image is lazy-loaded", "url": src})
        if likely_lcp and row["fetchpriority"] != "high":
            issues.append({"severity": "info", "message": "Likely LCP image lacks fetchpriority=high", "url": src})
        if ext in RASTER_FORMATS:
            issues.append({"severity": "info", "message": "Consider AVIF/WebP for raster image", "url": src, "evidence": ext})
        if not row["srcset"]:
            issues.append({"severity": "info", "message": "Image has no srcset", "url": src})
        if row["srcset"] and not row["sizes"]:
            issues.append({"severity": "info", "message": "Responsive image has srcset but no sizes", "url": src})
        if row["content_length"] and row["content_length"] > 250_000:
            issues.append({"severity": "warning", "message": "Large image transfer size", "url": src, "evidence": f"{row['content_length']} bytes"})
        images.append(row)

    known_bytes = sum(row["content_length"] or 0 for row in images)
    return {
        "url": url or source,
        "image_count": len(images),
        "known_image_bytes": known_bytes if fetch_images or any(row["content_length"] for row in images) else None,
        "modern_format_count": sum(1 for row in images if row["format"] in MODERN_FORMATS),
        "responsive_count": sum(1 for row in images if row["srcset"]),
        "issues": issues,
        "images": images,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit image weight and responsive-image performance")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--fetch-images", action="store_true", help="HEAD remote images for status and byte size")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()

    result = audit(args.source, args.fetch_images, args.timeout)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Images: {result['image_count']}; responsive: {result['responsive_count']}; issues: {len(result['issues'])}")


if __name__ == "__main__":
    main()
