import json
import re
import sys
sys.path.insert(0, "E:/AI_MAN/backend")

with open("E:/AI_MAN/backend/data/knowledge_base/knowledge_base.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

# Print all unique attraction names
names = [item["name"] for item in kb]
for n in sorted(set(names)):
    print(n)
print(f"\nTotal unique names: {len(set(names))}")
