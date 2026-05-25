import json

with open("E:/AI_MAN/backend/data/knowledge_base/knowledge_base.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total items: {len(data)}")
for item in data[:3]:
    print(f"  ID: {item['id']}")
    print(f"  Name: {item['name'][:50]}")
    print(f"  Type: {item['type']}")
    print(f"  Content preview: {item['content'][:100]}")
    print()

# Check a FAQ item
with open("E:/AI_MAN/backend/data/knowledge_base/faq.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)
print(f"Total FAQs: {len(faqs)}")
for faq in faqs[:3]:
    print(f"  Q: {faq['question'][:80]}")
    print(f"  A: {faq['answer'][:80]}")
    print()
