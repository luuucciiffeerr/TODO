# ─────────────────────────────────────────────────────────────────────────────
#  todo — Windows install script (PowerShell)
#  Usage:  .\install.ps1
#  Or one-liner from GitHub:
#    irm https://raw.githubusercontent.com/luuucciiffeerr/TODO/main/install.ps1 | iex
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$VERSION = "1.0.0"
$REPO_URL = "https://raw.githubusercontent.com/luuucciiffeerr/TODO/main"

# ── Colours ──────────────────────────────────────────────────────────────────
function Write-Info    { param($msg) Write-Host "  [>] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "  [+] $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host "  [x] $msg" -ForegroundColor Red; exit 1 }

# ── Banner ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ████████╗ ██████╗ ██████╗  ██████╗ " -ForegroundColor White
Write-Host "     ██╔══╝██╔═══██╗██╔══██╗██╔═══██╗" -ForegroundColor White
Write-Host "     ██║   ██║   ██║██║  ██║██║   ██║" -ForegroundColor White
Write-Host "     ██║   ██║   ██║██║  ██║██║   ██║" -ForegroundColor White
Write-Host "     ██║   ╚██████╔╝██████╔╝╚██████╔╝" -ForegroundColor White
Write-Host "     ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝ " -ForegroundColor White
Write-Host "  ultra-light CLI task manager — v$VERSION" -ForegroundColor DarkGray
Write-Host ""

# ── Python check ─────────────────────────────────────────────────────────────
Write-Info "Checking Python..."
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd -c "import sys; print(sys.version_info >= (3, 8))" 2>$null
        if ($ver -eq "True") { $pythonCmd = $cmd; break }
    } catch {}
}
if (-not $pythonCmd) {
    Write-Err "Python 3.8+ not found. Install from https://python.org"
}
$pyVer = & $pythonCmd --version 2>&1
Write-Success "Found $pyVer"

# ── Optional: cryptography ────────────────────────────────────────────────────
Write-Host ""
Write-Info "Checking optional encryption support..."
$hasCrypto = & $pythonCmd -c "import cryptography; print('yes')" 2>$null
if ($hasCrypto -eq "yes") {
    Write-Success "cryptography installed — encryption available"
} else {
    Write-Warn "cryptography not installed (optional, enables 'todo --encrypt')"
    $ans = Read-Host "  Install now? [Y/n]"
    if (-not $ans -or $ans.ToLower() -eq "y") {
        & $pythonCmd -m pip install cryptography --quiet
        if ($LASTEXITCODE -eq 0) { Write-Success "cryptography installed" }
        else { Write-Warn "Install failed — run 'pip install cryptography' manually later" }
    }
}

# ── Locate or download todo.py ────────────────────────────────────────────────
Write-Host ""
Write-Info "Locating todo.py..."
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$todoPyLocal = Join-Path $scriptDir "todo.py"

if (Test-Path $todoPyLocal) {
    $todoPy = $todoPyLocal
    Write-Success "Found: $todoPy"
} else {
    Write-Info "Downloading from GitHub..."
    $tmpFile = [System.IO.Path]::GetTempFileName() + ".py"
    try {
        Invoke-WebRequest -Uri "$REPO_URL/todo.py" -OutFile $tmpFile -UseBasicParsing
        Write-Success "Downloaded todo.py"
    } catch {
        Write-Err "Download failed: $_"
    }
    $todoPy = $tmpFile
}

# ── Installation scope ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Installation type:" -ForegroundColor White
Write-Host "  1) Global   — all users (requires admin, installs to Program Files)"
Write-Host "  2) User     — this user only (installs to %APPDATA%\todo)"
Write-Host "  3) Custom   — specify your own directory"
Write-Host ""
$scope = Read-Host "  Choice [1/2/3, default=2]"
if (-not $scope) { $scope = "2" }

switch ($scope) {
    "1" {
        $installDir = "$env:ProgramFiles\todo"
        $isGlobal = $true
    }
    "3" {
        $custom = Read-Host "  Install directory"
        $installDir = $custom
        $isGlobal = $false
    }
    default {
        $installDir = "$env:APPDATA\todo"
        $isGlobal = $false
    }
}

# ── Install ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Info "Installing to $installDir..."

if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

Copy-Item $todoPy (Join-Path $installDir "todo.py") -Force

# Create wrapper batch file
$batContent = "@echo off`r`n$pythonCmd `"$installDir\todo.py`" %*"
$batContent | Out-File -FilePath (Join-Path $installDir "todo.bat") -Encoding ASCII -Force

# Also create a .cmd version for better compatibility
$cmdContent = "@echo off`r`n$pythonCmd `"$installDir\todo.py`" %*"
$cmdContent | Out-File -FilePath (Join-Path $installDir "todo.cmd") -Encoding ASCII -Force

Write-Success "Installed: $installDir\todo.bat"

# ── PATH setup ────────────────────────────────────────────────────────────────
Write-Host ""
$currentPath = if ($isGlobal) {
    [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
} else {
    [System.Environment]::GetEnvironmentVariable("PATH", "User")
}

if ($currentPath -notlike "*$installDir*") {
    Write-Warn "$installDir is not in your PATH"
    Write-Host ""
    $pathAns = Read-Host "  Add to PATH automatically? [Y/n]"
    if (-not $pathAns -or $pathAns.ToLower() -eq "y") {
        $newPath = "$installDir;$currentPath"
        if ($isGlobal) {
            try {
                [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
                Write-Success "Added to system PATH (all users)"
            } catch {
                Write-Warn "Could not set system PATH (run as Administrator)"
                [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
                Write-Success "Added to user PATH instead"
            }
        } else {
            [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
            Write-Success "Added to user PATH"
        }
        $env:PATH = "$installDir;$env:PATH"
        Write-Info "PATH updated for this session"
    }
} else {
    Write-Success "$installDir already in PATH"
}

# ── Verify ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Info "Verifying installation..."
try {
    & (Join-Path $installDir "todo.bat") --version
    Write-Success "todo is ready!"
} catch {
    Write-Warn "Installed, but verify by opening a new terminal and running 'todo --version'"
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  All done! Get started:" -ForegroundColor Green
Write-Host "    todo -a my first task" -ForegroundColor Cyan
Write-Host "    todo --help" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Data lives at: $env:APPDATA\todo\tasks.json" -ForegroundColor DarkGray
Write-Host "  Docs:          https://github.com/luuucciiffeerr/TODO" -ForegroundColor DarkGray
Write-Host ""
