import json
import re
import sys
sys.path.insert(0, "E:/AI_MAN/backend")

# Load KB
with open("E:/AI_MAN/backend/data/knowledge_base/knowledge_base.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

# Test keyword search
query = "上海"
query_terms = set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
print(f"Query terms: {query_terms}")

matches = []
for item in kb:
    search_text = (item.get("name", "") + " " + item.get("keywords", "") + " " + item.get("type", "") + " " + item.get("content", "")[:1000]).lower()
    match_count = sum(1 for term in query_terms if term in search_text)
    if match_count > 0:
        matches.append((match_count, item["name"]))

matches.sort(key=lambda x: -x[0])
print(f"Found {len(matches)} matches:")
for m in matches[:5]:
    print(f"  {m}")

# Test actual faq match
with open("E:/AI_MAN/backend/data/knowledge_base/faq.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

test_q = "介绍一下山门"
for faq in faqs:
    if test_q.lower() in faq["question"].lower() or faq["question"].lower() in test_q.lower():
        print(f"\nFAQ match found:")
        print(f"  Q: {faq['question']}")
        print(f"  A: {faq['answer'][:100]}")
        break
else:
    print(f"\nNo FAQ match for: {test_q}")
    # Show some sample FAQs
    print("Sample FAQ questions:")
    for faq in faqs[:5]:
        print(f"  - {faq['question'][:80]}")
