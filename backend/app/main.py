import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import chat, knowledge, digital_human, admin, device, tts, demo

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
app.include_router(tts.router, prefix="/api/v1/tts", tags=["语音合成 TTS"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["演示"])


@app.on_event("startup")
async def warmup_intro_tts():
    async def _warmup():
        try:
            intro = demo._build_intro()
            await demo.tts_service.precache_texts([intro["intro_text"]], "female")
        except Exception as exc:
            print(f"[TTS] intro warmup failed: {type(exc).__name__}: {exc}")

    asyncio.create_task(_warmup())


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
