#!/usr/bin/env bash

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Bhanunamikaze/Agentic-SEO-Skill.git}"
GITHUB_REPO="${GITHUB_REPO:-Bhanunamikaze/Agentic-SEO-Skill}"
GITHUB_REF="${GITHUB_REF:-main}"
SKILL_NAME="seo"
TARGET="claude"
TARGET_EXPLICIT=0
PROJECT_DIR="$(pwd)"
PROJECT_DIR_EXPLICIT=0
FORCE=0
INSTALL_DEPS=0
INSTALL_PLAYWRIGHT=0
ONLINE_MODE=0
SOURCE_MODE="auto"
REPO_PATH=""
TEMP_DIR=""

# Payload paths copied into each install destination.
# docs/ and tests/ are intentionally excluded — docs/ only holds README
# screenshots, and tests/ is for repository CI rather than installed skills.
REQUIRED_PATHS=(
    "SKILL.md"
    "scripts"
    "resources"
)

usage() {
    cat <<'EOF'
Agentic SEO Skill Installer

Installs the SEO analysis skill for AI coding assistants and agent IDEs.

Each IDE target installs the skill in that IDE's native format:
  claude / codex / antigravity  ->  skills/ directory  (native skill support)
  cowork                        ->  <project>/<skill>.plugin  (Cowork plugin file; import via Cowork UI)
  cursor                        ->  .cursor/rules/seo.mdc  (Cursor MDC rule)
  windsurf                      ->  .windsurf/rules/seo.md (Windsurf rule)
  copilot                       ->  .github/copilot-instructions.md
  cline                         ->  .clinerules       (Cline project instructions)
  continue                      ->  .continue/prompts/seo.prompt (slash command)

Usage:
  bash install.sh [options]

Options:
  --target <target>
      Install target (default: claude). Valid targets:
        claude       -> ~/.claude/skills/seo
        codex        -> ~/.codex/skills/seo
        antigravity  -> <project>/.agent/skills/seo
        cowork       -> <project>/seo.plugin  (Cowork plugin file; import via Cowork UI)
        cursor       -> <project>/.cursor/rules/seo.mdc
        windsurf     -> <project>/.windsurf/rules/seo.md
        continue     -> <project>/.continue/prompts/seo.prompt
        copilot      -> <project>/.github/copilot-instructions.md
        cline        -> <project>/.clinerules
        global       -> claude + codex (user-wide)
        project      -> antigravity + cowork + cursor + windsurf + continue + copilot + cline
        all          -> global + project (every target)

  --project-dir <path>         Project directory for project-local installs (default: cwd)
  --skill-name <name>          Installed folder name for skills-dir targets (default: seo)
  --repo-url <url>             Git URL for remote source installs
  --source <auto|local|remote> Source mode (default: auto)
  --repo-path <path>           Use a specific local checkout as the install source
  --online                     Fetch latest release archive from GitHub instead of cloning.
                               When no --target is supplied, defaults to --target all.
  --ref <branch-or-tag>        Branch / tag to fetch in --online mode (default: main)
  --install-deps               Install Python dependencies (requests, beautifulsoup4)
  --install-playwright         Also install Playwright + Chromium
  --force                      Overwrite an existing installed skill
  -h, --help                   Show this help

Examples:
  bash install.sh --target claude
  bash install.sh --target global
  bash install.sh --target project --project-dir /path/to/your/project
  bash install.sh --target cursor  --project-dir /path/to/your/project
  bash install.sh --target all     --project-dir /path/to/your/project
  bash install.sh --online
  bash install.sh --online --ref develop

Safer remote install:
  curl -fsSLO https://raw.githubusercontent.com/Bhanunamikaze/Agentic-SEO-Skill/main/install.sh
  bash install.sh --target claude
EOF
}

cleanup() {
    if [[ -n "${TEMP_DIR}" && -d "${TEMP_DIR}" ]]; then
        rm -rf "${TEMP_DIR}"
    fi
}

trap cleanup EXIT

require_cmd() {
    local cmd="$1"
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        echo "Error: required command not found: ${cmd}" >&2
        exit 1
    fi
}

