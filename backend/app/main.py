from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import chat, knowledge, digital_human, admin, device

app = FastAPI(
    title=settings.APP_NAME,
    description="景区导览服务AI数字人后端API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1/chat", tags=["游客交互"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库"])
app.include_router(digital_human.router, prefix="/api/v1/digital-human", tags=["数字人"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理后台"])
app.include_router(device.router, prefix="/api/v1/device", tags=["ESP32设备"])

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
