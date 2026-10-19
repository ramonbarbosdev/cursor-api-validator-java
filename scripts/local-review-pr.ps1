<#
.SYNOPSIS
  Máquina local: prepara review da PR (ou da branch atual) no esimples-api.

.EXAMPLE
  cd C:\...\esimples-api
  ..\cursor-api-validator-java\scripts\local-review-pr.ps1 -Pr 123

.EXAMPLE
  # Já na branch da PR, sem número (só diff vs develop):
  ..\cursor-api-validator-java\scripts\local-review-pr.ps1
#>
param(
    [int]$Pr = 0,
    [string]$AppDir = "",
    [string]$Base = "develop",
    [string]$ValidatorRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $AppDir) {
    $here = (Get-Location).Path
    if (Test-Path (Join-Path $here "pom.xml")) { $AppDir = $here }
    else { throw "Execute na raiz do esimples-api ou passe -AppDir." }
}
$AppDir = (Resolve-Path $AppDir).Path

if (-not $ValidatorRoot) {
    $sibling = Join-Path (Split-Path $AppDir -Parent) "cursor-api-validator-java"
    if (Test-Path $sibling) { $ValidatorRoot = $sibling }
    elseif ($env:CURSOR_API_VALIDATOR_ROOT) { $ValidatorRoot = $env:CURSOR_API_VALIDATOR_ROOT }
    else { throw "Não encontrei cursor-api-validator-java. Passe -ValidatorRoot ou defina CURSOR_API_VALIDATOR_ROOT." }
}
$ValidatorRoot = (Resolve-Path $ValidatorRoot).Path

$reviewScript = Join-Path $ValidatorRoot "scripts\review-pr.ps1"
if (-not (Test-Path $reviewScript)) { throw "Falta $reviewScript" }

if ($Pr -gt 0) {
    & $reviewScript -AppDir $AppDir -Pr $Pr -Base $Base -Stack java-spring-esimples
    $prompt = Join-Path $AppDir ".api-validator-review\pr-$Pr-prompt.md"
} else {
    Push-Location $AppDir
    git fetch origin $Base 2>$null
    $baseRef = "origin/$Base"
    git rev-parse --verify $baseRef 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { $baseRef = $Base }

    $install = Join-Path $ValidatorRoot "install\install.ps1"
    & $install -Target $AppDir -Stack java-spring-esimples

    $branch = (git branch --show-current).Trim()
    $headSha = (git rev-parse HEAD).Trim()
    $diffStat = git diff --stat "$baseRef...HEAD" 2>$null
    if (-not $diffStat) { $diffStat = git diff --stat $baseRef HEAD }

    $outDir = Join-Path $AppDir ".api-validator-review"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    git diff "$baseRef...HEAD" 2>$null | Out-File -Encoding utf8 (Join-Path $outDir "branch-diff.patch")
    if (-not (Get-Item (Join-Path $outDir "branch-diff.patch")).Length) {
        git diff $baseRef HEAD | Out-File -Encoding utf8 (Join-Path $outDir "branch-diff.patch")
    }

    $specLine = "Sem docs/SPEC.md: gate enxuto (só diff)."
    if (Test-Path (Join-Path $AppDir "docs\SPEC.md")) {
        $specLine = "SPEC: docs/SPEC.md — escopo ampliado se houver Contrato HTTP; validador inteligente."
    }

    $prompt = Join-Path $outDir "branch-prompt.md"
    @"
# Prompt — api-validator (branch local)

**Branch:** ``$branch`` · **Base:** ``$baseRef`` · **HEAD:** ``$headSha``

``````text
/api-validator branch $branch — diff vs $baseRef.
$specLine
Seguir .cursor/agents/api-validator.md e .cursor/skills/revisao-api/SKILL.md — somente relatório.
``````

## git diff --stat
``````
$diffStat
``````

Diff: ``.api-validator-review/branch-diff.patch``
"@ | Out-File -Encoding utf8 $prompt
    Pop-Location
}

Write-Host ""
Write-Host "=== Próximo passo (Cursor) ===" -ForegroundColor Cyan
Write-Host "1. Abra a pasta esimples-api no Cursor (esta janela)."
Write-Host "2. Chat -> /api-validator"
Write-Host "3. Cole o conteúdo de:" -ForegroundColor Yellow
Write-Host "   $prompt"
Write-Host ""
if ($Pr -gt 0 -and -not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Dica: instale GitHub CLI (gh) para checkout automático da PR." -ForegroundColor DarkYellow
}
