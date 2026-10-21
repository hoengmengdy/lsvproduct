$ErrorActionPreference = 'Stop'
$statePath = Join-Path $PSScriptRoot '.runtime\hosting.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Host 'No LSVIndustry hosting state found.'; return }
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
foreach ($name in @('Tunnel', 'Server')) {
    $record = $state.$name
    if (-not $record) { continue }
    $running = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
    if ($running -and ([string]$running.StartTime.ToUniversalTime().Ticks -eq $record.StartTicks)) {
        Stop-Process -Id $record.Id
        Write-Host "Stopped LSVIndustry $name ($($record.Id))."
    }
}
Remove-Item -LiteralPath $statePath
