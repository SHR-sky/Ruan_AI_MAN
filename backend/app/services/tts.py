import io
import os
import hashlib
import time
import asyncio
import wave
from pathlib import Path
from typing import Optional

# Use HF mirror for model download if HF_ENDPOINT not already set
if not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from app.core.config import settings
from app.services.text_utils import preprocess_text, split_into_sentences


class TTSService:
    _shared_chat = None
    _shared_device = None
    _shared_load_error = None
    _shared_speaker_embeds = {}

    def __init__(self):
        self.cache_dir = Path(settings.UPLOAD_DIR) / "tts_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 音色预设 (通过 random seed 控制)
        self.voice_configs = {
            "default": {"seed": 42, "temperature": 0.3, "style": "normal"},
            "gentle": {"seed": 99, "temperature": 0.2, "style": "gentle"},
            "lively": {"seed": 66, "temperature": 0.5, "style": "lively"},
            "professional": {"seed": 77, "temperature": 0.3, "style": "professional"},
        }
        self.current_voice = "default"

    @property
    def chat(self):
        if self.__class__._shared_chat is None:
            import ChatTTS
            chat = ChatTTS.Chat()
            try:
                self._resolve_device()
                # Passing device explicitly can trigger "Cannot copy out of meta
                # tensor" in some ChatTTS/PyTorch builds. Let ChatTTS place the
                # model itself; torch.cuda availability is still reflected in status.
                ok = chat.load(compile=False, source="huggingface")
                if not ok:
                    raise RuntimeError("ChatTTS load returned False")
                self.__class__._shared_chat = chat
            except Exception as exc:
                self.__class__._shared_load_error = f"{type(exc).__name__}: {exc}"
                self.__class__._shared_chat = None
                raise
        return self.__class__._shared_chat

    def _resolve_device(self):
        import torch

        requested = settings.TTS_DEVICE.lower()
        if requested in ("auto", "cuda") and torch.cuda.is_available():
            self.__class__._shared_device = "cuda"
            return torch.device("cuda")
        self.__class__._shared_device = "cpu"
        return torch.device("cpu")

    def _get_speaker_embed(self, voice_type: str) -> str:
        if voice_type not in self._shared_speaker_embeds:
            seed = self._get_seed(voice_type)
            import random
            import torch
            random.seed(seed)
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            self._shared_speaker_embeds[voice_type] = self.chat.sample_random_speaker()
        return self._shared_speaker_embeds[voice_type]

    def _cache_path(self, text: str, voice_type: str) -> Path:
        speaker_tag = "fixed_speaker_v4_no_fallback"
        key = f"{speaker_tag}_{text}_{voice_type}_{self._get_seed(voice_type)}"
        filename = hashlib.md5(key.encode()).hexdigest() + ".wav"
        return self.cache_dir / filename

    def _get_seed(self, voice_type: str) -> int:
        config = self.voice_configs.get(voice_type, self.voice_configs["default"])
        return config["seed"]

    def _get_temperature(self, voice_type: str) -> float:
        config = self.voice_configs.get(voice_type, self.voice_configs["default"])
        return config["temperature"]

    def _infer_sync(self, text: str, voice_type: Optional[str] = None) -> tuple:
        voice = voice_type or self.current_voice
        clean_text = preprocess_text(text)

        cached = self._cache_path(clean_text, voice)
        if cached.exists():
            audio_bytes = cached.read_bytes()
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                duration = wf.getnframes() / wf.getframerate()
            timestamps = self._generate_timestamps(clean_text, duration)
            return audio_bytes, timestamps, clean_text

        seed = self._get_seed(voice)
        temperature = self._get_temperature(voice)
        refine_tokens = 384
        infer_tokens = 2048
        speaker_embed = self._get_speaker_embed(voice)

        from ChatTTS.core import Chat
        params_refine = Chat.RefineTextParams(
            temperature=temperature,
            top_P=0.7,
            top_K=20,
            manual_seed=seed,
            max_new_token=refine_tokens,
            show_tqdm=False,
        )
        params_infer = Chat.InferCodeParams(
            temperature=temperature,
            top_P=0.7,
            top_K=20,
            manual_seed=seed,
            spk_emb=speaker_embed,
            max_new_token=infer_tokens,
            show_tqdm=False,
        )

        wav = self.chat.infer(
            [clean_text],
            use_decoder=True,
            skip_refine_text=True,
            params_refine_text=params_refine,
            params_infer_code=params_infer,
        )

        audio_np = wav[0]
        sample_rate = 24000

        buf = io.BytesIO()
        import soundfile as sf
        sf.write(buf, audio_np, sample_rate, format="WAV")
        audio_bytes = buf.getvalue()
        duration = len(audio_np) / sample_rate

        cached.write_bytes(audio_bytes)

        timestamps = self._generate_timestamps(clean_text, duration)
        return audio_bytes, timestamps, clean_text

    def _generate_timestamps(self, text: str, duration: float) -> list:
        chars = list(text)
        seg = duration / max(len(chars), 1)
        ts = []
        start = 0.0
        for ch in chars:
            if ch.strip():
                ts.append({"char": ch, "start": round(start, 3), "end": round(start + seg, 3)})
            start += seg
        return ts

    async def synthesize(self, text: str, voice_type: Optional[str] = None) -> bytes:
        audio, _, _ = await asyncio.to_thread(self._infer_sync, text, voice_type)
        return audio

    async def synthesize_with_timestamps(self, text: str, voice_type: Optional[str] = None) -> dict:
        audio, timestamps, clean = await asyncio.to_thread(self._infer_sync, text, voice_type)
        return {"audio": audio, "timestamps": timestamps, "clean_text": clean}

    async def synthesize_stream(self, text: str, voice_type: Optional[str] = None):
        sentences = split_into_sentences(text)
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            audio, timestamps, clean = await asyncio.to_thread(self._infer_sync, sentence, voice_type)
            yield {"audio": audio, "timestamps": timestamps, "text": clean, "is_last": False}
        yield {"audio": b"", "timestamps": [], "text": "", "is_last": True}

    async def precache_texts(self, texts: list[str], voice_type: Optional[str] = None) -> int:
        count = 0
        for text in texts:
            if text and text.strip():
                await self.synthesize(text, voice_type)
                count += 1
        return count

    def set_voice(self, voice_type: str) -> bool:
        if voice_type in self.voice_configs:
            self.current_voice = voice_type
            return True
        return False

    def get_available_voices(self) -> list:
        return list(self.voice_configs.keys())

    def get_voice_config(self, voice_type: Optional[str] = None) -> dict:
        v = voice_type or self.current_voice
        cfg = self.voice_configs.get(v, self.voice_configs["default"])
        return {"voice_type": v, **cfg}

    def get_status(self) -> dict:
        return {
            "engine": "ChatTTS",
            "loaded": self.__class__._shared_chat is not None,
            "requested_device": settings.TTS_DEVICE,
            "runtime_device": self.__class__._shared_device,
            "fallback_enabled": False,
            "last_error": self.__class__._shared_load_error,
            "cache_dir": str(self.cache_dir),
        }

    def clear_cache(self, older_than_hours: int = 24) -> int:
        now = time.time()
        removed = 0
        for f in self.cache_dir.iterdir():
            if f.is_file() and f.suffix == ".wav" and now - f.stat().st_mtime > older_than_hours * 3600:
                f.unlink()
                removed += 1
        return removed
