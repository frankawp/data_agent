# Data Agent 后端 Docker 镜像
# 用于 Railway 部署

FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install .

# 复制源代码
COPY src/ ./src/

# 启动命令 - 使用 /bin/sh 确保环境变量被正确解析
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["exec uvicorn data_agent.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
