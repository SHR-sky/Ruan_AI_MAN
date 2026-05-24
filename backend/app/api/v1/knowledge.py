from fastapi import APIRouter, UploadFile, File, Depends
from app.services.rag import RAGService

router = APIRouter()
rag_service = RAGService()


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    doc_id = await rag_service.add_document(file.filename, content)
    return {"doc_id": doc_id, "filename": file.filename, "status": "processing"}


@router.get("/documents")
async def list_documents():
    return rag_service.list_documents()


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    await rag_service.delete_document(doc_id)
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/faq")
async def add_faq(question: str, answer: str):
    faq_id = await rag_service.add_faq(question, answer)
    return {"faq_id": faq_id, "status": "created"}


@router.get("/search")
async def search_knowledge(query: str, top_k: int = 5):
    results = await rag_service.search(query, top_k)
    return {"query": query, "results": results}
