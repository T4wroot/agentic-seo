#!/usr/bin/env pwsh

$ErrorActionPreference = 'Stop'

$REPO_URL        = if ($env:REPO_URL) { $env:REPO_URL } else { 'https://github.com/T4wroot/agentic-seo.git' }
$GITHUB_REPO     = if ($env:GITHUB_REPO) { $env:GITHUB_REPO } else { 'T4wroot/agentic-seo' }
$GITHUB_REF      = if ($env:GITHUB_REF)  { $env:GITHUB_REF }  else { 'main' }
$SKILL_NAME      = 'seo'
$TARGET          = 'claude'
$TARGET_EXPLICIT = $false
$PROJECT_DIR     = (Get-Location).Path
$PROJECT_DIR_EXPLICIT = $false
$FORCE           = $false
$INSTALL_DEPS    = $false
$INSTALL_PLAYWRIGHT = $false
$ONLINE_MODE     = $false
$SOURCE_MODE     = 'auto'
$REPO_PATH       = ''
$TEMP_DIR        = $null

# docs/ and tests/ are intentionally excluded â€” docs/ only holds README
# screenshots, and tests/ is for repository CI rather than installed skills.
$REQUIRED_PATHS  = @('SKILL.md', 'scripts', 'resources')

# Shared invocation block written into every IDE-native format file.
$SKILL_INVOCATION_TEXT = @'
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
2. Reason from explicit proof â€” every finding cites evidence.
3. Label confidence: Confirmed / Likely / Hypothesis.
4. Prioritise by impact and effort.
5. Produce a structured action plan (FULL-AUDIT-REPORT.md + ACTION-PLAN.md).

Read **SKILL.md** for the full multi-phase workflow.
'@

function Show-Usage {
@'
Agentic SEO Skill Installer (Windows / PowerShell)

Each IDE target installs the skill in that IDE's native format:
  claude / codex / antigravity  ->  skills\ directory  (native skill support)
  cowork                        ->  <project>\<skill>.plugin  (Cowork plugin file; import via Cowork UI)
  cursor                        ->  .cursor\rules\seo.mdc   (MDC rule)
  windsurf                      ->  .windsurf\rules\seo.md  (Windsurf rule)
  copilot                       ->  .github\copilot-instructions.md
  cline                         ->  .clinerules
  continue                      ->  .continue\prompts\seo.prompt

Usage:
  pwsh ./install.ps1 [options]

Options:
  --target <target>
      Install target (default: claude). Valid targets:
        claude       ->  ~\.claude\skills\seo
        codex        ->  ~\.codex\skills\seo
        antigravity  ->  <project>\.agent\skills\seo
        cowork       ->  <project>\seo.plugin  (Cowork plugin file; import via Cowork UI)
        cursor       ->  <project>\.cursor\rules\seo.mdc
        windsurf     ->  <project>\.windsurf\rules\seo.md
        continue     ->  <project>\.continue\prompts\seo.prompt
        copilot      ->  <project>\.github\copilot-instructions.md
        cline        ->  <project>\.clinerules
        global       ->  claude + codex (user-wide)
        project      ->  antigravity + cowork + cursor + windsurf + continue + copilot + cline
        all          ->  global + project (every target)

  --project-dir <path>         Project directory for project-local installs (default: cwd)
  --skill-name <name>          Installed folder name for skills-dir targets (default: seo)
  --repo-url <url>             Git URL for remote source installs
  --source <auto|local|remote> Source mode (default: auto)
  --repo-path <path>           Use a specific local checkout as the install source
  --online                     Fetch latest release zip from GitHub instead of cloning.
                               When no --target is supplied, defaults to --target all.
  --ref <branch-or-tag>        Branch / tag to fetch in --online mode (default: main)
  --install-deps               Install Python dependencies (requests, beautifulsoup4)
  --install-playwright         Also install Playwright + Chromium
  --force                      Overwrite an existing installed skill
  -h, --help                   Show this help

Examples:
  pwsh ./install.ps1 --target claude
  pwsh ./install.ps1 --target global
  pwsh ./install.ps1 --target project --project-dir C:\path\to\your\project
  pwsh ./install.ps1 --target cursor  --project-dir C:\path\to\your\project
  pwsh ./install.ps1 --target all     --project-dir C:\path\to\your\project
  pwsh ./install.ps1 --online
  pwsh ./install.ps1 --online --ref develop
'@ | Write-Host
}

function Require-Cmd {
    param([Parameter(Mandatory = $true)][string]$Cmd)
    if (-not (Get-Command -Name $Cmd -ErrorAction SilentlyContinue)) {
        throw "Error: required command not found: $Cmd"
    }
}

