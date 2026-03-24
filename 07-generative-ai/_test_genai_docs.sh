#!/usr/bin/env bash
# Test runner for all generative-ai documentation examples
# Runs: compile checks for LLM-dependent scripts, full MCP server test
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

FAILED=0
PORT=18301

echo "=== Generative AI documentation tests ==="
echo ""

# ---------------------------------------------------------------------------
# 1. Compile checks (pages 1, 3, 4 need a .flm to run, but must compile)
# ---------------------------------------------------------------------------
echo "--- Compile checks ---"
for f in generative-ai/1-overview.py generative-ai/3-serving-llms.py generative-ai/4-chatbot.py generative-ai/5-mcp.py; do
    if python -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>/dev/null; then
        echo "  PASS: $f compiles"
    else
        echo "  FAIL: $f does not compile"
        FAILED=1
    fi
done

# ---------------------------------------------------------------------------
# 2. Import verification (all imports from the docs must resolve)
# ---------------------------------------------------------------------------
echo ""
echo "--- Import checks ---"

python -c "
from flama import Flama
from flama.models import LLMResource
from flama.mcp.data_structures import Elicit, Elicitation
import flama

app = Flama()
assert hasattr(app, 'models')
assert hasattr(app.models, 'add_model')
assert hasattr(app.models, 'model_resource')
assert hasattr(app, 'mcp')
assert hasattr(app.mcp, 'add_server')
assert hasattr(app.mcp, 'tool')
assert hasattr(app.mcp, 'resource')
assert hasattr(app.mcp, 'prompt')
assert hasattr(app.mcp, 'app_template')
assert hasattr(flama, 'run')
print('  PASS: all imports and attributes')
"
if [ $? -ne 0 ]; then FAILED=1; fi

# ---------------------------------------------------------------------------
# 3. MCP server full test (page 5)
# ---------------------------------------------------------------------------
echo ""
echo "--- MCP server test (5-mcp.py) ---"

python generative-ai/5-mcp.py &
MCP_PID=$!
sleep 3

# tools/call: add(2,3)
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/tools/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: tools/call' -H 'Mcp-Name: add' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"add","arguments":{"a":2,"b":3}}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); assert r['result']['structuredContent']==5" 2>/dev/null; then
    echo "  PASS: tools/call add(2,3)=5"
else
    echo "  FAIL: tools/call add(2,3)"
    FAILED=1
fi

# tools/call: multiply(4,5) on math server
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/math/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: tools/call' -H 'Mcp-Name: multiply' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"multiply","arguments":{"a":4,"b":5}}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); assert r['result']['structuredContent']==20" 2>/dev/null; then
    echo "  PASS: tools/call multiply(4,5)=20"
else
    echo "  FAIL: tools/call multiply(4,5)"
    FAILED=1
fi

# tools/call: square(7) - background task
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/tools/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: tools/call' -H 'Mcp-Name: square' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"square","arguments":{"x":7}}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); assert r['result']['structuredContent']==49" 2>/dev/null; then
    echo "  PASS: tools/call square(7)=49 (task)"
else
    echo "  FAIL: tools/call square(7)"
    FAILED=1
fi

# tools/call: confirm - elicitation
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/tools/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: tools/call' -H 'Mcp-Name: confirm' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"confirm","arguments":{}}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); assert r['result']['resultType']=='inputRequired'" 2>/dev/null; then
    echo "  PASS: tools/call confirm (elicitation)"
else
    echo "  FAIL: tools/call confirm"
    FAILED=1
fi

# tools/call: with_ui
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/tools/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: tools/call' -H 'Mcp-Name: with_ui' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"with_ui","arguments":{}}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); assert r['result']['structuredContent']=='rendered'" 2>/dev/null; then
    echo "  PASS: tools/call with_ui (MCP App)"
else
    echo "  FAIL: tools/call with_ui"
    FAILED=1
fi

# resources/read
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/tools/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: resources/read' -H 'Mcp-Name: config://app' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":6,"method":"resources/read","params":{"uri":"config://app"}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); t=json.loads(r['result']['contents'][0]['text']); assert t=={'debug':True,'name':'flama-mcp'}" 2>/dev/null; then
    echo "  PASS: resources/read config://app"
else
    echo "  FAIL: resources/read config://app"
    FAILED=1
fi

# prompts/get
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/tools/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: prompts/get' -H 'Mcp-Name: summarise' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":7,"method":"prompts/get","params":{"name":"summarise","arguments":{"text":"Flama is great"}}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); assert 'Flama is great' in r['result']['messages'][0]['content']['text']" 2>/dev/null; then
    echo "  PASS: prompts/get summarise"
else
    echo "  FAIL: prompts/get summarise"
    FAILED=1
fi

# tools/list
R=$(curl -sf -X POST http://127.0.0.1:8000/mcp/tools/ \
  -H 'Content-Type: application/json' -H 'Mcp-Method: tools/list' -H 'MCP-Protocol-Version: 2026-07-28' \
  -d '{"jsonrpc":"2.0","id":8,"method":"tools/list","params":{}}')
if echo "$R" | python -c "import sys,json; r=json.load(sys.stdin); names=sorted(t['name'] for t in r['result']['tools']); assert names==['add','confirm','square','with_ui']" 2>/dev/null; then
    echo "  PASS: tools/list (4 tools)"
else
    echo "  FAIL: tools/list"
    FAILED=1
fi

kill $MCP_PID 2>/dev/null; wait $MCP_PID 2>/dev/null || true

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
echo ""
if [ $FAILED -eq 0 ]; then
    echo "=== generative-ai: ALL PASSED ==="
else
    echo "=== generative-ai: FAILURES ==="
    exit 1
fi
