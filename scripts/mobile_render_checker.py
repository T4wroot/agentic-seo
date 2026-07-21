#!/usr/bin/env python3
"""Check mobile rendering risks with static HTML plus optional Playwright signals."""

from __future__ import annotations

import argparse
import json
import re
import sys

try:
    from seo_common import load_html, parse_html
except ImportError:
    from scripts.seo_common import load_html, parse_html

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:  # pragma: no cover - optional dependency
    sync_playwright = None
    PlaywrightTimeout = TimeoutError


def _static_checks(source: str, timeout: int = 15) -> dict:
    html, final_url, fetched = load_html(source, timeout=timeout)
    parsed = parse_html(html, final_url)
    viewport = (parsed.get("meta") or {}).get("viewport", "")
    text = re.sub(r"\s+", " ", html or "")

    issues = []
    if "width=device-width" not in viewport.lower():
        issues.append({
            "severity": "critical",
            "finding": "Missing or incomplete viewport meta tag.",
            "fix": "Add `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">`.",
        })

    fixed_width_hits = re.findall(r"(?:width|min-width)\s*:\s*(\d{3,})px", text, flags=re.I)
    wide_values = [int(value) for value in fixed_width_hits if int(value) > 390]
    if wide_values:
        issues.append({
            "severity": "warning",
            "finding": f"Found {len(wide_values)} fixed-width CSS declarations wider than common mobile viewports.",
            "fix": "Replace fixed widths with responsive max-width, min(), clamp(), grid, or flex constraints.",
        })

    sticky_hits = len(re.findall(r"position\s*:\s*(fixed|sticky)", text, flags=re.I))
    if sticky_hits:
        issues.append({
            "severity": "info",
            "finding": f"Found {sticky_hits} fixed/sticky positioning declaration(s).",
            "fix": "Verify sticky headers, banners, and chat widgets do not cover mobile content or CTAs.",
        })

    return {
        "source": source,
        "url": final_url or source,
        "fetch": fetched,
        "viewport_meta": viewport,
        "fixed_width_values": wide_values[:25],
        "sticky_position_count": sticky_hits,
        "rendered": None,
        "issues": issues,
    }


def _rendered_checks(url: str, timeout_ms: int) -> dict:
    if sync_playwright is None:
        return {"available": False, "error": "playwright is not installed"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            metrics = page.evaluate(
                """() => {
                    const doc = document.documentElement;
                    const body = document.body;
                    const links = [...document.querySelectorAll('a,button,input,select,textarea')];
                    const smallTargets = links.map((el) => {
                        const r = el.getBoundingClientRect();
                        return {text: (el.innerText || el.value || el.ariaLabel || '').trim().slice(0, 80), width: r.width, height: r.height};
                    }).filter((r) => r.width > 0 && r.height > 0 && (r.width < 44 || r.height < 44)).slice(0, 20);
                    const clippedText = [...document.querySelectorAll('h1,h2,h3,p,a,button,li')]
                        .filter((el) => el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
                        .map((el) => ({tag: el.tagName.toLowerCase(), text: el.innerText.trim().slice(0, 120)}))
                        .slice(0, 20);
                    return {
                        viewportWidth: window.innerWidth,
                        scrollWidth: doc.scrollWidth,
                        horizontalScroll: doc.scrollWidth > window.innerWidth + 1,
                        bodyHeight: body ? body.scrollHeight : 0,
                        smallTargets,
                        clippedText
                    };
                }"""
            )
            browser.close()
            return {"available": True, **metrics}
    except PlaywrightTimeout:
        return {"available": True, "error": f"render timed out after {timeout_ms}ms"}
    except Exception as exc:  # pragma: no cover - browser/runtime dependent
        return {"available": True, "error": str(exc)}


def check_mobile_render(source: str, render: bool = False, timeout: int = 15) -> dict:
    report = _static_checks(source, timeout=timeout)
    is_url = bool(re.match(r"^https?://", source, re.I))
    if render and is_url:
        rendered = _rendered_checks(source, timeout * 1000)
        report["rendered"] = rendered
        if rendered.get("horizontalScroll"):
            report["issues"].append({
                "severity": "critical",
                "finding": "Rendered mobile page has horizontal scroll.",
                "fix": "Identify overflowing containers at 390px width and constrain media, tables, nav, and code blocks.",
            })
        if rendered.get("smallTargets"):
            report["issues"].append({
                "severity": "warning",
                "finding": f"{len(rendered['smallTargets'])} tap target(s) are smaller than 44px.",
                "fix": "Increase touch target size and spacing for mobile navigation and controls.",
            })
        if rendered.get("clippedText"):
            report["issues"].append({
                "severity": "warning",
                "finding": f"{len(rendered['clippedText'])} text element(s) appear clipped or overflowing.",
                "fix": "Allow wrapping, adjust line-height, or reduce container constraints on mobile.",
            })
    elif render and not is_url:
        report["rendered"] = {"available": False, "error": "render mode requires a URL"}

    report["summary"] = {
        "issues": len(report["issues"]),
        "critical": sum(1 for issue in report["issues"] if issue["severity"] == "critical"),
        "warning": sum(1 for issue in report["issues"] if issue["severity"] == "warning"),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check mobile rendering risks")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--render", action="store_true", help="Use Playwright for rendered mobile checks when source is a URL")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()

    report = check_mobile_render(args.source, render=args.render, timeout=args.timeout)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Mobile render issues: {report['summary']['issues']}")
        for issue in report["issues"]:
            print(f"- [{issue['severity']}] {issue['finding']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
