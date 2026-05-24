class TTSService:
    def __init__(self):
        self.model = None

    async def synthesize(self, text: str) -> str:
        return "[待接入TTS语音合成]"
