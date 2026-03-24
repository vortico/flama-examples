#!/usr/bin/env bash
# Tests for: 4-Flama CLI / 6-Upgrade.mdx
set -euo pipefail

FAILED=0

echo "=== CLI Upgrade tests ==="

# 1. Help output
OUTPUT=$(flama upgrade --help 2>&1)
if echo "$OUTPUT" | grep -q "Usage: flama upgrade" && \
   echo "$OUTPUT" | grep -q "\-\-to" && \
   echo "$OUTPUT" | grep -q "\-\-diff"; then
    echo "  PASS: upgrade --help"
else
    echo "  FAIL: upgrade --help"
    FAILED=1
fi

# 2. Preview mode on a file with old imports
TMPDIR=$(mktemp -d)
cat > "$TMPDIR/old_app.py" << 'EOF'
from flama.models import ModelResource
from flama.models import BaseModelResource
EOF

OUTPUT=$(flama upgrade "$TMPDIR" 2>&1 || true)
if echo "$OUTPUT" | grep -q "MLResource" && echo "$OUTPUT" | grep -q "BaseMLResource"; then
    echo "  PASS: upgrade preview (ModelResource -> MLResource)"
else
    echo "  FAIL: upgrade preview — got: $OUTPUT"
    FAILED=1
fi

# 3. Write mode
flama upgrade --write "$TMPDIR" 2>&1 > /dev/null || true
CONTENT=$(cat "$TMPDIR/old_app.py")
if echo "$CONTENT" | grep -q "MLResource" && echo "$CONTENT" | grep -q "BaseMLResource"; then
    echo "  PASS: upgrade --write"
else
    echo "  FAIL: upgrade --write — file content: $CONTENT"
    FAILED=1
fi

rm -rf "$TMPDIR"

if [ $FAILED -eq 0 ]; then
    echo -e "\n=== 6-upgrade: ALL PASSED ==="
else
    echo -e "\n=== 6-upgrade: FAILURES ==="
    exit 1
fi