# Resolve a usable Python interpreter. Windows installs usually have `python` or
# the `py` launcher, not `python3`. Returns @{ Command = '...'; PrefixArgs = @() }
# so callers can do: & $py.Command @($py.PrefixArgs + @('-m','pip', ...))
$script:PYTHON_CACHE = $null
function Resolve-Python {
    if ($script:PYTHON_CACHE) { return $script:PYTHON_CACHE }
    foreach ($name in @('python3','python')) {
        if (Get-Command -Name $name -ErrorAction SilentlyContinue) {
            $script:PYTHON_CACHE = @{ Command = $name; PrefixArgs = @() }
            return $script:PYTHON_CACHE
        }
    }
    if (Get-Command -Name 'py' -ErrorAction SilentlyContinue) {
        $script:PYTHON_CACHE = @{ Command = 'py'; PrefixArgs = @('-3') }
        return $script:PYTHON_CACHE
    }
    throw "Error: no Python interpreter found. Install Python 3.8+ (tried: python3, python, py)"
}

function Resolve-Dir {
    param([Parameter(Mandatory = $true)][string]$Dir)
    if (-not (Test-Path -LiteralPath $Dir -PathType Container)) {
        throw "Error: directory not found: $Dir"
    }
    return (Resolve-Path -LiteralPath $Dir).Path
}

function Get-RelativePathCompat {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $baseFull = [System.IO.Path]::GetFullPath($BasePath)
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    $relativeMethod = [System.IO.Path].GetMethod(
        'GetRelativePath',
        [System.Reflection.BindingFlags]::Public -bor [System.Reflection.BindingFlags]::Static,
        $null,
        [Type[]]@([string], [string]),
        $null
    )
    if ($relativeMethod) {
        return [System.IO.Path]::GetRelativePath($baseFull, $pathFull)
    }
    if (-not $baseFull.EndsWith([System.IO.Path]::DirectorySeparatorChar) -and
        -not $baseFull.EndsWith([System.IO.Path]::AltDirectorySeparatorChar)) {
        $baseFull += [System.IO.Path]::DirectorySeparatorChar
    }
    $baseUri = [System.Uri]$baseFull
    $pathUri = [System.Uri]$pathFull
    $relativeUri = $baseUri.MakeRelativeUri($pathUri)
    $relative = [System.Uri]::UnescapeDataString($relativeUri.ToString())
    return $relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}

function Test-IsExcluded {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][bool]$IsDirectory
    )
    $rel = $RelativePath.Replace('\', '/')
    if ($rel.StartsWith('./')) { $rel = $rel.Substring(2) }
    while ($rel.StartsWith('/')) { $rel = $rel.Substring(1) }
    if ([string]::IsNullOrWhiteSpace($rel) -or $rel -eq '.') { return $false }
    $segments = $rel.Split('/', [System.StringSplitOptions]::RemoveEmptyEntries)

    if ($segments -contains '.git') { return $true }
    if ($segments -contains '.github') { return $true }
    if ($segments -contains 'tests') { return $true }
    if ($segments -contains 'tmp') { return $true }
    if ($segments -contains '__pycache__') { return $true }

    if (-not $IsDirectory) {
        $name = [System.IO.Path]::GetFileName($rel)
        if ($name -like '*.pyc') { return $true }
        if ($name -like 'seo-report-*.html') { return $true }
        if ($name -eq 'plan.md') { return $true }
    }
    return $false
}

# â”€â”€ Skills-directory copy (Claude / Codex / Antigravity / Cowork) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function Copy-Skill {
    param(
        [Parameter(Mandatory = $true)][string]$Src,
        [Parameter(Mandatory = $true)][string]$Dest,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ((Test-Path -LiteralPath $Dest) -and (-not $FORCE)) {
        Write-Warning "  $Label target already exists: $Dest`n  Use --force to overwrite."
        return
    }

    foreach ($req in $REQUIRED_PATHS) {
        $srcPath = Join-Path $Src $req
        if (-not (Test-Path -LiteralPath $srcPath)) {
            throw "Error: required skill path not found: $srcPath"
        }
    }

    $destParent = Split-Path -Path $Dest -Parent
    if ($destParent -and -not (Test-Path -LiteralPath $destParent)) {
        New-Item -ItemType Directory -Path $destParent -Force | Out-Null
    }
    if (Test-Path -LiteralPath $Dest) {
        Remove-Item -LiteralPath $Dest -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null

    foreach ($req in $REQUIRED_PATHS) {
        $srcReq = Join-Path $Src $req
        if (Test-Path -LiteralPath $srcReq -PathType Container) {
            $destReq = Join-Path $Dest $req
            New-Item -ItemType Directory -Path $destReq -Force | Out-Null
            Get-ChildItem -LiteralPath $srcReq -Force -Recurse | ForEach-Object {
                $item = $_
                $relative = Get-RelativePathCompat -BasePath $srcReq -Path $item.FullName
                $isDir = $item.PSIsContainer
                if (Test-IsExcluded -RelativePath $relative -IsDirectory $isDir) { return }
                $targetPath = Join-Path $destReq $relative
                if ($isDir) {
                    if (-not (Test-Path -LiteralPath $targetPath)) {
                        New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
                    }
                }
                else {
                    $targetParent = Split-Path -Path $targetPath -Parent
                    if ($targetParent -and -not (Test-Path -LiteralPath $targetParent)) {
                        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
                    }
                    Copy-Item -LiteralPath $item.FullName -Destination $targetPath -Force
                }
            }
        }
        else {
            Copy-Item -LiteralPath $srcReq -Destination (Join-Path $Dest $req) -Force
        }
    }

    Write-Host "  Installed for ${Label}: $Dest"
}

# â”€â”€ Root resolution helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function Get-GlobalRootForTool {
    param([Parameter(Mandatory = $true)][string]$Tool)
    switch ($Tool) {
        'claude'      { if ($env:CLAUDE_HOME) { return $env:CLAUDE_HOME } else { return (Join-Path $HOME '.claude') } }
        'codex'       { if ($env:CODEX_HOME)  { return $env:CODEX_HOME  } else { return (Join-Path $HOME '.codex')  } }
        'antigravity' { return (Join-Path $HOME '.gemini/antigravity') }
        default       { throw "Error: unsupported tool: $Tool" }
    }
}

