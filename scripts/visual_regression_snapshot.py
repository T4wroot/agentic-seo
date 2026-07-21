#!/usr/bin/env python3
"""Create or compare visual regression snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:  # pragma: no cover - optional dependency
    sync_playwright = None
    PlaywrightTimeout = TimeoutError


VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
}


def file_fingerprint(path: Path) -> dict:
    data = path.read_bytes()
    return {
        "path": str(path),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def compare_files(baseline: Path, current: Path) -> dict:
    before = file_fingerprint(baseline)
    after = file_fingerprint(current)
    return {
        "baseline": before,
        "current": after,
        "changed": before["sha256"] != after["sha256"],
        "byte_delta": after["bytes"] - before["bytes"],
        "pixel_diff": None,
        "note": "Install Pillow to add pixel-level diff metrics." if not _pillow_available() else "",
    }


def _pillow_available() -> bool:
    try:
        import PIL.Image  # noqa: F401
        return True
    except ImportError:
        return False


def compare_pixels(baseline: Path, current: Path) -> dict:
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return compare_files(baseline, current)

    try:
        before = Image.open(baseline).convert("RGBA")
        after = Image.open(current).convert("RGBA")
    except Exception as exc:
        report = compare_files(baseline, current)
        report["note"] = f"Pixel diff unavailable: {exc}"
        return report
    report = compare_files(baseline, current)
    if before.size != after.size:
        report["pixel_diff"] = {
            "same_dimensions": False,
            "baseline_size": before.size,
            "current_size": after.size,
            "changed_pixels": None,
            "changed_ratio": None,
        }
        return report

    diff = ImageChops.difference(before, after)
    bbox = diff.getbbox()
    changed_pixels = 0
    if bbox:
        changed_pixels = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0, 0))
    total = before.size[0] * before.size[1]
    report["pixel_diff"] = {
        "same_dimensions": True,
        "baseline_size": before.size,
        "current_size": after.size,
        "changed_pixels": changed_pixels,
        "changed_ratio": round(changed_pixels / total, 6) if total else 0,
        "bounding_box": bbox,
    }
    return report


def capture_url(url: str, output_dir: Path, viewport: str, timeout_ms: int, full_page: bool) -> dict:
    if sync_playwright is None:
        return {"success": False, "error": "playwright is not installed"}
    if viewport not in VIEWPORTS:
        return {"success": False, "error": f"unknown viewport: {viewport}"}

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{viewport}.png"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport=VIEWPORTS[viewport])
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.screenshot(path=str(output), full_page=full_page)
            browser.close()
        return {"success": True, "url": url, "viewport": viewport, "output": str(output), **file_fingerprint(output)}
    except PlaywrightTimeout:
        return {"success": False, "url": url, "viewport": viewport, "error": f"render timed out after {timeout_ms}ms"}
    except Exception as exc:  # pragma: no cover - browser/runtime dependent
        return {"success": False, "url": url, "viewport": viewport, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or compare visual regression snapshots")
    parser.add_argument("--url", help="URL to capture")
    parser.add_argument("--output-dir", default="screenshots/visual-regression")
    parser.add_argument("--viewport", choices=VIEWPORTS.keys(), default="desktop")
    parser.add_argument("--all", action="store_true", help="Capture all viewport presets")
    parser.add_argument("--full-page", action="store_true")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    parser.add_argument("--baseline", help="Baseline image path for comparison")
    parser.add_argument("--current", help="Current image path for comparison")
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()

    if args.baseline and args.current:
        report = compare_pixels(Path(args.baseline), Path(args.current))
    elif args.url:
        viewports = VIEWPORTS.keys() if args.all else [args.viewport]
        captures = [
            capture_url(args.url, Path(args.output_dir), viewport, args.timeout * 1000, args.full_page)
            for viewport in viewports
        ]
        report = {"captures": captures, "success": all(item.get("success") for item in captures)}
    else:
        parser.error("provide either --url or --baseline plus --current")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
