"""FastAPI 应用主文件"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routes import analysis, chat, chat_stream, health
from src.config import settings
from src.models.mongodb import MongoDBManager
from src.utils.logger import get_logger, setup_logging
from src.utils.langchain_patch import apply_reasoning_patch

# 初始化日志
setup_logging()
logger = get_logger(__name__)

# 🔥 应用 LangChain reasoning content 补丁
# 此补丁使 LangChain 能够在流式输出中包含 reasoning_content 字段
apply_reasoning_patch()

# 创建 FastAPI 应用
app = FastAPI(
    title="DHUCI Agent API",
    description="智能 DevOps 项目分析 Agent API 服务",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔥 添加 422 验证错误处理器，打印详细的请求信息
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误，打印详细的请求信息"""
    try:
        body = await request.body()
        logger.error("=" * 80)
        logger.error(f"[422 ERROR] {request.method} {request.url.path}")
        logger.error(f"Content-Type: {request.headers.get('content-type')}")
        logger.error(f"Request body: {body.decode('utf-8') if body else '(empty)'}")
        logger.error("-" * 80)
        logger.error(f"Validation errors:")
        for error in exc.errors():
            logger.error(f"  Field: {error.get('loc')}")
            logger.error(f"  Message: {error.get('msg')}")
            logger.error(f"  Type: {error.get('type')}")
            logger.error(f"  Input: {error.get('input')}")
        logger.error("=" * 80)
    except Exception as e:
        logger.error(f"Error logging validation error: {str(e)}")

    # 返回标准的 422 错误响应
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


# 注册路由
app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(chat_stream.router, prefix="/api/v1")  # 流式对话接口
app.include_router(analysis.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("初始化 MongoDB 连接...")
    try:
        MongoDBManager.init_indexes()
        logger.info("MongoDB 连接成功")
        logger.info(f"MongoDB 数据库: {settings.mongodb_database}")
    except Exception as e:
        logger.warning(f"MongoDB 连接失败: {str(e)}")
        logger.warning("服务将继续运行，但数据持久化功能不可用")

    logger.info("DHUCI Agent API 启动成功")
    logger.info(f"API 地址: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"API 文档: http://{settings.api_host}:{settings.api_port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    MongoDBManager.close()
    logger.info("DHUCI Agent API 关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "DHUCI Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
