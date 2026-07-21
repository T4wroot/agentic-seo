# Troubleshooting

## PageSpeed Fails With a Rate Limit

Treat this as an environment limitation, not a confirmed site issue.

Recommended handling:

- Retry once.
- If it still fails, mark Core Web Vitals as `Hypothesis` or `Unknown`.
- Continue the audit with available page evidence.

## GitHub API Calls Fail

Use provider fallback:

```bash
python3 scripts/github_repo_audit.py --repo owner/repo --provider auto --json
```

Authenticate with either:

```bash
export GITHUB_TOKEN="..."
```

or:

```bash
gh auth login -h github.com
```

## Playwright or Screenshot Checks Fail

Install Chromium:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

If the environment does not support browsers, report visual findings as blocked instead of confirmed.

## Reference Freshness CI Fails

Run:

```bash
python3 scripts/reference_freshness.py resources/references --max-age-days 90
```

Fix missing, invalid, or future-dated markers.

Stale references are warnings unless `--fail-stale` is used.

## Installed Skill Inventory Fails

Run:

```bash
python3 scripts/validate_skill_inventory.py
```

The expected inventory is 16 skills, 10 agents, and 89 scripts.

## Noindex Pages Appear as SEO Problems

Noindex pages should not be treated the same as indexable pages for thin-content or duplicate-content findings. Findings against noindex pages should be skipped or clearly downgraded.

## Next.js Image Fill False Positives

Next.js `<Image fill>` outputs images with `data-nimg="fill"` and no fixed `width` or `height` attributes. These images are layout-constrained by CSS and should not be flagged as ordinary missing-dimension CLS risks.

