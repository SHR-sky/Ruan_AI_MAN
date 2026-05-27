import json
import os
import re
import hashlib
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent.parent
KB_DIR = BASE_DIR / "data" / "knowledge_base"


class RAGService:
    max_answer_chars = 120
    max_answer_sentences = 3

    def __init__(self):
        self.knowledge_items = []
        self.faqs = []
        self.uploaded_docs = {}
        self._loaded = False

    def _to_plain_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
        text = re.sub(r"`([^`]*)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
        text = re.sub(r"^\s*[*\-+•]\s+", "", text, flags=re.M)
        text = text.replace("**", "").replace("__", "")
        text = re.sub(r"(?<!\*)\*(?!\*)", "", text)
        text = re.sub(r"(?<!_)_(?!_)", "", text)
        text = text.replace("|", "，")
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"([。！？；，、：]){2,}", r"\1", text)
        return text.strip(" ，。；;:：")

    def _clamp_plain_answer(self, text: str, char_limit: Optional[int] = None) -> str:
        limit = char_limit or self.max_answer_chars
        plain = self._to_plain_text(text)
        if not plain:
            return "抱歉，我暂时没有整理出合适的介绍。"

        sentence_parts = re.split(r"(?<=[。！？!?])", plain)
        kept = []
        total = 0
        for part in sentence_parts:
            part = part.strip()
            if not part:
                continue
            if len(kept) >= self.max_answer_sentences:
                break
            if total + len(part) > limit and kept:
                break
            if len(part) > limit and not kept:
                trimmed = part[:limit].rstrip("，、；;：: ")
                kept.append(trimmed + ("。" if trimmed and trimmed[-1] not in "。！？!?" else ""))
                break
            kept.append(part)
            total += len(part)

        if not kept:
            trimmed = plain[:limit].rstrip("，、；;：: ")
            return trimmed + ("。" if trimmed and trimmed[-1] not in "。！？!?" else "")

        answer = "".join(kept)
        if len(answer) > limit:
            answer = answer[:limit].rstrip("，、；;：: ")
        if answer and answer[-1] not in "。！？!?":
            answer += "。"
        return answer

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

    def _find_item_by_name(self, query: str) -> Optional[dict]:
        query_lower = query.lower().strip()
        matches = []
        for item in self.knowledge_items:
            name = item.get("name", "").strip()
            if name and name.lower() in query_lower:
                matches.append(item)
        if not matches:
            return None
        return max(matches, key=lambda item: len(item.get("name", "")))

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
            name_lower = name.lower()
            name_boost = 4.0 if (query_lower in name_lower or name_lower in query_lower) else 1.0

            score = (phrase_match + term_ratio * 2 + char_ratio * 1) * name_boost

            if char_ratio > 0.3 or phrase_match > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: -x[0])
        return [
            {
                "content": item["content"],
                "score": round(s, 3),
                "name": item["name"],
                "type": item.get("type", "景点"),
            }
            for s, item in scored[:top_k] if s > 0.5
        ]

    def _search_faq(self, query: str) -> Optional[dict]:
        """FAQ 精确匹配"""
        query_lower = query.lower().strip()
        exact_matches = [
            faq for faq in self.faqs
            if faq["question"].lower().strip() == query_lower
            and self._is_complete_answer(faq.get("answer", ""))
        ]
        if exact_matches:
            return max(exact_matches, key=lambda faq: len(faq.get("answer", "")))

        # Fuzzy match: query contained in FAQ question
        best = None
        best_score = -1
        for faq in self.faqs:
            if not self._is_complete_answer(faq.get("answer", "")):
                continue
            q = faq["question"].lower()
            if query_lower in q or q in query_lower:
                score = len(q) * 10 + len(faq.get("answer", ""))
                if score > best_score:
                    best = faq
                    best_score = score
        return best

    def _is_complete_answer(self, answer: str) -> bool:
        text = answer.strip()
        if not text:
            return False
        if len(text) < 120:
            return True
        return text[-1] in "。！？.!?）】」”"

    async def generate(self, query: str, session_id: str = "default") -> str:
        self._ensure_loaded()

        if not query or not query.strip():
            return "请问您想了解什么？"

        from app.services.llm import LLMService
        llm = LLMService()

        results = self._keyword_search(query, top_k=3)

        if results:
            context_parts = []
            for r in results:
                context_parts.append(f"【{r['name']}】（{r['type']}）\n{r['content'][:500]}")
            context = "\n\n".join(context_parts)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个景区导览AI助手。请严格根据参考资料回答，不要补充资料里没有的事实。"
                        "输出要求："
                        "1）只能输出纯文本，禁止使用 Markdown、标题、序号、项目符号、星号、加粗、表格；"
                        "2）用自己的话概括，像景区导游口播，不要大段照抄原文；"
                        "3）控制在3句以内、120字以内，优先回答最重要的信息；"
                        "4）如果资料不足，直接明确说暂时没有足够信息。"
                    ),
                },
                {
                    "role": "user",
                        "content": f"参考资料：\n{context}\n\n游客问：{query}\n\n请回答：",
                },
            ]
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个景区导览AI助手。"
                        "如果游客的问题超出知识范围，只能输出简短纯文本。"
                        "禁止使用 Markdown、列表或长段说明。"
                        "请在2句以内礼貌告知暂时没有相关信息，并建议游客换个问法或咨询游客中心。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"游客问：{query}\n\n请回答：",
                },
            ]

        try:
            response = await llm.chat(messages, max_tokens=192, temperature=0.35)
            return self._clamp_plain_answer(response["content"])
        except Exception as exc:
            print(f"[RAG] LLM generate failed: {exc}")
            if results:
                return self._clamp_plain_answer(results[0]["content"])
            return self._clamp_plain_answer(
                f"关于{query}，我暂时没有找到准确资料。请换个问法，或者前往景区游客中心咨询。"
            )

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
