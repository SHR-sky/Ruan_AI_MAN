import json, re
import sys
sys.path.insert(0, "E:/AI_MAN/backend")
from app.services.rag import RAGService

rag = RAGService()

# Manually test keyword_search
query = "上海迪士尼"
query_lower = query.lower()
query_terms = set(re.findall(r"[\w\u4e00-\u9fff]+", query_lower))
print(f"query_lower: {repr(query_lower)}")
print(f"query_terms: {query_terms}")
print(f"query_terms repr: {[repr(t) for t in query_terms]}")

# Check a specific kb item
item = rag.knowledge_items[0]
name = item.get("name", "")
content = item.get("content", "")
keywords = item.get("keywords", "")
type_name = item.get("type", "")

search_text = (name + " " + keywords + " " + type_name + " " + content[:1000]).lower()
print(f"\nsearch_text[:100]: {repr(search_text[:100])}")

for term in query_terms:
    found = term in search_text
    print(f"  term {repr(term)} in search_text: {found}")

# Check all items
print("\n--- Full scan ---")
for item in rag.knowledge_items:
    search_text = (item.get("name","") + " " + item.get("keywords","") + " " + item.get("type","") + " " + item.get("content","")[:1000]).lower()
    match_count = sum(1 for term in query_terms if term in search_text)
    if match_count > 0:
        print(f"  Match! {item['name'][:40]}: {match_count} terms")
        break
else:
    print("  No matches found in any item")
    
    # Try simpler check
    for item in rag.knowledge_items:
        if "迪士尼" in item["content"] or "迪士尼" in item["name"]:
            print(f"  Direct check: found in {item['name'][:40]}")
            break
    else:
        print("  Direct check: '迪士尼' not found either")
