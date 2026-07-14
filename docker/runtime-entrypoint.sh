#!/bin/sh
set -eu

mkdir -p /config /work /artifacts

if [ -z "$(ls -A /work 2>/dev/null)" ]; then
  cp -R /opt/lllars/defaults/work/. /work/
fi

if [ ! -f /config/playground.example.json ]; then
  cp /opt/lllars/defaults/config/playground.example.json /config/playground.example.json
fi

python - <<'PY'
import json
import os
from pathlib import Path

source = Path('/config/playground.example.json')
if not source.exists():
    raise SystemExit('Missing /config/playground.example.json')

cfg = json.loads(source.read_text(encoding='utf-8'))
cfg['service_mode'] = 'serve'
cfg['project_root'] = '.'
cfg['mount_work_root'] = '/work'
cfg['mount_config_root'] = '/config'
cfg['mount_artifacts_root'] = '/artifacts'
cfg['provider-url'] = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
cfg['queue_backend'] = os.getenv('QUEUE_BACKEND', cfg.get('queue_backend', 'inmemory'))
cfg['network_policy'] = os.getenv('NETWORK_POLICY', cfg.get('network_policy', 'inherit'))
cfg['mcp_enabled'] = os.getenv('MCP_ENABLED', 'false').strip().lower() in {
    '1',
    'true',
    'yes',
    'on',
}

Path('/work/runtime.json').write_text(
    json.dumps(cfg, indent=2),
    encoding='utf-8',
)
PY

set -- \
  --config /work/runtime.json \
  --host "${LLLARS_HOST:-0.0.0.0}" \
  --port "${LLLARS_PORT:-8000}" \
  --workers "${LLLARS_WORKERS:-1}" \
  --queue-backend "${QUEUE_BACKEND:-inmemory}"

if [ "${SKIP_MCP_PREFLIGHT:-true}" = "true" ]; then
  set -- "$@" --skip-mcp-preflight
fi

exec lllars serve "$@"
