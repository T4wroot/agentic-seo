"""
Lightweight .env loader for Agentic-SEO scripts.

Loads KEY=VALUE pairs from `.env` files into ``os.environ`` so scripts can
read secrets (API keys, credential paths) without forcing the user to paste
them on the CLI.

Search order (first hit per key wins, real shell env always wins):
  1. The process environment (already exported by the user).
  2. ``.env`` in the current working directory (where the user invoked the script).
  3. ``.env`` in the SKILL_DIR root (the parent of ``scripts/``).
  4. ``$HOME/.agentic-seo/.env`` (cross-project default).

Usage:
    from env_loader import get_env, load_env
    load_env()  # idempotent; safe to call from every script
    api_key = get_env("PAGESPEED_API_KEY")

No third-party dependencies — uses only the standard library.
"""

from __future__ import annotations

import os
from pathlib import Path

_LOADED = False
_LOADED_FROM: list[str] = []


def _candidate_paths() -> list[Path]:
    paths: list[Path] = []
    try:
        paths.append(Path.cwd() / ".env")
    except OSError:
        pass

    # SKILL_DIR is the parent of the scripts/ directory containing this file.
    here = Path(__file__).resolve().parent
    paths.append(here.parent / ".env")

    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if home:
        paths.append(Path(home) / ".agentic-seo" / ".env")

    # Deduplicate while preserving order.
    seen = set()
    unique: list[Path] = []
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def _parse_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export "):].lstrip()
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    if not key:
        return None
    value = value.strip()
    if (len(value) >= 2) and (
        (value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")
    ):
        value = value[1:-1]
    return key, value


def _load_file(path: Path) -> int:
    """Load a single .env file. Does not overwrite existing env vars."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    count = 0
    for raw in text.splitlines():
        parsed = _parse_line(raw)
        if not parsed:
            continue
        key, value = parsed
        if key in os.environ:
            continue
        os.environ[key] = value
        count += 1
    return count


def load_env(force: bool = False) -> list[str]:
    """
    Load .env files into ``os.environ``. Idempotent unless ``force=True``.

    Returns the list of file paths that were actually read.
    """
    global _LOADED, _LOADED_FROM
    if _LOADED and not force:
        return list(_LOADED_FROM)

    loaded_from: list[str] = []
    for candidate in _candidate_paths():
        if candidate.is_file() and _load_file(candidate) > 0:
            loaded_from.append(str(candidate))

    _LOADED = True
    _LOADED_FROM = loaded_from
    return list(loaded_from)


def get_env(*names: str, default: str = "") -> str:
    """
    Return the first non-empty value among the given env var names.

    Triggers ``load_env()`` on first call so scripts can use this without
    explicit setup.
    """
    load_env()
    for name in names:
        value = os.environ.get(name, "")
        if value and value.strip():
            return value.strip()
    return default


__all__ = ["load_env", "get_env"]
