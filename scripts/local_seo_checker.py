#!/usr/bin/env python3
"""Check local SEO signals: NAP, LocalBusiness schema, GBP links, reviews, and maps."""

from __future__ import annotations

import argparse
import re
from typing import Any

from schema_required_props import extract_schema_documents, find_schema_nodes, load_source_html
from seo_common import parse_html, print_json_or_text, issue


PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
MAP_PATTERNS = ("google.com/maps", "maps.google.", "bing.com/maps", "openstreetmap.org")
GBP_PATTERNS = ("g.page/", "business.google.com", "search.google.com/local/writereview")


def check_local_seo(source: str, timeout: int = 15) -> dict[str, Any]:
    html, final_url, fetch = load_source_html(source, timeout=timeout)
    parsed = parse_html(html, final_url or source) if html else {}
    documents, _ = extract_schema_documents(source, timeout=timeout)
    local_nodes = find_schema_nodes(documents, "LocalBusiness")
    body_text = parsed.get("body_text", "")
    links = parsed.get("links", [])
    phones = sorted(set(match.group(1).strip() for match in PHONE_RE.finditer(body_text)))
    issues = []
    if not local_nodes:
        issues.append(issue("warning", "No LocalBusiness JSON-LD found", final_url or source))
    for row in local_nodes:
        node = row["node"]
        for prop in ("name", "address", "telephone"):
            if not node.get(prop):
                issues.append(issue("error", f"LocalBusiness is missing {prop}", evidence=row["path"]))
        if not node.get("areaServed") and not node.get("serviceArea"):
            issues.append(issue("info", "LocalBusiness is missing service area signal", evidence=row["path"]))
        if node.get("telephone") and phones and str(node["telephone"]).replace(" ", "") not in "".join(phones).replace(" ", ""):
            issues.append(issue("warning", "Schema telephone does not visibly match page phone text", evidence=row["path"]))
    map_embeds = html.count("google.com/maps") + html.count("maps.google.") + html.count("openstreetmap.org") if html else 0
    if not map_embeds and not any(any(pattern in link["href"] for pattern in MAP_PATTERNS) for link in links):
        issues.append(issue("info", "No map embed or map link found", final_url or source))
    if not any(any(pattern in link["href"] for pattern in GBP_PATTERNS) for link in links):
        issues.append(issue("info", "No Google Business Profile/review link found", final_url or source))
    if "review" not in body_text.lower() and not any(row["node"].get("aggregateRating") for row in local_nodes):
        issues.append(issue("info", "No visible reviews or aggregateRating signal found", final_url or source))
    return {
        "source": source,
        "final_url": final_url or source,
        "status": fetch.get("status"),
        "local_business_nodes": len(local_nodes),
        "phones_detected": phones,
        "map_embeds": map_embeds,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local SEO signals")
    parser.add_argument("source", help="URL or HTML file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    result = check_local_seo(args.source, timeout=args.timeout)
    lines = [
        f"Local SEO check for {args.source}",
        f"LocalBusiness nodes: {result['local_business_nodes']}  Phones: {len(result['phones_detected'])}  Issues: {len(result['issues'])}",
    ] + [f"[{item['severity']}] {item['message']} {item.get('evidence') or ''}" for item in result["issues"][:30]]
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
