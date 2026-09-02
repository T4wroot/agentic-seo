# GitHub SEO Report

- Repository: `T4wroot/agentic-seo`
- Generated (UTC): `2026-09-02T19:26:26+00:00`
- Provider mode: `auto`
- Overall score: `27.67`
- Verified findings: `21` (raw: `34`, dropped: `0`)

## Score Components

| Component | Score |
|-----------|-------|
| repo_audit | 0 |
| readme_lint | 83 |
| community_health | 0 |

## Script Status

| Script | Status |
|--------|--------|
| repo_audit | ok |
| readme_lint | ok |
| community_health | ok |
| traffic_archiver | ok |
| search_benchmark | ok |
| competitor_research | ok |

## Query Discovery

- Mode: `auto-derived`
- Source: `repo slug + metadata + title analysis`
- Queries: `agentic seo; agentic seo aeo ai agents; aeo; ai agents; ai search; geo`

## Limitations

- repo_audit: No GitHub token found. Using authenticated gh CLI session as fallback.
- search_benchmark: no explicit query supplied; using auto-derived repo-specific benchmark queries.
- community_health: No GitHub token provided. Using authenticated gh CLI fallback for remote profile checks.
- traffic_archiver: No GitHub token found. Using authenticated gh CLI fallback for traffic endpoints.
- search_benchmark: No GitHub token found. Using authenticated gh CLI fallback for search.
- competitor_research: No GitHub token found. Using authenticated gh CLI fallback for competitor research.

## Prioritized Findings

| Severity | Source | Finding | Evidence | Fix |
|----------|--------|---------|----------|-----|
| Critical | repo_audit, community_health | Missing required repository file: LICENSE. | Local file check indicates `LICENSE` is absent. | Add `LICENSE` to restore baseline project trust and discoverability. |
| Warning | repo_audit | Community health score is below recommended baseline. | GitHub community health is 28%. | Complete missing governance files and contribution docs to raise score. |
| Warning | repo_audit, community_health | Missing community profile component: code_of_conduct. | GitHub community profile `files.code_of_conduct` is missing. | Add the missing `code_of_conduct` file/template in repository root or `.github/`. |
| Warning | repo_audit, community_health | Missing community profile component: contributing. | GitHub community profile `files.contributing` is missing. | Add the missing `contributing` file/template in repository root or `.github/`. |
| Warning | repo_audit, community_health | Missing community profile component: issue_template. | GitHub community profile `files.issue_template` is missing. | Add the missing `issue_template` file/template in repository root or `.github/`. |
| Warning | repo_audit, community_health | Missing community profile component: pull_request_template. | GitHub community profile `files.pull_request_template` is missing. | Add the missing `pull_request_template` file/template in repository root or `.github/`. |
| Warning | repo_audit, community_health | Missing community profile component: license. | GitHub community profile `files.license` is missing. | Add the missing `license` file/template in repository root or `.github/`. |
| Warning | repo_audit, community_health | Missing recommended trust artifact: CONTRIBUTING.md. | Local file check indicates `CONTRIBUTING.md` is absent. | Add `CONTRIBUTING.md` to improve contribution readiness and credibility signals. |
| Warning | repo_audit, community_health | Missing recommended trust artifact: CODE_OF_CONDUCT.md. | Local file check indicates `CODE_OF_CONDUCT.md` is absent. | Add `CODE_OF_CONDUCT.md` to improve contribution readiness and credibility signals. |
| Warning | repo_audit, community_health | Missing recommended trust artifact: SECURITY.md. | Local file check indicates `SECURITY.md` is absent. | Add `SECURITY.md` to improve contribution readiness and credibility signals. |
| Warning | repo_audit, community_health | Missing recommended trust artifact: .github/ISSUE_TEMPLATE. | Local file check indicates `.github/ISSUE_TEMPLATE` is absent. | Add `.github/ISSUE_TEMPLATE` to improve contribution readiness and credibility signals. |
| Warning | repo_audit, community_health | Missing recommended trust artifact: CITATION.cff. | Local file check indicates `CITATION.cff` is absent. | Add `CITATION.cff` to improve contribution readiness and credibility signals. |
| Warning | readme_lint | README should contain exactly one H1 heading. | Detected H1 count: 38. | Keep a single H1 title and move other top-level sections to H2. |
| Warning | readme_lint | Heading hierarchy has level jumps. | Detected 3 jump(s) where heading level skips intermediary levels. | Normalize heading flow (H1 -> H2 -> H3) without skipping levels. |
| Warning | community_health | GitHub community profile health is below baseline target. | health_percentage=28 | Add missing governance artifacts until health percentage reaches >=85. |
| Warning | competitor_research | High-frequency competitor topics are missing from target repo. | Missing topic examples: claude-code, ai, marketing-automation, open-source, claude-code-skills | Add relevant missing topics (without exceeding 20 total) based on actual repository scope. |
| Info | repo_audit | Repository title can be better aligned to search intent keywords. | Suggested slug: `agentic-seo-aeo-ai-agents` / Suggested title: `Agentic SEO AEO AI Agents` | Consider renaming repository slug and updating description/topics to reflect the suggested intent keywords. |
| Info | competitor_research | Target repository description is shorter than competitor baseline. | Target words: 23, competitor average: 25.33 | Expand description with intent terms, scope, and supported environments. |
| Info | competitor_research | Competitors frequently include `install` sections. | 6 competitor repos include this pattern. | Ensure README has a clear `install` section near the top-level navigation flow. |
| Info | competitor_research | Competitors frequently include `usage/examples` sections. | 5 competitor repos include this pattern. | Ensure README has a clear `usage/examples` section near the top-level navigation flow. |
| Info | competitor_research | Competitors frequently include `contributing` sections. | 3 competitor repos include this pattern. | Ensure README has a clear `contributing` section near the top-level navigation flow. |

