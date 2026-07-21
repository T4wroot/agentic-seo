#!/usr/bin/env python3
"""Compare raw HTML against rendered DOM SEO elements when Playwright is available."""

from __future__ import annotations

import argparse
import json

from seo_common import fetch_url, load_html, parse_html


def summarize(html: str, url: str) -> dict:
    parsed = parse_html(html, url)
    return {
        "title": parsed["title"],
        "meta_description": parsed["meta_description"],
        "canonical": parsed["canonical"],
        "h1_count": len(parsed["headings"]["h1"]),
        "internal_link_count": len([l for l in parsed["links"] if url and l["href"].startswith(url.split("/", 3)[0] + "//" + url.split("/")[2])]) if url.startswith("http") else len(parsed["links"]),
        "schema_count": len(parsed["schema"]),
        "word_count": parsed["word_count"],
    }


def render_with_playwright(url: str, timeout_ms: int) -> tuple[str | None, str | None]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "playwright not installed"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            html = page.content()
            browser.close()
            return html, None
    except Exception as exc:  # noqa: BLE001 - CLI should report environment/browser errors
        return None, str(exc)


def audit(source: str, timeout: int = 15, render_timeout: int = 30000) -> dict:
    raw_html, final_url, fetched = load_html(source, timeout=timeout)
    raw = summarize(raw_html, final_url or source)
    rendered_html = None
    render_error = None
    if final_url.startswith("http"):
        rendered_html, render_error = render_with_playwright(final_url, render_timeout)
    else:
        render_error = "rendering requires an http(s) URL"
    rendered = summarize(rendered_html, final_url) if rendered_html else None
    diffs = []
    if rendered:
        for key in raw:
            if raw.get(key) != rendered.get(key):
                diffs.append({"field": key, "raw": raw.get(key), "rendered": rendered.get(key)})
    return {"url": final_url or source, "raw": raw, "rendered": rendered, "diffs": diffs, "render_error": render_error, "fetch_error": fetched.get("error")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare raw HTML and rendered DOM SEO signals")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--render-timeout", type=int, default=30000)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = audit(args.source, args.timeout, args.render_timeout)
    print(json.dumps(result, indent=2) if args.json else f"Diffs: {len(result['diffs'])}; render_error={result['render_error']}")


if __name__ == "__main__":
    main()
