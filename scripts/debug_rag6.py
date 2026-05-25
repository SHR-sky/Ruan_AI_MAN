import json, re
import sys
sys.path.insert(0, "E:/AI_MAN/backend")
from app.services.rag import RAGService

rag = RAGService()
rag._ensure_loaded()

# Test direct string matching
query = "上海迪士尼"
content_sample = rag.knowledge_items[0].get("content", "")

print(f"content_sample[:200]: {repr(content_sample[:200])}")
print(f"query in content_sample: {query in content_sample}")
print(f"'迪士尼' in content_sample: {'迪士尼' in content_sample}")
print(f"'上海' in content_sample: {'上海' in content_sample}")

# Check with lower
print(f"query.lower() in content_sample.lower(): {query.lower() in content_sample.lower()}")

# Search via method
results = rag._keyword_search(query)
print(f"\n_keyword_search results: {results}")

# Debug the method step by step
query_lower = query.lower()
query_terms = set(re.findall(r"[\w\u4e00-\u9fff]+", query_lower))
print(f"\nquery_terms: {[repr(t) for t in query_terms]}")

for item in rag.knowledge_items[:20]:
    name = item.get("name", "")
    keywords = item.get("keywords", "")
    type_name = item.get("type", "")
    content = item.get("content", "")
    
    search_text = (name + " " + keywords + " " + type_name + " " + content[:1000]).lower()
    match_count = sum(1 for term in query_terms if term in search_text)
    
    if match_count > 0:
        print(f"MATCH: {repr(name[:40])}: count={match_count}")
    
    # Also check if the query literally appears
    if query in content:
        print(f"DIRECT MATCH in content: {repr(name[:40])}")
