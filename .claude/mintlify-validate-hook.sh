#!/bin/bash
# mintlify-validate-hook.sh
# Claude Code PostToolUse hook: 当修改 /Users/yueyh/Projects/mintlify-docs/ 下的文件时，自动运行 mintlify validate

fp=$(jq -r '.tool_input.file_path' 2>/dev/null)

# 精确匹配路径前缀
if echo "$fp" | grep -q "^/Users/yueyh/Projects/mintlify-docs/"; then
  result=$(mintlify validate 2>&1)
  exit_code=$?

  if [ $exit_code -ne 0 ]; then
    # 用 python3 安全地构造 JSON，避免 shell 引号转义地狱
    python3 -c "
import sys, json
msg = sys.stdin.read()
obj = {'systemMessage': '❌ [mintlify validate] 验证失败\n' + msg[:500]}
print(json.dumps(obj))
" <<< "$result"
  else
    echo '{"systemMessage": "✅ [mintlify validate] 验证通过"}'
  fi
fi
