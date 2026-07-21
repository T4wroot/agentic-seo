#!/usr/bin/env python3
"""Validate required and recommended Schema.org properties in JSON-LD."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from typing import Any

from seo_common import issue, load_html, parse_html, print_json_or_text


REQUIRED_PROPS: dict[str, set[str]] = {
    "Article": {"headline", "author", "datePublished"},
    "BlogPosting": {"headline", "author", "datePublished"},
    "BreadcrumbList": {"itemListElement"},
    "FAQPage": {"mainEntity"},
    "HowTo": {"name", "step"},
    "LocalBusiness": {"name", "address", "telephone"},
    "Organization": {"name", "url"},
    "Product": {"name", "offers"},
    "ProductGroup": {"name", "productGroupID", "hasVariant"},
    "Review": {"itemReviewed", "reviewRating", "author"},
    "VideoObject": {"name", "description", "thumbnailUrl", "uploadDate"},
    "WebSite": {"name", "url"},
}

RECOMMENDED_PROPS: dict[str, set[str]] = {
    "Article": {"image", "dateModified", "publisher", "mainEntityOfPage"},
    "BlogPosting": {"image", "dateModified", "publisher", "mainEntityOfPage"},
    "BreadcrumbList": {"name", "position", "item"},
    "LocalBusiness": {"url", "image", "geo", "openingHoursSpecification", "sameAs", "aggregateRating"},
    "Organization": {"logo", "sameAs", "contactPoint"},
    "Product": {"image", "description", "sku", "brand", "aggregateRating", "review"},
    "ProductGroup": {"variesBy", "brand", "description"},
    "Review": {"reviewBody", "datePublished", "publisher"},
    "VideoObject": {"duration", "contentUrl", "embedUrl", "publisher", "transcript"},
    "WebSite": {"potentialAction"},
}

PLACEHOLDER_MARKERS = ("[", "REPLACE", "TODO", "INSERT", "example.com")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def schema_type_names(value: Any) -> list[str]:
    names = []
    for item in as_list(value):
        if isinstance(item, str):
            names.append(item)
    return names


def iter_schema_nodes(data: Any, path: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    """Yield every JSON-LD object, including @graph and nested entity objects."""
    if isinstance(data, list):
        for index, item in enumerate(data):
            yield from iter_schema_nodes(item, f"{path}[{index}]")
        return
    if not isinstance(data, dict):
        return
    yield path, data
    graph = data.get("@graph")
    if isinstance(graph, list):
        for index, item in enumerate(graph):
            yield from iter_schema_nodes(item, f"{path}.@graph[{index}]")
    for key, value in data.items():
        if key in {"@context", "@graph"}:
            continue
        if isinstance(value, dict):
            yield from iter_schema_nodes(value, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    yield from iter_schema_nodes(item, f"{path}.{key}[{index}]")


def load_source_html(source: str, timeout: int = 15) -> tuple[str, str, dict[str, Any]]:
    """Load local files before falling back to seo_common URL detection."""
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8") as fh:
            return fh.read(), source, {"url": source, "status": None, "headers": {}, "error": None}
    return load_html(source, timeout=timeout)


def extract_schema_documents(source: str, timeout: int = 15) -> tuple[list[Any], dict[str, Any]]:
    html_or_json, final_url, fetch = load_source_html(source, timeout=timeout)
    text = (html_or_json or "").strip()
    documents: list[Any] = []
    if text.startswith("{") or text.startswith("["):
        try:
            documents.append(json.loads(text))
        except json.JSONDecodeError:
            pass
    if not documents and html_or_json:
        parsed = parse_html(html_or_json, final_url or source)
        documents.extend(item for item in parsed.get("schema", []) if not (isinstance(item, dict) and item.get("error")))
    return documents, {"source": source, "final_url": final_url or source, "fetch": fetch}


def find_schema_nodes(documents: list[Any], schema_type: str | None = None) -> list[dict[str, Any]]:
    rows = []
    for doc_index, doc in enumerate(documents):
        for path, node in iter_schema_nodes(doc, f"$[{doc_index}]"):
            types = schema_type_names(node.get("@type"))
            if not types:
                continue
            if schema_type and schema_type not in types:
                continue
            rows.append({"path": path, "types": types, "node": node})
    return rows


def has_value(node: dict[str, Any], prop: str) -> bool:
    if prop not in node:
        return False
    value = node[prop]
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def contains_placeholder(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    upper = text.upper()
    return any(marker.upper() in upper for marker in PLACEHOLDER_MARKERS)


def validate_schema_required_props(documents: list[Any], schema_type: str | None = None) -> dict[str, Any]:
    rows = []
    issues = []
    nodes = find_schema_nodes(documents, schema_type)
    for row in nodes:
        node = row["node"]
        primary_type = row["types"][0]
        required = set()
        recommended = set()
        for type_name in row["types"]:
            required.update(REQUIRED_PROPS.get(type_name, set()))
            recommended.update(RECOMMENDED_PROPS.get(type_name, set()))
        missing_required = sorted(prop for prop in required if not has_value(node, prop))
        missing_recommended = sorted(prop for prop in recommended if not has_value(node, prop))
        placeholders = sorted(prop for prop, value in node.items() if contains_placeholder(value))
        for prop in missing_required:
            issues.append(issue("error", f"{primary_type} is missing required property '{prop}'", evidence=row["path"]))
        for prop in missing_recommended:
            issues.append(issue("warning", f"{primary_type} is missing recommended property '{prop}'", evidence=row["path"]))
        for prop in placeholders:
            issues.append(issue("warning", f"{primary_type} property '{prop}' appears to contain placeholder text", evidence=row["path"]))
        rows.append(
            {
                "path": row["path"],
                "types": row["types"],
                "missing_required": missing_required,
                "missing_recommended": missing_recommended,
                "placeholder_properties": placeholders,
            }
        )
    return {
        "schema_nodes": len(nodes),
        "checked_type": schema_type,
        "rows": rows,
        "issues": issues,
        "summary": {
            "errors": sum(1 for item in issues if item["severity"] == "error"),
            "warnings": sum(1 for item in issues if item["severity"] == "warning"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate required/recommended JSON-LD properties")
    parser.add_argument("source", help="URL, HTML file, or JSON-LD file")
    parser.add_argument("--type", dest="schema_type", help="Limit checks to one schema type, e.g. Product")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    documents, meta = extract_schema_documents(args.source, timeout=args.timeout)
    result = validate_schema_required_props(documents, args.schema_type)
    result.update({"source": args.source, "final_url": meta["final_url"]})
    lines = [
        f"Schema required properties for {args.source}",
        f"Nodes checked: {result['schema_nodes']}  Errors: {result['summary']['errors']}  Warnings: {result['summary']['warnings']}",
    ] + [f"[{item['severity']}] {item['message']} {item.get('evidence') or ''}" for item in result["issues"][:30]]
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
