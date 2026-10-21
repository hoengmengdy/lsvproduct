param([ValidateRange(1024, 65535)][int]$Port = 5000, [switch]$LocalOnly)
$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$runtime = Join-Path $project '.runtime'
$statePath = Join-Path $runtime 'hosting.json'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null

function Test-OwnedProcess($record) {
    if (-not $record) { return $false }
    $running = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
    return ($running -and ([string]$running.StartTime.ToUniversalTime().Ticks -eq $record.StartTicks))
}

function Save-State { $script:state | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8 }

function Get-ProcessRecord($process) {
    $process.Refresh()
    return @{ Id = $process.Id; StartTicks = [string]$process.StartTime.ToUniversalTime().Ticks }
}

function Test-Website($url) {
    try { return (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 }
    catch { return $false }
}

$state = @{ Port = $Port; Server = $null; Tunnel = $null; PublicUrl = $null }
if (Test-Path -LiteralPath $statePath) {
    $old = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ((Test-OwnedProcess $old.Server) -or (Test-OwnedProcess $old.Tunnel)) {
        if ($old.Port -ne $Port) { throw 'Run Stop-LSVIndustry.ps1 before changing ports.' }
        $state.Server = $old.Server
        $state.Tunnel = $old.Tunnel
        $state.PublicUrl = $old.PublicUrl
    }
}

$pythonPath = Join-Path $project '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = (Get-Command python -ErrorAction Stop).Source }
$cloudflaredPath = (Get-Command cloudflared -ErrorAction Stop).Source

if (-not (Test-OwnedProcess $state.Server)) {
    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listeners) { throw "Port $Port is already used by another process. Choose -Port or stop that process." }
    $server = Start-Process -FilePath $pythonPath -ArgumentList @('-u', ('"{0}"' -f (Join-Path $project 'run_lsvindustry.py')), '--port', $Port) -WorkingDirectory $project -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'server.out.log') -RedirectStandardError (Join-Path $runtime 'server.err.log') -PassThru
    $state.Server = Get-ProcessRecord $server
    Save-State
}

$localUrl = "http://127.0.0.1:$Port"
$ready = $false
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    if (Test-Website $localUrl) { $ready = $true; break }
    if (-not (Test-OwnedProcess $state.Server)) { break }
    Start-Sleep -Seconds 1
}
if (-not $ready) { throw "Server did not start. Check $runtime\server.err.log locally; logs may contain private information." }
Write-Host "LSVIndustry Local: http://localhost:$Port (verified)"
$addresses = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | ForEach-Object { $_.IPv4Address.IPAddress }
foreach ($address in $addresses) { Write-Host ('LSVIndustry Network: http://{0}:{1}' -f $address, $Port) }

if ($LocalOnly) { Write-Host "Local server is running. Existing tunnel processes are unchanged."; return }

$tunnelLog = Join-Path $runtime 'tunnel.err.log'
if (-not (Test-OwnedProcess $state.Tunnel)) {
    $tunnel = Start-Process -FilePath $cloudflaredPath -ArgumentList @('tunnel', '--no-autoupdate', '--url', $localUrl, '--protocol', 'http2') -WorkingDirectory $project -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'tunnel.out.log') -RedirectStandardError $tunnelLog -PassThru
    $state.Tunnel = Get-ProcessRecord $tunnel
    $state.PublicUrl = $null
    Save-State
}
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    if (Test-Path -LiteralPath $tunnelLog) {
        $logText = Get-Content -LiteralPath $tunnelLog -Raw
        $urlMatch = [regex]::Match([string]::Concat($logText, ''), 'https://[a-z0-9-]+\.trycloudflare\.com')
        if ($urlMatch.Success) { $state.PublicUrl = $urlMatch.Value; Save-State; break }
    }
    if (-not (Test-OwnedProcess $state.Tunnel)) { throw "Tunnel exited. Check $tunnelLog locally." }
    Start-Sleep -Seconds 1
}
if (-not $state.PublicUrl) { throw "Cloudflare has not returned a public URL. Check $tunnelLog locally." }
$publicReady = $false
for ($attempt = 0; $attempt -lt 8; $attempt++) {
    if (Test-Website $state.PublicUrl) { $publicReady = $true; break }
    Start-Sleep -Seconds 2
}
if ($publicReady) { Write-Host "LSVIndustry Public: $($state.PublicUrl) (verified)" }
else { Write-Warning "Public URL assigned but not yet responding: $($state.PublicUrl). Check the tunnel log." }
Write-Host "Background processes: server $($state.Server.Id), tunnel $($state.Tunnel.Id)."
Write-Host 'Keep this PC powered on, awake, and connected. Closing this PowerShell window is OK.'
