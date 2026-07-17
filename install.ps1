<#
.SYNOPSIS
    Installs the GitGo CLI (pygitgo) on Windows.
.DESCRIPTION
    Windows counterpart to install.sh. Creates an isolated Python virtual
    environment under $HOME\.gitgo, installs pygitgo from PyPI into it, and
    adds the venv's Scripts folder to your user PATH.
.NOTES
    Run directly:
        powershell -ExecutionPolicy Bypass -File install.ps1

    Or as a one-liner (mirrors the curl | bash install on Linux/macOS):
        irm https://raw.githubusercontent.com/Huerte/GitGo/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

# Windows PowerShell 5.1 can default to TLS 1.0, which GitHub rejects.
[Net.ServicePointManager]::SecurityProtocol = `
    [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

function Write-Info    { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Err     { param($msg) Write-Host $msg -ForegroundColor Red }
function Write-Warn    { param($msg) Write-Host $msg -ForegroundColor Yellow }

function Show-Banner {
    Write-Host ""
    Write-Host "╭────────────────────────────────────────────╮" -ForegroundColor Green
    
    Write-Host "│" -ForegroundColor Green -NoNewline
    Write-Host "                 GitGo CLI                  " -ForegroundColor Green -NoNewline
    Write-Host "│" -ForegroundColor Green
    
    Write-Host "│" -ForegroundColor Green -NoNewline
    Write-Host "          " -NoNewline
    Write-Host "Your Fast Git Companion" -ForegroundColor Cyan -NoNewline
    Write-Host "           " -NoNewline
    Write-Host "│" -ForegroundColor Green
    
    Write-Host "╰────────────────────────────────────────────╯" -ForegroundColor Green
    Write-Host ""
}

Show-Banner

Write-Info "Installing GitGo CLI..."

# Prefer the "py" launcher over bare "python" - on Windows, "python" with no
# real interpreter installed resolves to the Microsoft Store alias stub.
function Get-PythonCommand {
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue)     { $candidates += [PSCustomObject]@{ Exe = "py";     Args = @("-3") } }
    if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += [PSCustomObject]@{ Exe = "python"; Args = @() } }

    foreach ($c in $candidates) {
        try {
            $verOutput = & $c.Exe @($c.Args) "-c" "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $verOutput) {
                $parts = $verOutput.Trim().Split(".")
                if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 8) {
                    return $c
                }
            }
        } catch {
            continue
        }
    }
    return $null
}

$python = Get-PythonCommand
if (-not $python) {
    Write-Err "Error: Python 3.8+ is required but wasn't found."
    Write-Host "Install it from https://www.python.org/downloads/ and check 'Add python.exe to PATH' during setup."
    Write-Host ""
    Write-Host "If typing 'python' opens the Microsoft Store instead of running Python,"
    Write-Host "disable the alias at: Settings > Apps > Advanced app settings > App execution aliases"
    exit 1
}

$InstallDir = Join-Path $HOME ".gitgo"
$VenvDir    = Join-Path $InstallDir "venv"
$ScriptsDir = Join-Path $VenvDir "Scripts"

if (Test-Path $VenvDir) {
    Write-Host "Removing previous installation..."
    Remove-Item -Recurse -Force $VenvDir
}

Write-Host "Creating isolated Python environment in $VenvDir..."
try {
    & $python.Exe @($python.Args) "-m" "venv" $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "venv creation exited with code $LASTEXITCODE" }
} catch {
    Write-Err "Failed to create virtual environment."
    Write-Host "Make sure your Python install includes the 'venv' module (bundled by default with python.org installers)."
    exit 1
}

$venvPython = Join-Path $ScriptsDir "python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Err "Virtual environment looks incomplete: $venvPython was not created."
    exit 1
}

Write-Host "Installing pygitgo from PyPI..."
& $venvPython "-m" "pip" "install" "--quiet" "--upgrade" "pip"
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to upgrade pip in the virtual environment."
    exit 1
}
& $venvPython "-m" "pip" "install" "--quiet" "--upgrade" "pygitgo"
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to install pygitgo from PyPI."
    exit 1
}

$gitgoExe = Join-Path $ScriptsDir "gitgo.exe"
if (-not (Test-Path $gitgoExe)) {
    Write-Err "pygitgo installed, but gitgo.exe wasn't found in $ScriptsDir."
    exit 1
}

Write-Success "`nGitGo installed successfully!`n"

$userPath    = [Environment]::GetEnvironmentVariable("Path", "User")
$pathEntries = @()
if ($userPath) { $pathEntries = $userPath -split ";" | Where-Object { $_ -ne "" } }

if ($pathEntries -notcontains $ScriptsDir) {
    $newPath = if ($userPath) { "$userPath;$ScriptsDir" } else { $ScriptsDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$env:Path;$ScriptsDir"

    Write-Warn "Added $ScriptsDir to your user PATH."
    Write-Host "Open a new terminal window for it to take effect, then run: gitgo -r"
} else {
    Write-Info "You can now run gitgo from anywhere."
    Write-Host "Try running: gitgo -r"
}

# Warn if another 'gitgo' earlier on PATH would shadow this install.
$resolved = (Get-Command gitgo -ErrorAction SilentlyContinue).Source
if ($resolved -and ($resolved -ne $gitgoExe)) {
    Write-Warn "Note: a different 'gitgo' was found earlier on PATH at:"
    Write-Host "  $resolved"
    Write-Host "That one will run instead of this install unless it's removed or your PATH is reordered."
}