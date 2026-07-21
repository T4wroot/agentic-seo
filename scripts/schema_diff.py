#!/usr/bin/env python3
"""Compare existing JSON-LD against a recommended bundled schema template."""

from __future__ import annotations

import argparse
import json
from typing import Any

from schema_required_props import extract_schema_documents, find_schema_nodes
from schema_template_generator import get_template
from seo_common import issue, print_json_or_text


def prop_set(node: dict[str, Any]) -> set[str]:
    return {key for key in node if not key.startswith("@")}


def diff_schema(source: str, schema_type: str, timeout: int = 15) -> dict[str, Any]:
    documents, meta = extract_schema_documents(source, timeout=timeout)
    nodes = find_schema_nodes(documents, schema_type)
    template = get_template(schema_type, compact=True)
    recommended_props = prop_set(template)
    if not nodes:
        return {
            "source": source,
            "final_url": meta["final_url"],
            "type": schema_type,
            "matched_nodes": 0,
            "template": template,
            "diffs": [],
            "issues": [issue("error", f"No {schema_type} JSON-LD node found")],
        }
    diffs = []
    issues = []
    for row in nodes:
        current = row["node"]
        current_props = prop_set(current)
        missing = sorted(recommended_props - current_props)
        extra = sorted(current_props - recommended_props)
        changed_types = sorted(set(row["types"]) ^ set([schema_type]))
        for prop in missing:
            issues.append(issue("warning", f"Add recommended {schema_type} property '{prop}'", evidence=row["path"]))
        diffs.append(
            {
                "path": row["path"],
                "current_type": row["types"],
                "missing_properties": missing,
                "extra_properties": extra,
                "type_differences": changed_types,
                "suggested_patch": {prop: template[prop] for prop in missing if prop in template},
            }
        )
    return {
        "source": source,
        "final_url": meta["final_url"],
        "type": schema_type,
        "matched_nodes": len(nodes),
        "template": template,
        "diffs": diffs,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff current JSON-LD against a bundled schema template")
    parser.add_argument("source", help="URL, HTML file, or JSON-LD file")
    parser.add_argument("--type", dest="schema_type", required=True, help="Schema type to compare")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    result = diff_schema(args.source, args.schema_type, timeout=args.timeout)
    lines = [
        f"Schema diff for {result['type']} on {args.source}",
        f"Matched nodes: {result['matched_nodes']}  Issues: {len(result['issues'])}",
    ]
    for diff in result["diffs"]:
        lines.append(f"{diff['path']}: add {', '.join(diff['missing_properties']) or 'nothing'}")
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
