"""Verify Kokoro Chinese TTS in the aiman environment."""
import asyncio
import io
import sys
import wave
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))
from app.services.tts import TTSService


TEXT = "欢迎来到景区导览系统。我会为您介绍知识库中的景点内容。"


async def main():
    service = TTSService()
    audio = await service.synthesize(TEXT, "female")
    with wave.open(io.BytesIO(audio), "rb") as wav_file:
        duration = wav_file.getnframes() / wav_file.getframerate()
        print(f"engine={service.get_status()['engine']}")
        print(f"sample_rate={wav_file.getframerate()}")
        print(f"duration={duration:.2f}s")
        print(f"bytes={len(audio)}")


if __name__ == "__main__":
    asyncio.run(main())