function Get-WorkspaceRootForTool {
    param([Parameter(Mandatory = $true)][string]$Tool)
    switch ($Tool) {
        'antigravity' {
            if ($TARGET -eq 'antigravity' -or $PROJECT_DIR_EXPLICIT -or
                (Test-Path -LiteralPath (Join-Path $PROJECT_DIR '.agent') -PathType Container)) {
                return (Join-Path $PROJECT_DIR '.agent')
            }
        }
        'claude' {
            if ($PROJECT_DIR_EXPLICIT -and
                (Test-Path -LiteralPath (Join-Path $PROJECT_DIR '.claude') -PathType Container)) {
                return (Join-Path $PROJECT_DIR '.claude')
            }
        }
        'codex' {
            if ($PROJECT_DIR_EXPLICIT -and
                (Test-Path -LiteralPath (Join-Path $PROJECT_DIR '.codex') -PathType Container)) {
                return (Join-Path $PROJECT_DIR '.codex')
            }
        }
    }
    return $null
}

function Install-ToolAuto {
    param(
        [Parameter(Mandatory = $true)][string]$Src,
        [Parameter(Mandatory = $true)][string]$Tool,
        [Parameter(Mandatory = $true)][string]$SkillName
    )
    $wsRoot = Get-WorkspaceRootForTool -Tool $Tool
    if ($wsRoot) {
        $installRoot = $wsRoot
        $label = "${Tool}-local"
    }
    else {
        $installRoot = Get-GlobalRootForTool -Tool $Tool
        $label = "${Tool}-global"
    }
    $dest = Join-Path (Join-Path $installRoot 'skills') $SkillName
    Copy-Skill -Src $Src -Dest $dest -Label $label
}

function Install-ToolGlobal {
    param(
        [Parameter(Mandatory = $true)][string]$Src,
        [Parameter(Mandatory = $true)][string]$Tool,
        [Parameter(Mandatory = $true)][string]$SkillName
    )
    $installRoot = Get-GlobalRootForTool -Tool $Tool
    $dest = Join-Path (Join-Path $installRoot 'skills') $SkillName
    Copy-Skill -Src $Src -Dest $dest -Label "${Tool}-global"
}

# â”€â”€ IDE-native format installers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Cursor â€” .cursor\rules\seo.mdc  (MDC frontmatter format)
function Install-Cursor {
    param([Parameter(Mandatory = $true)][string]$Src)
    $rulesDir = Join-Path $PROJECT_DIR '.cursor/rules'
    $mdcFile  = Join-Path $rulesDir 'seo.mdc'

    if ((Test-Path -LiteralPath $mdcFile -PathType Leaf) -and (-not $FORCE)) {
        Write-Warning "  Cursor rule already exists: $mdcFile (use --force to overwrite)"
    }
    else {
        New-Item -ItemType Directory -Path $rulesDir -Force | Out-Null
        $header = @'
---
description: "Agentic SEO skill. Activate when the user asks to perform SEO analysis, audit a URL/repo, review technical SEO, schema, Core Web Vitals, E-E-A-T, GEO, AEO, or hreflang."
globs: []
alwaysApply: false
---

'@
        Set-Content -LiteralPath $mdcFile -Value ($header + $SKILL_INVOCATION_TEXT)
        Write-Host "  Installed Cursor rule: $mdcFile"
    }

    $dest = Join-Path (Join-Path $PROJECT_DIR '.cursor/skills') $SKILL_NAME
    try { Copy-Skill -Src $Src -Dest $dest -Label 'Cursor (.cursor/skills/)' } catch { Write-Warning "Skipped skill copy: $_" }
}

