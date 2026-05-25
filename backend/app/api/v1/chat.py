from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.rag import RAGService
from app.services.asr import ASRService
from app.services.tts import TTSService
from app.services.digital_human import DigitalHumanService

router = APIRouter()
rag_service = RAGService()
asr_service = ASRService()
tts_service = TTSService()
dh_service = DigitalHumanService()


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            response = await rag_service.generate(data)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        pass


@router.post("/text")
async def text_chat(
    query: str = Query(...),
    session_id: str = Query("default"),
    voice_type: str = Query(None, description="音色"),
    return_audio: bool = Query(False, description="是否同时返回语音"),
):
    answer = await rag_service.generate(query, session_id)
    result = {"answer": answer, "session_id": session_id}
    if return_audio:
        tts_result = await tts_service.synthesize_with_timestamps(answer, voice_type)
        result["audio"] = list(tts_result["audio"])
        result["timestamps"] = tts_result["timestamps"]
        expression = await dh_service.generate_expression(answer)
        result["expression_data"] = expression
    return result


@router.post("/voice")
async def voice_chat(
    audio_base64: str = Query(...),
    session_id: str = Query("default"),
    voice_type: str = Query(None, description="合成音色"),
):
    text = await asr_service.transcribe(audio_base64)
    answer = await rag_service.generate(text, session_id)
    tts_result = await tts_service.synthesize_with_timestamps(answer, voice_type)
    dh_data = await dh_service.generate_expression(answer)
    return {
        "transcribed_text": text,
        "answer": answer,
        "audio": list(tts_result["audio"]),
        "timestamps": tts_result["timestamps"],
        "expression_data": dh_data,
        "session_id": session_id,
    }
