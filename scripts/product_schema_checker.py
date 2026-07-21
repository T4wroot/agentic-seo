#!/usr/bin/env python3
"""Check Product and ProductGroup JSON-LD for ecommerce rich-result readiness."""

from __future__ import annotations

import argparse
import json
from typing import Any

from schema_required_props import extract_schema_documents, find_schema_nodes
from seo_common import issue, print_json_or_text


VALID_AVAILABILITY = {
    "https://schema.org/InStock",
    "https://schema.org/OutOfStock",
    "https://schema.org/PreOrder",
    "https://schema.org/BackOrder",
    "https://schema.org/LimitedAvailability",
    "InStock",
    "OutOfStock",
    "PreOrder",
    "BackOrder",
}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def check_offer(offer: dict[str, Any], path: str) -> list[dict[str, Any]]:
    issues = []
    if not offer.get("price") and not offer.get("lowPrice"):
        issues.append(issue("error", "Offer is missing price or lowPrice", evidence=path))
    if not offer.get("priceCurrency"):
        issues.append(issue("error", "Offer is missing priceCurrency", evidence=path))
    availability = offer.get("availability")
    if not availability:
        issues.append(issue("warning", "Offer is missing availability", evidence=path))
    elif availability not in VALID_AVAILABILITY:
        issues.append(issue("warning", "Offer availability should use a Schema.org ItemAvailability URL", evidence=path))
    if not offer.get("url"):
        issues.append(issue("info", "Offer is missing url", evidence=path))
    if not offer.get("shippingDetails"):
        issues.append(issue("info", "Offer is missing shippingDetails", evidence=path))
    if not offer.get("hasMerchantReturnPolicy"):
        issues.append(issue("info", "Offer is missing hasMerchantReturnPolicy", evidence=path))
    return issues


def check_product_schema(documents: list[Any]) -> dict[str, Any]:
    rows = []
    issues = []
    product_rows = find_schema_nodes(documents, "Product") + find_schema_nodes(documents, "ProductGroup")
    for row in product_rows:
        node = row["node"]
        row_issues = []
        for prop in ("name", "image", "description"):
            if not node.get(prop):
                severity = "error" if prop == "name" else "warning"
                row_issues.append(issue(severity, f"Product is missing {prop}", evidence=row["path"]))
        if "Product" in row["types"] and not node.get("offers"):
            row_issues.append(issue("error", "Product is missing offers", evidence=row["path"]))
        if "ProductGroup" in row["types"]:
            for prop in ("productGroupID", "variesBy", "hasVariant"):
                if not node.get(prop):
                    row_issues.append(issue("error", f"ProductGroup is missing {prop}", evidence=row["path"]))
        if not node.get("sku") and not node.get("gtin") and not node.get("mpn"):
            row_issues.append(issue("warning", "Product is missing sku/gtin/mpn identifier", evidence=row["path"]))
        if not node.get("brand"):
            row_issues.append(issue("info", "Product is missing brand", evidence=row["path"]))
        for index, offer in enumerate(as_list(node.get("offers"))):
            if isinstance(offer, dict):
                row_issues.extend(check_offer(offer, f"{row['path']}.offers[{index}]"))
        for index, variant in enumerate(as_list(node.get("hasVariant"))):
            if isinstance(variant, dict):
                if not variant.get("offers"):
                    row_issues.append(issue("error", "Product variant is missing offers", evidence=f"{row['path']}.hasVariant[{index}]"))
                for offer_index, offer in enumerate(as_list(variant.get("offers"))):
                    if isinstance(offer, dict):
                        row_issues.extend(check_offer(offer, f"{row['path']}.hasVariant[{index}].offers[{offer_index}]"))
        rows.append({"path": row["path"], "types": row["types"], "issues": row_issues})
        issues.extend(row_issues)
    return {"products": len(product_rows), "rows": rows, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Product/ProductGroup JSON-LD")
    parser.add_argument("source", help="URL, HTML file, or JSON-LD file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    documents, meta = extract_schema_documents(args.source, timeout=args.timeout)
    result = check_product_schema(documents)
    result.update({"source": args.source, "final_url": meta["final_url"]})
    lines = [f"Product schema check for {args.source}", f"Products: {result['products']}  Issues: {len(result['issues'])}"]
    lines.extend(f"[{item['severity']}] {item['message']} {item.get('evidence') or ''}" for item in result["issues"][:30])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
