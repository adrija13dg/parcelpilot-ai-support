# Remove ParcelPilot from Windows autostart
$TaskName = "ParcelPilot-AI-Support"
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Autostart disabled."
$StopScript = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "stop.ps1"
& $StopScript
