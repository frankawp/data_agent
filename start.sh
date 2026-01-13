#!/bin/sh
# Railway 启动脚本
exec uvicorn data_agent.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
