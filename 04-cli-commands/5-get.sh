#!/usr/bin/env bash
# Tests for: 4-Flama CLI / 5-Get.mdx
# Only tests the help output (actual download requires network and time)
set -euo pipefail

echo "=== CLI Get tests ==="

# 1. Help output has the expected structure
OUTPUT=$(flama get --help 2>&1)
if echo "$OUTPUT" | grep -q "Usage: flama get" && \
   echo "$OUTPUT" | grep -q "\-\-source" && \
   echo "$OUTPUT" | grep -q "\-\-family" && \
   echo "$OUTPUT" | grep -q "\-\-output"; then
    echo "  PASS: get --help"
else
    echo "  FAIL: get --help"
    exit 1
fi

echo -e "\n=== 5-get: ALL PASSED ==="
