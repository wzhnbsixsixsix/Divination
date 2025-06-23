from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from datetime import datetime

from .config import settings
from .database import create_tables
from .routers import divination
from .schemas import HealthCheck, ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    print("正在创建数据库表...")
    create_tables()
    print("数据库表创建完成")
    
    yield
    
    # 关闭时的清理工作
    print("应用正在关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="FateWave 占卜系统后端API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    if settings.debug:
        print(
            f"{request.method} {request.url} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    if settings.debug:
        print(f"全局异常: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            message="服务器内部错误",
            error_code="INTERNAL_SERVER_ERROR",
            details={"type": type(exc).__name__, "message": str(exc)} if settings.debug else None
        ).dict()
    )


# 注册路由
app.include_router(divination.router)


# 健康检查端点
@app.get("/health", response_model=HealthCheck, tags=["系统"])
async def health_check():
    """健康检查接口"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        database="connected"
    )


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """根路径欢迎信息"""
    return {
        "message": "欢迎使用 FateWave 占卜系统 API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation not available in production",
        "health": "/health"
    }


# 测试端点（仅在调试模式下可用）
if settings.debug:
    @app.get("/test/openrouter", tags=["测试"])
    async def test_openrouter():
        """测试OpenRouter API连接"""
        from .services.openrouter_service import openrouter_service
        
        try:
            is_connected = openrouter_service.test_connection()
            return {
                "success": is_connected,
                "message": "API连接成功" if is_connected else "API连接失败"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"API连接测试失败: {str(e)}"
            }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    ) 