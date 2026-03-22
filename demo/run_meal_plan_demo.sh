#!/usr/bin/env bash
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DEMO_DIR/.." && pwd)"
PORT="${1:-8504}"
SHARED_HOME="${HEALTHCLAW_SHARED_HOME:-}"

cd "$ROOT"

export ADB_SERVER_SOCKET="${ADB_SERVER_SOCKET:-tcp:127.0.0.1:15038}"
export HEALTHCLAW_ENABLE_PHONE_MEITUAN=1

if [ -z "$SHARED_HOME" ] && [ -d "$ROOT/../openclaw" ]; then
  SHARED_HOME="$(cd "$ROOT/../openclaw" && pwd)"
fi

if [ -n "$SHARED_HOME" ] && [ -f "$SHARED_HOME/healthclaw_env.sh" ]; then
  # shellcheck disable=SC1091
  source "$SHARED_HOME/healthclaw_env.sh"
fi

if [ -n "$SHARED_HOME" ] && [ -x "$SHARED_HOME/healthclaw/bin/streamlit" ]; then
  STREAMLIT="$SHARED_HOME/healthclaw/bin/streamlit"
else
  STREAMLIT="streamlit"
fi

echo "[MealPlanDemo] starting on http://127.0.0.1:${PORT}"
exec "$STREAMLIT" run demo/meal_plan_demo_app.py \
  --server.address 127.0.0.1 \
  --server.port "${PORT}" \
  --browser.gatherUsageStats false
