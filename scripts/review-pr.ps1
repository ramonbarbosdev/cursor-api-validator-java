param(
    [Parameter(Mandatory = $true)]
    [string]$AppDir,
    [Parameter(Mandatory = $true)]
    [int]$Pr,
    [string]$Base = "develop",
    [ValidateSet("java-spring-esimples", "")]
    [string]$Stack = "java-spring-esimples"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$AppDir = (Resolve-Path $AppDir).Path

if (-not (Test-Path (Join-Path $AppDir ".git"))) {
    throw "AppDir não é repositório git: $AppDir"
}

$OutDir = Join-Path $AppDir ".api-validator-review"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Push-Location $AppDir

$prTitle = ""
$prBody = ""
$hasGh = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

if ($hasGh) {
    $prTitle = (gh pr view $Pr --json title -q .title) 2>$null
    $prBody = (gh pr view $Pr --json body -q .body) 2>$null
    gh pr checkout $Pr --force 2>$null
    if ($LASTEXITCODE -ne 0) { gh pr checkout $Pr }
} else {
    Write-Warning "gh não encontrado; git fetch pull/$Pr/head"
    git fetch origin "pull/$Pr/head:refs/heads/api-validator-pr-$Pr"
    git checkout "api-validator-pr-$Pr"
}

git fetch origin $Base 2>$null
$baseRef = "origin/$Base"
git rev-parse --verify $baseRef 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { $baseRef = $Base }

$headSha = (git rev-parse HEAD).Trim()
$diffStat = git diff --stat "$baseRef...HEAD" 2>$null
if (-not $diffStat) { $diffStat = git diff --stat $baseRef HEAD }

git diff "$baseRef...HEAD" 2>$null | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-diff.patch")
if (-not (Test-Path (Join-Path $OutDir "pr-$Pr-diff.patch")) -or (Get-Item (Join-Path $OutDir "pr-$Pr-diff.patch")).Length -eq 0) {
    git diff $baseRef HEAD | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-diff.patch")
}

$installArgs = @{ Target = $AppDir }
if ($Stack) { & (Join-Path $PackageRoot "install\install.ps1") -Target $AppDir -Stack $Stack }
else { & (Join-Path $PackageRoot "install\install.ps1") -Target $AppDir }

$specPath = ""
if (Test-Path (Join-Path $AppDir "docs\SPEC.md")) {
    $specPath = "docs/SPEC.md"
} elseif ($prBody -match 'docs/SPEC[^\s]+\.md') {
    $specPath = $Matches[0]
}

$meta = @{
    pr       = $Pr
    title    = $prTitle
    base     = $Base
    base_ref = $baseRef
    head_sha = $headSha
    spec_path = $specPath
    stack    = $Stack
} | ConvertTo-Json
$meta | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-meta.json")

$promptLines = @(
    "# Prompt — api-validator (PR #$Pr)",
    "",
    "**Título:** $prTitle",
    "**Base:** ``$baseRef`` · **HEAD:** ``$headSha``",
    "",
    "``````text",
    "/api-validator PR #$Pr — diff vs $baseRef."
)
if ($specPath) {
    $promptLines += "SPEC: $specPath — escopo ampliado se houver Contrato HTTP; validador inteligente."
} else {
    $promptLines += "Sem docs/SPEC.md na branch: gate enxuto (só diff), salvo escopo no corpo da PR."
}
$promptLines += @(
    "Seguir .cursor/agents/api-validator.md e .cursor/skills/revisao-api/SKILL.md.",
    "``````",
    "",
    "## git diff --stat",
    "``````",
    $diffStat,
    "``````",
    "",
    "Diff completo: ``.api-validator-review/pr-$Pr-diff.patch``"
)
if ($prBody) {
    $promptLines += "", "## Corpo da PR (referência)", $prBody
}
$promptLines -join "`n" | Out-File -Encoding utf8 (Join-Path $OutDir "pr-$Pr-prompt.md")

Pop-Location

Write-Host "OK: $OutDir\pr-$Pr-prompt.md"
Write-Host "Branch: $(git -C $AppDir branch --show-current) @ $headSha"
