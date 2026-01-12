"""
FastAPI 后端入口

提供 Data Agent Web API，使用现有 DataAgent 处理对话。
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .chat import router as chat_router
from .routes import modes_router, database_router, sessions_router

# 创建 FastAPI 应用
app = FastAPI(
    title="Data Agent API",
    description="数据分析 Agent Web API",
    version="1.0.0",
)

# CORS 配置，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 开发服务器
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(modes_router, prefix="/api/modes", tags=["modes"])
app.include_router(database_router, prefix="/api/database", tags=["database"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "data-agent-api"}


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}


def main():
    """启动 API 服务器"""
    uvicorn.run(
        "data_agent.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
