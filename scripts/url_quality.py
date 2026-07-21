#!/usr/bin/env python3
"""Analyze URL hygiene and variant risks."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from urllib.parse import parse_qs, urlparse

from seo_common import read_urls


FACET_PARAMS = {"sort", "filter", "color", "size", "brand", "price", "min_price", "max_price", "page", "view", "category", "tag"}
TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "msclkid")


def analyze_urls(urls: list[str]) -> dict:
    rows = []
    path_variants = defaultdict(list)
    for url in urls:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        path = parsed.path or "/"
        flags = []
        if len(url) > 115:
            flags.append("long_url")
        if any(ch.isupper() for ch in path):
            flags.append("uppercase_path")
        if "_" in path:
            flags.append("underscore_in_path")
        if re.search(r"/(tag|category|author|page)/\d+/?$", path):
            flags.append("thin_archive_pattern")
        if len([seg for seg in path.split("/") if seg]) > 5:
            flags.append("deep_path")
        if params:
            flags.append("has_parameters")
        if any(key.startswith(TRACKING_PREFIXES) for key in params):
            flags.append("tracking_parameters")
        if any(key in FACET_PARAMS for key in params):
            flags.append("facet_parameters")
        normalized_key = (parsed.netloc.lower().removeprefix("www."), path.lower().rstrip("/") or "/", tuple(sorted(params)))
        path_variants[normalized_key].append(url)
        rows.append({"url": url, "path": path, "param_count": len(params), "params": sorted(params), "flags": flags, "score": max(0, 100 - 12 * len(flags))})

    variants = {str(key): vals for key, vals in path_variants.items() if len(vals) > 1}
    flag_counts = Counter(flag for row in rows for flag in row["flags"])
    return {"count": len(rows), "flag_counts": dict(flag_counts), "variant_groups": variants, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze URL quality")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--url-file")
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = analyze_urls(read_urls(args.urls, args.url_file))
    print(json.dumps(result, indent=2) if args.json else "\n".join(f"{r['score']}\t{','.join(r['flags']) or 'ok'}\t{r['url']}" for r in result["rows"]))


if __name__ == "__main__":
    main()
