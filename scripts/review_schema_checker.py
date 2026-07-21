#!/usr/bin/env python3
"""Check Review and AggregateRating markup for policy and misuse risks."""

from __future__ import annotations

import argparse
from typing import Any

from schema_required_props import extract_schema_documents, find_schema_nodes
from seo_common import issue, print_json_or_text


SELF_SERVING_TYPES = {"LocalBusiness", "Organization", "Service"}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def type_names(value: Any) -> set[str]:
    return {item for item in as_list(value) if isinstance(item, str)}


def check_rating_value(value: Any, path: str) -> list[dict[str, Any]]:
    issues = []
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        issues.append(issue("error", "ratingValue must be numeric", evidence=path))
        return issues
    if numeric < 1 or numeric > 5:
        issues.append(issue("warning", "ratingValue is outside the common 1-5 range", evidence=path))
    return issues


def check_review_schema(documents: list[Any]) -> dict[str, Any]:
    rows = []
    issues = []
    review_nodes = find_schema_nodes(documents, "Review")
    aggregate_nodes = [row for row in find_schema_nodes(documents) if row["node"].get("aggregateRating")]
    for row in review_nodes:
        node = row["node"]
        row_issues = []
        for prop in ("itemReviewed", "reviewRating", "author"):
            if not node.get(prop):
                row_issues.append(issue("error", f"Review is missing {prop}", evidence=row["path"]))
        rating = node.get("reviewRating") if isinstance(node.get("reviewRating"), dict) else {}
        if rating:
            row_issues.extend(check_rating_value(rating.get("ratingValue"), f"{row['path']}.reviewRating"))
        if not node.get("reviewBody"):
            row_issues.append(issue("warning", "Review is missing reviewBody", evidence=row["path"]))
        if not node.get("datePublished"):
            row_issues.append(issue("info", "Review is missing datePublished", evidence=row["path"]))
        rows.append({"path": row["path"], "types": row["types"], "issues": row_issues})
        issues.extend(row_issues)
    for row in aggregate_nodes:
        node = row["node"]
        agg = node.get("aggregateRating")
        if not isinstance(agg, dict):
            continue
        parent_types = type_names(node.get("@type"))
        if parent_types & SELF_SERVING_TYPES:
            issues.append(issue("warning", "AggregateRating on LocalBusiness/Organization/Service can be self-serving and ineligible", evidence=row["path"]))
        for prop in ("ratingValue", "reviewCount"):
            if not agg.get(prop):
                issues.append(issue("error", f"aggregateRating is missing {prop}", evidence=f"{row['path']}.aggregateRating"))
        if agg.get("ratingValue") is not None:
            issues.extend(check_rating_value(agg.get("ratingValue"), f"{row['path']}.aggregateRating"))
    return {"reviews": len(review_nodes), "aggregate_ratings": len(aggregate_nodes), "rows": rows, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Review/AggregateRating JSON-LD")
    parser.add_argument("source", help="URL, HTML file, or JSON-LD file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    documents, meta = extract_schema_documents(args.source, timeout=args.timeout)
    result = check_review_schema(documents)
    result.update({"source": args.source, "final_url": meta["final_url"]})
    lines = [f"Review schema check for {args.source}", f"Reviews: {result['reviews']}  Aggregate ratings: {result['aggregate_ratings']}  Issues: {len(result['issues'])}"]
    lines.extend(f"[{item['severity']}] {item['message']} {item.get('evidence') or ''}" for item in result["issues"][:30])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
