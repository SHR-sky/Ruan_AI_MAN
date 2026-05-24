import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(256), nullable=False)
    content = Column(Text, nullable=True)
    doc_type = Column(String(32), nullable=True)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FaqEntry(Base):
    __tablename__ = "faq_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(String(512), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    category = Column(String(64), nullable=True)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