# Windsurf â€” .windsurf\rules\seo.md
function Install-Windsurf {
    param([Parameter(Mandatory = $true)][string]$Src)
    $rulesDir  = Join-Path $PROJECT_DIR '.windsurf/rules'
    $ruleFile  = Join-Path $rulesDir 'seo.md'

    if ((Test-Path -LiteralPath $ruleFile -PathType Leaf) -and (-not $FORCE)) {
        Write-Warning "  Windsurf rule already exists: $ruleFile (use --force to overwrite)"
    }
    else {
        New-Item -ItemType Directory -Path $rulesDir -Force | Out-Null
        Set-Content -LiteralPath $ruleFile -Value $SKILL_INVOCATION_TEXT
        Write-Host "  Installed Windsurf rule: $ruleFile"
    }

    $dest = Join-Path (Join-Path $PROJECT_DIR '.windsurf/skills') $SKILL_NAME
    try { Copy-Skill -Src $Src -Dest $dest -Label 'Windsurf (.windsurf/skills/)' } catch { Write-Warning "Skipped skill copy: $_" }
}

# Continue.dev â€” .continue\prompts\seo.prompt
function Install-Continue {
    param([Parameter(Mandatory = $true)][string]$Src)
    $promptsDir = Join-Path $PROJECT_DIR '.continue/prompts'
    $promptFile = Join-Path $promptsDir 'seo.prompt'

    if ((Test-Path -LiteralPath $promptFile -PathType Leaf) -and (-not $FORCE)) {
        Write-Warning "  Continue prompt already exists: $promptFile (use --force to overwrite)"
    }
    else {
        New-Item -ItemType Directory -Path $promptsDir -Force | Out-Null
        $promptContent = @'
name: seo
description: Run Agentic SEO analysis on the supplied URL, blog post, or GitHub repository
---
You have the Agentic SEO skill loaded.

{{{ input }}}

Use the full SEO workflow:
1. Identify the audit target (URL, page, article, or GitHub repo) from the user's request.
2. Collect evidence first (read_url_content, then bundled scripts as needed).
3. Run the appropriate sub-skill (audit / page / article / technical / content / schema /
   sitemap / images / geo / aeo / links / hreflang / github / plan).
4. Apply the llm-audit-rubric: evidence -> impact -> fix, with confidence labels.
5. Produce FULL-AUDIT-REPORT.md and ACTION-PLAN.md with prioritised fixes.

Read SKILL.md for the complete multi-phase workflow.
'@
        Set-Content -LiteralPath $promptFile -Value $promptContent
        Write-Host "  Installed Continue.dev prompt: $promptFile"
    }

    $dest = Join-Path (Join-Path $PROJECT_DIR '.continue/skills') $SKILL_NAME
    try { Copy-Skill -Src $Src -Dest $dest -Label 'Continue.dev (.continue/skills/)' } catch { Write-Warning "Skipped skill copy: $_" }
}

# GitHub Copilot â€” .github\copilot-instructions.md
function Install-Copilot {
    param([Parameter(Mandatory = $true)][string]$Src)
    $githubDir       = Join-Path $PROJECT_DIR '.github'
    $instructionFile = Join-Path $githubDir 'copilot-instructions.md'
    New-Item -ItemType Directory -Path $githubDir -Force | Out-Null

    if (Test-Path -LiteralPath $instructionFile -PathType Leaf) {
        $existing = Get-Content -LiteralPath $instructionFile -Raw -ErrorAction SilentlyContinue
        if ($existing -like '*Agentic SEO Skill*') {
            Write-Host "  GitHub Copilot instructions already contain Agentic SEO Skill (skipping)"
        }
        else {
            Add-Content -LiteralPath $instructionFile -Value ("`n---`n`n" + $SKILL_INVOCATION_TEXT)
            Write-Host "  Updated GitHub Copilot instructions: $instructionFile"
        }
    }
    else {
        Set-Content -LiteralPath $instructionFile -Value $SKILL_INVOCATION_TEXT
        Write-Host "  Created GitHub Copilot instructions: $instructionFile"
    }

    $dest = Join-Path (Join-Path $githubDir 'skills') $SKILL_NAME
    try { Copy-Skill -Src $Src -Dest $dest -Label 'GitHub Copilot (.github/skills/)' } catch { Write-Warning "Skipped skill copy: $_" }
}

