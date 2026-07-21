#!/usr/bin/env python3
"""Assess citation and entity readiness for AI answers."""

from __future__ import annotations

import argparse
import json
import os
import re
from urllib.parse import urlparse

from seo_common import load_html, parse_html


CLAIM_RE = re.compile(
    r"(\d+(?:\.\d+)?%|\$[\d,.]+|\b(?:20\d{2}|19\d{2})\b|"
    r"\b(?:study|research|survey|report|data|according to|found that|shows that|largest|first|only|most)\b)",
    re.I,
)
HIGH_TRUST_HOST_RE = re.compile(
    r"((^|\.)gov(\.|$)|(^|\.)edu$|who\.int$|nih\.gov$|cdc\.gov$|worldbank\.org$|oecd\.org$|wikipedia\.org$)",
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


def _schema_entity_signals(schema_items: list) -> dict:
    names = set()
    same_as = set()
    types = set()
    for item in schema_items:
        for node in _walk_json(item):
            if node.get("@type"):
                types.add(str(node["@type"]))
            if node.get("name"):
                names.add(str(node["name"]))
            value = node.get("sameAs")
            if isinstance(value, str):
                same_as.add(value)
            elif isinstance(value, list):
                same_as.update(str(v) for v in value)
    return {"types": sorted(types), "names": sorted(names), "sameAs": sorted(same_as)}


def check_citation_readiness(source: str, timeout: int = 15) -> dict:
    html, url, fetched = _load_source(source, timeout)
    parsed = parse_html(html, url)
    soup = parsed["soup"]
    page_host = urlparse(url).netloc if url else ""

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", parsed.get("body_text", "")) if sentence.strip()]
    factual_claims = [sentence for sentence in sentences if CLAIM_RE.search(sentence)]
    external_links = []
    trusted_links = []
    for link in parsed.get("links", []):
        host = urlparse(link.get("href", "")).netloc
        if not host or host == page_host:
            continue
        external_links.append(link)
        if HIGH_TRUST_HOST_RE.search(host):
            trusted_links.append(link)

    cite_tags = [tag.get_text(" ", strip=True) for tag in soup.find_all(["cite", "blockquote"])]
    footnote_links = [
        link for link in parsed.get("links", [])
        if re.search(r"(footnote|reference|citation|source)", " ".join(map(str, link.get("rel", []))) + " " + link.get("href", ""), re.I)
    ]
    entity_signals = _schema_entity_signals(parsed.get("schema", []))
    author_signals = bool(entity_signals["names"]) or bool(soup.find(attrs={"class": re.compile(r"(author|byline)", re.I)}))

    citation_capacity = len(external_links) + len(cite_tags) + len(footnote_links)
    claim_coverage = min(1.0, citation_capacity / max(1, len(factual_claims)))
    score = 0
    score += int(claim_coverage * 35)
    score += min(20, len(trusted_links) * 5)
    score += 15 if author_signals else 0
    score += min(20, len(entity_signals["sameAs"]) * 5)
    score += 10 if parsed.get("canonical") else 0

    issues = []
    if factual_claims and citation_capacity < len(factual_claims):
        issues.append({"severity": "warning", "message": "Factual claims outnumber visible citation/source signals."})
    if not trusted_links:
        issues.append({"severity": "info", "message": "No high-trust external source domains detected."})
    if not author_signals:
        issues.append({"severity": "warning", "message": "No clear author or entity name signal detected."})
    if not entity_signals["sameAs"]:
        issues.append({"severity": "info", "message": "No sameAs entity links found in JSON-LD."})

    return {
        "url": url or source,
        "score": min(100, score),
        "factual_claims": len(factual_claims),
        "claim_samples": factual_claims[:10],
        "citation_signals": {
            "external_links": len(external_links),
            "trusted_external_links": len(trusted_links),
            "cite_or_blockquote_tags": len(cite_tags),
            "footnote_links": len(footnote_links),
        },
        "entity_signals": entity_signals,
        "issues": issues,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Assess source, claim, author, and entity citation readiness.")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = check_citation_readiness(args.source, args.timeout)
    print(json.dumps(result, indent=2) if args.json else f"Score: {result['score']} Claims: {result['factual_claims']}")


if __name__ == "__main__":
    main()
