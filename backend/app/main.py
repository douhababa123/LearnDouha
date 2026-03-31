"""
FastAPI 主应用
数学冒险岛 - Math Adventure API
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.routers import auth, children, missions, questions, reports

# 自动加载项目根目录下的 .env 文件（开发时方便配置 DASHSCOPE_API_KEY 等）
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass  # python-dotenv 未安装时静默跳过

app = FastAPI(
    title="数学冒险岛 API",
    description="Math Adventure - 二年级数学练习游戏化系统",
    version="1.0.0",
)

# CORS（前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(children.router, prefix="/api/children", tags=["孩子"])
app.include_router(missions.router, prefix="/api/missions", tags=["任务"])
app.include_router(questions.router, prefix="/api/questions", tags=["题目"])
app.include_router(reports.router, prefix="/api/reports", tags=["报告"])


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/")
def root():
    return {"message": "数学冒险岛 API v1.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