resolve_dir() {
    local dir="$1"
    if [[ ! -d "${dir}" ]]; then
        echo "Error: directory not found: ${dir}" >&2
        exit 1
    fi
    (cd "${dir}" && pwd)
}

# ── Skills-directory copy (Claude / Codex / Antigravity / Cowork) ────────────

copy_skill() {
    local src="$1"
    local dest="$2"
    local label="$3"

    if [[ -e "${dest}" && "${FORCE}" -ne 1 ]]; then
        echo "  Warning: ${label} target already exists: ${dest}" >&2
        echo "  Use --force to overwrite." >&2
        return 1
    fi

    local required_path
    for required_path in "${REQUIRED_PATHS[@]}"; do
        if [[ ! -e "${src}/${required_path}" ]]; then
            echo "  Error: required skill path not found: ${src}/${required_path}" >&2
            return 1
        fi
    done

    mkdir -p "$(dirname "${dest}")"
    if [[ -e "${dest}" ]]; then
        rm -rf "${dest}"
    fi
    mkdir -p "${dest}"

    if command -v rsync >/dev/null 2>&1; then
        local p
        for p in "${REQUIRED_PATHS[@]}"; do
            rsync -a \
                --exclude ".git/" \
                --exclude ".github/" \
                --exclude "__pycache__/" \
                --exclude "*.pyc" \
                --exclude "seo-report-*.html" \
                --exclude "plan.md" \
                --exclude "tests/" \
                --exclude "tmp/" \
                "${src}/${p}" "${dest}/"
        done
    else
        (
            cd "${src}"
            tar \
                --exclude=".git" \
                --exclude=".git/*" \
                --exclude=".github" \
                --exclude=".github/*" \
                --exclude="__pycache__" \
                --exclude="*/__pycache__" \
                --exclude="*.pyc" \
                --exclude="seo-report-*.html" \
                --exclude="plan.md" \
                --exclude="tests" \
                --exclude="tests/*" \
                --exclude="tmp" \
                --exclude="tmp/*" \
                -cf - \
                "${REQUIRED_PATHS[@]}"
        ) | (
            cd "${dest}"
            tar -xf -
        )
    fi

    find "${dest}" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
    find "${dest}" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "${dest}" -type f -name "seo-report-*.html" -delete 2>/dev/null || true

    echo "  Installed for ${label}: ${dest}"
}

# ── Root resolution helpers ───────────────────────────────────────────────────

global_root_for_tool() {
    local tool="$1"
    case "${tool}" in
        claude)      printf '%s\n' "${CLAUDE_HOME:-${HOME}/.claude}" ;;
        codex)       printf '%s\n' "${CODEX_HOME:-${HOME}/.codex}" ;;
        antigravity) printf '%s\n' "${HOME}/.gemini/antigravity" ;;
        *)           return 1 ;;
    esac
}

workspace_root_for_tool() {
    local tool="$1"
    case "${tool}" in
        antigravity)
            if [[ "${TARGET}" == "antigravity" || "${PROJECT_DIR_EXPLICIT}" -eq 1 || -d "${PROJECT_DIR}/.agent" ]]; then
                printf '%s\n' "${PROJECT_DIR}/.agent"
                return 0
            fi
            ;;
        claude)
            if [[ "${PROJECT_DIR_EXPLICIT}" -eq 1 && -d "${PROJECT_DIR}/.claude" ]]; then
                printf '%s\n' "${PROJECT_DIR}/.claude"
                return 0
            fi
            ;;
        codex)
            if [[ "${PROJECT_DIR_EXPLICIT}" -eq 1 && -d "${PROJECT_DIR}/.codex" ]]; then
                printf '%s\n' "${PROJECT_DIR}/.codex"
                return 0
            fi
            ;;
    esac
    return 1
}

install_tool_auto() {
    local tool="$1"
    local install_root="" label=""
    if install_root="$(workspace_root_for_tool "${tool}")"; then
        label="${tool}-local"
    else
        install_root="$(global_root_for_tool "${tool}")"
        label="${tool}-global"
    fi
    copy_skill "${SRC_DIR}" "${install_root}/skills/${SKILL_NAME}" "${label}"
}

install_tool_global() {
    local tool="$1"
    local global_root
    global_root="$(global_root_for_tool "${tool}")"
    copy_skill "${SRC_DIR}" "${global_root}/skills/${SKILL_NAME}" "${tool}-global"
}

