@echo off
echo Starting XClaw Agentic Godot Game Engine Services...

echo Starting FastAPI Backend...
start cmd /k "cd vibe-game-engine && scripts\start_api.bat"

echo Starting Next.js Dashboard...
start cmd /k "cd vibe-game-engine\dashboard-nextjs && npm run dev"

echo All services started!
