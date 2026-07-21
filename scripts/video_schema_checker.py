#!/usr/bin/env python3
"""Check VideoObject JSON-LD for video rich-result readiness."""

from __future__ import annotations

import argparse
import re
from typing import Any

from schema_required_props import extract_schema_documents, find_schema_nodes
from seo_common import issue, print_json_or_text


ISO_DURATION_RE = re.compile(r"^P(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def check_video_schema(documents: list[Any]) -> dict[str, Any]:
    rows = []
    issues = []
    videos = find_schema_nodes(documents, "VideoObject")
    for row in videos:
        node = row["node"]
        row_issues = []
        for prop in ("name", "description", "thumbnailUrl", "uploadDate"):
            if not node.get(prop):
                row_issues.append(issue("error", f"VideoObject is missing {prop}", evidence=row["path"]))
        if node.get("uploadDate") and not DATE_RE.match(str(node["uploadDate"])):
            row_issues.append(issue("warning", "uploadDate should be ISO-like YYYY-MM-DD or datetime", evidence=row["path"]))
        if node.get("duration") and not ISO_DURATION_RE.match(str(node["duration"])):
            row_issues.append(issue("warning", "duration should be ISO 8601, e.g. PT2M30S", evidence=row["path"]))
        if not node.get("contentUrl") and not node.get("embedUrl"):
            row_issues.append(issue("error", "VideoObject needs contentUrl or embedUrl", evidence=row["path"]))
        if not node.get("publisher"):
            row_issues.append(issue("warning", "VideoObject is missing publisher", evidence=row["path"]))
        if not node.get("transcript") and not node.get("caption"):
            row_issues.append(issue("info", "VideoObject is missing transcript/caption signal", evidence=row["path"]))
        clips = [part for part in as_list(node.get("hasPart")) if isinstance(part, dict) and part.get("@type") == "Clip"]
        if clips:
            for index, clip in enumerate(clips):
                for prop in ("name", "startOffset", "url"):
                    if clip.get(prop) in (None, ""):
                        row_issues.append(issue("warning", f"Clip is missing {prop}", evidence=f"{row['path']}.hasPart[{index}]"))
        actions = [action for action in as_list(node.get("potentialAction")) if isinstance(action, dict)]
        if actions and not any(action.get("@type") == "SeekToAction" for action in actions):
            row_issues.append(issue("info", "potentialAction exists but no SeekToAction found", evidence=row["path"]))
        rows.append({"path": row["path"], "issues": row_issues})
        issues.extend(row_issues)
    return {"videos": len(videos), "rows": rows, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check VideoObject JSON-LD")
    parser.add_argument("source", help="URL, HTML file, or JSON-LD file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    documents, meta = extract_schema_documents(args.source, timeout=args.timeout)
    result = check_video_schema(documents)
    result.update({"source": args.source, "final_url": meta["final_url"]})
    lines = [f"Video schema check for {args.source}", f"Videos: {result['videos']}  Issues: {len(result['issues'])}"]
    lines.extend(f"[{item['severity']}] {item['message']} {item.get('evidence') or ''}" for item in result["issues"][:30])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
