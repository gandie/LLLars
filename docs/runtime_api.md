# Runtime API

## Serve Mode

Inspect serve options:

```powershell
lllars serve --help
```

Common overrides:

- `--host`
- `--port`
- `--workers`
- `--queue-backend` (`inmemory` or `redis`)

Note: current runtime path accepts `--workers`, but execution remains single-process.

## Endpoints

Serve mode exposes:

- `GET /` (static operator frontend)
- `GET /health`
- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs/{job_id}/logs`
- `POST /jobs/{job_id}/cancel`

## Static Frontend

The runtime frontend at `GET /` supports:

- submit prompt
- poll lifecycle status
- fetch job logs
- terminal-state visibility (`succeeded`, `failed`, `canceled`)

## Manual Smoke

Start service:

```powershell
lllars serve --config .\playground.split.example.json --host 127.0.0.1 --port 8000
```

Submit and poll from PowerShell:

```powershell
$submit = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/jobs" -ContentType "application/json" -Body '{"prompt":"Describe this repository"}'
$jobId = $submit.job_id
do {
  $status = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/jobs/$jobId"
} while ($status.status -in @("queued", "running"))
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/jobs/$jobId/logs"
```

## Payload Contracts

Runtime payload models live in `lllars_core/runtime/models.py`:

- `JobSpec`
- `RunResult`
- `JobStatus`
- `ErrorEnvelope`