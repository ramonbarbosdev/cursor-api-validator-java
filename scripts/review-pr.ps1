param(
    [Parameter(Mandatory = $true)]
    [string]$AppDir,
    [Parameter(Mandatory = $true)]
    [int]$Pr,
    [string]$Base = "develop",
    [ValidateSet("java-spring-esimples", "")]
    [string]$Stack = "java-spring-esimples",
    [switch]$SkipCheckout
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & git @Args 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "git $($Args -join ' ') falhou (exit $LASTEXITCODE)" }
}

$PackageRoot = Split-Path -Parent $PSScriptRoot
$AppDir = (Resolve-Path $AppDir).Path

if (-not (Test-Path (Join-Path $AppDir ".git"))) {
    throw "AppDir nao e repositorio git: $AppDir"
}

$OutDir = Join-Path $AppDir ".api-validator-review"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Push-Location $AppDir

$prTitle = ""
$prBody = ""
$hasGh = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

if ($SkipCheckout) {
    Write-Host "SkipCheckout: usando HEAD atual (ex.: checkout do Actions na PR)."
} elseif ($hasGh) {
    $prTitle = (gh pr view $Pr --json title -q .title) 2>$null
    $prBody = (gh pr view $Pr --json body -q .body) 2>$null
    gh pr checkout $Pr --force 2>$null
    if ($LASTEXITCODE -ne 0) { gh pr checkout $Pr }
} else {
    Write-Warning "gh nao encontrado; git fetch pull/$Pr/head"
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git fetch origin "pull/$Pr/head:refs/heads/api-validator-pr-$Pr" 2>&1 | Out-Null
    $ErrorActionPreference = $prev
    if ($LASTEXITCODE -ne 0) {
        & git fetch origin "pull/$Pr/head" 2>&1 | Out-Null
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Nao foi possivel buscar PR #$Pr (instale gh ou use -SkipCheckout no CI)."
    }
    Invoke-Git checkout "api-validator-pr-$Pr"
}

Invoke-Git fetch origin $Base
$baseRef = "origin/$Base"
& git rev-parse --verify $baseRef 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { $baseRef = $Base }

$headSha = (git rev-parse HEAD).Trim()
$diffStat = git diff --stat "$baseRef...HEAD" 2>&1
if (-not $diffStat) { $diffStat = git diff --stat $baseRef HEAD 2>&1 }

git diff "$baseRef...HEAD" 2>&1 | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-diff.patch")
if (-not (Test-Path (Join-Path $OutDir "pr-$Pr-diff.patch")) -or (Get-Item (Join-Path $OutDir "pr-$Pr-diff.patch")).Length -eq 0) {
    git diff $baseRef HEAD 2>&1 | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-diff.patch")
}

if ($Stack) {
    $install = Join-Path $PackageRoot "install\install.ps1"
    & $install -Target $AppDir -Stack $Stack
} else {
    & (Join-Path $PackageRoot "install\install.ps1") -Target $AppDir
}

$specPath = ""
if (Test-Path (Join-Path $AppDir "docs\SPEC.md")) {
    $specPath = "docs/SPEC.md"
} elseif ($prBody -match 'docs/SPEC[^\s]+\.md') {
    $specPath = $Matches[0]
}

$meta = @{
    pr        = $Pr
    title     = $prTitle
    base      = $Base
    base_ref  = $baseRef
    head_sha  = $headSha
    spec_path = $specPath
    stack     = $Stack
} | ConvertTo-Json
$meta | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-meta.json")

$fence = '```'
$promptLines = @(
    "# Prompt - api-validator (PR #$Pr)",
    "",
    "**Titulo:** $prTitle",
    "**Base:** $baseRef | **HEAD:** $headSha",
    "",
    $fence + "text",
    "/api-validator PR #$Pr - diff vs $baseRef."
)
if ($specPath) {
    $promptLines += "SPEC: $specPath - escopo ampliado se houver Contrato HTTP; validador inteligente."
} else {
    $promptLines += "Sem docs/SPEC.md na branch: gate enxuto (so diff)."
}
$promptLines += @(
    "Seguir .cursor/agents/api-validator.md e .cursor/skills/revisao-api/SKILL.md.",
    $fence,
    "",
    "## git diff --stat",
    $fence,
    $diffStat,
    $fence,
    "",
    "Diff completo: .api-validator-review/pr-$Pr-diff.patch"
)
if ($prBody) {
    $promptLines += "", "## Corpo da PR", $prBody
}
($promptLines -join [Environment]::NewLine) | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-prompt.md")

Pop-Location

Write-Host "OK: $OutDir\pr-$Pr-prompt.md"
Write-Host "Branch: $(git -C $AppDir branch --show-current) @ $headSha"
