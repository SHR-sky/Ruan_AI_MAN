from fastapi import APIRouter, Query, Body
from fastapi.responses import StreamingResponse, Response
from app.services.tts import TTSService

router = APIRouter()
tts_service = TTSService()


@router.post("/synthesize")
async def synthesize(
    text: str = Body(..., embed=True, description="要合成的文本"),
    voice_type: str = Body("default", embed=True, description="音色: default/gentle/lively/professional"),
):
    """文本合成语音，返回 WAV 音频 + 音素时间戳"""
    result = await tts_service.synthesize_with_timestamps(text, voice_type)
    return {
        "audio": list(result["audio"]),
        "timestamps": result["timestamps"],
        "clean_text": result["clean_text"],
    }


@router.post("/synthesize-file")
async def synthesize_file(
    text: str = Body(..., embed=True),
    voice_type: str = Body("default", embed=True),
):
    """直接返回 WAV 文件下载"""
    audio_bytes = await tts_service.synthesize(text, voice_type)
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/synthesize-stream")
async def synthesize_stream(
    text: str = Body(..., embed=True),
    voice_type: str = Body("default", embed=True),
):
    """流式合成，逐句推送 WAV 音频块"""
    async def generate():
        async for chunk in tts_service.synthesize_stream(text, voice_type):
            if chunk["is_last"]:
                yield b"__END__"
            else:
                yield chunk["audio"]

    return StreamingResponse(generate(), media_type="application/octet-stream")


@router.get("/voices")
async def list_voices():
    """获取可用音色列表"""
    return {
        "voices": tts_service.get_available_voices(),
        "current": tts_service.current_voice,
    }


@router.get("/status")
async def tts_status():
    """获取 TTS 引擎状态，供网页和 ESP32 网关自检使用。"""
    return tts_service.get_status()


@router.post("/voice")
async def set_voice(voice_type: str = Body(..., embed=True)):
    """切换当前音色"""
    ok = tts_service.set_voice(voice_type)
    if not ok:
        return {"status": "error", "message": f"未知音色: {voice_type}"}
    config = tts_service.get_voice_config(voice_type)
    return {"status": "ok", "config": config}


@router.get("/voice-config")
async def get_voice_config(voice_type: str = Query(None)):
    """获取音色配置"""
    return tts_service.get_voice_config(voice_type)


@router.post("/precache")
async def precache(
    texts: list = Body(..., description="要预合成的文本列表"),
    voice_type: str = Body("default"),
):
    """预合成常用文本到缓存"""
    count = await tts_service.precache_texts(texts, voice_type)
    return {"status": "ok", "count": count}


@router.post("/clear-cache")
async def clear_cache(older_than_hours: int = 24):
    """清理旧缓存"""
    removed = tts_service.clear_cache(older_than_hours)
    return {"status": "ok", "removed": removed}
