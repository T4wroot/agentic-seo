#!/usr/bin/env python3
"""Generate sitemap XML or sitemap indexes from URL manifests."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import date
from urllib.parse import urlparse

from seo_common import normalize_url


def read_manifest(path: str | None) -> list[dict]:
    rows = []
    lines = sys.stdin.read().splitlines() if not path or path == "-" else open(path, "r", encoding="utf-8").read().splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("{"):
            data = json.loads(line)
            url = data.get("url") or data.get("loc")
            if url:
                rows.append(data | {"url": normalize_url(url)})
            continue
        parts = [p.strip() for p in line.split(",")]
        rows.append({"url": normalize_url(parts[0]), "lastmod": parts[1] if len(parts) > 1 and parts[1] else None})
    return rows


def build_urlset(rows: list[dict], default_lastmod: str | None = None) -> str:
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    root = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
    for row in rows:
        item = ET.SubElement(root, "url")
        ET.SubElement(item, "loc").text = row["url"]
        lastmod = row.get("lastmod") or default_lastmod
        if lastmod:
            ET.SubElement(item, "lastmod").text = lastmod
        if row.get("changefreq"):
            ET.SubElement(item, "changefreq").text = str(row["changefreq"])
        if row.get("priority") is not None:
            ET.SubElement(item, "priority").text = str(row["priority"])
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def build_index(sitemap_urls: list[str], default_lastmod: str | None = None) -> str:
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    root = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex")
    for url in sitemap_urls:
        item = ET.SubElement(root, "sitemap")
        ET.SubElement(item, "loc").text = normalize_url(url)
        if default_lastmod:
            ET.SubElement(item, "lastmod").text = default_lastmod
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sitemap XML from a URL manifest")
    parser.add_argument("--input", "-i", help="URL manifest file; stdin when omitted. CSV lines: url,lastmod or JSONL")
    parser.add_argument("--index", action="store_true", help="Treat input as sitemap URLs and emit sitemapindex")
    parser.add_argument("--lastmod-today", action="store_true", help="Use today's date when lastmod is missing")
    parser.add_argument("--json", "-j", action="store_true", help="Output metadata JSON instead of XML")
    args = parser.parse_args()

    rows = read_manifest(args.input)
    default_lastmod = date.today().isoformat() if args.lastmod_today else None
    urls = [row["url"] for row in rows]
    xml = build_index(urls, default_lastmod) if args.index else build_urlset(rows, default_lastmod)
    result = {
        "type": "sitemapindex" if args.index else "urlset",
        "count": len(urls),
        "hosts": sorted({urlparse(url).netloc for url in urls}),
        "xml": xml,
    }
    print(json.dumps(result, indent=2) if args.json else xml)


if __name__ == "__main__":
    main()
