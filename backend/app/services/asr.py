class ASRService:
    def __init__(self):
        self.model = None

    async def transcribe(self, audio_base64: str) -> str:
        return "[待接入ASR语音识别]"
