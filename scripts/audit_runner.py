#!/usr/bin/env python3
"""
Run the bundled SEO audit checks and write machine-readable plus report artifacts.

This script reuses generate_report.py's collection, scoring, HTML, and Markdown
renderers so there is one reporting contract and one scoring config.

Usage:
    python audit_runner.py https://example.com
    python audit_runner.py https://example.com --json audit.json --html SEO-REPORT.html
"""

import argparse
import json
import os
from urllib.parse import urlparse

from generate_report import (
    calculate_overall_score,
    collect_data,
    generate_html,
    load_scoring_config,
    render_action_plan,
    render_markdown_report,
    write_text_output,
)


def default_html_path(url: str) -> str:
    domain = urlparse(url).netloc.replace(".", "_")
    return f"seo-report-{domain}.html"


def write_json(path: str, payload: dict) -> str:
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return os.path.abspath(path)


def main():
    parser = argparse.ArgumentParser(description="Run SEO audit and write report artifacts")
    parser.add_argument("url", help="Website URL to audit")
    parser.add_argument("--json", dest="json_output", default="audit-results.json",
                        help="JSON output path (default: audit-results.json)")
    parser.add_argument("--html", default="", help="HTML report output path")
    parser.add_argument("--markdown", default="FULL-AUDIT-REPORT.md",
                        help="Markdown audit output path (default: FULL-AUDIT-REPORT.md)")
    parser.add_argument("--action-plan", default="ACTION-PLAN.md",
                        help="Markdown action-plan output path (default: ACTION-PLAN.md)")
    parser.add_argument("--no-html", action="store_true", help="Do not write the HTML dashboard")
    parser.add_argument("--no-json", action="store_true", help="Do not write JSON results")
    parser.add_argument("--no-markdown", action="store_true", help="Do not write markdown/action-plan artifacts")
    args = parser.parse_args()

    scoring_config = load_scoring_config()
    data = collect_data(args.url)
    scores = calculate_overall_score(data, scoring_config=scoring_config)
    payload = {
        "url": args.url,
        "scores": scores,
        "data": data,
    }

    written = []
    if not args.no_json:
        written.append(("JSON results", write_json(args.json_output, payload)))
    if not args.no_html:
        written.append(("HTML report", write_text_output(args.html or default_html_path(args.url), generate_html(data, scores))))
    if not args.no_markdown:
        written.append(("Full audit report", write_text_output(args.markdown, render_markdown_report(data, scores, scoring_config))))
        written.append(("Action plan", write_text_output(args.action_plan, render_action_plan(data, scores))))

    print("\nAudit artifacts:")
    for label, path in written:
        print(f"   {label}: {path}")
    print(f"   Overall Score: {scores['overall']}/100")


if __name__ == "__main__":
    main()
