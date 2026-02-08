# Islamic PWA Sync Server - Windows Service Installer
# Run as Administrator: powershell -ExecutionPolicy Bypass -File install_service.ps1

$ErrorActionPreference = "Stop"

$ServerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    exit 1
}

$TaskName = "IslamicPWASyncServer"
$Port = 8420

Write-Host "=== Islamic PWA Sync Server Installer ===" -ForegroundColor Green
Write-Host "Server directory: $ServerDir"
Write-Host "Python: $PythonExe"
Write-Host ""

# Step 1: Install dependencies
Write-Host "[1/3] Installing Python dependencies..." -ForegroundColor Cyan
& $PythonExe -m pip install -r "$ServerDir\requirements.txt" --quiet
Write-Host "  Done." -ForegroundColor Green

# Step 2: Add firewall rule
Write-Host "[2/3] Adding firewall rule for port $Port..." -ForegroundColor Cyan
$existingRule = Get-NetFirewallRule -DisplayName "Islamic PWA Sync" -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "  Firewall rule already exists." -ForegroundColor Yellow
} else {
    New-NetFirewallRule -DisplayName "Islamic PWA Sync" `
        -Direction Inbound -Protocol TCP -LocalPort $Port `
        -Action Allow -Profile Any | Out-Null
    Write-Host "  Firewall rule added." -ForegroundColor Green
}

# Step 3: Create scheduled task (runs at system startup)
Write-Host "[3/3] Creating scheduled task '$TaskName'..." -ForegroundColor Cyan

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "  Removed existing task." -ForegroundColor Yellow
}

$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "-m uvicorn server:app --host 0.0.0.0 --port $Port" `
    -WorkingDirectory $ServerDir

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest -LogonType S4U

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal | Out-Null

# Start the task now
Start-ScheduledTask -TaskName $TaskName
Write-Host "  Task created and started." -ForegroundColor Green

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host "Server running at: http://0.0.0.0:$Port" -ForegroundColor Cyan
Write-Host "Tailscale URL: http://100.74.117.61:$Port" -ForegroundColor Cyan
Write-Host ""
Write-Host "Auth token (save this in the PWA sync settings):" -ForegroundColor Yellow

# Read and display the token from config
$configContent = Get-Content "$ServerDir\config.py" -Raw
if ($configContent -match '"([^"]+)"') {
    Write-Host "  $($Matches[1])" -ForegroundColor White
}
