import hashlib
import io
import time
import wave
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.services.text_utils import preprocess_text
from app.services.tts_engines.kokoro_engine import KokoroTTSEngine

BACKEND_DIR = Path(__file__).resolve().parents[2]


class TTSService:
    _engine = KokoroTTSEngine()
    _cache_version = "kokoro_zh_v2"

    def __init__(self):
        upload_dir = Path(settings.UPLOAD_DIR)
        if not upload_dir.is_absolute():
            upload_dir = BACKEND_DIR / upload_dir
        self.cache_dir = upload_dir / "tts_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.current_voice = settings.TTS_VOICE or "female"

    def _cache_path(self, text: str, voice_type: str) -> Path:
        voice = self._engine.resolve_voice(voice_type)
        key = f"{self._cache_version}_{text}_{voice}_{self._engine.sample_rate}"
        filename = hashlib.md5(key.encode("utf-8")).hexdigest() + ".wav"
        return self.cache_dir / filename

    def _write_cache_atomic(self, path: Path, audio_bytes: bytes) -> None:
        path.write_bytes(audio_bytes)

    def _generate_timestamps(self, text: str, duration: float) -> list:
        chars = list(text)
        seg = duration / max(len(chars), 1)
        timestamps = []
        start = 0.0
        for char in chars:
            if char.strip():
                timestamps.append({
                    "char": char,
                    "start": round(start, 3),
                    "end": round(start + seg, 3),
                })
            start += seg
        return timestamps

    async def synthesize(self, text: str, voice_type: Optional[str] = None) -> bytes:
        clean = preprocess_text(text)
        if not clean:
            return b""

        voice = voice_type or self.current_voice
        cached = self._cache_path(clean, voice)
        if settings.TTS_CACHE_ENABLED and cached.exists():
            return cached.read_bytes()

        audio_bytes = await self._engine.synthesize_wav(clean, voice)
        if settings.TTS_CACHE_ENABLED:
            self._write_cache_atomic(cached, audio_bytes)
        return audio_bytes

    async def synthesize_with_timestamps(self, text: str, voice_type: Optional[str] = None) -> dict:
        audio_bytes = await self.synthesize(text, voice_type)
        clean = preprocess_text(text)
        if not audio_bytes:
            return {"audio": b"", "timestamps": [], "clean_text": clean}

        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            duration = wav_file.getnframes() / wav_file.getframerate()
        return {
            "audio": audio_bytes,
            "timestamps": self._generate_timestamps(clean, duration),
            "clean_text": clean,
        }

    async def synthesize_stream(self, text: str, voice_type: Optional[str] = None):
        async for chunk in self._engine.synthesize_stream(preprocess_text(text), voice_type or self.current_voice):
            yield chunk

    async def precache_texts(self, texts: list[str], voice_type: Optional[str] = None) -> int:
        count = 0
        for text in texts:
            if text and text.strip():
                await self.synthesize(text, voice_type)
                count += 1
        return count

    def set_voice(self, voice_type: str) -> bool:
        if voice_type in self.get_available_voices():
            self.current_voice = voice_type
            return True
        return False

    def get_available_voices(self) -> list:
        return list(self._engine.voice_map.keys())

    def get_voice_config(self, voice_type: Optional[str] = None) -> dict:
        selected = voice_type or self.current_voice
        return {
            "voice_type": selected,
            "speaker": self._engine.resolve_voice(selected),
            "engine": self._engine.name,
            "sample_rate": self._engine.sample_rate,
        }

    def get_status(self) -> dict:
        return {
            **self._engine.get_status(),
            "cache_dir": str(self.cache_dir),
            "cache_enabled": settings.TTS_CACHE_ENABLED,
        }

    def clear_cache(self, older_than_hours: int = 24) -> int:
        now = time.time()
        removed = 0
        for file_path in self.cache_dir.iterdir():
            if file_path.is_file() and file_path.suffix == ".wav" and now - file_path.stat().st_mtime > older_than_hours * 3600:
                file_path.unlink()
                removed += 1
        return removed
