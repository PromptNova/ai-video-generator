# Ngrok Installer Script - FINAL FIXED VERSION
$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "=== Installing ngrok safely... ==="
Write-Host ""

# 1. Download ngrok zip (official)
$ngrokZip = "$env:TEMP\ngrok.zip"
Invoke-WebRequest -Uri "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip" -OutFile $ngrokZip

# 2. Create folder and unzip
$ngrokFolder = "C:\ngrok"
if (!(Test-Path $ngrokFolder)) {
    New-Item -Path $ngrokFolder -ItemType Directory | Out-Null
}
Expand-Archive -Path $ngrokZip -DestinationPath $ngrokFolder -Force

# 3. Add ngrok to PATH
$oldPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($oldPath -notlike "*C:\ngrok*") {
    [Environment]::SetEnvironmentVariable("Path", "$oldPath;C:\ngrok", "Machine")
    Write-Host "✅ Added C:\ngrok to system PATH"
} else {
    Write-Host "ℹ️ C:\ngrok is already in PATH"
}

# 4. Clean up temp file
Remove-Item $ngrokZip -Force

# 5. Verify installation
Write-Host ""
Write-Host "=== Testing ngrok installation ==="
Write-Host ""
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList 'ngrok version'