# Claude Cowork â€” packages the skill as a .plugin file (zip) for import via Cowork UI
# Structure: .claude-plugin\plugin.json  +  skills\<name>\  (not .claude\skills\)
function Install-Cowork {
    param([Parameter(Mandatory = $true)][string]$Src)
    $pluginFile = Join-Path $PROJECT_DIR "$SKILL_NAME.plugin"

    if ((Test-Path -LiteralPath $pluginFile -PathType Leaf) -and (-not $FORCE)) {
        Write-Warning "  Cowork plugin already exists: $pluginFile`n  Use --force to overwrite."
        return
    }

    # Build plugin structure in a temp directory
    $buildDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path (Join-Path $buildDir '.claude-plugin') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $buildDir "skills\$SKILL_NAME") -Force | Out-Null

    # Manifest goes in .claude-plugin\plugin.json (NOT at the plugin root)
    $manifest = "{`n  `"name`": `"$SKILL_NAME`",`n  `"version`": `"1.0.0`",`n  `"description`": `"LLM-first SEO audits for websites, blog posts, and GitHub repos`"`n}"
    Set-Content -LiteralPath (Join-Path $buildDir '.claude-plugin\plugin.json') -Value $manifest -Encoding UTF8

    # Populate skill files using Copy-Skill (handles all exclusions)
    Copy-Skill -Src $Src -Dest (Join-Path $buildDir "skills\$SKILL_NAME") -Label 'Cowork plugin build'

    # Ensure output directory exists
    if (-not (Test-Path -LiteralPath $PROJECT_DIR)) {
        New-Item -ItemType Directory -Path $PROJECT_DIR -Force | Out-Null
    }
    if (Test-Path -LiteralPath $pluginFile) { Remove-Item -LiteralPath $pluginFile -Force }

    # Compress-Archive rejects non-.zip extensions; ZipFile has no such restriction
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($buildDir, $pluginFile)

    Remove-Item -LiteralPath $buildDir -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "  Created Cowork plugin: $pluginFile"
    Write-Host ''
    Write-Host '  To install in Cowork:'
    Write-Host '    1. Open claude.ai -> Cowork'
    Write-Host '    2. Go to Customize -> Plugins -> Install from file'
    Write-Host "    3. Select: $pluginFile"
}

# Cline â€” .clinerules
function Install-Cline {
    param([Parameter(Mandatory = $true)][string]$Src)
    $rulesFile = Join-Path $PROJECT_DIR '.clinerules'
    $marker    = '<!-- agentic-seo-skill -->'

    if ((Test-Path -LiteralPath $rulesFile -PathType Leaf) -and
        ((Get-Content -LiteralPath $rulesFile -Raw) -like '*agentic-seo-skill*')) {
        if (-not $FORCE) {
            Write-Warning "  .clinerules already contains Agentic SEO Skill (use --force to overwrite)"
            return
        }
        else {
            $text = Get-Content -LiteralPath $rulesFile -Raw
            $text = [regex]::Replace($text, '<!-- agentic-seo-skill -->.*?<!-- /agentic-seo-skill -->\r?\n?', '', [System.Text.RegularExpressions.RegexOptions]::Singleline)
            Set-Content -LiteralPath $rulesFile -Value $text
        }
    }

    $block = "`n${marker}`n" + $SKILL_INVOCATION_TEXT + "`n<!-- /agentic-seo-skill -->`n"
    Add-Content -LiteralPath $rulesFile -Value $block
    Write-Host "  Updated .clinerules: $rulesFile"

    $dest = Join-Path (Join-Path $PROJECT_DIR '.cline/skills') $SKILL_NAME
    try { Copy-Skill -Src $Src -Dest $dest -Label 'Cline (.cline/skills/)' } catch { Write-Warning "Skipped skill copy: $_" }
}

# â”€â”€ Argument parsing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

$idx = 0
while ($idx -lt $args.Count) {
    $arg = $args[$idx]
    switch ($arg) {
        '--target' {
            if (($idx + 1) -ge $args.Count) { throw 'Error: missing value for --target' }
            $TARGET = $args[$idx + 1]; $TARGET_EXPLICIT = $true; $idx += 2; continue
        }
        '--project-dir' {
            if (($idx + 1) -ge $args.Count) { throw 'Error: missing value for --project-dir' }
            $PROJECT_DIR = $args[$idx + 1]; $PROJECT_DIR_EXPLICIT = $true; $idx += 2; continue
        }
        '--skill-name' {
            if (($idx + 1) -ge $args.Count) { throw 'Error: missing value for --skill-name' }
            $SKILL_NAME = $args[$idx + 1]; $idx += 2; continue
        }
        '--repo-url' {
            if (($idx + 1) -ge $args.Count) { throw 'Error: missing value for --repo-url' }
            $REPO_URL = $args[$idx + 1]; $idx += 2; continue
        }
        '--source' {
            if (($idx + 1) -ge $args.Count) { throw 'Error: missing value for --source' }
            $SOURCE_MODE = $args[$idx + 1]; $idx += 2; continue
        }
        '--repo-path' {
            if (($idx + 1) -ge $args.Count) { throw 'Error: missing value for --repo-path' }
            $REPO_PATH = $args[$idx + 1]; $idx += 2; continue
        }
        '--ref' {
            if (($idx + 1) -ge $args.Count) { throw 'Error: missing value for --ref' }
            $GITHUB_REF = $args[$idx + 1]; $idx += 2; continue
        }
        '--install-deps'       { $INSTALL_DEPS = $true; $idx += 1; continue }
        '--install-playwright' { $INSTALL_PLAYWRIGHT = $true; $INSTALL_DEPS = $true; $idx += 1; continue }
        '--online'             { $ONLINE_MODE = $true; $FORCE = $true; $idx += 1; continue }
        '--force'              { $FORCE = $true; $idx += 1; continue }
        '-h'                   { Show-Usage; exit 0 }
        '--help'               { Show-Usage; exit 0 }
        default {
            Show-Usage
            throw "Unknown option: $arg"
        }
    }
}

$VALID_TARGETS = @('claude','codex','antigravity','cowork','cursor','windsurf','continue','copilot','cline','global','project','all')
if ($TARGET -notin $VALID_TARGETS) {
    throw "Error: invalid --target: $TARGET`nValid targets: $($VALID_TARGETS -join ', ')"
}
if ($SOURCE_MODE -notin @('auto','local','remote')) {
    throw "Error: invalid --source: $SOURCE_MODE"
}
if ($ONLINE_MODE -and (-not $TARGET_EXPLICIT)) { $TARGET = 'all' }

