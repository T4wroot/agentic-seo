#!/usr/bin/env python3
"""Check E-E-A-T signals in HTML content."""

from __future__ import annotations

import argparse
import json
import os
import re
from urllib.parse import urlparse

from seo_common import load_html, parse_html


CREDENTIAL_RE = re.compile(
    r"\b(phd|m\.?d\.?|doctor|professor|certified|licensed|editor|reviewed by|fact[- ]checked|"
    r"years? of experience|award[- ]winning|expert|specialist)\b",
    re.I,
)
FIRST_HAND_RE = re.compile(
    r"\b(we tested|our testing|hands[- ]on|first[- ]hand|case study|in our experience|"
    r"we measured|we reviewed|original research|surveyed)\b",
    re.I,
)


def _load_source(source: str, timeout: int) -> tuple[str, str, dict]:
    if os.path.exists(source):
        with open(source, "r", encoding="utf-8") as fh:
            return fh.read(), "", {"url": source, "status": None, "headers": {}, "error": None}
    return load_html(source, timeout=timeout)


def _walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _schema_values(schema_items: list, keys: set[str]) -> list[str]:
    values = []
    for item in schema_items:
        for node in _walk_json(item):
            for key in keys:
                value = node.get(key)
                if isinstance(value, str):
                    values.append(value)
                elif isinstance(value, dict) and value.get("name"):
                    values.append(str(value["name"]))
                elif isinstance(value, list):
                    values.extend(str(v.get("name") if isinstance(v, dict) else v) for v in value)
    return [value for value in values if value and value != "None"]


def check_eeat(source: str, timeout: int = 15) -> dict:
    html, url, fetched = _load_source(source, timeout)
    parsed = parse_html(html, url)
    soup = parsed["soup"]
    body = parsed.get("body_text", "")

    author_meta = [
        tag.get("content") or tag.get_text(" ", strip=True)
        for tag in soup.find_all(["meta", "span", "a"], attrs={"name": "author"})
        + soup.find_all(["a", "span"], rel=lambda value: value and "author" in value)
    ]
    class_authors = [
        tag.get_text(" ", strip=True)
        for tag in soup.find_all(attrs={"class": re.compile(r"(author|byline)", re.I)})
        if tag.get_text(strip=True)
    ]
    schema_authors = _schema_values(parsed.get("schema", []), {"author", "reviewedBy", "publisher"})
    authors = sorted({value.strip() for value in author_meta + class_authors + schema_authors if value and value.strip()})

    credential_hits = sorted({match.group(0) for match in CREDENTIAL_RE.finditer(body)})
    experience_hits = sorted({match.group(0) for match in FIRST_HAND_RE.finditer(body)})
    links = parsed.get("links", [])
    policy_links = [
        link for link in links
        if re.search(r"\b(editorial|review policy|fact[- ]check|corrections?|ethics)\b", link.get("text", ""), re.I)
        or re.search(r"(editorial|review-policy|fact-check|corrections|ethics)", link.get("href", ""), re.I)
    ]
    trust_links = [
        link for link in links
        if re.search(r"\b(about|contact|privacy|terms|team|authors?)\b", link.get("text", ""), re.I)
        or re.search(r"/(about|contact|privacy|terms|team|author)", link.get("href", ""), re.I)
    ]
    page_host = urlparse(url).netloc if url else ""
    external_citations = [
        link for link in links
        if urlparse(link.get("href", "")).netloc and urlparse(link.get("href", "")).netloc != page_host
    ]

    score = 0
    score += 20 if authors else 0
    score += min(20, len(credential_hits) * 7)
    score += min(20, len(experience_hits) * 7)
    score += 15 if policy_links else 0
    score += 15 if trust_links else 0
    score += min(10, len(external_citations) * 2)

    issues = []
    if not authors:
        issues.append({"severity": "warning", "message": "No clear author, byline, reviewer, or publisher signal found."})
    if not credential_hits:
        issues.append({"severity": "info", "message": "No visible credential or review language found."})
    if not policy_links:
        issues.append({"severity": "info", "message": "No editorial, review, corrections, or fact-check policy link detected."})
    if not trust_links:
        issues.append({"severity": "warning", "message": "No obvious about/contact/privacy/team trust links detected."})

    return {
        "url": url or source,
        "score": min(100, score),
        "signals": {
            "authors": authors[:20],
            "credential_markers": credential_hits[:20],
            "first_hand_experience_markers": experience_hits[:20],
            "policy_links": policy_links[:20],
            "trust_links": trust_links[:20],
            "external_citations": len(external_citations),
        },
        "issues": issues,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check visible E-E-A-T signals in a URL or HTML file.")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = check_eeat(args.source, args.timeout)
    print(json.dumps(result, indent=2) if args.json else f"Score: {result['score']} Issues: {len(result['issues'])}")


if __name__ == "__main__":
    main()
