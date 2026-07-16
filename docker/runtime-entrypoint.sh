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

detect_shell() {
  for candidate in bash sh; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf "%s" "$candidate"
      return 0
    fi
  done
  return 1
}

if detected_shell="$(detect_shell)"; then
  detected_shell_path="$(command -v "$detected_shell")"
  if [ "${LLLARS_RUNTIME_STARTUP_DIAGNOSTICS:-true}" = "true" ]; then
    echo "[runtime-entrypoint] detected shell: ${detected_shell} (${detected_shell_path})"
  fi
else
  echo "[runtime-entrypoint] no supported shell detected (expected bash or sh)" >&2
  exit 1
fi

set -- --config /work/runtime.container.json

if [ "${SKIP_MCP_PREFLIGHT:-true}" = "true" ]; then
  set -- "$@" --skip-mcp-preflight
fi

exec lllars serve "$@"
