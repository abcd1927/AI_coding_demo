"""FastAPI 应用入口，CORS 配置，路由挂载，统一异常处理。"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import chat, messages, status

app = FastAPI(title="AI Agent Demo", version="0.1.0")

# CORS 配置：允许前端 localhost:5173 访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(chat.router)
app.include_router(status.router)
app.include_router(messages.router)


# === 统一异常处理 ===


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一 HTTP 异常响应格式。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_type": exc.detail if isinstance(exc.detail, str) else "HTTP_ERROR",
            "message": str(exc.detail),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一 422 验证错误响应格式。"""
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "error_type": "VALIDATION_ERROR",
            "message": str(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """捕获未预期异常，返回 500。"""
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_type": "INTERNAL_ERROR",
            "message": "服务器内部错误",
        },
    )


@app.get("/api/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "ok"}
