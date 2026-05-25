import json, re
import sys
sys.path.insert(0, "E:/AI_MAN/backend")
from app.services.rag import RAGService

rag = RAGService()
rag._ensure_loaded()

print(f"knowledge_items count: {len(rag.knowledge_items)}")

if rag.knowledge_items:
    print(f"First item name: {repr(rag.knowledge_items[0]['name'])}")
    
    # Direct search
    query = "上海迪士尼"
    query_lower = query.lower()
    query_terms = set(re.findall(r"[\w\u4e00-\u9fff]+", query_lower))
    
    print(f"Query terms: {[repr(t) for t in query_terms]}")
    
    for item in rag.knowledge_items[:5]:
        name = item.get("name", "")
        content = item.get("content", "")[:1000]
        search_text = (name + item.get("keywords","") + item.get("type","") + content).lower()
        
        for term in query_terms:
            if term in search_text:
                print(f"  MATCH: term={repr(term)} in name={repr(name[:30])}")
                break
        else:
            print(f"  NO MATCH: name={repr(name[:30])}")
else:
    print("ERROR: knowledge_items is empty after _ensure_loaded!")
    # Check the file directly
    import os
    kb_path = "E:/AI_MAN/backend/data/knowledge_base/knowledge_base.json"
    print(f"KB file exists: {os.path.exists(kb_path)}")
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        print(f"Direct load: {len(d)} items")
