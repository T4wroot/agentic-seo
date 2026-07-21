#!/usr/bin/env python3
"""Build a weekly GitHub SEO scorecard from local and API-backed checks."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from github_api import get_token, resolve_repo
from repo_docs_site_checker import check_docs_site
from repo_file_inventory import inventory_repository
from repo_release_seo import audit_release_seo
from repo_social_preview_checker import check_social_preview
from repo_topic_suggester import suggest_topics
from seo_common import print_json_or_text


def _score_from_inventory(result: dict) -> int:
    return int(result.get("summary", {}).get("score", 0))


def _score_from_release(result: dict) -> int:
    return int(result.get("summary", {}).get("score", 0))


def build_scorecard(repo: str | None = None, path: str = ".", token: str = "", provider: str = "auto", offline: bool = False) -> dict:
    limitations = []
    resolved_repo = ""
    try:
        resolved_repo = resolve_repo(repo, cwd=path)
    except Exception as exc:
        limitations.append(str(exc))

    effective_provider = "api" if offline else provider
    effective_token = "" if offline else token
    inventory = inventory_repository(path)
    release = audit_release_seo(resolved_repo or repo, path=path, token=effective_token, provider=effective_provider)
    docs = check_docs_site(resolved_repo or repo, path=path, token=effective_token, provider=effective_provider)
    social = check_social_preview(resolved_repo or repo, path=path, token=effective_token, provider=effective_provider)
    topics = suggest_topics(resolved_repo or repo, path=path, token=effective_token, provider=effective_provider)

    if offline:
        limitations.append("Offline mode requested; GitHub/API checks use local fallbacks where available.")

    category_scores = {
        "file_inventory": _score_from_inventory(inventory),
        "release_seo": _score_from_release(release),
        "docs_site": int(docs.get("summary", {}).get("score", 0)),
        "social_preview": int(social.get("summary", {}).get("score", 0)),
        "topics": max(0, 100 - max(0, 3 - topics.get("summary", {}).get("current_topic_count", 0)) * 20),
    }
    overall = round(sum(category_scores.values()) / len(category_scores))
    all_issues = []
    for category, result in (
        ("file_inventory", inventory),
        ("release_seo", release),
        ("docs_site", docs),
        ("social_preview", social),
        ("topics", topics),
    ):
        for issue in result.get("issues", []):
            row = dict(issue)
            row["category"] = category
            all_issues.append(row)
        limitations.extend(result.get("limitations", []))

    return {
        "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo": resolved_repo or repo or "",
        "summary": {"overall_score": overall, "issue_count": len(all_issues)},
        "category_scores": category_scores,
        "checks": {
            "file_inventory": inventory,
            "release_seo": release,
            "docs_site": docs,
            "social_preview": social,
            "topics": topics,
        },
        "top_issues": all_issues[:25],
        "limitations": sorted(set(limitations)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a weekly GitHub SEO scorecard")
    parser.add_argument("--repo", help="Repository slug or URL (defaults to local git origin)")
    parser.add_argument("--path", default=".", help="Local repository path")
    parser.add_argument("--token", help="GitHub token override")
    parser.add_argument("--provider", choices=["auto", "api", "gh"], default="auto")
    parser.add_argument("--offline", action="store_true", help="Avoid authenticated GitHub checks and use local fallbacks")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = build_scorecard(args.repo, path=args.path, token=get_token(args.token), provider=args.provider, offline=args.offline)
    lines = [
        f"GitHub weekly SEO scorecard for {result['repo'] or args.path}",
        f"Overall score: {result['summary']['overall_score']}  Issues: {result['summary']['issue_count']}",
    ]
    lines.extend(f"{name}: {score}" for name, score in result["category_scores"].items())
    lines.extend(f"Limitation: {item}" for item in result["limitations"][:10])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
