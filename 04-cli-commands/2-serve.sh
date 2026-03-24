#!/usr/bin/env bash
# Tests for: 4-Flama CLI / 2-Serve.mdx
# Requires: flama installed, .flm model artifacts
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

MODELS="$(cd "$SCRIPT_DIR/../../../flama-site/public/models" && pwd)"
PORT=18202
FAILED=0

echo "=== CLI Serve tests ==="

# 1. Basic serve
flama serve --model "$MODELS/sklearn_model.flm" --server-port $PORT &
PID=$!
sleep 5

RESULT=$(curl -sf -X POST http://127.0.0.1:$PORT/predict/ \
    -H 'Content-Type: application/json' \
    -d '{"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}')
if echo "$RESULT" | grep -q '"output":\[0,1,1,0\]'; then
    echo "  PASS: serve basic (predict)"
else
    echo "  FAIL: serve basic (predict) — got: $RESULT"
    FAILED=1
fi

# docs endpoint
if curl -sf -o /dev/null http://127.0.0.1:$PORT/docs/; then
    echo "  PASS: serve basic (docs)"
else
    echo "  FAIL: serve basic (docs)"
    FAILED=1
fi

kill $PID 2>/dev/null; wait $PID 2>/dev/null || true
sleep 1

# 2. Extended model spec with url and name
PORT=$((PORT + 1))
flama serve --model "file=$MODELS/sklearn_model.flm,url=/xor,name=xor-classifier" --server-port $PORT &
PID=$!
sleep 5

RESULT=$(curl -sf -X POST http://127.0.0.1:$PORT/xor/predict/ \
    -H 'Content-Type: application/json' \
    -d '{"input": [[0, 0], [0, 1], [1, 0], [1, 1]]}')
if echo "$RESULT" | grep -q '"output":\[0,1,1,0\]'; then
    echo "  PASS: serve extended spec (url=/xor)"
else
    echo "  FAIL: serve extended spec — got: $RESULT"
    FAILED=1
fi

kill $PID 2>/dev/null; wait $PID 2>/dev/null || true
sleep 1

# 3. Multiple models
PORT=$((PORT + 1))
flama serve \
    --model "file=$MODELS/sklearn_model.flm,url=/sklearn,name=sklearn" \
    --model "file=$MODELS/pytorch_model.flm,url=/pytorch,name=pytorch" \
    --server-port $PORT &
PID=$!
sleep 5

SK=$(curl -sf -X POST http://127.0.0.1:$PORT/sklearn/predict/ \
    -H 'Content-Type: application/json' -d '{"input": [[0, 0], [1, 1]]}')
PT=$(curl -sf -X POST http://127.0.0.1:$PORT/pytorch/predict/ \
    -H 'Content-Type: application/json' -d '{"input": [[0, 0], [1, 1]]}')
if echo "$SK" | grep -q '"output"' && echo "$PT" | grep -q '"output"'; then
    echo "  PASS: serve multiple models"
else
    echo "  FAIL: serve multiple models — sklearn=$SK pytorch=$PT"
    FAILED=1
fi

kill $PID 2>/dev/null; wait $PID 2>/dev/null || true

if [ $FAILED -eq 0 ]; then
    echo -e "\n=== 2-serve: ALL PASSED ==="
else
    echo -e "\n=== 2-serve: FAILURES ==="
    exit 1
fi
