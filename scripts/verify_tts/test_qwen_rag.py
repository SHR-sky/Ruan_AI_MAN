"""Verify Qwen GGUF + RAG pipeline in the aiman environment."""
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.rag import RAGService


async def main():
    r = RAGService()
    queries = ["华山有哪些景点", "故宫的历史", "你好", "门票多少钱"]
    for q in queries:
        print(f"\nQ: {q}")
        ans = await r.generate(q)
        print(f"A: {ans[:200]}")
        print(f"  ({len(ans)} chars)")


if __name__ == "__main__":
    asyncio.run(main())