# ── IDE-native format installers ─────────────────────────────────────────────

# Shared invocation summary written into IDE-specific rule / prompt files.
_skill_invocation_text() {
    cat <<'SKILL_CONTENT'
# Agentic SEO Skill

You have access to the Agentic SEO analysis skill (16 sub-skills, 10 specialist agents, 89 scripts).

## When to activate

Activate whenever the user asks to:
- Perform an SEO analysis / audit on a URL, blog post, or GitHub repository
- Review technical SEO (crawlability, indexability, Core Web Vitals, security headers)
- Evaluate content quality, E-E-A-T, or AI-content signals
- Validate / generate Schema.org JSON-LD
- Analyse sitemaps, hreflang, image SEO, internal/external link profiles
- Optimise for Generative Engine Optimisation (GEO) or Answer Engine Optimisation (AEO)
- Audit a GitHub repository's metadata, README, community profile, or search ranking
- Generate a prioritised SEO action plan

## Invocation

| Command | Sub-Skill | Description |
|---------|-----------|-------------|
| `seo audit <url>`       | Full audit          | Evidence-backed site/page audit            |
| `seo page <url>`        | Page deep-dive      | Single-page SEO analysis                   |
| `seo article <url>`     | Article SEO         | Content optimisation for a blog post       |
| `seo technical <url>`   | Technical SEO       | Crawl, index, CWV, AI crawler checks       |
| `seo content <url>`     | Content / E-E-A-T   | Quality, expertise, trust scoring          |
| `seo schema <url>`      | Schema.org          | JSON-LD detection, validation, generation  |
| `seo sitemap <url>`     | Sitemaps            | XML sitemap validation and quality gates   |
| `seo images <url>`      | Images              | Alt text, formats, lazy loading, CLS       |
| `seo geo <url>`         | GEO                 | AI Overviews / ChatGPT / Perplexity        |
| `seo aeo <url>`         | AEO                 | Featured snippets, PAA, Knowledge Panel    |
| `seo links <url>`       | Link profile        | Internal/backlink + anchor analysis        |
| `seo hreflang <url>`    | International       | hreflang validation                        |
| `seo github <repo>`     | GitHub SEO          | Repo metadata, README, community, traffic  |
| `seo plan <topic>`      | Strategic plan      | Topical clusters, industry templates       |

## Workflow

Apply the rubric in `resources/references/llm-audit-rubric.md`:
1. Collect page evidence (`read_url_content` first; bundled scripts as needed).
2. Reason from explicit proof — every finding cites evidence.
3. Label confidence: Confirmed / Likely / Hypothesis.
4. Prioritise by impact and effort.
5. Produce a structured action plan (`FULL-AUDIT-REPORT.md` + `ACTION-PLAN.md`).

Read **SKILL.md** for the full multi-phase workflow.
SKILL_CONTENT
}

# Cursor — .cursor/rules/seo.mdc  (MDC frontmatter format)
install_cursor() {
    local rules_dir="${PROJECT_DIR}/.cursor/rules"
    local mdc_file="${rules_dir}/seo.mdc"

    if [[ -f "${mdc_file}" && "${FORCE}" -ne 1 ]]; then
        echo "  Warning: Cursor rule already exists: ${mdc_file} (use --force to overwrite)"
        return 0
    fi

    mkdir -p "${rules_dir}"

    {
        cat <<'MDC_HEADER'
---
description: "Agentic SEO skill. Activate when the user asks to perform SEO analysis, audit a URL/repo, review technical SEO, schema, Core Web Vitals, E-E-A-T, GEO, AEO, or hreflang."
globs: []
alwaysApply: false
---
MDC_HEADER
        _skill_invocation_text
    } > "${mdc_file}"

    echo "  Installed Cursor rule: ${mdc_file}"

    copy_skill "${SRC_DIR}" "${PROJECT_DIR}/.cursor/skills/${SKILL_NAME}" "Cursor (.cursor/skills/)" || true
}

