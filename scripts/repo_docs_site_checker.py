#!/usr/bin/env python3
"""Check repository homepage/docs URLs and install CTA paths."""

from __future__ import annotations

import argparse
import os
import re
from urllib.parse import urlparse

from github_api import auth_context, fetch_json, get_token, resolve_repo
from seo_common import fetch_url, print_json_or_text


URL_RE = re.compile(r"https?://[^\s)\]\"'>]+")


def _readme_urls(path: str) -> list[str]:
    readme = os.path.join(path, "README.md")
    if not os.path.exists(readme):
        return []
    text = open(readme, "r", encoding="utf-8", errors="replace").read()
    return sorted(set(URL_RE.findall(text)))


def _readme_install_cta(path: str) -> dict:
    readme = os.path.join(path, "README.md")
    if not os.path.exists(readme):
        return {"present": False, "install_mentions": 0, "quickstart_mentions": 0, "code_blocks": 0}
    text = open(readme, "r", encoding="utf-8", errors="replace").read()
    lower = text.lower()
    return {
        "present": True,
        "install_mentions": lower.count("install"),
        "quickstart_mentions": lower.count("quickstart"),
        "code_blocks": text.count("```"),
    }


def _check_url(url: str, timeout: int) -> dict:
    fetched = fetch_url(url, timeout=timeout, max_bytes=1_000_000)
    return {
        "url": url,
        "status": fetched.get("status"),
        "final_url": fetched.get("url"),
        "redirect_chain": fetched.get("redirect_chain", []),
        "error": fetched.get("error"),
        "title_present": "<title" in (fetched.get("text") or "").lower(),
        "meta_description_present": 'name="description"' in (fetched.get("text") or "").lower() or "name='description'" in (fetched.get("text") or "").lower(),
    }


def check_docs_site(repo: str | None = None, path: str = ".", token: str = "", provider: str = "auto", homepage: str | None = None, timeout: int = 15, max_urls: int = 10) -> dict:
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

    candidate_urls = []
    if homepage:
        candidate_urls.append(homepage)
    if metadata.get("homepage"):
        candidate_urls.append(metadata["homepage"])
    if resolved_repo:
        owner, name = resolved_repo.split("/", 1)
        candidate_urls.extend([f"https://{owner}.github.io/{name}/", f"https://github.com/{resolved_repo}#readme"])
    for url in _readme_urls(path):
        host = urlparse(url).netloc.lower()
        if any(token in host for token in ("github.io", "readthedocs.io", "docs.", "pages.dev", "vercel.app", "netlify.app")):
            candidate_urls.append(url)

    deduped = []
    seen = set()
    for url in candidate_urls:
        cleaned = url.rstrip(".,")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduped.append(cleaned)

    checks = [_check_url(url, timeout=timeout) for url in deduped[:max_urls]]
    readme_cta = _readme_install_cta(path)
    issues = []
    live_docs = [row for row in checks if row.get("status") and row["status"] < 400]
    if not checks:
        issues.append({"severity": "warning", "type": "no_docs_url", "message": "No homepage/docs URL was discovered"})
    elif not live_docs:
        issues.append({"severity": "warning", "type": "docs_unavailable", "message": "No checked docs/homepage URL returned a live status"})
    if readme_cta["present"] and readme_cta["install_mentions"] == 0:
        issues.append({"severity": "warning", "type": "missing_install_cta", "message": "README does not clearly mention installation"})
    if any(row.get("status") and row["status"] >= 400 for row in checks):
        issues.append({"severity": "warning", "type": "broken_docs_url", "message": "At least one docs/homepage URL returned 4xx/5xx"})

    score = 100 - 20 * len([i for i in issues if i["severity"] == "warning"])
    return {
        "repo": resolved_repo or repo or "",
        "auth_context": ctx,
        "metadata": {"homepage": metadata.get("homepage"), "description": metadata.get("description")},
        "summary": {"score": max(0, score), "urls_checked": len(checks), "live_urls": len(live_docs)},
        "readme_install_cta": readme_cta,
        "url_checks": checks,
        "issues": issues,
        "limitations": limitations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check repository docs/homepage URLs and install CTA")
    parser.add_argument("--repo", help="Repository slug or URL (defaults to local git origin)")
    parser.add_argument("--path", default=".", help="Local repository path")
    parser.add_argument("--homepage", help="Explicit homepage/docs URL")
    parser.add_argument("--token", help="GitHub token override")
    parser.add_argument("--provider", choices=["auto", "api", "gh"], default="auto")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = check_docs_site(args.repo, path=args.path, token=get_token(args.token), provider=args.provider, homepage=args.homepage, timeout=args.timeout)
    lines = [
        f"Docs site check for {result['repo'] or args.path}",
        f"Score: {result['summary']['score']}  URLs checked: {result['summary']['urls_checked']}  Live: {result['summary']['live_urls']}",
    ]
    lines.extend(f"[{issue['severity']}] {issue['message']}" for issue in result["issues"])
    lines.extend(f"Limitation: {item}" for item in result["limitations"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
