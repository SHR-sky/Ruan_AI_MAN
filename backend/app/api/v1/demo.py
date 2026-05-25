from fastapi import APIRouter, Query
from fastapi.responses import Response
from app.services.rag import RAGService
from app.services.tts import TTSService

router = APIRouter()
rag_service = RAGService()
tts_service = TTSService()


def _first_complete_sentence(text: str, limit: int = 50) -> str:
    compact = text.replace("\n", " ").strip()
    if not compact:
        return ""
    for mark in "。！？!?":
        idx = compact.find(mark)
        if 0 < idx <= limit:
            return compact[:idx + 1]
    if len(compact) <= limit:
        return compact
    cut = compact[:limit].rstrip("，、；;：:")
    return f"{cut}。"


def _build_intro() -> dict:
    rag_service._ensure_loaded()
    if not rag_service.knowledge_items:
        text = "欢迎使用景区导览服务。暂无景点数据，请先导入资料。"
        return {
            "name": "景区导览",
            "type": "系统导览",
            "intro_text": text,
            "full_text": text,
            "source": "empty",
        }

    first = rag_service.knowledge_items[0]
    name = first.get("name", "示范景区")
    content = first.get("content", "")
    summary = content.replace("\n", " ").strip()
    intro_text = (
        f"欢迎来到{name}。我是AI导游小导，为您介绍景区特色和推荐路线。"
    )
    first_sentence = _first_complete_sentence(summary)
    if first_sentence:
        intro_text = f"{intro_text}{first_sentence}"

    return {
        "name": name,
        "type": first.get("type", "景点"),
        "intro_text": intro_text,
        "full_text": content[:800],
        "source": first.get("source", "knowledge_base"),
    }


@router.get("/intro")
async def get_intro():
    """获取网页演示导览文案和音频入口。"""
    intro = _build_intro()
    return {
        **intro,
        "audio_url": "/api/v1/demo/intro/audio?voice_type=female",
        "tts_status": tts_service.get_status(),
    }


@router.get("/intro/audio")
async def get_intro_audio(voice_type: str = Query("female")):
    """获取默认导览的 WAV 音频。"""
    intro = _build_intro()
    audio_bytes = await tts_service.synthesize(intro["intro_text"], voice_type)
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Cache-Control": "public, max-age=86400",
        },
    )


@router.post("/intro/precache")
async def precache_intro(voice_type: str = Query("female")):
    """提前生成导览音频，降低网页首次播放等待时间。"""
    intro = _build_intro()
    count = await tts_service.precache_texts([intro["intro_text"]], voice_type)
    return {"status": "ok", "count": count, "tts_status": tts_service.get_status()}


@router.get("/attractions")
async def list_attractions():
    """列出所有景点名称"""
    rag_service._ensure_loaded()
    items = [
        {"name": item["name"], "type": item["type"]}
        for item in rag_service.knowledge_items[:50]
    ]
    return {"count": len(items), "attractions": items}
