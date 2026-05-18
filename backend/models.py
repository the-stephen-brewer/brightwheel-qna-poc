from sqlalchemy import Column, String, Boolean, DateTime, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class KnowledgeDoc(Base):
    __tablename__ = "front_desk_knowledge"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    metadata = Column(JSONB)
    # Note: embedding column is handled via pgvector extension, 
    # we might need a custom type if we use it directly in SQLAlchemy,
    # but for RAG we usually use LangChain's SupabaseVectorStore.

class FrontDeskLog(Base):
    __tablename__ = "front_desk_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    feedback = Column(String)  # 'thumbs_up', 'thumbs_down', null
    needs_review = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSONB)

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'parent', 'admin', 'staff'
    school_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
