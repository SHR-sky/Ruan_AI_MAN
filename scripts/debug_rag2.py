import json
import re
import sys
sys.path.insert(0, "E:/AI_MAN/backend")

with open("E:/AI_MAN/backend/data/knowledge_base/knowledge_base.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

# Manual test
query = "上海迪士尼"
query_terms = set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
print(f"Query terms: {query_terms}")
print(f"Query terms repr: {[repr(t) for t in query_terms]}")

# Check if 上海迪士尼 appears in any content
for item in kb:
    name = item["name"]
    content = item["content"]
    search_text = (name + " " + content[:1000]).lower()
    # Direct substring check
    if "迪士尼" in search_text or "迪士尼" in name:
        print(f"\nFound '迪士尼' in: {repr(name)}")
        print(f"Content starts with: {repr(content[:100])}")

if not any("迪士尼" in item["name"] for item in kb):
    print("\nNo item contains '迪士尼' in name. Searching for '上海之' pattern...")
    for item in kb:
        if "上海" in item["name"]:
            print(f"  Shanghai item: {repr(item['name'][:60])}")
