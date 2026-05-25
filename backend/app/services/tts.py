import io
import os
import hashlib
import json
import time
import asyncio
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import settings
from app.services.text_utils import preprocess_text, split_into_sentences


class TTSService:
    def __init__(self):
        self._model = None
        self._speaker_ids = None
        self.cache_dir = Path(settings.UPLOAD_DIR) / "tts_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.voice_configs = {
            "default": {"speed": 1.0, "language": "ZH"},
            "gentle": {"speed": 0.85, "language": "ZH"},
            "lively": {"speed": 1.15, "language": "ZH"},
            "professional": {"speed": 1.0, "language": "ZH"},
        }
        self.current_voice = "default"

    @property
    def model(self):
        if self._model is None:
            from melo.api import TTS
            self._model = TTS(language="ZH", device="cpu")
            self._speaker_ids = self._model.hps.data.spk2id
        return self._model

    @property
    def speaker_ids(self):
        if self._speaker_ids is None:
            _ = self.model
        return self._speaker_ids

    def _cache_path(self, text: str, voice_type: str, speed: float) -> Path:
        key = f"{text}_{voice_type}_{speed}"
        filename = hashlib.md5(key.encode()).hexdigest() + ".wav"
        return self.cache_dir / filename

    def _get_audio_duration(self, audio_data: np.ndarray, sample_rate: int = 24000) -> float:
        return len(audio_data) / sample_rate

    def _generate_phoneme_timestamps(self, text: str, duration: float) -> list:
        chars = list(text)
        seg_duration = duration / max(len(chars), 1)
        timestamps = []
        start = 0.0
        for ch in chars:
            if ch.strip():
                timestamps.append({
                    "char": ch,
                    "start": round(start, 3),
                    "end": round(start + seg_duration, 3),
                })
            start += seg_duration
        return timestamps

    def synthesize_sync(self, text: str, voice_type: Optional[str] = None) -> tuple:
        voice = voice_type or self.current_voice
        config = self.voice_configs.get(voice, self.voice_configs["default"])
        clean_text = preprocess_text(text)

        cached = self._cache_path(clean_text, voice, config["speed"])
        if cached.exists():
            with open(cached, "rb") as f:
                audio_bytes = f.read()
            duration = 0
        else:
            speaker = self.speaker_ids["ZH"]
            audio_np = self.model.tts(clean_text, speaker, config["speed"])
            duration = self._get_audio_duration(audio_np)
            buf = io.BytesIO()
            import soundfile as sf
            sf.write(buf, audio_np, 24000, format="WAV")
            audio_bytes = buf.getvalue()
            cached.write_bytes(audio_bytes)

        timestamps = self._generate_phoneme_timestamps(clean_text, duration or self._estimate_duration(clean_text, config["speed"]))
        return audio_bytes, timestamps, clean_text

    async def synthesize(self, text: str, voice_type: Optional[str] = None) -> bytes:
        audio_bytes, _, _ = await asyncio.to_thread(self.synthesize_sync, text, voice_type)
        return audio_bytes

    async def synthesize_with_timestamps(self, text: str, voice_type: Optional[str] = None) -> dict:
        audio_bytes, timestamps, clean_text = await asyncio.to_thread(self.synthesize_sync, text, voice_type)
        return {
            "audio": audio_bytes,
            "timestamps": timestamps,
            "clean_text": clean_text,
        }

    async def synthesize_stream(self, text: str, voice_type: Optional[str] = None):
        """流式合成：按句子分割，逐句合成并 yield"""
        voice = voice_type or self.current_voice
        sentences = split_into_sentences(text)
        for sentence in sentences:
            if not sentence.strip():
                continue
            audio_bytes, timestamps, clean = await asyncio.to_thread(self.synthesize_sync, sentence, voice)
            yield {
                "audio": audio_bytes,
                "timestamps": timestamps,
                "text": clean,
                "is_last": False,
            }
        yield {"audio": b"", "timestamps": [], "text": "", "is_last": True}

    def precache_texts(self, texts: list, voice_type: Optional[str] = None):
        """预合成常用文本到缓存（如FAQ）"""
        for text in texts:
            self.synthesize_sync(text, voice_type)

    def set_voice(self, voice_type: str) -> bool:
        if voice_type in self.voice_configs:
            self.current_voice = voice_type
            return True
        return False

    def get_available_voices(self) -> list:
        return list(self.voice_configs.keys())

    def get_voice_config(self, voice_type: Optional[str] = None) -> dict:
        voice = voice_type or self.current_voice
        config = self.voice_configs.get(voice, self.voice_configs["default"])
        return {"voice_type": voice, **config}

    def clear_cache(self, older_than_hours: int = 24):
        now = time.time()
        removed = 0
        for f in self.cache_dir.iterdir():
            if f.is_file() and f.suffix == ".wav":
                if now - f.stat().st_mtime > older_than_hours * 3600:
                    f.unlink()
                    removed += 1
        return removed

    def _estimate_duration(self, text: str, speed: float) -> float:
        return len(text) * 0.12 / speed
