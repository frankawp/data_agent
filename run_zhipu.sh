#!/bin/bash

# 智谱AI版数据开发Agent启动脚本

API_KEY="a2d9aad92f254c17b3c71495177cc94b.vXbdUFVOvhGZnqf8"
BASE_URL="https://open.bigmodel.cn/api/paas/v4"
MODEL="glm-4"

echo "🚀 启动数据开发Agent（智谱AI版）"
echo "模型: $MODEL"
echo ""

# 激活虚拟环境（如果存在）
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 启动Agent
python -m data_agent.main \
    --provider zhipu \
    --api-key "$API_KEY" \
    --model "$MODEL" \
    --base-url "$BASE_URL"
