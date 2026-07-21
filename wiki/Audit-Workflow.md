# Audit Workflow

The skill is LLM-first, but script-backed. The LLM should reason from direct page evidence and use scripts to verify facts, extract structured data, and avoid guesswork.

## Single Page Audit

```bash
python3 <SKILL_DIR>/scripts/fetch_page.py https://example.com --output /tmp/page.html
python3 <SKILL_DIR>/scripts/parse_html.py /tmp/page.html --url https://example.com --json
python3 <SKILL_DIR>/scripts/readability.py /tmp/page.html --json
python3 <SKILL_DIR>/scripts/pagespeed.py https://example.com --strategy mobile
python3 <SKILL_DIR>/scripts/security_headers.py https://example.com
python3 <SKILL_DIR>/scripts/social_meta.py https://example.com
```

Then synthesize findings into:

- `FULL-AUDIT-REPORT.md`
- `ACTION-PLAN.md`

## Full Website Audit

```bash
python3 <SKILL_DIR>/scripts/audit_runner.py https://example.com --output-dir audit-output
```

The runner coordinates baseline evidence collection and report generation.

## HTML Dashboard

```bash
python3 <SKILL_DIR>/scripts/generate_report.py https://example.com --output SEO-REPORT.html
```

Use this when the user wants a shareable browser report.

## GitHub Repository SEO

Use provider fallback mode unless a specific provider is required:

```bash
python3 <SKILL_DIR>/scripts/github_repo_audit.py --repo owner/repo --provider auto --json
python3 <SKILL_DIR>/scripts/github_readme_lint.py README.md --json
python3 <SKILL_DIR>/scripts/github_community_health.py --repo owner/repo --provider auto --json
python3 <SKILL_DIR>/scripts/github_seo_report.py --repo owner/repo --provider auto --markdown GITHUB-SEO-REPORT.md --action-plan GITHUB-ACTION-PLAN.md --json
```

Authentication options:

```bash
export GITHUB_TOKEN="..."
gh auth login -h github.com
```

## Confidence Labels

Every finding should use one of these confidence labels:

- `Confirmed`: directly observed in page/source/API evidence.
- `Likely`: supported by partial evidence, but missing one confirming source.
- `Hypothesis`: plausible, but blocked by environment, rate limit, or missing data.

## Failure Handling

If a script fails due network, DNS, permissions, or API limits:

- Report it as an environment limitation.
- Do not treat it as a confirmed site issue.
- Retry at most once.
- Continue with available evidence.

