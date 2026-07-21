# Release and Packaging

## Current Release

Current release: `v3.0.0`

https://github.com/Bhanunamikaze/Agentic-SEO-Skill/releases/tag/v3.0.0

Published assets:

- `Agentic-SEO-Skill-v3.0.0.zip`
- `Agentic-SEO-Skill-v3.0.0.tar.gz`

## Tag-Based Packaging

The package workflow runs for tags matching:

```text
v*
```

Release flow:

```bash
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

## Runtime Allowlist

Release packages include only:

- `SKILL.md`
- `scripts/`
- `resources/`

This keeps installed skills small and avoids shipping repository-only files.

## Excluded From Release Assets

These are intentionally not part of the installed skill bundle:

- `tests/`
- `.github/`
- README and governance files
- `pyproject.toml`
- local `tmp/` outputs
- generated audit reports
- caches and bytecode

## CI Checks

The CI workflow validates:

- Python script compilation
- Skill inventory drift
- Reference freshness markers

Reference freshness warnings are acceptable for stale but still valid references. Missing, invalid, or future-dated markers fail CI.

