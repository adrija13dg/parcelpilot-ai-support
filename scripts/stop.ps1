# Stop ParcelPilot background server
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PidFile = Join-Path $Root ".parcelpilot.pid"

if (Test-Path $PidFile) {
    $processId = Get-Content $PidFile
    $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $processId -Force
        Write-Host "Stopped ParcelPilot (PID $processId)"
    }
    Remove-Item $PidFile -Force
} else {
    Write-Host "No PID file found. Trying port 8000..."
    Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Write-Host "Done."
}
