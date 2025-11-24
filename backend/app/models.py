
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Document(Base):
    """SQLAlchemy model for a single document (article or video)."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String, unique=True)
    published_at = Column(DateTime, index=True)
    full_content = Column(Text)
    source_type = Column(String)  # 'article' or 'video'
    topic_id = Column(Integer, ForeignKey("topics.id"))

    topic = relationship("Topic", back_populates="documents")

class Topic(Base):
    """SQLAlchemy model for a discovered topic."""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # e.g., "Topic 1: AI, Startups, Funding"
    count = Column(Integer)
    keywords = Column(Text)  # Comma-separated keywords

    documents = relationship("Document", back_populates="topic")
    temporal_data = relationship("TemporalData", back_populates="topic")

class TemporalData(Base):
    """SQLAlchemy model for storing topic frequency over time."""
    __tablename__ = "temporal_data"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    timestamp = Column(DateTime, index=True)
    frequency = Column(Integer)

    topic = relationship("Topic", back_populates="temporal_data")
