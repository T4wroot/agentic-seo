#!/usr/bin/env python3
"""Inventory repository SEO, docs, demo, and governance files."""

from __future__ import annotations

import argparse
from pathlib import Path

from seo_common import print_json_or_text


CHECKS = {
    "core": ["README.md", "LICENSE", "CHANGELOG.md"],
    "docs": ["docs", "examples", "demo", "site"],
    "governance": ["CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "SUPPORT.md", "CITATION.cff"],
    "github": [".github/workflows", ".github/ISSUE_TEMPLATE", ".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", ".github/CODEOWNERS", ".github/dependabot.yml"],
    "package": ["pyproject.toml", "package.json", "requirements.txt", "setup.py"],
}


def path_exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def inventory_repository(path: str = ".") -> dict:
    root = Path(path).resolve()
    sections = {}
    missing = []
    present = []
    for section, items in CHECKS.items():
        rows = []
        for rel in items:
            exists = path_exists(root, rel)
            row = {"path": rel, "present": exists, "type": "directory" if (root / rel).is_dir() else "file"}
            rows.append(row)
            (present if exists else missing).append(rel)
        sections[section] = rows

    readme = root / "README.md"
    readme_stats = {"present": readme.exists(), "bytes": 0, "headings": 0, "install_mentions": 0, "demo_mentions": 0}
    if readme.exists():
        text = readme.read_text(encoding="utf-8", errors="replace")
        readme_stats.update(
            {
                "bytes": len(text.encode("utf-8")),
                "headings": sum(1 for line in text.splitlines() if line.startswith("#")),
                "install_mentions": text.lower().count("install"),
                "demo_mentions": text.lower().count("demo"),
            }
        )

    issues = []
    for rel in ("README.md", "LICENSE"):
        if rel in missing:
            issues.append({"severity": "error", "type": "missing_required_file", "path": rel, "message": f"{rel} is missing"})
    for rel in ("CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md"):
        if rel in missing:
            issues.append({"severity": "warning", "type": "missing_trust_file", "path": rel, "message": f"{rel} improves repository trust and SEO"})
    if readme_stats["present"] and readme_stats["install_mentions"] == 0:
        issues.append({"severity": "warning", "type": "readme_install_cta", "path": "README.md", "message": "README has no obvious install call-to-action"})

    score = max(0, round(100 * len(present) / max(1, len(present) + len(missing))) - len([i for i in issues if i["severity"] == "warning"]) * 2)
    return {
        "path": str(root),
        "summary": {"present": len(present), "missing": len(missing), "score": score},
        "sections": sections,
        "readme": readme_stats,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory repository SEO and trust files")
    parser.add_argument("--path", default=".", help="Repository path (default: current directory)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = inventory_repository(args.path)
    lines = [
        f"Repository file inventory for {result['path']}",
        f"Score: {result['summary']['score']}  Present: {result['summary']['present']}  Missing: {result['summary']['missing']}",
    ]
    lines.extend(f"[{issue['severity']}] {issue['message']}" for issue in result["issues"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
