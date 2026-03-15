# Vibe Dashboard (Next.js + Tailwind)

## Start in dev mode

From workspace root:

```powershell
python ./scripts/dashboard_server.py
```

Or directly:

```powershell
Set-Location "vibe-game-engine/dashboard-nextjs"
npm install
npm run dev
```

Dashboard URL:
- http://127.0.0.1:3000

## Dashboard routes
- `/overview`
- `/agents`
- `/jobs`
- `/logs`
- `/engine`
- `/configs`

## Available API routes
- `GET /api/overview`
- `GET /api/jobs`
- `GET /api/commands`
- `POST /api/commands/run` with JSON body `{ "commandId": "run_tests" }`
- `GET /api/system`
- `GET /api/logs` and `GET /api/logs?file=<log-file-name>&maxLines=180`
