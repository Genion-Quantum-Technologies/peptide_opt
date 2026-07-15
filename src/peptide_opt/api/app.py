#!/usr/bin/env python3
"""
FastAPI 应用工厂

创建和配置 FastAPI 应用实例
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from peptide_opt.config import settings
from peptide_opt.config.logging import setup_logging
from peptide_opt.tasks.processor import AsyncTaskProcessor

logger = logging.getLogger(__name__)

# 全局异步任务处理器
_async_processor: Optional[AsyncTaskProcessor] = None


def get_async_processor() -> AsyncTaskProcessor:
    """获取异步任务处理器实例"""
    if _async_processor is None:
        raise RuntimeError("Async processor not initialized")
    return _async_processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _async_processor
    
    # —— 应用启动时执行 ——
    logger.info("Starting Peptide Optimization API...")

    # 初始化异步任务处理器
    logger.info("Initializing async task processor...")
    _async_processor = AsyncTaskProcessor()

    # —— 数据库轮询：默认关闭（ADR 0012 P2）——
    #
    # 这个轮询器已经是死代码：集群里由 Argo Workflows 领活，`peptide-opt` Deployment 已置
    # `replicas: 0`。但**代码还活着** —— 只要这个 FastAPI 应用一启动，它就会开始抢 `tasks` 表。
    #
    # 🔴 为什么必须默认关掉，而不是只写句注释：
    # compute-foundry operator 的领活条件是 `status='pending' AND workflow_name IS NULL`。它提交
    # Workflow 后**先写 `workflow_name`**，而 `status` 要等下一次 project() 才变成 `processing`
    # —— 这中间有个最长 10 秒的窗口，行仍然是 `pending`。任何人在本地
    # `docker compose up` / `python -m peptide_opt serve` 并把 DB_HOST 指向生产库，就会在这个
    # 窗口里把任务领走 → **同一个任务跑两遍，并且两次都去抢那张唯一的 GPU。**
    #
    # 回滚路径仍然可用：三个 worker 的 k8s Deployment 显式设了 `LEGACY_POLLER=1`，所以
    # `kubectl scale deploy/peptide-opt --replicas=1` 依然能把老模式原样拉回来。
    if os.environ.get("LEGACY_POLLER", "0") == "1":
        logger.warning(
            "LEGACY_POLLER=1 —— 启动数据库轮询。这是 ADR 0012 之前的模式；"
            "除非你正在回滚，否则不该看到这行日志。"
        )
        await _async_processor.start_polling()
    else:
        logger.info(
            "数据库轮询已禁用（ADR 0012：调度由 Argo Workflows + compute-foundry operator 接管）。"
            "本进程只提供 HTTP 接口；计算走 `python -m peptide_opt.steps <stage>`。"
        )

    logger.info("Peptide Optimization API startup complete")

    yield
    
    # —— 应用关闭时执行 ——
    logger.info("Shutting down Peptide Optimization API...")
    if _async_processor:
        await _async_processor.shutdown()
    logger.info("Peptide Optimization API shutdown complete")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例
    
    Returns:
        配置完成的 FastAPI 应用
    """
    # 设置日志
    setup_logging(level="INFO")
    
    app = FastAPI(
        lifespan=lifespan,
        title="Peptide Optimization API",
        description="Peptide structure optimization and sequence design service using ProteinMPNN and molecular docking.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册异常处理器
    _register_exception_handlers(app)
    
    # 注册路由
    _register_routes(app)
    
    return app


def _register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "body": exc.body}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTP error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


def _register_routes(app: FastAPI):
    """注册路由"""
    from peptide_opt.api.routes import health
    
    # 健康检查路由
    app.include_router(health.router, tags=["Health"])
    
    # 根路由
    @app.get("/")
    async def root():
        """根路径重定向到文档"""
        return {
            "message": "Peptide Optimization API",
            "version": "1.0.0",
            "docs": "/docs",
        }


# 创建默认应用实例（用于 uvicorn 直接引用）
app = create_app()
