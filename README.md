# Multimodal News Topic Monitoring System

This project is a complete, end-to-end system for ingesting, processing, and visualizing news topics from text articles and video transcripts related to "Indian Tech News".

## Overview & Architecture

The system is composed of four main components orchestrated with Docker:

1.  **Database (PostgreSQL)**: The single source of truth for all data, running in a Docker container.
2.  **Backend (FastAPI)**: A Python API that handles data ingestion, runs the NLP pipeline (BERTopic) for topic modeling, and serves the results to the frontend. It includes a scheduler for periodic data fetching and model updates.
3.  **Frontend (React + Chakra UI)**: An interactive web dashboard that provides a user-friendly interface to visualize the discovered topics, their evolution over time, and the underlying documents.
4.  **Deployment (Docker)**: The entire application is containerized using `docker-compose`, ensuring a consistent and reproducible setup across different environments.

## Technology Stack

*   **Backend**: FastAPI, Uvicorn, SQLAlchemy, Psycopg2, APScheduler, python-dotenv
*   **NLP**: BERTopic, Sentence-Transformers, Scikit-learn
*   **Data Ingestion**: NewsAPI-Python, Google API Python Client, YouTube Transcript API, Newspaper3k
*   **Frontend**: React, React Router, Chakra UI, Axios, Recharts, React-Player
*   **Database**: PostgreSQL
*   **Deployment**: Docker, Docker Compose

## Setup & Installation

### Prerequisites

*   Docker and Docker Compose installed on your local machine.
*   API keys for NewsAPI and YouTube Data API.

### Configuration

1.  **Clone the repository** (or have the files generated in your local directory).
2.  **Create the environment file**: Rename the `.env.example` file to `.env` (or create it manually).
3.  **Add your API Keys**: Open the `.env` file and replace the placeholder values for `NEWS_API_KEY` and `YOUTUBE_API_KEY` with your actual keys.
4.  **Customize Database Credentials** (Optional): You can change the `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` values in the `.env` file if you wish.

## How to Run (Initial Setup)

**CRITICAL NOTE**: You do not need to install PostgreSQL locally. Docker runs it in a container for you.

Follow these steps in order to build and run the application for the first time.

1.  **Build all the services**:
    ```bash
    docker-compose build
    ```

2.  **Start the database service**:
    ```bash
    docker-compose up -d db
    ```
    **Wait for about 30 seconds** for the PostgreSQL database to initialize completely.

3.  **Run the initial data ingestion scripts**:
    These scripts will run on your local machine and fetch the initial "golden set" of articles and videos, creating two JSON files.
    
    First, install the required Python packages locally:
    ```bash
    pip install newsapi-python newspaper3k google-api-python-client youtube-transcript-api python-dotenv
    ```
    Then, run the scripts:
    ```bash
    python scripts/ingest_articles.py
    python scripts/ingest_videos.py
    ```

4.  **Start the backend service**:
    The backend service will automatically copy the generated JSON files from the root directory into the container.
    ```bash
    docker-compose up -d backend
    ```
    Wait for a minute for the service to start and the application to initialize.

5.  **Manually trigger the first model training**:
    Open a terminal and run the following `curl` command. This tells the backend to ingest the data from the JSON files and train the first topic model. This process can take several minutes.
    ```bash
    curl -X POST http://localhost:8000/api/train
    ```

6.  **Start the frontend service**:
    ```bash
    docker-compose up -d frontend
    ```

## How to Access

*   **React Dashboard**: Access the main web interface at `http://localhost:3000`
*   **Backend API**: The API is available at `http://localhost:8000`. You can access the auto-generated documentation at `http://localhost:8000/docs`.

## Scheduled Tasks

The application includes a background scheduler that automates data management:

*   **Data Ingestion**: Every 6 hours, the backend attempts to ingest new data by re-reading the root JSON files (in a real-world scenario, this would be a direct API call).
*   **Model Retraining**: Every 24 hours, the backend automatically retrains the NLP model with any new documents that have been ingested since the last update.
