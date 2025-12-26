Write-Host "[:] Vertex Symbiotic Deployment" -ForegroundColor Cyan

# 1. Clone Core
if (-not (Test-Path "core")) {
    Write-Host "    Cloning Core Orchestrator..."
    git clone https://github.com/brian95240/universal-living-memory.git core
}

# 2. Launch Infra
Set-Location core
python genesis.py
docker compose up -d
if ($LASTEXITCODE -ne 0) { Write-Error "Docker failed"; exit 1 }

# 3. Health Wait
Write-Host "    Waiting for Brain (localhost:8000)..."
$retries = 0
while ($retries -lt 30) {
    try {
        $r = Invoke-RestMethod "http://localhost:8000/health" -ErrorAction Stop
        if ($r.status -eq "online") { break }
    } catch { Start-Sleep -Seconds 2 }
    $retries++
}

# 4. Launch Studio
Set-Location ..
pip install -r studio/requirements.txt
Write-Host "[:] Launching Studio..."
python studio/genesis_studio.py
