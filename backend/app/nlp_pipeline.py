
import pickle
from pathlib import Path
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sqlalchemy.orm import Session
from . import crud

# --- CONFIGURATION ---
MODEL_PATH = Path("/app/model/bertopic_model.pkl")
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

# --- MODEL LOADING ---

def get_embedding_model():
    """Initializes and returns the sentence transformer model."""
    return SentenceTransformer("all-MiniLM-L6-v2")

def get_bertopic_model(embedding_model):
    """Initializes and returns the BERTopic model."""
    # Initialize UMAP with a fixed random_state for reproducibility
    # We also set n_components to 5 (default) explicitly
    from umap import UMAP
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=42)

    vectorizer_model = CountVectorizer(stop_words="english")
    return BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        vectorizer_model=vectorizer_model,
        language="english",
        calculate_probabilities=True,
        verbose=True
    )

def load_model():
    """Loads the BERTopic model from disk if it exists."""
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return None

def save_model(model):
    """Saves the BERTopic model to disk."""
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

# --- NLP PIPELINE FUNCTIONS ---

def train_initial_model(db: Session):
    """Trains the BERTopic model on the initial set of documents."""
    print("Starting initial model training...")
    
    # 1. Get all documents from the database
    docs_data = crud.get_all_documents_content(db)
    if not docs_data:
        print("No documents found in the database to train on.")
        return
        
    doc_ids, corpus, timestamps = zip(*docs_data)
    
    # 2. Initialize models
    embedding_model = get_embedding_model()
    topic_model = get_bertopic_model(embedding_model)

    # 3. Train the model
    print(f"Training model on {len(corpus)} documents...")
    topic_predictions, _ = topic_model.fit_transform(corpus)

    # 4. Save the model
    save_model(topic_model)
    print(f"Model trained and saved to {MODEL_PATH}")

    # 5. Update the database with topic information
    update_database_with_model_results(db, topic_model, doc_ids, topic_predictions)
    
    # 6. Run temporal analysis
    run_temporal_analysis(db, topic_model, corpus, timestamps)

def update_model(db: Session):
    """Updates the BERTopic model with new documents (online/incremental training)."""
    print("Starting model update...")
    
    topic_model = load_model()
    if not topic_model:
        print("No existing model found. Running initial training first.")
        train_initial_model(db)
        return

    # 1. Get new documents (those without a topic_id)
    new_docs_data = [(doc.id, doc.full_content, doc.published_at) for doc in crud.get_documents(db) if doc.topic_id is None]
    if not new_docs_data:
        print("No new documents to update the model with.")
        return

    doc_ids, corpus, timestamps = zip(*new_docs_data)

    # 2. Update the model (online training)
    print(f"Updating model with {len(corpus)} new documents...")
    topic_predictions, _ = topic_model.transform(corpus)

    # 3. Save the updated model
    save_model(topic_model)
    print("Model updated and saved.")

    # 4. Update the database
    crud.assign_documents_to_topics(db, doc_ids, topic_predictions)
    print("New documents assigned to topics.")

def run_temporal_analysis(db: Session, topic_model: BERTopic, corpus: list, timestamps: list):
    """Performs temporal analysis and saves the results to the database."""
    print("Running temporal analysis...")
    try:
        # This function requires a trained model and the original data
        topics_over_time = topic_model.topics_over_time(corpus, timestamps, nr_bins=20)
        
        # Save results to the database
        crud.create_temporal_data(db, topics_over_time)
        print("Temporal analysis complete and data saved.")
    except Exception as e:
        print(f"Could not run temporal analysis: {e}")


def update_database_with_model_results(db: Session, topic_model: BERTopic, doc_ids: list, topic_predictions: list):
    """Clears old topic data and saves the new model's results to the DB."""
    print("Updating database with new model results...")
    
    # 1. Get topic info dataframe from the model
    topics_df = topic_model.get_topic_info()
    
    # 2. Clear old topics and create new ones
    crud.clear_and_create_topics(db, topics_df)
    print("Cleared old topics and created new ones.")
    
    # 3. Assign all documents to their new topics
    crud.assign_documents_to_topics(db, doc_ids, topic_predictions)
    print("Assigned documents to new topics.")
