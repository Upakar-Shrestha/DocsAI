from pydantic import BaseModel, ConfigDict
import uuid
from app.document.model import DocumentStatus

class DocumentCreate(BaseModel):
    title: str  

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    file_path: str
    content: str | None
    user_id: uuid.UUID
    status: DocumentStatus

class ChatRequest(BaseModel):
    question: str

class ChatSourceChunk(BaseModel):
    chunk_index: int
    content: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceChunk]