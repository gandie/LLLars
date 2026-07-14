#!/bin/sh
set -eu

mkdir -p /config /work /artifacts

if [ -z "$(ls -A /work 2>/dev/null)" ]; then
  cp -R /opt/lllars/defaults/work/. /work/
fi

if [ ! -f /config/.env.runtime ]; then
  cp /opt/lllars/defaults/config/.env.runtime.example /config/.env.runtime
fi

if [ ! -f /work/runtime.container.json ]; then
  cp /opt/lllars/defaults/config/runtime.container.json /work/runtime.container.json
fi

set -- --config /work/runtime.container.json

if [ "${SKIP_MCP_PREFLIGHT:-true}" = "true" ]; then
  set -- "$@" --skip-mcp-preflight
fi

exec lllars serve "$@"
