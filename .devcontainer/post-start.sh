#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

pkill -f "uvicorn api.main:app" 2>/dev/null || true
sleep 1
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > /tmp/parcelpilot.log 2>&1 &

for _ in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    echo "✓ ParcelPilot running at port 8000 (open the forwarded port for your public URL)"
    exit 0
  fi
  sleep 2
done

echo "⚠️  Server did not start in time. Check /tmp/parcelpilot.log"
exit 1
