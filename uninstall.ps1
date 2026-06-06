# ─────────────────────────────────────────────────────────────────────────────
#  todo — Windows uninstall script (PowerShell)
#  Usage:  .\uninstall.ps1
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

function Write-Info    { param($msg) Write-Host "  [>] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "  [+] $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host "  [x] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  ████████╗ ██████╗ ██████╗  ██████╗ " -ForegroundColor White
Write-Host "     ██╔══╝██╔═══██╗██╔══██╗██╔═══██╗" -ForegroundColor White
Write-Host "     ██║   ██║   ██║██║  ██║██║   ██║" -ForegroundColor White
Write-Host "     ██║   ██║   ██║██║  ██║██║   ██║" -ForegroundColor White
Write-Host "     ██║   ╚██████╔╝██████╔╝╚██████╔╝" -ForegroundColor White
Write-Host "     ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝ " -ForegroundColor White
Write-Host "  uninstall" -ForegroundColor DarkGray
Write-Host ""

# ── Locate installation ──────────────────────────────────────────────────────
Write-Info "Looking for todo..."
$todoCmd = Get-Command "todo" -ErrorAction SilentlyContinue
if (-not $todoCmd) {
    $paths = @("$env:ProgramFiles\todo\todo.bat", "$env:APPDATA\todo\todo.bat")
    foreach ($p in $paths) {
        if (Test-Path $p) { $todoCmd = @{Source = (Split-Path $p -Parent)}; break }
    }
}
if (-not $todoCmd) {
    Write-Err "todo not found on your system."
}

$installDir = if ($todoCmd.Source) { $todoCmd.Source } else { Split-Path $todoCmd.Source -Parent }

Write-Warn "This will remove todo from: $installDir"
Write-Host ""
$confirm = Read-Host "  Continue? [y/N]"
if ($confirm.ToLower() -ne "y") { Write-Host "  Aborted."; exit }

# ── Remove files ─────────────────────────────────────────────────────────────
Write-Info "Removing todo files..."
Remove-Item (Join-Path $installDir "todo.py") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $installDir "todo.bat") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $installDir "todo.cmd") -Force -ErrorAction SilentlyContinue
Write-Success "Removed todo from $installDir"

# ── Remove data directory ─────────────────────────────────────────────────────
$dataDir = "$env:APPDATA\todo"
if (Test-Path $dataDir) {
    Write-Host ""
    Write-Warn "Remove your task data at $dataDir?"
    $dataConfirm = Read-Host "  Remove all data? [y/N]"
    if ($dataConfirm.ToLower() -eq "y") {
        Remove-Item $dataDir -Recurse -Force
        Write-Success "Data removed."
    } else {
        Write-Warn "Data kept at $dataDir"
    }
}

# ── PATH cleanup (optional) ───────────────────────────────────────────────────
Write-Host ""
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -like "*$installDir*") {
    $pathAns = Read-Host "  Remove $installDir from your PATH? [y/N]"
    if ($pathAns.ToLower() -eq "y") {
        $newPath = ($userPath.Split(';') | Where-Object { $_ -ne $installDir }) -join ';'
        [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        Write-Success "Removed from PATH"
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
