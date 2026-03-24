# College Admission Assistant RAG

FastAPI service for answering college admission questions with a mix of:

- official evidence retrieved from curated documents and URLs
- public signals gathered from Reddit and YouTube
- a lightweight verification pass over the final answer

## What It Does

This project combines three workflows:

- Official evidence retrieval: indexes official PDFs, HTML pages, and text files, then retrieves the most relevant chunks for a question.
- Public signals analysis: gathers student-reported sentiment, recurring themes, and possible promotional bias from Reddit and YouTube.
- Final answer verification: checks whether generated claims are supported by the retrieved evidence.

## Stack

- Python 3.11+
- FastAPI
- ChromaDB
- BeautifulSoup
- httpx
- PyPDF
- `youtube-transcript-api`
- `yt-dlp`

## Project Layout

```text
app/
  api/              FastAPI routes
  official/         Official document corpus, ingestion, retrieval, vector store
  public_signals/   Reddit/YouTube analysis pipeline
  verification/     Final answer verification
  models.py         Shared request/response models
data/
  official_corpus.json
tests/
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Run The API

```bash
uvicorn app.api.main:app --reload
```

The API will start on `http://127.0.0.1:8000`.

## Run Tests

```bash
pytest
```

## API Endpoints

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Ask A Question

`POST /query`

This endpoint combines official retrieval, optional public signals, and verification.

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is campus life like at IIT Hyderabad?",
    "college_name": "IIT Hyderabad",
    "run_verification": true
  }'
```

### Analyze Public Signals Only

`POST /query/college-signals`

```bash
curl -X POST http://127.0.0.1:8000/query/college-signals \
  -H "Content-Type: application/json" \
  -d '{
    "college_name": "IIT Hyderabad",
    "focus": "campus life and placements"
  }'
```

### Ingest Official Sources

`POST /admin/ingest`

Use this to add official URLs or local files to the retrieval corpus.

```bash
curl -X POST http://127.0.0.1:8000/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "college_name": "IIT Hyderabad",
    "urls": ["https://www.iith.ac.in/"],
    "file_paths": [],
    "title": "Institute Home Page",
    "source_kind": "official"
  }'
```

## Notes

- The repo ignores `data/chroma/`, so the local vector index is rebuilt on each machine.
- `data/official_corpus.json` is committed and acts as the seed document registry.
- Public signals are advisory. Official documents should remain the source of truth for admissions, fees, counselling, and deadlines.
