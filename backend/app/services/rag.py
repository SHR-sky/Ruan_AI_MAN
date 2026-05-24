class RAGService:
    def __init__(self):
        self.documents = {}
        self.faqs = []

    async def generate(self, query: str, session_id: str = "default") -> str:
        return f"[待接入RAG] 您的问题是: {query}"

    async def add_document(self, filename: str, content: bytes) -> str:
        doc_id = f"doc_{len(self.documents)}"
        self.documents[doc_id] = {"filename": filename, "content": content}
        return doc_id

    def list_documents(self):
        return [{"id": k, "filename": v["filename"]} for k, v in self.documents.items()]

    async def delete_document(self, doc_id: str):
        self.documents.pop(doc_id, None)

    async def add_faq(self, question: str, answer: str) -> str:
        faq_id = f"faq_{len(self.faqs)}"
        self.faqs.append({"id": faq_id, "question": question, "answer": answer})
        return faq_id

    async def search(self, query: str, top_k: int = 5):
        return [{"content": f"搜索结果占位: {query}", "score": 1.0}]
