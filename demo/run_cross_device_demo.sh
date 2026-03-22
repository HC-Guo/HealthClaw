#!/usr/bin/env bash
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DEMO_DIR/.." && pwd)"
PORT="${1:-8503}"

cd "$ROOT"
if [ -f "$ROOT/healthclaw_env.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/healthclaw_env.sh"
fi

if [ -x "$ROOT/healthclaw/bin/streamlit" ]; then
  STREAMLIT="$ROOT/healthclaw/bin/streamlit"
else
  STREAMLIT="streamlit"
fi

echo "[CrossDeviceDemo] starting on http://127.0.0.1:${PORT}"
exec "$STREAMLIT" run demo/cross_device_demo_app.py \
  --server.address 127.0.0.1 \
  --server.port "${PORT}" \
  --browser.gatherUsageStats false
