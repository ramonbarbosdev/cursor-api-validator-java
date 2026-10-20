<#
  Sobe o webhook local (igual ao fluxo SIPEC + ngrok).
  Copie scripts/env.pr-review.example para scripts/.env.pr-review e ajuste.
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $PSScriptRoot ".env.pr-review"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
        $n, $v = $_ -split '=', 2
        [Environment]::SetEnvironmentVariable($n.Trim(), $v.Trim(), "Process")
    }
}
if (-not $env:REPO_ROOT) {
    $sibling = Join-Path (Split-Path $root -Parent) "esimples-api"
    if (Test-Path (Join-Path $sibling "pom.xml")) { $env:REPO_ROOT = $sibling }
}
if (-not $env:CURSOR_API_VALIDATOR_ROOT) { $env:CURSOR_API_VALIDATOR_ROOT = $root }
$py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $py -3 (Join-Path $PSScriptRoot "pr_review_webhook.py")
