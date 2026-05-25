import asyncio
import io
import os
import re
import threading
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[4]
KOKORO_MODEL_DIR = PROJECT_ROOT / "models" / "kokoro"
KOKORO_CONFIG_PATH = KOKORO_MODEL_DIR / "config.json"
KOKORO_MODEL_PATH = KOKORO_MODEL_DIR / "kokoro-v1_0.pth"
KOKORO_VOICES_DIR = KOKORO_MODEL_DIR / "voices"


class KokoroTTSEngine:
    name = "Kokoro-82M-ZH"
    repo_id = "hexgrad/Kokoro-82M"
    language_code = "z"
    sample_rate = 24000
    max_chunk_chars = 180
    chunk_pause_seconds = 0.015

    voice_map = {
        "default": "zf_xiaoxiao",
        "female": "zf_xiaoxiao",
        "gentle": "zf_xiaoni",
        "lively": "zf_xiaobei",
        "professional": "zf_xiaoxiao",
        "male": "zm_yunxi",
    }

    _pipeline = None
    _load_lock = threading.Lock()
    _synthesis_lock = asyncio.Lock()
    _load_error = None

    @property
    def pipeline(self):
        if self.__class__._pipeline is None:
            with self.__class__._load_lock:
                if self.__class__._pipeline is None:
                    try:
                        self._prepare_huggingface_env()
                        from kokoro import KPipeline
                        from kokoro.model import KModel

                        self._ensure_local_model_files()
                        model = KModel(
                            repo_id=self.repo_id,
                            config=str(KOKORO_CONFIG_PATH),
                            model=str(KOKORO_MODEL_PATH),
                        ).to(self._resolve_device()).eval()

                        self.__class__._pipeline = KPipeline(
                            lang_code=self.language_code,
                            repo_id=self.repo_id,
                            model=model,
                        )
                        self.__class__._load_error = None
                    except Exception as exc:
                        self.__class__._load_error = str(exc)
                        raise
        return self.__class__._pipeline

    def _prepare_huggingface_env(self) -> None:
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            value = os.environ.get(key, "")
            if "127.0.0.1:9" in value:
                os.environ.pop(key, None)

    def _ensure_local_model_files(self) -> None:
        missing = [
            str(path)
            for path in (KOKORO_CONFIG_PATH, KOKORO_MODEL_PATH, self._voice_path("default"))
            if not path.exists()
        ]
        if missing:
            raise FileNotFoundError(
                "Kokoro local model files are missing. Expected files under "
                f"{KOKORO_MODEL_DIR}: {missing}"
            )

    def _voice_path(self, voice_type: Optional[str]) -> Path:
        voice_name = self.voice_map.get(voice_type or settings.TTS_VOICE, self.voice_map["default"])
        voice_path = KOKORO_VOICES_DIR / f"{voice_name}.pt"
        if voice_path.exists():
            return voice_path
        return KOKORO_VOICES_DIR / f"{self.voice_map['default']}.pt"

    def resolve_voice(self, voice_type: Optional[str]) -> str:
        return str(self._voice_path(voice_type))

    def _split_chunks(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []

        chunks: list[str] = []
        current = ""
        pieces = re.findall(r"[^。！？!?；;\n]+[。！？!?；;\n]?", normalized)
        for piece in pieces or [normalized]:
            piece = piece.strip()
            if not piece:
                continue
            if len(piece) > self.max_chunk_chars:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_long_piece(piece))
                continue
            if current and len(current) + len(piece) > self.max_chunk_chars:
                chunks.append(current)
                current = piece
            else:
                current += piece
        if current:
            chunks.append(current)
        return chunks

    def _split_long_piece(self, text: str) -> list[str]:
        chunks: list[str] = []
        current = ""
        parts: list[str] = []
        buffer = ""
        for char in text:
            buffer += char
            if char in "，,、：:":
                parts.append(buffer)
                buffer = ""
        if buffer:
            parts.append(buffer)

        for part in parts:
            if len(part) > self.max_chunk_chars:
                if current:
                    chunks.append(current)
                    current = ""
                for start in range(0, len(part), self.max_chunk_chars):
                    chunks.append(part[start:start + self.max_chunk_chars])
            elif current and len(current) + len(part) > self.max_chunk_chars:
                chunks.append(current)
                current = part
            else:
                current += part
        if current:
            chunks.append(current)
        return [chunk for chunk in chunks if chunk.strip()]

    def _synthesize_chunk_sync(self, text: str, voice: str) -> np.ndarray:
        generator = self.pipeline(text, voice=voice, speed=1, split_pattern=r"\n+")
        parts: list[np.ndarray] = []
        for _, _, audio in generator:
            audio_array = np.asarray(audio, dtype=np.float32)
            if audio_array.ndim > 1:
                audio_array = np.mean(audio_array, axis=1, dtype=np.float32)
            if audio_array.size:
                parts.append(audio_array)
        if not parts:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(parts)

    async def _synthesize_chunk(self, text: str, voice: str) -> np.ndarray:
        async with self.__class__._synthesis_lock:
            return await asyncio.to_thread(self._synthesize_chunk_sync, text, voice)

    def _to_wav(self, audio: np.ndarray) -> bytes:
        buffer = io.BytesIO()
        sf.write(buffer, audio, self.sample_rate, format="WAV")
        return buffer.getvalue()

    async def synthesize_wav(self, text: str, voice_type: Optional[str] = None) -> bytes:
        chunks = self._split_chunks(text)
        if not chunks:
            return b""

        voice = self.resolve_voice(voice_type)
        pause = np.zeros(int(self.sample_rate * self.chunk_pause_seconds), dtype=np.float32)
        segments: list[np.ndarray] = []
        for index, chunk in enumerate(chunks):
            audio = await self._synthesize_chunk(chunk, voice)
            if audio.size:
                segments.append(audio)
                if index < len(chunks) - 1:
                    segments.append(pause)

        if not segments:
            return b""
        return self._to_wav(np.concatenate(segments))

    async def synthesize_stream(self, text: str, voice_type: Optional[str] = None):
        voice = self.resolve_voice(voice_type)
        for chunk in self._split_chunks(text):
            audio = await self._synthesize_chunk(chunk, voice)
            yield {
                "audio": self._to_wav(audio),
                "timestamps": [],
                "text": chunk,
                "is_last": False,
            }
        yield {"audio": b"", "timestamps": [], "text": "", "is_last": True}

    def _resolve_device(self) -> str:
        requested = settings.TTS_DEVICE.lower()
        if requested in ("auto", "cuda"):
            try:
                import torch

                return "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                return "unknown"
        return requested

    def get_status(self) -> dict:
        device = self._resolve_device()
        gpu_name = ""
        if device == "cuda":
            try:
                import torch

                gpu_name = torch.cuda.get_device_name(0)
                vram = torch.cuda.get_device_properties(0).total_memory // (1024 ** 3)
                gpu_name = f"{gpu_name} ({vram}GB VRAM)"
            except Exception:
                gpu_name = ""

        return {
            "engine": self.name,
            "loaded": self.__class__._pipeline is not None,
            "requested_device": settings.TTS_DEVICE,
            "runtime_device": device,
            "gpu_name": gpu_name,
            "language": self.language_code,
            "sample_rate": self.sample_rate,
            "voices": self.voice_map,
            "model_dir": str(KOKORO_MODEL_DIR),
            "model_path": str(KOKORO_MODEL_PATH),
            "config_path": str(KOKORO_CONFIG_PATH),
            "voices_dir": str(KOKORO_VOICES_DIR),
            "last_error": self.__class__._load_error,
        }
