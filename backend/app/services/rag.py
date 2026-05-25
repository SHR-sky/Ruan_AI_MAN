import json
import os
import re
import hashlib
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent.parent
KB_DIR = BASE_DIR / "data" / "knowledge_base"


class RAGService:
    def __init__(self):
        self.knowledge_items = []
        self.faqs = []
        self.uploaded_docs = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._load_knowledge_base()
        self._load_faq()
        self._loaded = True

    def _load_knowledge_base(self):
        json_path = KB_DIR / "knowledge_base.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                self.knowledge_items = json.load(f)
            print(f"[RAG] Loaded {len(self.knowledge_items)} knowledge items from {json_path}")
        else:
            print(f"[RAG] Warning: {json_path} not found")

    def _load_faq(self):
        json_path = KB_DIR / "faq.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                self.faqs = json.load(f)
            print(f"[RAG] Loaded {len(self.faqs)} FAQ items from {json_path}")
        else:
            print(f"[RAG] Warning: {json_path} not found")

    def _tokenize(self, text: str) -> set:
        """中文分词：按字+双字组合，不依赖 jieba"""
        chars = list(text)
        tokens = set(chars)
        tokens.add(text)
        for i in range(len(chars) - 1):
            tokens.add(chars[i] + chars[i + 1])
        return tokens

    def _keyword_search(self, query: str, top_k: int = 5) -> list:
        """关键词搜索：字符级 + 词组级混合匹配"""
        query_lower = query.lower().strip()
        query_terms = self._tokenize(query_lower)
        query_chars = set(query_lower)

        scored = []
        for item in self.knowledge_items:
            name = item.get("name", "")
            content = item.get("content", "")
            keywords = item.get("keywords", "")
            type_name = item.get("type", "")
            search_text = (name + keywords + type_name + content[:2000]).lower()

            # Full phrase match (highest weight)
            phrase_match = 3.0 if query_lower in search_text else 0.0

            # Term match (words + bigrams)
            term_match = sum(1 for t in query_terms if t in search_text)
            term_ratio = term_match / max(len(query_terms), 1)

            # Character match (lenient)
            char_match = sum(1 for c in query_chars if c in search_text)
            char_ratio = char_match / max(len(query_chars), 1)

            # Name boost
            name_boost = 2.0 if query_lower in name.lower() else 1.0

            score = (phrase_match + term_ratio * 2 + char_ratio * 1) * name_boost

            if char_ratio > 0.3 or phrase_match > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: -x[0])
        return [{"content": item["content"][:1000], "score": round(s, 3), "name": item["name"]}
                for s, item in scored[:top_k] if s > 0.5]

    def _search_faq(self, query: str) -> Optional[dict]:
        """FAQ 精确匹配"""
        query_lower = query.lower().strip()
        for faq in self.faqs:
            if faq["question"].lower() == query_lower:
                return faq
        # Fuzzy match: query contained in FAQ question
        best = None
        best_len = 0
        for faq in self.faqs:
            q = faq["question"].lower()
            if query_lower in q or q in query_lower:
                if len(q) > best_len:
                    best = faq
                    best_len = len(q)
        return best

    async def generate(self, query: str, session_id: str = "default") -> str:
        self._ensure_loaded()

        if not query or not query.strip():
            return "请问您想了解什么？"

        # 1. FAQ exact match first
        faq_match = self._search_faq(query)
        if faq_match:
            return faq_match["answer"]

        # 2. Keyword search in knowledge base
        results = self._keyword_search(query, top_k=3)
        if results:
            best = results[0]
            # If name matches, return a structured answer
            name = best.get("name", "")
            if name and any(term in query for term in [name, name[:2]]):
                return best["content"][:800]

            # General answer with top results
            answer_parts = [f"为您找到以下相关信息："]
            for r in results:
                snippet = r["content"][:200]
                answer_parts.append(f"\n▶ {r['name']}：{snippet}")
            return "\n".join(answer_parts)

        # 3. Fallback
        return (f"关于「{query}」，我暂时没有找到准确的资料。"
                f"请尝试换一个问法，或者前往景区游客中心咨询。")

    async def search(self, query: str, top_k: int = 5) -> list:
        self._ensure_loaded()
        return self._keyword_search(query, top_k)

    async def add_document(self, filename: str, content: bytes) -> str:
        doc_id = hashlib.md5(filename.encode()).hexdigest()[:12]
        text = content.decode("utf-8", errors="ignore")
        self.uploaded_docs[doc_id] = {
            "filename": filename,
            "content": text,
            "type": "upload",
        }
        # Add to searchable items
        self.knowledge_items.append({
            "id": f"upload_{doc_id}",
            "name": filename,
            "type": "上传文档",
            "content": text,
            "keywords": filename,
            "source": "upload",
        })
        return doc_id

    def list_documents(self):
        return [{"id": k, "filename": v["filename"]} for k, v in self.uploaded_docs.items()]

    async def delete_document(self, doc_id: str):
        self.uploaded_docs.pop(doc_id, None)
        self.knowledge_items = [k for k in self.knowledge_items if f"upload_{doc_id}" != k.get("id")]

    async def add_faq(self, question: str, answer: str) -> str:
        faq_id = f"faq_{len(self.faqs):05d}"
        self.faqs.append({
            "id": faq_id,
            "question": question,
            "answer": answer,
            "category": "manual",
        })
        return faq_id

    def get_stats(self) -> dict:
        self._ensure_loaded()
        return {
            "knowledge_items": len(self.knowledge_items),
            "faq_items": len(self.faqs),
            "uploaded_docs": len(self.uploaded_docs),
        }
