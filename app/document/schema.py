from pydantic import BaseModel

class DocumentCreate(BaseModel):
    title: str  
    content: str
    author_id: int

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    author_id: int