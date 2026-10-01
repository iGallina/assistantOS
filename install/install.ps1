# assistantOS — install on Windows. From the repo folder, in PowerShell:
#   powershell -ExecutionPolicy Bypass -File install\install.ps1
# Bypass applies to this one run only; the machine's script policy is not changed. Safe to run again.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$local = "$env:USERPROFILE\.local\bin"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:Path = "$local;$env:Path"
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    $env:Path = "$local;$env:Path"
}
uv sync --locked
uv run aos setup
exit $LASTEXITCODE
