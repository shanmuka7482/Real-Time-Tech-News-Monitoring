
from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Dict, Any
from datetime import datetime

# --- Document CRUD ---

def get_document(db: Session, doc_id: int):
    return db.query(models.Document).filter(models.Document.id == doc_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Document).offset(skip).limit(limit).all()

def get_documents_by_topic(db: Session, topic_id: int):
    return db.query(models.Document).filter(models.Document.topic_id == topic_id).all()

def get_all_documents_content(db: Session):
    """Returns a list of all document contents and their IDs."""
    return db.query(models.Document.id, models.Document.full_content, models.Document.published_at).all()

def create_document(db: Session, doc: schemas.DocumentCreate):
    db_doc = models.Document(**doc.dict())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def bulk_create_documents(db: Session, docs: List[Dict[str, Any]]):
    """Creates multiple documents from a list of dicts, avoiding duplicates based on URL."""
    existing_urls = {item[0] for item in db.query(models.Document.url).all()}
    
    # Get valid column names for the Document model
    valid_columns = {c.name for c in models.Document.__table__.columns}
    
    new_docs = []
    for doc_data in docs:
        if doc_data['url'] not in existing_urls:
            # Filter out keys that are not in the model (e.g., 'source_name', 'video_id')
            filtered_data = {k: v for k, v in doc_data.items() if k in valid_columns}
            new_docs.append(models.Document(**filtered_data))
    
    if new_docs:
        db.bulk_save_objects(new_docs)
        db.commit()
    return len(new_docs)


# --- Topic CRUD ---

def get_topic(db: Session, topic_id: int):
    return db.query(models.Topic).filter(models.Topic.id == topic_id).first()

def get_topics(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Topic).order_by(models.Topic.count.desc()).offset(skip).limit(limit).all()

def clear_and_create_topics(db: Session, topics_df):
    """Deletes all existing topics and creates new ones from the BERTopic dataframe."""
    # Clear existing topics and document assignments
    db.query(models.Document).update({models.Document.topic_id: None})
    db.query(models.TemporalData).delete()
    db.query(models.Topic).delete()
    db.commit()

    # Create new topics
    for _, row in topics_df.iterrows():
        # BERTopic might create topic -1 for outliers
        if row['Topic'] == -1:
            continue
        
        topic = models.Topic(
            id=row['Topic'],
            name=row['Name'],
            count=row['Count'],
            keywords=", ".join([word[0] for word in row['Representation']])
        )
        db.add(topic)
    db.commit()

def assign_documents_to_topics(db: Session, doc_ids: List[int], topic_predictions: List[int]):
    """Updates the topic_id for a list of documents."""
    for doc_id, topic_id in zip(doc_ids, topic_predictions):
        # Ensure topic_id is a standard integer, not numpy.int64
        topic_id = int(topic_id)
        if topic_id != -1:
            db.query(models.Document).filter(models.Document.id == doc_id).update({"topic_id": topic_id})
    db.commit()


# --- TemporalData CRUD ---

def get_temporal_data(db: Session):
    return db.query(models.TemporalData).order_by(models.TemporalData.timestamp).all()

def create_temporal_data(db: Session, temporal_data_df):
    """Saves the temporal data from BERTopic analysis."""
    for _, row in temporal_data_df.iterrows():
        temporal_entry = models.TemporalData(
            topic_id=row['Topic'],
            timestamp=row['Timestamp'],
            frequency=row['Frequency']
        )
        db.add(temporal_entry)
    db.commit()