# Windsurf — .windsurf/rules/seo.md
install_windsurf() {
    local rules_dir="${PROJECT_DIR}/.windsurf/rules"
    local rule_file="${rules_dir}/seo.md"

    if [[ -f "${rule_file}" && "${FORCE}" -ne 1 ]]; then
        echo "  Warning: Windsurf rule already exists: ${rule_file} (use --force to overwrite)"
        return 0
    fi

    mkdir -p "${rules_dir}"
    _skill_invocation_text > "${rule_file}"

    echo "  Installed Windsurf rule: ${rule_file}"

    copy_skill "${SRC_DIR}" "${PROJECT_DIR}/.windsurf/skills/${SKILL_NAME}" "Windsurf (.windsurf/skills/)" || true
}

# Continue.dev — .continue/prompts/seo.prompt  (slash command format)
install_continue() {
    local prompts_dir="${PROJECT_DIR}/.continue/prompts"
    local prompt_file="${prompts_dir}/seo.prompt"

    if [[ -f "${prompt_file}" && "${FORCE}" -ne 1 ]]; then
        echo "  Warning: Continue prompt already exists: ${prompt_file} (use --force to overwrite)"
        return 0
    fi

    mkdir -p "${prompts_dir}"

    cat > "${prompt_file}" <<'PROMPT_FILE'
name: seo
description: Run Agentic SEO analysis on the supplied URL, blog post, or GitHub repository
---
You have the Agentic SEO skill loaded.

{{{ input }}}

Use the full SEO workflow:
1. Identify the audit target (URL, page, article, or GitHub repo) from the user's request.
2. Collect evidence first (`read_url_content`, then bundled scripts as needed).
3. Run the appropriate sub-skill (audit / page / article / technical / content / schema /
   sitemap / images / geo / aeo / links / hreflang / github / plan).
4. Apply the llm-audit-rubric: evidence -> impact -> fix, with confidence labels.
5. Produce FULL-AUDIT-REPORT.md and ACTION-PLAN.md with prioritised fixes.

Read SKILL.md for the complete multi-phase workflow.
PROMPT_FILE

    echo "  Installed Continue.dev prompt: ${prompt_file}"

    copy_skill "${SRC_DIR}" "${PROJECT_DIR}/.continue/skills/${SKILL_NAME}" "Continue.dev (.continue/skills/)" || true
}

# GitHub Copilot — .github/copilot-instructions.md
install_copilot() {
    local github_dir="${PROJECT_DIR}/.github"
    local instructions_file="${github_dir}/copilot-instructions.md"
    mkdir -p "${github_dir}"

    local skill_block
    skill_block="$(
        printf '%s\n\n' '---'
        _skill_invocation_text
    )"

    if [[ -f "${instructions_file}" ]]; then
        if grep -q "Agentic SEO Skill" "${instructions_file}" 2>/dev/null; then
            echo "  GitHub Copilot instructions already contain Agentic SEO Skill (skipping)"
        else
            printf '\n%s\n' "${skill_block}" >> "${instructions_file}"
            echo "  Updated GitHub Copilot instructions: ${instructions_file}"
        fi
    else
        printf '%s\n' "${skill_block}" > "${instructions_file}"
        echo "  Created GitHub Copilot instructions: ${instructions_file}"
    fi

    copy_skill "${SRC_DIR}" "${github_dir}/skills/${SKILL_NAME}" "GitHub Copilot (.github/skills/)" || true
}

