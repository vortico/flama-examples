#!/usr/bin/env bash
# Tests for: 4-Flama CLI / 4-Model.mdx
# Requires: flama installed, .flm model artifacts
# LLM tests require: mlx, mlx-lm, mlx-vlm, transformers
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

MODELS="$(cd "$SCRIPT_DIR/../../../flama-site/public/models" && pwd)"
FAILED=0

echo "=== CLI Model tests (predictive) ==="

# 1. inspect
OUTPUT=$(flama model "$MODELS/sklearn_model.flm" inspect --pretty)
if echo "$OUTPUT" | grep -q '"family": "ml"' && echo "$OUTPUT" | grep -q '"lib": "sklearn"'; then
    echo "  PASS: inspect --pretty (sklearn)"
else
    echo "  FAIL: inspect --pretty (sklearn)"
    FAILED=1
fi

# 2. run (inline)
OUTPUT=$(echo '[[0, 0], [0, 1], [1, 0], [1, 1]]' | flama model "$MODELS/sklearn_model.flm" run)
if [ "$OUTPUT" = "[0, 1, 1, 0]" ]; then
    echo "  PASS: run (inline sklearn)"
else
    echo "  FAIL: run (inline sklearn) — got: $OUTPUT"
    FAILED=1
fi

# 3. run --pretty
OUTPUT=$(echo '[[0, 0], [0, 1], [1, 0], [1, 1]]' | flama model "$MODELS/sklearn_model.flm" run --pretty)
if echo "$OUTPUT" | grep -q "0," && echo "$OUTPUT" | grep -q "1,"; then
    echo "  PASS: run --pretty (sklearn)"
else
    echo "  FAIL: run --pretty (sklearn)"
    FAILED=1
fi

# 4. run with file I/O
echo '[[0, 0], [0, 1], [1, 0], [1, 1]]' > /tmp/flama_input.json
flama model "$MODELS/sklearn_model.flm" run --input /tmp/flama_input.json --output /tmp/flama_output.json
OUTPUT=$(cat /tmp/flama_output.json)
if [ "$OUTPUT" = "[0, 1, 1, 0]" ]; then
    echo "  PASS: run --input/--output (file I/O)"
else
    echo "  FAIL: run --input/--output — got: $OUTPUT"
    FAILED=1
fi
rm -f /tmp/flama_input.json /tmp/flama_output.json

# 5. stream
OUTPUT=$(echo '[[0, 0], [0, 1], [1, 0], [1, 1]]' | flama model "$MODELS/sklearn_model.flm" stream)
if [ "$OUTPUT" = "[0][1][1][0]" ]; then
    echo "  PASS: stream (sklearn)"
else
    echo "  FAIL: stream (sklearn) — got: $OUTPUT"
    FAILED=1
fi

# 6. stream --buffer
OUTPUT=$(echo '[[0, 0], [0, 1], [1, 0], [1, 1]]' | flama model "$MODELS/sklearn_model.flm" stream --buffer)
if echo "$OUTPUT" | grep -q "\[0\]\[1\]"; then
    echo "  PASS: stream --buffer (sklearn)"
else
    echo "  FAIL: stream --buffer (sklearn) — got: $OUTPUT"
    FAILED=1
fi

# 7. inspect tensorflow
OUTPUT=$(flama model "$MODELS/tensorflow_model.flm" inspect --pretty)
if echo "$OUTPUT" | grep -q '"lib": "tensorflow"'; then
    echo "  PASS: inspect (tensorflow)"
else
    echo "  FAIL: inspect (tensorflow)"
    FAILED=1
fi

# 8. inspect pytorch
OUTPUT=$(flama model "$MODELS/pytorch_model.flm" inspect --pretty)
if echo "$OUTPUT" | grep -q '"lib": "torch"'; then
    echo "  PASS: inspect (pytorch)"
else
    echo "  FAIL: inspect (pytorch)"
    FAILED=1
fi

echo ""
echo "=== CLI Model tests (generative) ==="

# Check if LLM model is available
LLM_MODEL=""
for candidate in \
    "$SCRIPT_DIR/../../../flama/mlx-community_gemma-4-E2B-it-qat-4bit.flm" \
    "$SCRIPT_DIR/../../../flama/google_gemma-4-E2B-it.flm"; do
    if [ -f "$candidate" ]; then
        LLM_MODEL="$candidate"
        break
    fi
done

if [ -z "$LLM_MODEL" ]; then
    echo "  SKIP: no LLM .flm model found (set LLM_MODEL env var or place model in ../flama/)"
else
    # 9. LLM inspect
    OUTPUT=$(flama model "$LLM_MODEL" inspect --pretty 2>/dev/null)
    if echo "$OUTPUT" | grep -q '"family": "llm"'; then
        echo "  PASS: inspect (LLM)"
    else
        echo "  FAIL: inspect (LLM)"
        FAILED=1
    fi

    # 10. LLM run
    OUTPUT=$(echo "Say hello in one word." | flama model "$LLM_MODEL" run --param max_tokens=10 2>/dev/null)
    if [ -n "$OUTPUT" ]; then
        echo "  PASS: run (LLM) — output: $(echo "$OUTPUT" | head -c 60)"
    else
        echo "  FAIL: run (LLM) — empty output"
        FAILED=1
    fi

    # 11. LLM stream
    OUTPUT=$(echo "Say hi." | flama model "$LLM_MODEL" stream --param max_tokens=10 2>/dev/null)
    if [ -n "$OUTPUT" ]; then
        echo "  PASS: stream (LLM) — output: $(echo "$OUTPUT" | head -c 60)"
    else
        echo "  FAIL: stream (LLM) — empty output"
        FAILED=1
    fi

    # 12. LLM run --channel all
    OUTPUT=$(echo "2+2?" | flama model "$LLM_MODEL" run --channel all --param max_tokens=10 2>/dev/null)
    if echo "$OUTPUT" | grep -q '"channel"'; then
        echo "  PASS: run --channel all (LLM)"
    else
        echo "  FAIL: run --channel all (LLM) — got: $(echo "$OUTPUT" | head -c 80)"
        FAILED=1
    fi

    # 13. LLM conversation transport
    OUTPUT=$(echo '[{"role":"user","content":"Say hello"}]' | flama model "$LLM_MODEL" run --transport conversation --param max_tokens=10 2>/dev/null)
    if [ -n "$OUTPUT" ]; then
        echo "  PASS: run --transport conversation (LLM)"
    else
        echo "  FAIL: run --transport conversation (LLM)"
        FAILED=1
    fi
fi

if [ $FAILED -eq 0 ]; then
    echo -e "\n=== 4-model: ALL PASSED ==="
else
    echo -e "\n=== 4-model: FAILURES ==="
    exit 1
fi
