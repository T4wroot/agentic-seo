#!/usr/bin/env python3
"""Validate hreflang annotations across sitemap indexes and sitemap URL sets."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict

from hreflang_checker import validate_lang_code
from seo_common import discover_sitemap_urls, fetch_url, issue, normalize_url, print_json_or_text


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def parse_hreflang_sitemap(xml_text: str, sitemap_url: str = "") -> dict:
    try:
        root = ET.fromstring((xml_text or "").encode("utf-8"))
    except ET.ParseError as exc:
        return {"type": "invalid", "sitemaps": [], "urls": [], "error": str(exc)}
    if local_name(root.tag) == "sitemapindex":
        sitemaps = []
        for node in root:
            if local_name(node.tag) != "sitemap":
                continue
            loc = next((child.text for child in node if local_name(child.tag) == "loc"), None)
            if loc:
                sitemaps.append(normalize_url(loc, sitemap_url))
        return {"type": "sitemapindex", "sitemaps": sitemaps, "urls": [], "error": None}
    urls = []
    for node in root:
        if local_name(node.tag) != "url":
            continue
        loc = next((child.text for child in node if local_name(child.tag) == "loc"), None)
        alternates = []
        for child in node:
            if local_name(child.tag) != "link":
                continue
            attrs = child.attrib
            rel = attrs.get("rel") or attrs.get("{http://www.w3.org/1999/xhtml}rel")
            hreflang = attrs.get("hreflang") or attrs.get("{http://www.w3.org/1999/xhtml}hreflang")
            href = attrs.get("href") or attrs.get("{http://www.w3.org/1999/xhtml}href")
            if rel == "alternate" and hreflang and href:
                alternates.append({"lang": hreflang.lower() if hreflang != "x-default" else "x-default", "raw_lang": hreflang, "url": normalize_url(href, sitemap_url)})
        if loc:
            urls.append({"loc": normalize_url(loc, sitemap_url), "alternates": alternates})
    return {"type": "urlset", "sitemaps": [], "urls": urls, "error": None}


def validate_hreflang_sitemaps(site: str, sitemap_urls: list[str] | None = None, timeout: int = 15, max_sitemaps: int = 50) -> dict:
    queue = list(dict.fromkeys(sitemap_urls or discover_sitemap_urls(site, timeout=timeout)))
    seen = set()
    rows = []
    issues = []
    alternate_map = defaultdict(dict)
    while queue and len(seen) < max_sitemaps:
        sitemap_url = normalize_url(queue.pop(0), site)
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        fetched = fetch_url(sitemap_url, timeout=timeout, max_bytes=8_000_000)
        entry = {"url": sitemap_url, "status": fetched.get("status"), "type": None, "urls": 0, "alternates": 0, "error": fetched.get("error")}
        if fetched.get("status") != 200:
            issues.append(issue("error", f"Sitemap returned HTTP {fetched.get('status')}", sitemap_url, fetched.get("error")))
            rows.append(entry)
            continue
        parsed = parse_hreflang_sitemap(fetched.get("text") or "", sitemap_url)
        entry["type"] = parsed["type"]
        entry["error"] = parsed["error"]
        if parsed["error"]:
            issues.append(issue("error", f"Invalid sitemap XML: {parsed['error']}", sitemap_url))
        if parsed["type"] == "sitemapindex":
            queue.extend(parsed["sitemaps"])
        for url_row in parsed["urls"]:
            entry["urls"] += 1
            entry["alternates"] += len(url_row["alternates"])
            if not url_row["alternates"]:
                continue
            has_self = any(alt["url"].rstrip("/") == url_row["loc"].rstrip("/") for alt in url_row["alternates"])
            if not has_self:
                issues.append(issue("error", "Sitemap hreflang set is missing self reference", url_row["loc"]))
            has_x_default = any(alt["lang"] == "x-default" for alt in url_row["alternates"])
            if not has_x_default:
                issues.append(issue("warning", "Sitemap hreflang set is missing x-default", url_row["loc"]))
            seen_langs = set()
            for alt in url_row["alternates"]:
                if alt["lang"] in seen_langs:
                    issues.append(issue("warning", f"Duplicate hreflang '{alt['lang']}' in sitemap set", url_row["loc"]))
                seen_langs.add(alt["lang"])
                validation = validate_lang_code(alt["raw_lang"])
                if not validation["valid"]:
                    issues.extend(issue("error", text, url_row["loc"], alt["raw_lang"]) for text in validation["issues"])
                alternate_map[url_row["loc"]][alt["lang"]] = alt["url"]
        rows.append(entry)
    for source_url, alternates in alternate_map.items():
        for lang, alternate_url in alternates.items():
            if lang == "x-default" or alternate_url not in alternate_map:
                continue
            reverse = alternate_map[alternate_url]
            if not any(url.rstrip("/") == source_url.rstrip("/") for url in reverse.values()):
                issues.append(issue("error", "Missing reciprocal sitemap hreflang return tag", source_url, f"{lang} -> {alternate_url}"))
    return {
        "site": normalize_url(site),
        "sitemaps_checked": len(rows),
        "rows": rows,
        "hreflang_url_sets": len(alternate_map),
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate hreflang annotations in sitemap indexes and urlsets")
    parser.add_argument("site", help="Site URL")
    parser.add_argument("--sitemap", action="append", help="Explicit sitemap URL; can be repeated")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--max-sitemaps", type=int, default=50)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    result = validate_hreflang_sitemaps(args.site, args.sitemap, args.timeout, args.max_sitemaps)
    lines = [
        f"Hreflang sitemap validation for {args.site}",
        f"Sitemaps: {result['sitemaps_checked']}  URL sets: {result['hreflang_url_sets']}  Issues: {len(result['issues'])}",
    ] + [f"[{item['severity']}] {item['message']} {item.get('url') or ''} {item.get('evidence') or ''}" for item in result["issues"][:30]]
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
