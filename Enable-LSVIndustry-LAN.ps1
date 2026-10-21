#Requires -RunAsAdministrator
param([ValidateRange(1024, 65535)][int]$Port = 5000)
$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = (Get-Command python -ErrorAction Stop).Source }
$ruleName = "LSVIndustry-HTTP-$Port-PrivateLAN"
if (-not (Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name $ruleName -DisplayName "LSVIndustry HTTP $Port - private LAN only" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -RemoteAddress LocalSubnet -Profile Private -Program $pythonPath | Out-Null
}
Write-Host "LSVIndustry TCP port $Port is allowed from the local subnet on Private networks."