# Claude Cowork — packages the skill as a .plugin file (zip) for import via Cowork UI
# Structure: .claude-plugin/plugin.json  +  skills/<name>/  (no flat .claude/skills/ copy)
install_cowork() {
    local plugin_file="${PROJECT_DIR}/${SKILL_NAME}.plugin"

    if [[ -f "${plugin_file}" && "${FORCE}" -ne 1 ]]; then
        echo "  Warning: Cowork plugin already exists: ${plugin_file}" >&2
        echo "  Use --force to overwrite." >&2
        return 1
    fi

    mkdir -p "${PROJECT_DIR}"

    local build_dir
    build_dir="$(mktemp -d)"

    # Build required plugin directory layout
    mkdir -p "${build_dir}/.claude-plugin"
    mkdir -p "${build_dir}/skills/${SKILL_NAME}"

    # Manifest — .claude-plugin/plugin.json (NOT plugin.json at root)
    cat > "${build_dir}/.claude-plugin/plugin.json" <<EOF
{
  "name": "${SKILL_NAME}",
  "version": "1.0.0",
  "description": "LLM-first SEO audits for websites, blog posts, and GitHub repos"
}
EOF

    # Populate skill files into the plugin's skills/ directory
    if ! copy_skill "${SRC_DIR}" "${build_dir}/skills/${SKILL_NAME}" "Cowork plugin build"; then
        rm -rf "${build_dir}"
        return 1
    fi

    # Package as .plugin (zip archive)
    if command -v zip >/dev/null 2>&1; then
        (cd "${build_dir}" && zip -rq "${plugin_file}" . \
            --exclude "*.DS_Store" \
            --exclude "__pycache__/*" \
            --exclude "*.pyc")
    else
        python3 - "${build_dir}" "${plugin_file}" <<'PYEOF'
import zipfile, os, sys
build_dir, plugin_file = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(plugin_file, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(build_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fname in files:
            if fname.endswith('.pyc'):
                continue
            abs_path = os.path.join(root, fname)
            zf.write(abs_path, os.path.relpath(abs_path, build_dir))
PYEOF
    fi

    rm -rf "${build_dir}"
    echo "  Created Cowork plugin: ${plugin_file}"
    echo ""
    echo "  To install in Cowork:"
    echo "    1. Open claude.ai → Cowork"
    echo "    2. Go to Customize → Plugins → Install from file"
    echo "    3. Select: ${plugin_file}"
}

# Cline — .clinerules  (project-level instruction file)
install_cline() {
    local rules_file="${PROJECT_DIR}/.clinerules"
    local marker="<!-- agentic-seo-skill -->"

    if [[ -f "${rules_file}" ]] && grep -q "agentic-seo-skill" "${rules_file}" 2>/dev/null; then
        if [[ "${FORCE}" -ne 1 ]]; then
            echo "  Warning: .clinerules already contains Agentic SEO entry (use --force to overwrite)"
            return 0
        fi
        python3 -c "
import re
text = open('${rules_file}').read()
text = re.sub(r'<!-- agentic-seo-skill -->.*?<!-- /agentic-seo-skill -->\n?', '', text, flags=re.DOTALL)
open('${rules_file}', 'w').write(text)
"
    fi

    {
        printf '\n%s\n' "${marker}"
        _skill_invocation_text
        printf '<!-- /agentic-seo-skill -->\n'
    } >> "${rules_file}"

    echo "  Updated .clinerules: ${rules_file}"

    copy_skill "${SRC_DIR}" "${PROJECT_DIR}/.cline/skills/${SKILL_NAME}" "Cline (.cline/skills/)" || true
}

# ── Argument parsing ──────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)              TARGET="${2:-}"; TARGET_EXPLICIT=1; shift 2 ;;
        --project-dir)         PROJECT_DIR="${2:-}"; PROJECT_DIR_EXPLICIT=1; shift 2 ;;
        --skill-name)          SKILL_NAME="${2:-}"; shift 2 ;;
        --repo-url)            REPO_URL="${2:-}"; shift 2 ;;
        --source)              SOURCE_MODE="${2:-}"; shift 2 ;;
        --repo-path)           REPO_PATH="${2:-}"; shift 2 ;;
        --ref)                 GITHUB_REF="${2:-}"; shift 2 ;;
        --install-deps)        INSTALL_DEPS=1; shift ;;
        --install-playwright)  INSTALL_PLAYWRIGHT=1; INSTALL_DEPS=1; shift ;;
        --online)              ONLINE_MODE=1; FORCE=1; shift ;;
        --force)               FORCE=1; shift ;;
        -h|--help)             usage; exit 0 ;;
        *)                     echo "Unknown option: $1" >&2; usage; exit 1 ;;
    esac
done

VALID_TARGETS="claude codex antigravity cowork cursor windsurf continue copilot cline global project all"
if ! echo "${VALID_TARGETS}" | grep -qw "${TARGET}"; then
    echo "Error: invalid --target: ${TARGET}" >&2
    echo "Valid targets: ${VALID_TARGETS}" >&2
    exit 1
fi

if [[ "${SOURCE_MODE}" != "auto" && "${SOURCE_MODE}" != "local" && "${SOURCE_MODE}" != "remote" ]]; then
    echo "Error: invalid --source: ${SOURCE_MODE}" >&2
    exit 1
