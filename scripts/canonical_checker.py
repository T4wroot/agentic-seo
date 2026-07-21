#!/usr/bin/env python3
"""Check canonical tags for self/cross-domain/chained targets."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict

from seo_common import fetch_url, issue, normalize_url, parse_html, read_urls, same_host


def check_canonicals(urls: list[str], timeout: int = 15, check_targets: bool = False) -> dict:
    rows = []
    issues = []
    canonical_to_pages = defaultdict(list)
    for url in urls:
        fetched = fetch_url(url, timeout=timeout, max_bytes=1_500_000)
        row = {"url": normalize_url(url), "status": fetched.get("status"), "final_url": fetched.get("url"), "canonical": None, "verdict": "unknown", "issues": []}
        if fetched.get("text"):
            html = parse_html(fetched["text"], fetched.get("url") or url)
            row["canonical"] = html.get("canonical")
        if not row["canonical"]:
            row["verdict"] = "missing"
            row["issues"].append("missing canonical")
            issues.append(issue("warning", "Missing canonical", row["url"]))
        else:
            canonical = normalize_url(row["canonical"], fetched.get("url") or url)
            row["canonical"] = canonical
            canonical_to_pages[canonical].append(row["url"])
            if canonical == normalize_url(fetched.get("url") or url):
                row["verdict"] = "self_canonical"
            elif not same_host(row["url"], canonical):
                row["verdict"] = "cross_host"
                row["issues"].append("cross-host canonical")
                issues.append(issue("warning", "Cross-host canonical", row["url"], canonical))
            else:
                row["verdict"] = "canonicalized"
            if check_targets:
                target = fetch_url(canonical, timeout=timeout, max_bytes=1_000_000)
                row["canonical_status"] = target.get("status")
                if target.get("status") != 200:
                    row["issues"].append(f"canonical target HTTP {target.get('status')}")
                    issues.append(issue("error", "Canonical target is not 200", row["url"], str(target.get("status"))))
                if target.get("text"):
                    target_html = parse_html(target["text"], target.get("url") or canonical)
                    if target_html.get("canonical") and normalize_url(target_html["canonical"]) != canonical:
                        row["issues"].append("canonical chain detected")
                        issues.append(issue("warning", "Canonical target points elsewhere", row["url"], target_html["canonical"]))
        rows.append(row)
    duplicates = {canonical: pages for canonical, pages in canonical_to_pages.items() if len(pages) > 1}
    return {"count": len(rows), "rows": rows, "duplicate_canonical_targets": duplicates, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check canonical tags")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--url-file")
    parser.add_argument("--check-targets", action="store_true")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = check_canonicals(read_urls(args.urls, args.url_file), args.timeout, args.check_targets)
    print(json.dumps(result, indent=2) if args.json else "\n".join(f"{r['verdict']}\t{r['url']}\t{r.get('canonical') or ''}" for r in result["rows"]))


if __name__ == "__main__":
    main()