## Query Benchmark

| Query | Rank | Sampled | Total Results |
|-------|------|---------|---------------|
| agentic seo | 72 | 100 | 2539 |
| agentic seo aeo ai agents | 15 | 50 | 136 |
| aeo | Not found | 100 | 9181 |
| ai agents | Not found | 100 | 448352 |
| ai search | Not found | 100 | 86204 |
| geo | Not found | 100 | 354795 |

## Competitor Research

- Competitors analyzed: `6` across `6` queries

| Competitor | Seen Queries | Best Rank | Stars | Topics |
|------------|--------------|-----------|-------|--------|
| AgriciDaniel/claude-seo | 3 | 1 | 16135 | 7 |
| gbessoni/seobuild-onpage | 2 | 2 | 247 | 14 |
| chroma-core/chroma | 2 | 2 | 29205 | 6 |
| codyschneiderx/seo-ai-search-dashboard | 2 | 3 | 30 | 0 |
| addyosmani/agentic-seo | 2 | 4 | 307 | 5 |
| cgallic/kai-cmo-harness | 2 | 4 | 47 | 20 |

### Topic Gaps

- `claude-code` (covered by 3 competitors)
- `ai` (covered by 2 competitors)
- `marketing-automation` (covered by 2 competitors)
- `open-source` (covered by 2 competitors)
- `claude-code-skills` (covered by 2 competitors)
- `agents` (covered by 2 competitors)
- `ai-seo` (covered by 1 competitors)
- `claude-code-skill` (covered by 1 competitors)
- `agent-skills` (covered by 1 competitors)
- `ahrefs` (covered by 1 competitors)

### Competitor Opportunities

- [Warning] High-frequency competitor topics are missing from target repo.
  Evidence: Missing topic examples: claude-code, ai, marketing-automation, open-source, claude-code-skills
  Fix: Add relevant missing topics (without exceeding 20 total) based on actual repository scope.
- [Info] Target repository description is shorter than competitor baseline.
  Evidence: Target words: 23, competitor average: 25.33
  Fix: Expand description with intent terms, scope, and supported environments.
- [Info] Competitors frequently include `install` sections.
  Evidence: 6 competitor repos include this pattern.
  Fix: Ensure README has a clear `install` section near the top-level navigation flow.
- [Info] Competitors frequently include `usage/examples` sections.
  Evidence: 5 competitor repos include this pattern.
  Fix: Ensure README has a clear `usage/examples` section near the top-level navigation flow.
- [Info] Competitors frequently include `contributing` sections.
  Evidence: 3 competitor repos include this pattern.
  Fix: Ensure README has a clear `contributing` section near the top-level navigation flow.

## Traffic Snapshot

- Views: `924` (unique: `431`)
- Clones: `56` (unique: `55`)
- Archive history: `.github-seo-data/traffic_history.jsonl`
- Latest snapshot: `.github-seo-data/latest_traffic_snapshot.json`

## Title Optimization

- Current name: `agentic-seo`
- Recommended slug: `agentic-seo-aeo-ai-agents`
- Recommended title: `Agentic SEO AEO AI Agents`
- Intent keywords: `agentic, seo, aeo, ai, agents, search, geo, github, llm, marketing, python, schema`

## Backlink Distribution Plan

- Target repo URL: `https://github.com/T4wroot/agentic-seo`

### Suggested Post Titles

- How I Built Agentic SEO AEO AI Agents for SEO Automation
- GitHub SEO Playbook: Improving Discoverability for Agentic SEO AEO AI Agents
- Agentic SEO AEO AI Agents: From Idea to Open-Source SEO Workflow
- Open-Source Guide: agentic, seo, aeo with Agentic SEO AEO AI Agents

### Channels

| Channel | Content Type | Cadence | CTA |
|---------|--------------|---------|-----|
| Medium | Technical case study | 1 post per major release | Link to repo + install quickstart + release notes |
| Dev.to | Tutorial / launch post | 1 launch post + update posts quarterly | Link to GitHub repo and usage examples |
| Hashnode | Deep-dive engineering write-up | Bi-monthly | Link to architecture docs and scripts |
| Personal/Company Blog | Canonical long-form article | Monthly | Link to repo, docs, and comparison pages |
| LinkedIn Article | Problem/solution summary for practitioners | Per release | Link to repo and demo outputs |
| Reddit (relevant subreddits) | Show-and-tell with value-first context | Selective (major feature drops) | Share repo only after explaining workflow and results |

### Anchor Guidance

- Exact-match anchor cap: `10%`
- Brand anchors (repo/owner name)
- Partial-match anchors (e.g., 'agentic SEO skill')
- Generic anchors ('GitHub repo', 'source code')
- Naked URL anchors
