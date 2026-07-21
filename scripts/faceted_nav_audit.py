#!/usr/bin/env python3
"""Detect faceted navigation crawl traps from URLs and optional page fetches."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from urllib.parse import parse_qs, urlparse

from seo_common import fetch_url, parse_html, read_urls


FACET_KEYS = {"sort", "filter", "color", "size", "brand", "price", "min_price", "max_price", "rating", "page", "view", "availability", "material"}


def audit(urls: list[str], fetch: bool = False, timeout: int = 15) -> dict:
    rows = []
    by_path = defaultdict(list)
    param_counts = Counter()
    for url in urls:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        facet_params = sorted(k for k in params if k.lower() in FACET_KEYS or k.lower().startswith("filter"))
        flags = []
        if len(params) >= 3:
            flags.append("parameter_combination")
        if facet_params:
            flags.append("facet_parameters")
        if "sort" in params:
            flags.append("sort_url")
        if "page" in params and len(params) > 1:
            flags.append("paginated_filtered_url")
        row = {"url": url, "path": parsed.path or "/", "params": sorted(params), "facet_params": facet_params, "flags": flags}
        if fetch:
            page = fetch_url(url, timeout=timeout, max_bytes=1_500_000)
            row["status"] = page.get("status")
            if page.get("text"):
                html = parse_html(page["text"], page.get("url") or url)
                row["canonical"] = html.get("canonical")
                row["meta_robots"] = html.get("meta_robots")
                if facet_params and not html.get("canonical"):
                    flags.append("facet_missing_canonical")
                if facet_params and not (html.get("meta_robots") and "noindex" in html["meta_robots"].lower()):
                    flags.append("facet_not_noindexed")
        for key in params:
            param_counts[key] += 1
        by_path[row["path"]].append(url)
        rows.append(row)
    path_explosions = {path: vals for path, vals in by_path.items() if len(vals) >= 5}
    issues = []
    if path_explosions:
        issues.append({"severity": "warning", "message": "Multiple parameter variants share the same path", "count": len(path_explosions)})
    frequent_params = {k: v for k, v in param_counts.items() if v >= 3}
    if frequent_params:
        issues.append({"severity": "info", "message": "Frequent URL parameters detected", "evidence": frequent_params})
    return {"count": len(rows), "frequent_params": frequent_params, "path_explosions": path_explosions, "rows": rows, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit faceted navigation URLs")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--url-file")
    parser.add_argument("--fetch", action="store_true", help="Fetch pages for canonical/noindex checks")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = audit(read_urls(args.urls, args.url_file), args.fetch, args.timeout)
    print(json.dumps(result, indent=2) if args.json else "\n".join(f"{','.join(r['flags']) or 'ok'}\t{r['url']}" for r in result["rows"]))


if __name__ == "__main__":
    main()
