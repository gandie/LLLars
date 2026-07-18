# Docker Runtime

## Compose Startup

Prepare environment file if needed:

```powershell
Copy-Item .\.env.runtime.example .\.env.runtime -Force
```

Run runtime service:

```powershell
docker compose -f .\docker-compose.runtime.yml --env-file .\.env.runtime up --build
```

## Mount Model

Compose mounts:

- `/work`
- `/config`
- `/artifacts`

Runtime config uses `env_file=/config/.env.runtime`.

## Behavior Notes

- Image is built from `Dockerfile.runtime`.
- Startup seeds defaults into mounted volumes on first run.
- Serve startup only needs `service` settings; `run` fields are needed at job submit time.
- Container startup reports detected shell diagnostics and fails fast if no supported shell exists.

## Minimal API Check

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/jobs" -ContentType "application/json" -Body '{"prompt":"runtime smoke"}'
```

## Smoke Script

```powershell
.\venv\Scripts\python.exe .\runtime_api_smoke_test.py --prompt "docker runtime smoke"
```