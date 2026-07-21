#!/usr/bin/env python3
"""Validate documented skill, agent, and script inventory counts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SKILL = ROOT / "SKILL.md"
WIKI_SCRIPT_INVENTORY = ROOT / "wiki" / "Script-Inventory.md"
SKILLS_DIR = ROOT / "resources" / "skills"
AGENTS_DIR = ROOT / "resources" / "agents"
SCRIPTS_DIR = ROOT / "scripts"


def list_files(directory: Path, pattern: str) -> list[Path]:
    return sorted(path for path in directory.glob(pattern) if path.is_file())


def documented_count(text: str, patterns: list[str]) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate README.md and SKILL.md inventory counts against files on disk."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable results.")
    args = parser.parse_args()

    readme_exists = README.exists()
    readme_text = README.read_text(encoding="utf-8") if readme_exists else ""
    wiki_inventory_exists = WIKI_SCRIPT_INVENTORY.exists()
    wiki_inventory_text = WIKI_SCRIPT_INVENTORY.read_text(encoding="utf-8") if wiki_inventory_exists else ""
    skill_text = SKILL.read_text(encoding="utf-8")

    skill_files = list_files(SKILLS_DIR, "*.md")
    agent_files = list_files(AGENTS_DIR, "*.md")
    python_scripts = [path for path in list_files(SCRIPTS_DIR, "*.py") if path.name != "__init__.py"]
    shell_scripts = list_files(SCRIPTS_DIR, "*.sh")
    all_scripts = sorted(python_scripts + shell_scripts)

    expected = {
        "skills": len(skill_files),
        "agents": len(agent_files),
        "scripts": len(all_scripts),
        "python_scripts": len(python_scripts),
        "shell_scripts": len(shell_scripts),
    }

    observed = {
        "readme_skills": documented_count(readme_text, [r"Specialized sub-skills:\s*`?(\d+)`?"]),
        "readme_agents": documented_count(readme_text, [r"Specialist agents:\s*`?(\d+)`?"]),
        "readme_scripts": documented_count(readme_text, [r"Scripts in `scripts/`:\s*`?(\d+)`?"]),
        "readme_python_scripts": documented_count(readme_text, [r"`?(\d+)`?\s+Python"]),
        "readme_shell_scripts": documented_count(readme_text, [r"`?(\d+)`?\s+shell"]),
        "skill_intro_scripts": documented_count(skill_text, [r"and\s+(\d+)\s+scripts"]),
    }

    errors: list[str] = []

    checks = {"skill_intro_scripts": "scripts"}
    if readme_exists:
        checks.update({
            "readme_skills": "skills",
            "readme_agents": "agents",
            "readme_scripts": "scripts",
            "readme_python_scripts": "python_scripts",
            "readme_shell_scripts": "shell_scripts",
        })
    for observed_key, expected_key in checks.items():
        if observed[observed_key] != expected[expected_key]:
            errors.append(
                f"{observed_key}={observed[observed_key]!r}, expected {expected[expected_key]}"
            )

    for path in skill_files:
        rel = path.relative_to(ROOT).as_posix()
        if rel not in skill_text:
            errors.append(f"SKILL.md does not reference {rel}")
        if readme_exists and rel not in readme_text:
            errors.append(f"README.md does not reference {rel}")

    if readme_exists:
        for path in all_scripts:
            name = path.name
            if name not in readme_text and name not in wiki_inventory_text:
                errors.append(f"script inventory docs do not list {name}")

    payload = {
        "expected": expected,
        "observed": observed,
        "readme_present": readme_exists,
        "wiki_inventory_present": wiki_inventory_exists,
        "skills": [path.name for path in skill_files],
        "agents": [path.name for path in agent_files],
        "scripts": [path.name for path in all_scripts],
        "errors": errors,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "Inventory: "
            f"{expected['skills']} skills, "
            f"{expected['agents']} agents, "
            f"{expected['scripts']} scripts "
            f"({expected['python_scripts']} Python + {expected['shell_scripts']} shell)"
        )
        if errors:
            print("Errors:")
            for error in errors:
                print(f"- {error}")
        else:
            print("OK: documented inventory matches files on disk.")
            if not readme_exists:
                print("Note: README.md not present; README inventory checks were skipped.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
