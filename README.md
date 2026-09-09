# FlyRank Capstone: AI Image Understanding & Content Matching Engine

## Design Overview
This system processes an image library using Gemini Vision Flash to extract schema-validated metadata and embeddings. Blog posts are matched to images using cosine similarity combined with a safety layer (Mismatch Guard) to reject inaccurate matches.

## Core Non-Goal
- Not building an image editor, web frontend, or large-scale real-time video processor.

## Data Model
- **Image**: Stores raw file path, schema-validated JSON attributes, Gemini captions, confidence scores, and vector embeddings.
- **Post**: Blog post content and text embeddings.
- **AICostLog**: Tracks usage cost per Gemini call.
- **ImageMatchReview**: Stores approved/rejected image recommendations with guard reasons.

## Setup & Run Instructions
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload