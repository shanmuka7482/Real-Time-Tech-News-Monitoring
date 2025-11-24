
import json
import threading
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware

from . import crud, models, schemas, nlp_pipeline
from .database import SessionLocal, engine, get_db

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CORS MIDDLEWARE ---
# This allows the React frontend (running on localhost:3000) to communicate with the backend.
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BACKGROUND SCHEDULER ---

def ingest_data_from_files():
    """Scheduled job to ingest data from the JSON files."""
    print("Scheduler: Running data ingestion job...")
    db = SessionLocal()
    try:
        # In a real-world scenario, you'd fetch from APIs here.
        # For this project, we load from the pre-generated JSON files.
        with open("indian_tech_articles.json", 'r', encoding='utf-8') as f:
            articles = json.load(f)
        with open("indian_tech_videos.json", 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        # Convert published_at strings to datetime objects
        for item in articles + videos:
            item['published_at'] = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))

        print(f"Ingesting {len(articles)} articles and {len(videos)} videos.")
        crud.bulk_create_documents(db, articles)
        crud.bulk_create_documents(db, videos)
        print("Data ingestion job finished.")
    except FileNotFoundError:
        print("Scheduler: JSON data files not found. Skipping ingestion.")
    finally:
        db.close()

def update_nlp_model_job():
    """Scheduled job to update the NLP model with new data."""
    print("Scheduler: Running NLP model update job...")
    db = SessionLocal()
    try:
        nlp_pipeline.update_model(db)
        print("NLP model update job finished.")
    finally:
        db.close()

@app.on_event("startup")
def start_scheduler():
    """Initializes and starts the background scheduler on app startup."""
    scheduler = BackgroundScheduler()
    # Schedule data ingestion to run every 6 hours
    scheduler.add_job(ingest_data_from_files, 'interval', hours=6, id="ingest_data")
    # Schedule model retraining to run every 24 hours
    scheduler.add_job(update_nlp_model_job, 'interval', hours=24, id="update_model")
    scheduler.start()
    print("Background scheduler started.")


# --- API ENDPOINTS ---

# Global lock to prevent concurrent training
training_lock = threading.Lock()

@app.post("/api/train", status_code=202)
def trigger_initial_training(db: Session = Depends(get_db)):
    """
    Endpoint to manually trigger the initial training of the BERTopic model.
    This should be called once after the initial data has been loaded.
    """
    if training_lock.locked():
        raise HTTPException(status_code=409, detail="Training is already in progress.")

    print("API: Received request to trigger initial training.")
    
    # Acquire the lock non-blocking (double-check, though locked() check above handles most cases)
    if not training_lock.acquire(blocking=False):
         raise HTTPException(status_code=409, detail="Training is already in progress.")
    
    try:
        # Ingest data first to ensure DB is populated
        ingest_data_from_files()
        # Start the training process
        nlp_pipeline.train_initial_model(db)
    finally:
        training_lock.release()
        
    return {"message": "Initial model training has been triggered. This may take a while."}

@app.get("/api/topics", response_model=List[schemas.TopicResponse])
def read_topics(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Returns a list of all discovered topics, sorted by document count."""
    topics = crud.get_topics(db, skip=skip, limit=limit)
    return topics

@app.get("/api/topics/temporal", response_model=List[Dict[str, Any]])
def read_temporal_data(db: Session = Depends(get_db)):
    """
    Returns the topic frequency over time.
    Data is reshaped for easy use with charting libraries like Recharts.
    """
    temporal_data = crud.get_temporal_data(db)
    
    # Reshape data: group by timestamp
    reshaped_data = {}
    topic_names = {topic.id: topic.name for topic in crud.get_topics(db, limit=1000)} # Cache topic names

    for item in temporal_data:
        ts_str = item.timestamp.strftime("%Y-%m-%d")
        if ts_str not in reshaped_data:
            reshaped_data[ts_str] = {"timestamp": ts_str}
        
        topic_name = topic_names.get(item.topic_id)
        if topic_name:
            reshaped_data[ts_str][topic_name] = item.frequency
            
    return list(reshaped_data.values())


@app.get("/api/documents/{topic_id}", response_model=List[schemas.Document])
def read_documents_for_topic(topic_id: int, db: Session = Depends(get_db)):
    """Returns all documents associated with a specific topic ID."""
    documents = crud.get_documents_by_topic(db, topic_id=topic_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found for this topic")
    return documents
