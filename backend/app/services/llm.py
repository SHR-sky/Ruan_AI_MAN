class LLMService:
    def __init__(self):
        self.model_name = ""

    async def chat(self, messages: list, stream: bool = False):
        return {"role": "assistant", "content": "[待接入大模型]"}

    async def chat_stream(self, messages: list):
        yield "[待接入流式大模型]"
