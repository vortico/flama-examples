#!/usr/bin/env bash
# Tests for: 4-Flama CLI / 1-Run.mdx
# Requires: flama installed, fundamentals/1-applications.py in parent dir
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

PORT=18201
FAILED=0

echo "=== CLI Run tests ==="

# 1. flama run with import string
flama run fundamentals.1-applications:app --server-port $PORT &
PID=$!
sleep 4

if curl -sf http://127.0.0.1:$PORT/ | grep -q "Hello"; then
    echo "  PASS: flama run (import string)"
else
    echo "  FAIL: flama run (import string)"
    FAILED=1
fi

kill $PID 2>/dev/null; wait $PID 2>/dev/null || true

if [ $FAILED -eq 0 ]; then
    echo -e "\n=== 1-run: ALL PASSED ==="
else
    echo -e "\n=== 1-run: FAILURES ==="
    exit 1
fi
