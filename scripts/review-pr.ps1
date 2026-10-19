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
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git @Args 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { throw "git $($Args -join ' ') falhou (exit $code)" }
}

function Invoke-GitOut {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & git @Args 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { return $null }
    return $out
}

function Format-GitOut {
    param($Value)
    if ($null -eq $Value) { return "" }
    return ($Value | Out-String).Trim()
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
    if ($env:GITHUB_PR_TITLE) { $prTitle = $env:GITHUB_PR_TITLE.Trim() }
    if ($env:GITHUB_PR_BODY) { $prBody = $env:GITHUB_PR_BODY }
    if (-not $prTitle -and $hasGh) {
        $prTitle = (gh pr view $Pr --json title -q .title) 2>$null
        if (-not $prBody) { $prBody = (gh pr view $Pr --json body -q .body) 2>$null }
    }
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

if ($SkipCheckout) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git fetch origin $Base 2>&1 | Out-Null
    $ErrorActionPreference = $prev
} else {
    Invoke-Git fetch origin $Base
}
$baseRef = "origin/$Base"
if (-not (Invoke-GitOut rev-parse --verify $baseRef)) { $baseRef = $Base }

$headSha = Format-GitOut (Invoke-GitOut rev-parse HEAD)
$diffStat = Format-GitOut (Invoke-GitOut diff --stat "$baseRef...HEAD")
if (-not $diffStat) { $diffStat = Format-GitOut (Invoke-GitOut diff --stat $baseRef HEAD) }

$patch = Invoke-GitOut diff "$baseRef...HEAD"
if (-not $patch) { $patch = Invoke-GitOut diff $baseRef HEAD }
($patch | Out-String) | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-diff.patch")

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
