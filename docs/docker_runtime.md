# Docker Runtime

## Compose Startup

Prepare environment file if needed:

```powershell
Copy-Item .\.env.runtime.example .\.env.runtime -Force
```

For OpenAI or OpenAI-compatible providers, add `OPENAI_API_KEY` to
`.env.runtime`. Docker Compose passes that variable into the runtime process,
and startup model probes use it as a bearer token for `/v1/models`.

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
- Entrypoint does not copy runtime config/profile/env files into mounted volumes.
- Service starts with `--config /opt/lllars/docker/runtime.container.json`.
- Docker runtime command profiles are loaded from `/opt/lllars/docker/runtime.command-profiles.yaml`.
- In serve mode, when `run.project_root` is not set, effective project root resolves to `service.mount_work_root` (`/work`). Mount your workspace content there when needed.
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