$PY = Resolve-Python

$SCRIPT_DIR  = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$SRC_DIR     = ''
$SHOULD_CLONE = $false

# â”€â”€ Source resolution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if ($ONLINE_MODE) {
    $TEMP_DIR    = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString('N'))
    $extractRoot = Join-Path $TEMP_DIR 'extracted'
    New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null
    $zipPath     = Join-Path $TEMP_DIR 'package.zip'

    # Resolve a download URL. Preference order:
    #   1. Latest release asset listed by the GitHub API (any filename).
    #   2. Source archive for the latest release tag.
    #   3. Branch archive for $GITHUB_REF.
    Write-Host "Fetching latest release info from $GITHUB_REPO..."
    $downloadUrl = $null
    $downloadDesc = $null
    try {
        $releaseInfo = Invoke-RestMethod `
            -Uri "https://api.github.com/repos/$GITHUB_REPO/releases/latest" `
            -ErrorAction Stop
        $latestTag = $releaseInfo.tag_name
        if (-not [string]::IsNullOrWhiteSpace($latestTag)) {
            Write-Host "  Latest release: $latestTag"
            # Expand-Archive only handles .zip â€” never pick a .tar.gz asset
            # here even if one is listed first by the API.
            $asset = $releaseInfo.assets |
                Where-Object { $_.name -match '\.zip$' } |
                Select-Object -First 1
            if ($asset) {
                $downloadUrl  = $asset.browser_download_url
                $downloadDesc = "release asset: $($asset.name)"
            }
            else {
                $downloadUrl  = "https://github.com/$GITHUB_REPO/archive/refs/tags/$latestTag.zip"
                $downloadDesc = "source archive for tag $latestTag"
            }
        }
    }
    catch {
        # API call failed â€” fall through to branch archive below.
    }
    if (-not $downloadUrl) {
        $downloadUrl  = "https://github.com/$GITHUB_REPO/archive/refs/heads/$GITHUB_REF.zip"
        $downloadDesc = "branch archive: $GITHUB_REF"
    }
    Write-Host "  Downloading $downloadDesc..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -ErrorAction Stop

    # Expand-Archive's default error action is Continue on PS 5.1 â€” make it
    # fatal so a bad download surfaces here, not as "SKILL.md not found".
    Expand-Archive -Path $zipPath -DestinationPath $extractRoot -Force -ErrorAction Stop
    Remove-Item -Path $zipPath -Force

    # Locate SKILL.md. Release-asset zips may be flat (SKILL.md at the root);
    # GitHub source archives nest contents under one top-level dir like
    # `Repo-Tag/`. Support either.
    if (Test-Path -LiteralPath (Join-Path $extractRoot 'SKILL.md') -PathType Leaf) {
        $SRC_DIR = $extractRoot
    }
    else {
        $found = Get-ChildItem -LiteralPath $extractRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') -PathType Leaf } |
            Select-Object -First 1
        if (-not $found) {
            $entries = (
                Get-ChildItem -LiteralPath $extractRoot -Force -ErrorAction SilentlyContinue |
                    Select-Object -First 15 |
                    ForEach-Object { $_.Name }
            ) -join ', '
            throw "Error: downloaded archive did not contain SKILL.md.`n  Source URL: $downloadUrl`n  Extract dir: $extractRoot`n  Top-level entries: $entries"
        }
        $SRC_DIR = $found.FullName
    }
    Write-Host "Using downloaded package source: $SRC_DIR"
}
elseif (-not [string]::IsNullOrWhiteSpace($REPO_PATH)) {
    $SRC_DIR = Resolve-Dir -Dir $REPO_PATH
    Write-Host "Using repo path source: $SRC_DIR"
}
elseif ($SOURCE_MODE -eq 'local') {
    $SRC_DIR = $SCRIPT_DIR
    Write-Host "Using local source: $SRC_DIR"
}
elseif ($SOURCE_MODE -eq 'remote') {
    $SHOULD_CLONE = $true
}
elseif (Test-Path -LiteralPath (Join-Path $SCRIPT_DIR 'SKILL.md') -PathType Leaf) {
    $SRC_DIR = $SCRIPT_DIR
    Write-Host "Using local source: $SRC_DIR"
}
else {
    $SHOULD_CLONE = $true
}

