import asyncio
import threading
from pathlib import Path

from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "Qwen3.5-0.8B-IQ4_NL.gguf"


class LLMService:
    _instance = None
    _lock = threading.Lock()
    _load_error = None

    def __init__(self):
        self.model_path = settings.LLM_MODEL_PATH or str(DEFAULT_MODEL_PATH)
        self.name = "Qwen3.5-0.8B-GGUF"

    @property
    def model(self):
        if self.__class__._instance is None:
            with self.__class__._lock:
                if self.__class__._instance is None:
                    try:
                        from llama_cpp import Llama
                        self.__class__._instance = Llama(
                            model_path=self.model_path,
                            n_gpu_layers=-1,
                            n_ctx=2048,
                            verbose=False,
                        )
                        self.__class__._load_error = None
                    except Exception as exc:
                        self.__class__._load_error = str(exc)
                        raise
        return self.__class__._instance

    async def chat(self, messages: list) -> dict:
        def _sync():
            result = self.model.create_chat_completion(
                messages=messages,
                max_tokens=512,
                temperature=0.7,
            )
            content = result["choices"][0]["message"]["content"].strip()
            return {"role": "assistant", "content": content}
        return await asyncio.to_thread(_sync)

    async def chat_stream(self, messages: list):
        def _sync():
            return list(self.model.create_chat_completion(
                messages=messages,
                max_tokens=512,
                temperature=0.7,
                stream=True,
            ))
        chunks = await asyncio.to_thread(_sync)
        for chunk in chunks:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                yield delta["content"]

    def get_status(self) -> dict:
        return {
            "engine": self.name,
            "model_path": self.model_path,
            "loaded": self.__class__._instance is not None,
            "last_error": self.__class__._load_error,
        }
