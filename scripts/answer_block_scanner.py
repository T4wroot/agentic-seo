#!/usr/bin/env python3
"""Scan pages for answer-block and featured-snippet-ready formatting."""

from __future__ import annotations

import argparse
import json
import os
import re

from seo_common import load_html, parse_html


QUESTION_RE = re.compile(r"^(what|why|how|when|where|who|which|can|does|is|are)\b|\?$", re.I)
DEFINITION_RE = re.compile(r"\b([A-Z][A-Za-z0-9 -]{2,80})\s+(?:is|are|refers to|means)\s+.{20,220}", re.S)


def _load_source(source: str, timeout: int) -> tuple[str, str, dict]:
    if os.path.exists(source):
        with open(source, "r", encoding="utf-8") as fh:
            return fh.read(), "", {"url": source, "status": None, "headers": {}, "error": None}
    return load_html(source, timeout=timeout)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def scan_answer_blocks(source: str, timeout: int = 15) -> dict:
    html, url, fetched = _load_source(source, timeout)
    parsed = parse_html(html, url)
    soup = parsed["soup"]

    questions = []
    direct_answers = []
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        heading_text = heading.get_text(" ", strip=True)
        if not QUESTION_RE.search(heading_text):
            continue
        questions.append(heading_text)
        sibling = heading.find_next_sibling()
        while sibling and sibling.name in {"script", "style"}:
            sibling = sibling.find_next_sibling()
        if sibling:
            answer_text = sibling.get_text(" ", strip=True)
            words = _word_count(answer_text)
            if sibling.name in {"p", "div"} and 20 <= words <= 70:
                direct_answers.append({"question": heading_text, "answer": answer_text[:320], "word_count": words})

    definitions = []
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if 20 <= _word_count(text) <= 80 and DEFINITION_RE.search(text):
            definitions.append(text[:320])

    lists = []
    for node in soup.find_all(["ol", "ul"]):
        items = [li.get_text(" ", strip=True) for li in node.find_all("li", recursive=False)]
        if len(items) >= 3:
            lists.append({"type": node.name, "items": len(items), "sample": items[:5]})

    tables = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if len(rows) >= 2:
            tables.append({"rows": len(rows), "headers": headers[:10]})

    score = min(100, len(direct_answers) * 20 + len(definitions) * 12 + len(lists) * 10 + len(tables) * 12)
    issues = []
    if not direct_answers:
        issues.append({"severity": "info", "message": "No 20-70 word answer paragraph immediately follows a question heading."})
    if not definitions:
        issues.append({"severity": "info", "message": "No concise definition paragraph detected."})
    if not lists and not tables:
        issues.append({"severity": "info", "message": "No snippet-friendly list or table detected."})

    return {
        "url": url or source,
        "score": score,
        "questions": questions[:50],
        "direct_answers": direct_answers[:50],
        "definitions": definitions[:50],
        "lists": lists[:50],
        "tables": tables[:50],
        "issues": issues,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan for direct answers, definitions, lists, and tables.")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = scan_answer_blocks(args.source, args.timeout)
    print(json.dumps(result, indent=2) if args.json else f"Score: {result['score']} Direct answers: {len(result['direct_answers'])}")


if __name__ == "__main__":
    main()
