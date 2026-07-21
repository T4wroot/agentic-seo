#!/usr/bin/env python3
"""Audit GitHub release cadence and release-note SEO quality."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from datetime import datetime, timezone

from github_api import GitHubAPIError, auth_context, fetch_json, get_token, resolve_repo
from seo_common import print_json_or_text


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _local_tags(cwd: str, limit: int = 20) -> list[dict]:
    try:
        output = subprocess.check_output(
            ["git", "for-each-ref", "--sort=-creatordate", "--format=%(refname:short)%09%(creatordate:iso8601)", f"--count={limit}", "refs/tags"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return []
    rows = []
    for line in output.splitlines():
        if not line.strip():
            continue
        name, _, date = line.partition("\t")
        rows.append({"tag_name": name, "name": name, "published_at": date, "body": "", "source": "git_tag"})
    return rows


def _load_changelog(cwd: str) -> dict:
    path = os.path.join(cwd, "CHANGELOG.md")
    if not os.path.exists(path):
        return {"present": False, "bytes": 0, "release_headings": 0}
    text = open(path, "r", encoding="utf-8", errors="replace").read()
    return {"present": True, "bytes": len(text.encode("utf-8")), "release_headings": len(re.findall(r"^##\s+", text, flags=re.M))}


def _release_quality(release: dict, keywords: list[str]) -> dict:
    title = release.get("name") or release.get("tag_name") or ""
    body = release.get("body") or ""
    text = f"{title}\n{body}".lower()
    matched = [kw for kw in keywords if kw.lower() in text]
    return {
        "tag": release.get("tag_name") or "",
        "title": title,
        "published_at": release.get("published_at") or release.get("created_at") or "",
        "body_length": len(body),
        "has_summary": len(body.strip()) >= 120,
        "has_bullets": bool(re.search(r"^\s*[-*]\s+", body, flags=re.M)),
        "keyword_matches": matched,
        "draft": bool(release.get("draft")),
        "prerelease": bool(release.get("prerelease")),
        "source": release.get("source", "github_release"),
    }


def audit_release_seo(repo: str | None = None, path: str = ".", token: str = "", provider: str = "auto", keywords: list[str] | None = None, limit: int = 20) -> dict:
    keywords = keywords or []
    ctx = auth_context(token=token)
    limitations = []
    releases = []
    resolved_repo = ""
    try:
        resolved_repo = resolve_repo(repo, cwd=path)
        payload = fetch_json(f"/repos/{resolved_repo}/releases", token=token, params={"per_page": min(limit, 100)}, provider=provider)
        releases = payload.get("data") or []
    except GitHubAPIError as exc:
        limitations.append(f"GitHub releases unavailable: {exc}")
    except Exception as exc:
        limitations.append(f"GitHub releases unavailable: {exc}")

    if not releases:
        releases = _local_tags(path, limit=limit)
        if releases:
            limitations.append("Using local git tags because GitHub releases were unavailable.")

    rows = [_release_quality(r, keywords) for r in releases[:limit]]
    dates = [dt for dt in (_parse_date(r["published_at"]) for r in rows) if dt]
    newest_days = None
    if dates:
        newest_days = (datetime.now(timezone.utc) - max(dates)).days
    with_notes = sum(1 for r in rows if r["has_summary"])
    with_keywords = sum(1 for r in rows if r["keyword_matches"])
    changelog = _load_changelog(path)

    issues = []
    if not rows:
        issues.append({"severity": "warning", "type": "no_releases", "message": "No GitHub releases or local tags were found"})
    if newest_days is not None and newest_days > 180:
        issues.append({"severity": "warning", "type": "stale_releases", "message": "Latest release/tag is older than 180 days", "days": newest_days})
    if rows and with_notes / len(rows) < 0.5:
        issues.append({"severity": "info", "type": "thin_release_notes", "message": "Most releases have short release notes"})
    if keywords and rows and with_keywords == 0:
        issues.append({"severity": "info", "type": "keyword_alignment", "message": "Release notes do not mention target keywords"})
    if not changelog["present"]:
        issues.append({"severity": "warning", "type": "missing_changelog", "message": "CHANGELOG.md is missing"})

    score = 100
    score -= 20 if not rows else 0
    score -= 15 if newest_days and newest_days > 180 else 0
    score -= 10 if rows and with_notes / len(rows) < 0.5 else 0
    score -= 10 if not changelog["present"] else 0
    return {
        "repo": resolved_repo or repo or "",
        "auth_context": ctx,
        "summary": {
            "score": max(0, score),
            "releases_analyzed": len(rows),
            "latest_release_age_days": newest_days,
            "release_notes_with_summary": with_notes,
            "release_notes_with_keywords": with_keywords,
        },
        "changelog": changelog,
        "releases": rows,
        "issues": issues,
        "limitations": limitations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit GitHub release cadence and release-note SEO")
    parser.add_argument("--repo", help="Repository slug or URL (defaults to local git origin)")
    parser.add_argument("--path", default=".", help="Local repository path")
    parser.add_argument("--token", help="GitHub token override")
    parser.add_argument("--provider", choices=["auto", "api", "gh"], default="auto")
    parser.add_argument("--keyword", action="append", default=[], help="Target keyword to look for in release notes")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = audit_release_seo(args.repo, path=args.path, token=get_token(args.token), provider=args.provider, keywords=args.keyword, limit=args.limit)
    lines = [
        f"Release SEO audit for {result['repo'] or args.path}",
        f"Score: {result['summary']['score']}  Releases: {result['summary']['releases_analyzed']}  Latest age days: {result['summary']['latest_release_age_days']}",
    ]
    lines.extend(f"[{issue['severity']}] {issue['message']}" for issue in result["issues"])
    lines.extend(f"Limitation: {item}" for item in result["limitations"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
