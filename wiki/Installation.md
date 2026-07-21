# Installation

This page mirrors the README installation detail, but keeps it organized by target and workflow.

Current release package: `v3.0.0`

Release page:

https://github.com/T4wroot/agentic-seo/releases/tag/v3.0.0

## IDE Targets

The installer writes the skill in each IDE's native format.

| Target | Install location | Native format |
|---|---|---|
| `claude` | `~/.claude/skills/seo` | Skill directory |
| `codex` | `~/.codex/skills/seo` | Skill directory |
| `antigravity` | `<project>/.agent/skills/seo` | Skill directory |
| `cowork` | `<project>/.claude/skills/seo` | Project-scoped skill |
| `cursor` | `<project>/.cursor/rules/seo.mdc` plus `.cursor/skills/seo/` | Cursor MDC rule |
| `windsurf` | `<project>/.windsurf/rules/seo.md` plus `.windsurf/skills/seo/` | Windsurf rule |
| `continue` | `<project>/.continue/prompts/seo.prompt` plus `.continue/skills/seo/` | Continue prompt |
| `copilot` | `<project>/.github/copilot-instructions.md` plus `.github/skills/seo/` | Copilot repo instructions |
| `cline` | `<project>/.clinerules` plus `.cline/skills/seo/` | Cline project rules |
| `global` | Claude plus Codex | User-wide install |
| `project` | Antigravity, Cowork, Cursor, Windsurf, Continue, Copilot, Cline | Project-local install |
| `all` | Global plus project targets | Every supported target |

## Quick Install From Release

Use `--online` for normal installs. With no `--target`, online mode installs to every supported target.

### Linux and macOS

Install every target:

```bash
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online
```

Claude only:

```bash
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online --target claude
```

Codex only:

```bash
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online --target codex
```

User-wide Claude plus Codex:

```bash
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online --target global
```

All project-local targets:

```bash
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online --target project --project-dir /path/to/your/project
```

Everything, including global and project-local targets:

```bash
curl -fsSL https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh | bash -s -- --online --target all --project-dir /path/to/your/project
```

Pin a specific release tag:

```bash
curl -fsSLO https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh
bash install.sh --online --ref v3.0.0 --target codex --force
```

### Windows PowerShell

Download the installer:

```powershell
iwr https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.ps1 -OutFile install.ps1
```

Install every target:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online
```

Claude only:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online --target claude
```

Codex only:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online --target codex
```

Everything for a project:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online --target all --project-dir C:\path\to\your\project
```

Pin a release tag:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online --ref v3.0.0 --target codex --force
```

## Install From Source

Use source installs when developing the skill or testing unreleased changes.

```bash
git clone https://github.com/T4wroot/agentic-seo.git
cd agentic-seo
```

Claude:

```bash
bash install.sh --target claude
```

Codex:

```bash
bash install.sh --target codex
```

Project-scoped Cowork:

```bash
bash install.sh --target cowork --project-dir /path/to/your/project
```

Cursor:

```bash
bash install.sh --target cursor --project-dir /path/to/your/project
```

Windsurf:

```bash
bash install.sh --target windsurf --project-dir /path/to/your/project
```

Continue:

```bash
bash install.sh --target continue --project-dir /path/to/your/project
```

Copilot:

```bash
bash install.sh --target copilot --project-dir /path/to/your/project
```

Cline:

```bash
bash install.sh --target cline --project-dir /path/to/your/project
```

Antigravity:

```bash
bash install.sh --target antigravity --project-dir /path/to/your/project
```

All project-local IDEs:

```bash
bash install.sh --target project --project-dir /path/to/your/project
```

Every target:

```bash
bash install.sh --target all --project-dir /path/to/your/project
```

## Safer Remote Install

If you want to inspect the installer before running it:

```bash
curl -fsSLO https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.sh
less install.sh
bash install.sh --online --target codex
```

PowerShell equivalent:

```powershell
iwr https://raw.githubusercontent.com/T4wroot/agentic-seo/main/install.ps1 -OutFile install.ps1
notepad install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online --target codex
```

## Installer Flags

| Flag | Default | Purpose |
|---|---|---|
| `--target <name>` | `claude` | Pick one target. With `--online` and no target, defaults to `all`. |
| `--project-dir <path>` | current directory | Destination project for project-local targets. |
| `--skill-name <name>` | `seo` | Override the installed skill folder name for skill-directory targets. |
| `--online` | off | Fetch the release/archive payload from GitHub instead of using the local tree. |
| `--ref <branch-or-tag>` | `main` | Branch or tag to use in online mode. Use release tags for stable installs. |
| `--repo-url <url>` | upstream repo | Override the remote source repository. |
| `--source <auto|local|remote>` | `auto` | Force source resolution mode. |
| `--repo-path <path>` | empty | Use a specific local checkout as the install source. |
| `--install-deps` | off | Install Python dependencies used by common scripts. |
| `--install-playwright` | off | Install Playwright and Chromium for screenshots and rendered checks. |
| `--force` | off | Overwrite an existing installed skill. Online mode implies force for extracted payloads. |
| `-h`, `--help` | off | Show installer usage. |

## Optional Dependencies

Core scripts use Python plus common parsing and network libraries.

From a source checkout:

```bash
python3 -m pip install -r requirements.txt
```

Minimal manual install:

```bash
python3 -m pip install requests beautifulsoup4 lxml
```

Visual analysis requires Playwright:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

The installer can do this automatically:

```bash
bash install.sh --target codex --install-deps --install-playwright
```

## Verify Installation

Ask your IDE or agent one of these:

```text
Run an SEO audit on https://example.com.
```

```text
Check schema markup on my homepage and generate corrected JSON-LD.
```

```text
Analyze Core Web Vitals for https://example.com and prioritize fixes.
```

```text
Run GitHub SEO analysis for owner/repo and produce GITHUB-SEO-REPORT.md and GITHUB-ACTION-PLAN.md.
```

For Codex, you can explicitly invoke:

```text
$seo audit https://example.com
```

## What Gets Installed

Installed skill bundles need only:

- `SKILL.md`
- `scripts/`
- `resources/`

Repository-only files are not required inside the skill runtime:

- `tests/`
- `.github/`
- `wiki/`
- governance docs
- generated reports
- local `tmp/` output

Release packaging uses this runtime allowlist so installed skills stay small and predictable.

## Common Issues

### Existing Skill Directory

If the target already exists, rerun with:

```bash
bash install.sh --target codex --force
```

### Browser Checks Fail

Install Playwright and Chromium:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

### GitHub or PageSpeed API Limits

API failures do not mean the installation failed. They should be reported as environment limitations during audits.

### Windows Execution Policy

If PowerShell blocks local scripts, run PowerShell as a user with script execution allowed, or use:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --online --target codex
```

