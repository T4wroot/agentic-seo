#!/usr/bin/env python3
"""Run local Lighthouse when available and normalize key audit output."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_CATEGORIES = ("performance", "seo", "accessibility", "best-practices")


def _is_url(value: str) -> bool:
    return urlparse(value).scheme in ("http", "https")


def _find_lighthouse_command() -> tuple[list[str] | None, str | None]:
    lighthouse = shutil.which("lighthouse")
    if lighthouse:
        return [lighthouse], None
    npx = shutil.which("npx")
    if npx:
        return [npx, "--no-install", "lighthouse"], None
    return None, "Lighthouse is not installed. Install it with npm install -g lighthouse, or add it to the project."


def _category_scores(lhr: dict) -> dict:
    scores = {}
    for key, category in lhr.get("categories", {}).items():
        raw_score = category.get("score")
        scores[key] = {
            "title": category.get("title", key),
            "score": round(raw_score * 100) if isinstance(raw_score, (int, float)) else None,
        }
    return scores


def _audit_summary(lhr: dict) -> dict:
    audit_ids = [
        "largest-contentful-paint",
        "total-blocking-time",
        "cumulative-layout-shift",
        "speed-index",
        "interactive",
        "server-response-time",
        "render-blocking-resources",
        "unused-javascript",
        "unused-css-rules",
        "uses-optimized-images",
        "uses-webp-images",
        "font-display",
        "third-party-summary",
    ]
    audits = {}
    for audit_id in audit_ids:
        audit = lhr.get("audits", {}).get(audit_id)
        if audit:
            audits[audit_id] = {
                "title": audit.get("title", audit_id),
                "score": audit.get("score"),
                "numeric_value": audit.get("numericValue"),
                "display": audit.get("displayValue"),
            }
    return audits


def parse_lighthouse_result(payload: dict, source: str, strategy: str) -> dict:
    lhr = payload.get("lighthouseResult", payload)
    return {
        "source": source,
        "final_url": lhr.get("finalDisplayedUrl") or lhr.get("finalUrl") or source,
        "strategy": strategy,
        "fetch_time": lhr.get("fetchTime"),
        "lighthouse_version": lhr.get("lighthouseVersion"),
        "environment": lhr.get("environment", {}),
        "categories": _category_scores(lhr),
        "audits": _audit_summary(lhr),
        "error": None,
    }


def run_lighthouse(
    source: str,
    strategy: str = "mobile",
    categories: tuple[str, ...] = DEFAULT_CATEGORIES,
    timeout: int = 120,
) -> dict:
    if not _is_url(source):
        path = Path(source)
        return {
            "source": source,
            "final_url": str(path),
            "strategy": strategy,
            "categories": {},
            "audits": {},
            "error": "Lighthouse requires an http(s) URL; local HTML can be checked with the static performance scripts.",
        }

    command, error = _find_lighthouse_command()
    if error:
        return {
            "source": source,
            "final_url": source,
            "strategy": strategy,
            "categories": {},
            "audits": {},
            "error": error,
        }

    form_factor = "desktop" if strategy == "desktop" else "mobile"
    args = [
        *command,
        source,
        "--quiet",
        "--output=json",
        "--output-path=stdout",
        f"--only-categories={','.join(categories)}",
        f"--emulated-form-factor={form_factor}",
        "--chrome-flags=--headless",
    ]
    try:
        completed = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {
            "source": source,
            "final_url": source,
            "strategy": strategy,
            "categories": {},
            "audits": {},
            "error": f"Lighthouse timed out after {timeout}s",
        }
    except OSError as exc:
        return {
            "source": source,
            "final_url": source,
            "strategy": strategy,
            "categories": {},
            "audits": {},
            "error": str(exc),
        }

    if completed.returncode != 0:
        return {
            "source": source,
            "final_url": source,
            "strategy": strategy,
            "categories": {},
            "audits": {},
            "error": (completed.stderr or completed.stdout or "Lighthouse failed").strip()[:1000],
        }

    try:
        return parse_lighthouse_result(json.loads(completed.stdout), source, strategy)
    except json.JSONDecodeError as exc:
        return {
            "source": source,
            "final_url": source,
            "strategy": strategy,
            "categories": {},
            "audits": {},
            "error": f"Could not parse Lighthouse JSON: {exc}",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Lighthouse locally when the optional CLI is available")
    parser.add_argument("source", help="HTTP(S) URL to audit")
    parser.add_argument("--strategy", choices=("mobile", "desktop"), default="mobile")
    parser.add_argument("--category", action="append", choices=DEFAULT_CATEGORIES, help="Lighthouse category to include")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()

    categories = tuple(args.category) if args.category else DEFAULT_CATEGORIES
    result = run_lighthouse(args.source, args.strategy, categories, args.timeout)
    if args.json:
        print(json.dumps(result, indent=2))
    elif result["error"]:
        print(f"Lighthouse unavailable: {result['error']}")
    else:
        scores = ", ".join(f"{key}={value['score']}" for key, value in result["categories"].items())
        print(f"Lighthouse {args.strategy}: {scores}")


if __name__ == "__main__":
    main()
