#!/usr/bin/env bash
# 简化的API测试 - 单个3轮对话测试（curl 版）
#
# 测试场景：
# - 第1轮：使用RAG检索模式
# - 第2轮：使用无检索对话模式
# - 第3轮：使用RAG检索模式

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

print_header() {
  printf "\n%s\n" "$(printf '%.0s=' {1..70})"
  printf "%s\n" "$1"
  printf "%s\n" "$(printf '%.0s=' {1..70})"
}

print_section() {
  printf "\n%s\n" "$(printf '%.0s-' {1..70})"
  printf "%s\n" "$1"
  printf "%s\n" "$(printf '%.0s-' {1..70})"
}

print_header "3轮对话测试（第1、3轮用检索，第2轮不用）"

health_url="$BASE_URL/health"
health_resp=$(curl -fsS "$health_url")
printf "URL: %s\nJSON:\n%s\n" "$health_url" "$health_resp"

init_url="$BASE_URL/api/sessions/init"
init_resp=$(curl -fsS -X POST "$init_url")
printf "\nURL: %s\nJSON:\n%s\n" "$init_url" "$init_resp"
session_id=$(python3 - "$init_resp" <<'PY'
import json,sys
try:
  obj=json.loads(sys.argv[1])
  print(obj.get("session_id", ""))
except Exception:
  print("")
PY
)
if [[ -z "$session_id" ]]; then
  printf "❌ 初始化失败，未获取到session_id\n"
  exit 1
fi

# ==================== 第1轮：RAG检索模式 ====================
print_section "第1轮对话 - RAG检索模式"
message1='{"content":"如何提交我写好的python训练程序？","use_retrieval":true,"top_k":5}'
start_ts=$(date +%s)
chat1_url="$BASE_URL/api/chat?session_id=$session_id"
resp1=$(curl -fsS -X POST "$chat1_url" \
  -H "Content-Type: application/json" \
  -d "$message1")
end_ts=$(date +%s)
elapsed=$((end_ts - start_ts))
printf "URL: %s\nJSON:\n%s\n" "$chat1_url" "$resp1"

# ==================== 第2轮：无检索模式 ====================
print_section "第2轮对话 - 无检索模式"
message2='{"content":"再详细解释一下第一步","use_retrieval":false}'
start_ts=$(date +%s)
chat2_url="$BASE_URL/api/chat?session_id=$session_id"
resp2=$(curl -fsS -X POST "$chat2_url" \
  -H "Content-Type: application/json" \
  -d "$message2")
end_ts=$(date +%s)
elapsed=$((end_ts - start_ts))
printf "URL: %s\nJSON:\n%s\n" "$chat2_url" "$resp2"

# ==================== 第3轮：RAG检索模式 ====================
print_section "第3轮对话 - RAG检索模式"
message3='{"content":"提交任务后如何查看日志？","use_retrieval":true,"top_k":3}'
start_ts=$(date +%s)
chat3_url="$BASE_URL/api/chat?session_id=$session_id"
resp3=$(curl -fsS -X POST "$chat3_url" \
  -H "Content-Type: application/json" \
  -d "$message3")
end_ts=$(date +%s)
elapsed=$((end_ts - start_ts))
printf "URL: %s\nJSON:\n%s\n" "$chat3_url" "$resp3"

# ==================== 多轮对话测试 ====================
print_section "多轮对话测试 - 无检索模式"
multi_init_url="$BASE_URL/api/sessions/init"
multi_init_resp=$(curl -fsS -X POST "$multi_init_url")
printf "URL: %s\nJSON:\n%s\n" "$multi_init_url" "$multi_init_resp"
multi_session_id=$(python3 - "$multi_init_resp" <<'PY'
import json,sys
try:
  obj=json.loads(sys.argv[1])
  print(obj.get("session_id", ""))
except Exception:
  print("")
PY
)
if [[ -z "$multi_session_id" ]]; then
  printf "❌ 多轮对话初始化失败，未获取到session_id\n"
  exit 1
fi

multi_turns=(
  "我已经准备好训练脚本，下一步做什么？"
  "再详细解释一下上一条的第一步。"
)

for i in "${!multi_turns[@]}"; do
  msg="${multi_turns[$i]}"
  if [[ "$i" -eq 0 ]]; then
    use_retrieval="true"
  else
    use_retrieval="false"
  fi
  message=$(printf '{"content":"%s","use_retrieval":%s}' "$msg" "$use_retrieval")
  start_ts=$(date +%s)
  multi_chat_url="$BASE_URL/api/chat?session_id=$multi_session_id"
  multi_resp=$(curl -fsS -X POST "$multi_chat_url" \
    -H "Content-Type: application/json" \
    -d "$message")
  end_ts=$(date +%s)
  elapsed=$((end_ts - start_ts))
  printf "URL: %s\nJSON:\n%s\n" "$multi_chat_url" "$multi_resp"
done

# ==================== 查看会话信息 ====================
print_section "会话总结"
printf "ℹ️  本简化脚本不解析会话信息。\n"

# ==================== 保存会话 ====================
printf "\n💾 保存会话...\n"
printf "ℹ️  本简化脚本不执行保存会话。\n"

print_header "✅ 3轮对话测试完成！"
