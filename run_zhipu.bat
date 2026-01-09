@echo off
REM 智谱AI版数据开发Agent启动脚本 (Windows)

set API_KEY=a2d9aad92f254c17b3c71495177cc94b.vXbdUFVOvhGZnqf8
set BASE_URL=https://open.bigmodel.cn/api/paas/v4
set MODEL=glm-4

echo 🚀 启动数据开发Agent（智谱AI版）
echo 模型: %MODEL%
echo.

REM 激活虚拟环境（如果存在）
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM 启动Agent
python -m data_agent.main --provider zhipu --api-key %API_KEY% --model %MODEL% --base-url %BASE_URL%
