#!/usr/bin/env bash
# Tests for: 4-Flama CLI / 3-Start.mdx
# Requires: flama installed, .flm model artifacts
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

MODELS="$(cd "$SCRIPT_DIR/../../../flama-site/public/models" && pwd)"
PORT=18210
FAILED=0

echo "=== CLI Start tests ==="

# 1. --create-config simple
flama start --create-config simple
if [ -f flama.json ]; then
    if python3 -c "import json; d=json.load(open('flama.json')); assert 'app' in d and 'server' in d"; then
        echo "  PASS: create-config simple"
    else
        echo "  FAIL: create-config simple (bad structure)"
        FAILED=1
    fi
    rm -f flama.json
else
    echo "  FAIL: create-config simple (file not created)"
    FAILED=1
fi

# 2. Start with import string
cat > /tmp/flama_test_start.json << EOF
{
  "app": "fundamentals.1-applications:app",
  "server": { "host": "127.0.0.1", "port": $PORT }
}
EOF

flama start /tmp/flama_test_start.json &
PID=$!
sleep 4

if curl -sf http://127.0.0.1:$PORT/ | grep -q "Hello"; then
    echo "  PASS: start with import string"
else
    echo "  FAIL: start with import string"
    FAILED=1
fi

kill $PID 2>/dev/null; wait $PID 2>/dev/null || true
sleep 1

# 3. Start with single model config
PORT=$((PORT + 1))
cat > /tmp/flama_test_model.json << EOF
{
  "app": {
    "debug": false,
    "title": "Scikit Learn Model API",
    "version": "0.1.0",
    "description": "Test",
    "schema": "/schema/",
    "docs": "/docs/",
    "models": [{ "url": "/sklearn/", "path": "$MODELS/sklearn_model.flm", "name": "sklearn-classifier" }]
  },
  "server": { "host": "127.0.0.1", "port": $PORT }
}
EOF

flama start /tmp/flama_test_model.json &
PID=$!
sleep 5

RESULT=$(curl -sf -X POST http://127.0.0.1:$PORT/sklearn/predict/ \
    -H 'Content-Type: application/json' \
    -d '{"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}')
if echo "$RESULT" | grep -q '"output":\[0,1,1,0\]'; then
    echo "  PASS: start with model config"
else
    echo "  FAIL: start with model config — got: $RESULT"
    FAILED=1
fi

kill $PID 2>/dev/null; wait $PID 2>/dev/null || true

rm -f /tmp/flama_test_start.json /tmp/flama_test_model.json

if [ $FAILED -eq 0 ]; then
    echo -e "\n=== 3-start: ALL PASSED ==="
else
    echo -e "\n=== 3-start: FAILURES ==="
    exit 1
fi
