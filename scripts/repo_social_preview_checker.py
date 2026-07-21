#!/usr/bin/env python3
"""Check GitHub repository social-preview readiness signals."""

from __future__ import annotations

import argparse

from github_api import auth_context, fetch_json, get_token, resolve_repo
from seo_common import print_json_or_text


def check_social_preview(repo: str | None = None, path: str = ".", token: str = "", provider: str = "auto") -> dict:
    ctx = auth_context(token=token)
    limitations = []
    metadata = {}
    resolved_repo = ""
    try:
        resolved_repo = resolve_repo(repo, cwd=path)
        payload = fetch_json(f"/repos/{resolved_repo}", token=token, provider=provider)
        metadata = payload.get("data") or {}
    except Exception as exc:
        limitations.append(f"GitHub metadata unavailable: {exc}")

    description = metadata.get("description") or ""
    topics = metadata.get("topics") or []
    homepage = metadata.get("homepage") or ""
    owner = metadata.get("owner") or {}
    open_graph_image = metadata.get("open_graph_image_url") or owner.get("avatar_url") or ""
    issues = []
    if not metadata:
        issues.append({"severity": "info", "type": "metadata_unavailable", "message": "GitHub metadata could not be fetched; social preview image cannot be verified through REST fallback"})
    if metadata and not description:
        issues.append({"severity": "warning", "type": "missing_description", "message": "Repository description is empty"})
    if metadata and len(description) > 160:
        issues.append({"severity": "info", "type": "long_description", "message": "Repository description may truncate in social previews"})
    if metadata and len(topics) < 3:
        issues.append({"severity": "warning", "type": "few_topics", "message": "Repository has fewer than three topics"})
    if metadata and not homepage:
        issues.append({"severity": "info", "type": "missing_homepage", "message": "Repository homepage URL is empty"})
    if metadata and not open_graph_image:
        issues.append({"severity": "info", "type": "social_preview_unknown", "message": "Social preview image was not exposed by available GitHub API data"})

    score = 100
    score -= 30 if not metadata else 0
    score -= 20 if metadata and not description else 0
    score -= 15 if metadata and len(topics) < 3 else 0
    score -= 10 if metadata and not homepage else 0
    return {
        "repo": resolved_repo or repo or "",
        "auth_context": ctx,
        "summary": {
            "score": max(0, score),
            "description_present": bool(description),
            "topic_count": len(topics),
            "homepage_present": bool(homepage),
            "open_graph_image_detected": bool(open_graph_image),
        },
        "metadata": {
            "name": metadata.get("name"),
            "description": description,
            "homepage": homepage,
            "topics": topics,
            "open_graph_image_url": open_graph_image,
        },
        "issues": issues,
        "limitations": limitations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check GitHub repository social-preview readiness")
    parser.add_argument("--repo", help="Repository slug or URL (defaults to local git origin)")
    parser.add_argument("--path", default=".", help="Local repository path")
    parser.add_argument("--token", help="GitHub token override")
    parser.add_argument("--provider", choices=["auto", "api", "gh"], default="auto")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = check_social_preview(args.repo, path=args.path, token=get_token(args.token), provider=args.provider)
    lines = [
        f"Social preview check for {result['repo'] or args.path}",
        f"Score: {result['summary']['score']}  Topics: {result['summary']['topic_count']}  Description: {result['summary']['description_present']}",
    ]
    lines.extend(f"[{issue['severity']}] {issue['message']}" for issue in result["issues"])
    lines.extend(f"Limitation: {item}" for item in result["limitations"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
