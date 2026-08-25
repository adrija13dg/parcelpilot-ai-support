# ParcelPilot — production server (single process, UI + API on port 8000)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$LogDir = Join-Path $Root "logs"
$PidFile = Join-Path $Root ".parcelpilot.pid"
$Port = 8000

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-PortInUse($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "ParcelPilot is already running (PID $oldPid) -> http://localhost:$Port"
        exit 0
    }
}

if (Test-PortInUse $Port) {
    Write-Host "Port $Port is already in use. ParcelPilot may already be running."
    Write-Host "Open http://localhost:$Port"
    exit 0
}

$Dist = Join-Path $Root "frontend\dist\index.html"
if (-not (Test-Path $Dist)) {
    Write-Host "Building frontend (first time)..."
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Push-Location (Join-Path $Root "frontend")
    if (-not (Test-Path "node_modules")) { npm install }
    npm run build
    Pop-Location
}

$LogFile = Join-Path $LogDir "server.log"
$PyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($PyCmd) { $Py = $PyCmd.Source } else {
    $PyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($PyCmd) { $Py = $PyCmd.Source } else { throw "Python not found. Install Python 3.12+." }
}

Write-Host "Starting ParcelPilot on http://localhost:$Port ..."

$proc = Start-Process -FilePath $Py `
    -ArgumentList "-3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "$Port" `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError $LogFile `
    -PassThru

$proc.Id | Set-Content $PidFile
Start-Sleep -Seconds 3

if (Test-PortInUse $Port) {
    Write-Host "ParcelPilot is running -> http://localhost:$Port"
    Write-Host "Logs: $LogFile"
} else {
    Write-Host "Failed to start. Check $LogFile"
    exit 1
}
