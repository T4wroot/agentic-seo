#!/usr/bin/env python3
"""Suggest GitHub topics from repository metadata, README, and competitors."""

from __future__ import annotations

import argparse
import os
import re
from collections import Counter

from github_api import auth_context, fetch_json, get_token, resolve_repo
from seo_common import print_json_or_text


STOP_WORDS = {
    "the", "and", "for", "with", "from", "into", "this", "that", "your", "you", "are", "was", "were",
    "will", "would", "should", "could", "about", "using", "use", "used", "all", "any", "not", "can",
    "how", "why", "what", "when", "where", "which", "than", "then", "them", "they", "our", "their",
}

CANONICAL_TOPICS = {
    "search-engine-optimization": ["seo", "search engine optimization"],
    "technical-seo": ["technical seo", "crawlability", "indexability"],
    "github-seo": ["github seo", "repository seo", "repo seo"],
    "llm": ["llm", "large language model"],
    "generative-ai": ["generative ai", "ai search"],
    "python": ["python"],
    "cli": ["cli", "command line"],
    "automation": ["automation", "workflow"],
    "audit": ["audit", "auditing"],
    "schema-org": ["schema", "json-ld", "structured data"],
}


def _local_text(path: str) -> str:
    parts = []
    for rel in ("README.md", "pyproject.toml", "package.json"):
        fpath = os.path.join(path, rel)
        if os.path.exists(fpath):
            parts.append(open(fpath, "r", encoding="utf-8", errors="replace").read())
    return "\n".join(parts)


def _topicify(token: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", token.lower()).strip("-")[:50]


def suggest_topics(repo: str | None = None, path: str = ".", token: str = "", provider: str = "auto", competitors: list[str] | None = None, intent_terms: list[str] | None = None, limit: int = 20) -> dict:
    competitors = competitors or []
    intent_terms = intent_terms or []
    ctx = auth_context(token=token)
    limitations = []
    resolved_repo = ""
    metadata = {}
    try:
        resolved_repo = resolve_repo(repo, cwd=path)
        payload = fetch_json(f"/repos/{resolved_repo}", token=token, provider=provider)
        metadata = payload.get("data") or {}
    except Exception as exc:
        limitations.append(f"GitHub metadata unavailable: {exc}")

    current_topics = set(metadata.get("topics") or [])
    text = "\n".join([metadata.get("name") or "", metadata.get("description") or "", _local_text(path), " ".join(intent_terms)])
    lower = text.lower()
    candidates = Counter()
    evidence = {}

    for topic, phrases in CANONICAL_TOPICS.items():
        matched = [phrase for phrase in phrases if phrase in lower]
        if matched:
            score = 0
            for phrase in matched:
                phrase_hits = lower.count(phrase)
                phrase_words = len(phrase.split())
                score += phrase_hits * (20 + max(0, phrase_words - 1) * 12)
            candidates[topic] += score
            evidence.setdefault(topic, []).extend(matched)

    words = re.findall(r"[a-z][a-z0-9-]{2,}", lower)
    for word in words:
        if word in STOP_WORDS or len(word) > 35:
            continue
        candidates[_topicify(word)] += 1

    competitor_topics = Counter()
    for competitor in competitors:
        try:
            slug = resolve_repo(competitor)
            payload = fetch_json(f"/repos/{slug}", token=token, provider=provider)
            for topic in payload.get("data", {}).get("topics") or []:
                competitor_topics[topic] += 1
        except Exception as exc:
            limitations.append(f"Competitor topics unavailable for {competitor}: {exc}")
    for topic, count in competitor_topics.items():
        candidates[topic] += count * 5
        evidence.setdefault(topic, []).append("competitor topic")

    suggestions = []
    for topic, score in candidates.most_common():
        if topic in current_topics or topic in STOP_WORDS or len(topic) < 3:
            continue
        suggestions.append({"topic": topic, "score": score, "evidence": sorted(set(evidence.get(topic, [])))})
        if len(suggestions) >= limit:
            break

    issues = []
    if len(current_topics) < 3:
        issues.append({"severity": "warning", "type": "few_current_topics", "message": "Repository has fewer than three current topics"})
    if not suggestions:
        issues.append({"severity": "info", "type": "no_suggestions", "message": "No new topic suggestions were produced from available evidence"})

    return {
        "repo": resolved_repo or repo or "",
        "auth_context": ctx,
        "summary": {"current_topic_count": len(current_topics), "suggestions": len(suggestions), "competitors_used": len(competitors)},
        "current_topics": sorted(current_topics),
        "suggested_topics": suggestions,
        "competitor_topics": dict(competitor_topics.most_common()),
        "issues": issues,
        "limitations": limitations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest GitHub topics from repo metadata and search-intent terms")
    parser.add_argument("--repo", help="Repository slug or URL (defaults to local git origin)")
    parser.add_argument("--path", default=".", help="Local repository path")
    parser.add_argument("--token", help="GitHub token override")
    parser.add_argument("--provider", choices=["auto", "api", "gh"], default="auto")
    parser.add_argument("--competitor", action="append", default=[], help="Competitor owner/repo; can be repeated")
    parser.add_argument("--intent-term", action="append", default=[], help="Search-intent phrase; can be repeated")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = suggest_topics(args.repo, path=args.path, token=get_token(args.token), provider=args.provider, competitors=args.competitor, intent_terms=args.intent_term, limit=args.limit)
    lines = [
        f"Topic suggestions for {result['repo'] or args.path}",
        f"Current topics: {result['summary']['current_topic_count']}  Suggestions: {result['summary']['suggestions']}",
    ]
    lines.extend(f"- {row['topic']} (score {row['score']})" for row in result["suggested_topics"][:15])
    lines.extend(f"Limitation: {item}" for item in result["limitations"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
