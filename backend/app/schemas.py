
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# --- Document Schemas ---
class DocumentBase(BaseModel):
    title: str
    url: str
    published_at: datetime
    full_content: str
    source_type: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    topic_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Topic Schemas ---
class TopicBase(BaseModel):
    id: int
    name: str
    count: int
    keywords: str

class Topic(TopicBase):
    documents: List[Document] = []

    class Config:
        from_attributes = True

# --- Temporal Data Schemas ---
class TemporalDataBase(BaseModel):
    timestamp: datetime
    frequency: int
    topic_id: int

class TemporalData(TemporalDataBase):
    id: int

    class Config:
        from_attributes = True

# --- API Response Schemas ---
class TopicResponse(BaseModel):
    id: int
    name: str
    count: int
    keywords: str

class TemporalDataResponse(BaseModel):
    timestamp: str # Return as string for easy frontend parsing
    topics: dict[str, int] # { "Topic 1": 12, "Topic 2": 5 }
