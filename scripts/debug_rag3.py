import json, re
import sys
sys.path.insert(0, "E:/AI_MAN/backend")
from app.services.rag import RAGService
import asyncio

async def test():
    rag = RAGService()
    result = await rag.search("上海迪士尼", top_k=5)
    print("Search results:")
    for r in result:
        print(f"  Score: {r['score']}, Name: {r['name'][:40]}, Content: {r['content'][:80]}")
    
    print()
    answer = await rag.generate("上海迪士尼")
    print("Generate answer:")
    print(answer[:300])

asyncio.run(test())
