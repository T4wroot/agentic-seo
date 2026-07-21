#!/usr/bin/env python3
"""Accessibility checks with direct SEO/UX impact."""

from __future__ import annotations

import argparse
import json
import re

from seo_common import load_html, parse_html


def checker(source: str, timeout: int = 15) -> dict:
    html, url, fetched = load_html(source, timeout=timeout)
    parsed = parse_html(html, url)
    soup = parsed["soup"]
    issues = []
    h1_count = len(parsed["headings"]["h1"])
    if h1_count != 1:
        issues.append({"severity": "warning", "message": f"Expected one H1, found {h1_count}"})
    if not parsed.get("lang"):
        issues.append({"severity": "warning", "message": "Missing html lang attribute"})
    if not parsed.get("viewport"):
        issues.append({"severity": "warning", "message": "Missing viewport meta tag"})
    missing_alt = [img.get("src") or "" for img in soup.find_all("img") if img.get("alt") is None]
    for src in missing_alt[:25]:
        issues.append({"severity": "warning", "message": "Image missing alt attribute", "url": src})
    inputs = soup.find_all(["input", "select", "textarea"])
    labelled = 0
    for field in inputs:
        field_id = field.get("id")
        if field.get("aria-label") or field.get("aria-labelledby") or field.get("title"):
            labelled += 1
        elif field_id and soup.find("label", attrs={"for": field_id}):
            labelled += 1
    if inputs and labelled < len(inputs):
        issues.append({"severity": "warning", "message": f"{len(inputs) - labelled} form field(s) appear unlabeled"})
    if parsed["landmarks"]["main"] == 0:
        issues.append({"severity": "info", "message": "No <main> landmark found"})
    generic_anchors = [a.get_text(" ", strip=True) for a in soup.find_all("a", href=True) if re.fullmatch(r"(click here|read more|more|learn more)", a.get_text(" ", strip=True).lower())]
    if generic_anchors:
        issues.append({"severity": "info", "message": f"{len(generic_anchors)} generic link text instance(s)"})
    # Static contrast check for inline style hex colors only; avoids pretending to compute full CSS cascade.
    contrast_candidates = 0
    for tag in soup.find_all(style=True):
        style = tag["style"]
        if "color" in style and "background" in style and re.search(r"#[0-9a-fA-F]{3,6}", style):
            contrast_candidates += 1
    return {
        "url": url or source,
        "score": max(0, 100 - 8 * len(issues)),
        "checks": {
            "h1_count": h1_count,
            "lang": parsed.get("lang"),
            "viewport": bool(parsed.get("viewport")),
            "images_missing_alt": len(missing_alt),
            "form_controls": len(inputs),
            "labeled_controls": labelled,
            "landmarks": parsed["landmarks"],
            "inline_contrast_candidates": contrast_candidates,
        },
        "issues": issues,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check accessibility signals relevant to SEO")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = checker(args.source, args.timeout)
    print(json.dumps(result, indent=2) if args.json else f"Score: {result['score']} Issues: {len(result['issues'])}")


if __name__ == "__main__":
    main()
