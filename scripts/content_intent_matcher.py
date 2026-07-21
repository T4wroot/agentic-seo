#!/usr/bin/env python3
"""Match page content to a target keyword and search intent."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter

from seo_common import load_html, parse_html


INTENT_MARKERS = {
    "informational": {
        "what", "how", "why", "guide", "tutorial", "learn", "examples", "definition", "checklist", "tips",
    },
    "commercial": {
        "best", "top", "review", "compare", "comparison", "alternative", "alternatives", "vs", "pricing",
    },
    "transactional": {
        "buy", "order", "download", "demo", "trial", "quote", "book", "subscribe", "pricing", "coupon",
    },
    "navigational": {
        "login", "sign in", "support", "docs", "documentation", "contact", "about", "portal", "dashboard",
    },
}


def _load_source(source: str, timeout: int) -> tuple[str, str, dict]:
    if os.path.exists(source):
        with open(source, "r", encoding="utf-8") as fh:
            return fh.read(), "", {"url": source, "status": None, "headers": {}, "error": None}
    return load_html(source, timeout=timeout)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9'-]*", (text or "").lower())


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(r"\b" + re.escape(phrase.lower()) + r"\b", (text or "").lower()) is not None


def infer_intent(keyword: str, page_text: str) -> str:
    haystack = f"{keyword} {page_text}".lower()
    scores = {}
    for intent, markers in INTENT_MARKERS.items():
        scores[intent] = sum(1 for marker in markers if re.search(r"\b" + re.escape(marker) + r"\b", haystack))
    return max(scores, key=scores.get) if any(scores.values()) else "informational"


def match_intent(source: str, keyword: str, intent: str | None = None, timeout: int = 15) -> dict:
    html, url, fetched = _load_source(source, timeout)
    parsed = parse_html(html, url)
    keyword = keyword.strip().lower()
    target_intent = intent or infer_intent(keyword, parsed.get("body_text", ""))
    keyword_terms = [term for term in _tokens(keyword) if len(term) > 1]
    body_tokens = _tokens(parsed.get("body_text", ""))
    body_counts = Counter(body_tokens)
    body_total = max(1, len(body_tokens))

    title = parsed.get("title") or ""
    meta_description = parsed.get("meta_description") or ""
    h1_text = " ".join(parsed.get("headings", {}).get("h1", []))
    headings = " ".join(sum((values for values in parsed.get("headings", {}).values()), []))

    fields = {
        "title": title,
        "h1": h1_text,
        "meta_description": meta_description,
        "headings": headings,
        "body": parsed.get("body_text", ""),
    }
    exact_matches = {name: _contains_phrase(text, keyword) for name, text in fields.items()}
    coverage = {
        name: round(sum(1 for term in keyword_terms if term in set(_tokens(text))) / max(1, len(keyword_terms)), 3)
        for name, text in fields.items()
    }
    density = sum(body_counts[term] for term in keyword_terms) / body_total
    marker_hits = sorted(
        marker
        for marker in INTENT_MARKERS.get(target_intent, set())
        if re.search(r"\b" + re.escape(marker) + r"\b", parsed.get("body_text", "").lower())
    )

    score = 0
    score += 18 if exact_matches["title"] else int(12 * coverage["title"])
    score += 18 if exact_matches["h1"] else int(12 * coverage["h1"])
    score += 12 if exact_matches["meta_description"] else int(8 * coverage["meta_description"])
    score += min(18, int(coverage["headings"] * 18))
    score += min(16, int(density * 1400))
    score += min(18, len(marker_hits) * 4)

    issues = []
    if not exact_matches["title"]:
        issues.append({"severity": "warning", "message": "Title does not contain the exact target keyword."})
    if not exact_matches["h1"]:
        issues.append({"severity": "warning", "message": "H1 does not contain the exact target keyword."})
    if not marker_hits:
        issues.append({"severity": "info", "message": f"No clear {target_intent} intent markers found in body copy."})
    if parsed.get("word_count", 0) < 300:
        issues.append({"severity": "warning", "message": "Page body is short for intent matching evidence."})

    return {
        "url": url or source,
        "keyword": keyword,
        "intent": target_intent,
        "score": min(100, score),
        "word_count": parsed.get("word_count", 0),
        "exact_matches": exact_matches,
        "term_coverage": coverage,
        "keyword_density": round(density, 4),
        "intent_markers": marker_hits,
        "issues": issues,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Match title, H1, meta, headings, and body text to keyword intent.")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--keyword", required=True, help="Target keyword or query")
    parser.add_argument("--intent", choices=sorted(INTENT_MARKERS), help="Expected intent. Defaults to inferred intent.")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = match_intent(args.source, args.keyword, args.intent, args.timeout)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Score: {result['score']} Intent: {result['intent']} Issues: {len(result['issues'])}")


if __name__ == "__main__":
    main()
