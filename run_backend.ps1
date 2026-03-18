param(
	[int]$Port = 8000,
	[string]$App = "api.server:app",
	[switch]$KillConflictingPort = $true
)

$ErrorActionPreference = "Stop"

$projectDir = "E:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine"
$pythonExe = Join-Path $projectDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
	throw "Python executable not found at $pythonExe"
}

$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existing) {
	$pid = $existing.OwningProcess
	if ($KillConflictingPort) {
		Write-Host "Port $Port is in use by PID $pid. Stopping process..."
		Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
		Start-Sleep -Milliseconds 300
	} else {
		throw "Port $Port is already in use by PID $pid"
	}
}

Set-Location $projectDir
& $pythonExe -m uvicorn $App --port $Port
