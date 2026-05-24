from fastapi import APIRouter, WebSocket, WebSocketDisconnect
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
async def text_chat(query: str, session_id: str = "default"):
    answer = await rag_service.generate(query, session_id)
    return {"answer": answer, "session_id": session_id}


@router.post("/voice")
async def voice_chat(audio_base64: str, session_id: str = "default"):
    text = await asr_service.transcribe(audio_base64)
    answer = await rag_service.generate(text, session_id)
    audio_bytes = await tts_service.synthesize(answer)
    dh_data = await dh_service.generate_expression(answer)
    return {
        "transcribed_text": text,
        "answer": answer,
        "audio": audio_bytes,
        "expression_data": dh_data,
        "session_id": session_id,
    }