fi

if [[ "${ONLINE_MODE}" -eq 1 && "${TARGET_EXPLICIT}" -ne 1 ]]; then
    TARGET="all"
fi

require_cmd bash
require_cmd python3

SCRIPT_PATH="${BASH_SOURCE[0]-$0}"
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
SRC_DIR=""
SHOULD_CLONE=0

# ── Source resolution ─────────────────────────────────────────────────────────

if [[ "${ONLINE_MODE}" -eq 1 ]]; then
    require_cmd curl
    require_cmd tar
    TEMP_DIR="$(mktemp -d)"
    EXTRACT_DIR="${TEMP_DIR}/extracted"
    mkdir -p "${EXTRACT_DIR}"
    PKG="${TEMP_DIR}/package"

    # Resolve a download URL. Preference order:
    #   1. The first .tar.gz / .tgz asset listed on the latest release.
    #   2. The latest release source tarball (always exists for any tag).
    #   3. The configured branch archive (final fallback).
    echo "Fetching latest release info from ${GITHUB_REPO}..."
    RELEASE_JSON=$(curl -fsSL "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" 2>/dev/null || true)
    LATEST_TAG=$(printf '%s' "${RELEASE_JSON}" | grep '"tag_name":' | head -n 1 | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/' || true)

    DOWNLOAD_URL=""
    DOWNLOAD_DESC=""
    if [[ -n "${LATEST_TAG}" && "${LATEST_TAG}" != "null" ]]; then
        echo "  Latest release: ${LATEST_TAG}"
        ASSET_URL=$(
            printf '%s' "${RELEASE_JSON}" \
                | grep -oE '"browser_download_url": *"[^"]+\.(tar\.gz|tgz)"' \
                | head -n 1 \
                | sed -E 's/.*"browser_download_url": *"([^"]+)".*/\1/' || true
        )
        if [[ -n "${ASSET_URL}" ]]; then
            DOWNLOAD_URL="${ASSET_URL}"
            DOWNLOAD_DESC="release asset: $(basename "${ASSET_URL}")"
        else
            DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/archive/refs/tags/${LATEST_TAG}.tar.gz"
            DOWNLOAD_DESC="source archive for tag ${LATEST_TAG}"
        fi
    fi
    if [[ -z "${DOWNLOAD_URL}" ]]; then
        DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/archive/refs/heads/${GITHUB_REF}.tar.gz"
        DOWNLOAD_DESC="branch archive: ${GITHUB_REF}"
    fi
    echo "  Downloading ${DOWNLOAD_DESC}..."
    if ! curl -fsSL -o "${PKG}" "${DOWNLOAD_URL}"; then
        echo "Error: download failed: ${DOWNLOAD_URL}" >&2
        exit 1
    fi
    if ! tar -xzf "${PKG}" -C "${EXTRACT_DIR}"; then
        echo "Error: extract failed for ${PKG}" >&2
        exit 1
    fi
    rm -f "${PKG}"

    # Locate SKILL.md. Release-asset tarballs may be flat (SKILL.md at root);
    # GitHub source tarballs nest contents under a single top-level dir like
    # `Repo-Tag/`. Support either.
    if [[ -f "${EXTRACT_DIR}/SKILL.md" ]]; then
        SRC_DIR="${EXTRACT_DIR}"
    else
        SRC_DIR=""
        for d in "${EXTRACT_DIR}"/*/; do
            if [[ -f "${d}SKILL.md" ]]; then
                SRC_DIR="${d%/}"
                break
            fi
        done
        if [[ -z "${SRC_DIR}" ]]; then
            echo "Error: downloaded archive did not contain SKILL.md." >&2
            echo "  Source URL: ${DOWNLOAD_URL}" >&2
            echo "  Extract dir: ${EXTRACT_DIR}" >&2
            echo "  Top-level entries:" >&2
            ls -1 "${EXTRACT_DIR}" 2>/dev/null | head -15 | sed 's/^/    /' >&2
            exit 1
        fi
    fi
    echo "Using downloaded package source: ${SRC_DIR}"
elif [[ -n "${REPO_PATH}" ]]; then
    SRC_DIR="$(resolve_dir "${REPO_PATH}")"
    echo "Using repo path source: ${SRC_DIR}"
elif [[ "${SOURCE_MODE}" == "local" ]]; then
    SRC_DIR="${SCRIPT_DIR}"
    echo "Using local source: ${SRC_DIR}"
elif [[ "${SOURCE_MODE}" == "remote" ]]; then
    SHOULD_CLONE=1
elif [[ -f "${SCRIPT_DIR}/SKILL.md" ]]; then
    SRC_DIR="${SCRIPT_DIR}"
    echo "Using local source: ${SRC_DIR}"
else
    SHOULD_CLONE=1
fi

if [[ "${SHOULD_CLONE}" -eq 1 ]]; then
    require_cmd git
    TEMP_DIR="$(mktemp -d)"
    echo "Cloning source repo: ${REPO_URL}"
    if ! git clone --depth 1 "${REPO_URL}" "${TEMP_DIR}/repo" >/dev/null 2>&1; then
        echo "Error: failed to clone source repo: ${REPO_URL}" >&2
        echo "Tip: pass --repo-path <local-path> or --online to avoid cloning." >&2
        exit 1
    fi
    SRC_DIR="${TEMP_DIR}/repo"
    echo "Using remote source: ${SRC_DIR}"
fi

if [[ ! -f "${SRC_DIR}/SKILL.md" ]]; then
    echo "Error: SKILL.md not found in source directory: ${SRC_DIR}" >&2
    exit 1
fi

echo ""
echo "Installing Agentic SEO Skill"
echo "Target:     ${TARGET}"
echo "Skill name: ${SKILL_NAME}"
echo ""

# ── Install per target ────────────────────────────────────────────────────────

case "${TARGET}" in
    claude)      install_tool_auto "claude" ;;
    codex)       install_tool_auto "codex" ;;
    antigravity) install_tool_auto "antigravity" ;;
    cowork)      install_cowork ;;
    cursor)      install_cursor ;;
    windsurf)    install_windsurf ;;
    continue)    install_continue ;;
    copilot)     install_copilot ;;
    cline)       install_cline ;;
    global)
        install_tool_global "claude" || true
        install_tool_global "codex"  || true
        ;;
    project)
        install_tool_auto "antigravity" || true
        install_cowork                  || true
        install_cursor                  || true
        install_windsurf                || true
        install_continue                || true
        install_copilot                 || true
        install_cline                   || true
        ;;
    all)
        install_tool_global "claude"    || true
        install_tool_global "codex"     || true
        install_tool_auto "antigravity" || true
        install_cowork                  || true
        install_cursor                  || true
        install_windsurf                || true
        install_continue                || true
        install_copilot                 || true
        install_cline                   || true
        ;;
esac

# ── Python dependencies ───────────────────────────────────────────────────────

if [[ "${INSTALL_DEPS}" -eq 1 ]]; then
    echo ""
    echo "Installing Python dependencies..."
    DEPS_OK=0
    if [[ -f "${SRC_DIR}/requirements.txt" ]] && python3 -m pip install --user -r "${SRC_DIR}/requirements.txt"; then
        echo "  Installed dependencies from requirements.txt"
        DEPS_OK=1
    elif python3 -m pip install --user requests beautifulsoup4; then
        echo "  Installed requests + beautifulsoup4"
        DEPS_OK=1
    else
        echo "  Warning: could not auto-install Python dependencies. Install manually:"
        echo "    python3 -m pip install --user requests beautifulsoup4"
    fi

    if [[ "${INSTALL_PLAYWRIGHT}" -eq 1 ]]; then
        if python3 -m pip install --user playwright && python3 -m playwright install chromium; then
            echo "  Installed Playwright + Chromium"
        else
            echo "  Warning: could not auto-install Playwright. Install manually:"
            echo "    python3 -m pip install --user playwright && python3 -m playwright install chromium"
        fi
    fi
fi

echo ""
echo "Install complete."
echo ""
echo "Next steps:"
echo "  1. Restart your IDE/agent session to pick up the skill."
echo "  2. Ask: 'perform seo analysis on https://example.com'"
echo "  3. Or:  'seo github https://github.com/owner/repo'"
