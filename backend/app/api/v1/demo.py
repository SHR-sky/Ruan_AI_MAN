from fastapi import APIRouter, Query
from fastapi.responses import Response
from app.services.rag import RAGService
from app.services.tts import TTSService

router = APIRouter()
rag_service = RAGService()
tts_service = TTSService()


@router.get("/intro")
async def get_intro():
    """获取默认景点介绍（仅文字，不含语音）"""
    rag_service._ensure_loaded()
    if not rag_service.knowledge_items:
        return {"text": "暂无知识库数据"}

    first = rag_service.knowledge_items[0]
    return {
        "name": first["name"],
        "type": first["type"],
        "full_text": first["content"][:800],
    }


@router.get("/intro/audio")
async def get_intro_audio(voice_type: str = Query("default")):
    """获取默认介绍的 WAV 音频（首次调用会加载ChatTTS模型，约需5-10秒）"""
    rag_service._ensure_loaded()
    if not rag_service.knowledge_items:
        return Response(content=b"", media_type="audio/wav")

    first = rag_service.knowledge_items[0]
    intro_text = f"欢迎来到{first['name']}。{first['content'][:300]}"
    audio_bytes = await tts_service.synthesize(intro_text, voice_type)
    return Response(content=audio_bytes, media_type="audio/wav")


@router.get("/attractions")
async def list_attractions():
    """列出所有景点名称"""
    rag_service._ensure_loaded()
    items = [
        {"name": item["name"], "type": item["type"]}
        for item in rag_service.knowledge_items[:50]
    ]
    return {"count": len(items), "attractions": items}