try {
    if ($SHOULD_CLONE) {
        # Resolve git to its real executable (not a PS alias, not a profile
        # function) so the call operator below is guaranteed to invoke the
        # real git binary / .cmd shim.
        $gitCmd = Get-Command -Name 'git' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $gitCmd) {
            throw "Error: git executable not found on PATH. Install Git for Windows (https://git-scm.com/download/win) or pass --online to download a release archive instead."
        }
        $gitExe = $gitCmd.Source

        $TEMP_DIR = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $TEMP_DIR -Force | Out-Null
        $cloneDir = Join-Path $TEMP_DIR 'repo'
        Write-Host "Cloning source repo: $REPO_URL"
        Write-Host "  using git:   $gitExe"
        Write-Host "  destination: $cloneDir"

        # Direct invocation â€” git's stdout/stderr stream through to the user.
        # No wrapper function (would otherwise capture stdout into a variable
        # and leave the user wondering whether git actually ran).
        & $gitExe clone --depth 1 $REPO_URL $cloneDir
        $cloneExit = $LASTEXITCODE

        if ($cloneExit -ne 0) {
            throw "Error: git clone exited with code $cloneExit.`nTip: pass --online to download a release archive instead of cloning."
        }
        if (-not (Test-Path -LiteralPath $cloneDir -PathType Container)) {
            throw "Error: git clone reported success but did not create the destination directory: $cloneDir"
        }
        $SRC_DIR = $cloneDir
        Write-Host "Using remote source: $SRC_DIR"
    }

    if (-not (Test-Path -LiteralPath (Join-Path $SRC_DIR 'SKILL.md') -PathType Leaf)) {
        $listing = ''
        if (Test-Path -LiteralPath $SRC_DIR -PathType Container) {
            $entries = Get-ChildItem -LiteralPath $SRC_DIR -Force -ErrorAction SilentlyContinue |
                Select-Object -First 15 |
                ForEach-Object { $_.Name }
            if ($entries) { $listing = "`n  Source dir contents (first 15): $($entries -join ', ')" }
            else { $listing = "`n  Source dir is empty." }
        }
        else {
            $listing = "`n  Source dir does not exist on disk."
        }
        throw "Error: SKILL.md not found in source directory: $SRC_DIR$listing"
    }

    Write-Host ''
    Write-Host 'Installing Agentic SEO Skill'
    Write-Host "Target:     $TARGET"
    Write-Host "Skill name: $SKILL_NAME"
    Write-Host ''

    # â”€â”€ Install per target â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    switch ($TARGET) {
        'claude'      { Install-ToolAuto  -Src $SRC_DIR -Tool 'claude'      -SkillName $SKILL_NAME }
        'codex'       { Install-ToolAuto  -Src $SRC_DIR -Tool 'codex'       -SkillName $SKILL_NAME }
        'antigravity' { Install-ToolAuto  -Src $SRC_DIR -Tool 'antigravity' -SkillName $SKILL_NAME }
        'cowork'      { Install-Cowork    -Src $SRC_DIR }
        'cursor'      { Install-Cursor    -Src $SRC_DIR }
        'windsurf'    { Install-Windsurf  -Src $SRC_DIR }
        'continue'    { Install-Continue  -Src $SRC_DIR }
        'copilot'     { Install-Copilot   -Src $SRC_DIR }
        'cline'       { Install-Cline     -Src $SRC_DIR }
        'global' {
            try { Install-ToolGlobal -Src $SRC_DIR -Tool 'claude' -SkillName $SKILL_NAME } catch { Write-Warning "Skipped claude-global: $_" }
            try { Install-ToolGlobal -Src $SRC_DIR -Tool 'codex'  -SkillName $SKILL_NAME } catch { Write-Warning "Skipped codex-global: $_" }
        }
        'project' {
            try { Install-ToolAuto -Src $SRC_DIR -Tool 'antigravity' -SkillName $SKILL_NAME } catch { Write-Warning "Skipped antigravity: $_" }
            try { Install-Cowork   -Src $SRC_DIR }                                            catch { Write-Warning "Skipped cowork: $_" }
            try { Install-Cursor   -Src $SRC_DIR }                                            catch { Write-Warning "Skipped cursor: $_" }
            try { Install-Windsurf -Src $SRC_DIR }                                            catch { Write-Warning "Skipped windsurf: $_" }
            try { Install-Continue -Src $SRC_DIR }                                            catch { Write-Warning "Skipped continue: $_" }
            try { Install-Copilot  -Src $SRC_DIR }                                            catch { Write-Warning "Skipped copilot: $_" }
            try { Install-Cline    -Src $SRC_DIR }                                            catch { Write-Warning "Skipped cline: $_" }
        }
        'all' {
            try { Install-ToolGlobal -Src $SRC_DIR -Tool 'claude' -SkillName $SKILL_NAME }   catch { Write-Warning "Skipped claude-global: $_" }
            try { Install-ToolGlobal -Src $SRC_DIR -Tool 'codex'  -SkillName $SKILL_NAME }   catch { Write-Warning "Skipped codex-global: $_" }
            try { Install-ToolAuto -Src $SRC_DIR -Tool 'antigravity' -SkillName $SKILL_NAME } catch { Write-Warning "Skipped antigravity: $_" }
            try { Install-Cowork   -Src $SRC_DIR }                                            catch { Write-Warning "Skipped cowork: $_" }
            try { Install-Cursor   -Src $SRC_DIR }                                            catch { Write-Warning "Skipped cursor: $_" }
            try { Install-Windsurf -Src $SRC_DIR }                                            catch { Write-Warning "Skipped windsurf: $_" }
            try { Install-Continue -Src $SRC_DIR }                                            catch { Write-Warning "Skipped continue: $_" }
            try { Install-Copilot  -Src $SRC_DIR }                                            catch { Write-Warning "Skipped copilot: $_" }
            try { Install-Cline    -Src $SRC_DIR }                                            catch { Write-Warning "Skipped cline: $_" }
        }
    }

    # â”€â”€ Python dependencies â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    if ($INSTALL_DEPS) {
        Write-Host ''
        Write-Host 'Installing Python dependencies...'

        # Direct invocation so pip's progress is visible. Splat the prefix
        # args (e.g. '-3' for the `py` launcher) ahead of the pip command.
        $reqPath = Join-Path $SRC_DIR 'requirements.txt'
        $depsInstalled = $false

        if (Test-Path -LiteralPath $reqPath) {
            & $PY.Command @($PY.PrefixArgs) -m pip install --user -r $reqPath
            if ($LASTEXITCODE -eq 0) {
                Write-Host '  Installed dependencies from requirements.txt'
                $depsInstalled = $true
            }
        }
        if (-not $depsInstalled) {
            & $PY.Command @($PY.PrefixArgs) -m pip install --user requests beautifulsoup4
            if ($LASTEXITCODE -eq 0) {
                Write-Host '  Installed requests + beautifulsoup4'
                $depsInstalled = $true
            }
        }
        if (-not $depsInstalled) {
            $pyCli = ($PY.Command + ' ' + ($PY.PrefixArgs -join ' ')).Trim()
            Write-Warning "  Could not auto-install Python dependencies. Install manually:`n    $pyCli -m pip install --user requests beautifulsoup4"
        }

        if ($INSTALL_PLAYWRIGHT) {
            $playwrightOk = $false
            & $PY.Command @($PY.PrefixArgs) -m pip install --user playwright
            if ($LASTEXITCODE -eq 0) {
                & $PY.Command @($PY.PrefixArgs) -m playwright install chromium
                $playwrightOk = ($LASTEXITCODE -eq 0)
            }
            if ($playwrightOk) {
                Write-Host '  Installed Playwright + Chromium'
            }
            else {
                $pyCli = ($PY.Command + ' ' + ($PY.PrefixArgs -join ' ')).Trim()
                Write-Warning "  Could not auto-install Playwright. Install manually:`n    $pyCli -m pip install --user playwright`n    $pyCli -m playwright install chromium"
            }
        }
    }

    Write-Host ''
    Write-Host 'Install complete.'
    Write-Host ''
    Write-Host 'Next steps:'
    Write-Host '  1. Restart your IDE/agent session to pick up the skill.'
    Write-Host "  2. Ask: 'perform seo analysis on https://example.com'"
    Write-Host "  3. Or:  'seo github https://github.com/owner/repo'"
}
finally {
    if ($TEMP_DIR -and (Test-Path -LiteralPath $TEMP_DIR)) {
        Remove-Item -LiteralPath $TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
    }
}
