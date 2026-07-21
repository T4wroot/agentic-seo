#!/usr/bin/env python3
"""Generate JSON-LD templates from bundled schema templates."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from schema_required_props import load_source_html
from seo_common import parse_html, print_json_or_text


TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "resources" / "schema" / "templates.json"

FALLBACK_TEMPLATES: dict[str, dict[str, Any]] = {
    "Product": {
        "type": "Product",
        "description": "Standard ecommerce product page with Offer, product identifiers, images, and rating/review hooks.",
        "template": {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "[Product Name]",
            "description": "[Product Description]",
            "image": ["[Product Image URL]"],
            "sku": "[SKU]",
            "brand": {"@type": "Brand", "name": "[Brand Name]"},
            "offers": {
                "@type": "Offer",
                "url": "[Product URL]",
                "price": "[Price]",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
        },
    },
    "Review": {
        "type": "Review",
        "description": "Review markup for first-party or editorial reviews with rating and reviewed entity.",
        "template": {
            "@context": "https://schema.org",
            "@type": "Review",
            "itemReviewed": {"@type": "Thing", "name": "[Reviewed Item]"},
            "reviewRating": {"@type": "Rating", "ratingValue": "[1-5]", "bestRating": "5", "worstRating": "1"},
            "author": {"@type": "Person", "name": "[Reviewer Name]"},
            "reviewBody": "[Review text]",
            "datePublished": "[YYYY-MM-DD]",
        },
    },
}


def load_templates(path: Path = TEMPLATE_PATH) -> dict[str, dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    templates = {item["type"]: item for item in data.get("templates", [])}
    templates.update({key: value for key, value in FALLBACK_TEMPLATES.items() if key not in templates})
    return templates


def detect_template_type(source: str, timeout: int = 15) -> str:
    html, final_url, _ = load_source_html(source, timeout=timeout)
    parsed = parse_html(html, final_url or source) if html else {}
    text = " ".join(
        [
            parsed.get("title") or "",
            parsed.get("meta_description") or "",
            " ".join(parsed.get("headings", {}).get("h1", [])),
        ]
    ).lower()
    schema_types = []
    for doc in parsed.get("schema", []):
        if isinstance(doc, dict):
            value = doc.get("@type")
            schema_types.extend(value if isinstance(value, list) else [value])
    for type_name in schema_types:
        if type_name in load_templates():
            return type_name
    if any(word in text for word in ("video", "webinar", "watch")):
        return "VideoObject"
    if any(word in text for word in ("product", "price", "buy", "cart")):
        return "ProductGroup"
    if any(word in text for word in ("near me", "hours", "location", "appointment")):
        return "LocalBusiness"
    if any(word in text for word in ("blog", "guide", "article")):
        return "BlogPosting"
    return "WebSite"


def get_template(schema_type: str, compact: bool = False) -> dict[str, Any]:
    templates = load_templates()
    if schema_type not in templates:
        available = ", ".join(sorted(templates))
        raise SystemExit(f"Unknown template type '{schema_type}'. Available: {available}")
    template = deepcopy(templates[schema_type]["template"])
    if compact:
        return template
    return {
        "type": schema_type,
        "description": templates[schema_type].get("description"),
        "json_ld": template,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a JSON-LD template from bundled schema templates")
    parser.add_argument("--type", dest="schema_type", help="Schema type to generate")
    parser.add_argument("--detect-from", help="URL or HTML file to infer a page/schema type")
    parser.add_argument("--list", action="store_true", help="List available template types")
    parser.add_argument("--compact", action="store_true", help="Print only the JSON-LD object")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON instead of a script tag")
    args = parser.parse_args()

    templates = load_templates()
    if args.list:
        result = {"templates": [{"type": key, "description": value.get("description")} for key, value in sorted(templates.items())]}
        print_json_or_text(result, args.json, [item["type"] for item in result["templates"]])
        return
    schema_type = args.schema_type or (detect_template_type(args.detect_from, args.timeout) if args.detect_from else None)
    if not schema_type:
        raise SystemExit("Provide --type, --detect-from, or --list.")
    result = get_template(schema_type, compact=args.compact)
    payload = result if args.compact else result["json_ld"]
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print('<script type="application/ld+json">')
        print(json.dumps(payload, indent=2))
        print("</script>")


if __name__ == "__main__":
    main()
