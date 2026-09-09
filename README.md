# FlyRank — AI Image Matching Engine

FlyRank is an automated AI-powered image matching engine designed for media platforms. It ingests corpus images, extracts vision metadata, computes text embeddings, and provides semantic matching against content posts using a multi-layered safety guard to eliminate false positives.

---

## Key Features

* **Automated Vision Metadata Ingestion:** Categorizes raw images into subjects, attributes, categories, and confidence scores.
* **Resilient Fallback Pipeline:** Gracefully shifts from live LLM APIs to pre-generated metadata caches (`corpus_metadata.json`) during upstream rate limits or service unavailability.
* **768-Dimensional Vector Search:** Computes dense vector embeddings and uses cosine similarity to rank content relevance.
* **Multi-Layered Mismatch Guard:** Applies confidence filtering, category validation, and semantic score thresholds to prevent irrelevant matches.
* **Background Batch Processing & Cost Tracking:** Processes image queues asynchronously while tracking token counts and operational costs per task.
* **Automated Evaluation Benchmark:** Built-in evaluation suite measuring Top-1 Match Precision and Mean Reciprocal Rank (MRR).

---

## System Architecture

```text
[ Raw Image Ingestion ]
           │
           ▼
[ Vision Service Pipeline ]
  ├── 1. Primary: Gemini Vision API (gemini-3.6-flash)
  └── 2. Fallback: Local Metadata Mock (corpus_metadata.json)
           │
           ▼
[ Metadata Storage & Vector Embedding ]
  ├── Image Attributes & Confidence → SQLite (app.db)
  └── 768-dim Dense Vectors → Cosine Similarity Engine
           │
           ▼
[ Mismatch Safety Guard ]
  ├── Confidence Score Check (≥ 0.70)
  ├── Strict Category Alignment
  └── Vector Similarity Threshold
           │
           ▼
[ Ranked Relevant Image Matches ]
```

---

## Architectural Note: Vision API Resiliency & Fallback Strategy

During production testing, third-party free-tier vision models (such as `gemini-2.0-flash` and `gemini-3.6-flash`) experienced severe rate limits and service spikes (`503 UNAVAILABLE`).

To preserve system reliability and ensure fully testable pipeline evaluation:

1. `app/services/vision_service.py` attempts a live HTTP call to the primary Vision API.
2. If the API returns a rate limit, service-unavailable response, or network exception, the engine seamlessly falls back to pre-analyzed, schema-validated metadata from `corpus_metadata.json`.
3. The metadata is validated against the Pydantic `ImageMetadata` schema and processed identically through the downstream pipeline, ensuring database persistence, vector calculation, and safety guard verification remain active and testable.

---

## Evaluation Benchmark

The evaluation benchmark (`evals/run_eval.py`) tests candidate ranking against a ground-truth dataset (`evals/dataset.json`).

### Benchmark Results

```text
=======================================================
      FLYRANK MATCHING ENGINE - EVALUATION BENCHMARK
=======================================================
 Total Evaluation Queries     : 3
 Top-1 Match Precision        : 100.00%
 Mean Reciprocal Rank (MRR)   : 1.0000
=======================================================
```

---

## Getting Started

### 1. Local Environment Setup

#### Clone Repository & Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./app.db
```

#### Seed Database & Run Ingestion

```bash
python seed_posts.py
python seed.py
```

#### Start Development Server

```bash
uvicorn app.main:app --reload
```

Access the interactive API documentation at:

`http://localhost:8000/docs`

---

## Docker Deployment

### Using Docker Compose

```bash
docker compose up -d --build
```

### Using a Standalone Docker Container

#### Build Image

```bash
docker build -t flyrank-api:latest .
```

#### Run Container

```bash
docker run -d \
  --name flyrank_container \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your_api_key_here" \
  flyrank-api:latest
```

---

## Running Benchmarks & Tests

### Run the Evaluation Benchmark

```bash
python -m evals.run_eval
```

### Run the Test Suite

```bash
pytest
```

---
