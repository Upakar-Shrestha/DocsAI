from pydantic import BaseModel, ConfigDict
import uuid

class DocumentCreate(BaseModel):
    title: str  
    content: str
    user_id: uuid.UUID  

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    content: str
    user_id: uuid.UUID