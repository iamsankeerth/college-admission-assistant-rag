# College Admission Assistant RAG

Production-style RAG and recommendation backend for answering college questions with **official evidence first**, optional public signals second, and a React frontend for personalized college shortlisting.

## Why This Project Exists

This repo is designed to look like the kind of AI backend a hiring manager can inspect and say:

- retrieval quality is measured
- answer generation is grounded in retrieved evidence
- unsupported questions abstain instead of hallucinating
- prompts and models are configured explicitly
- CI protects quality instead of only checking syntax

The default product story is:

1. ingest official college documents
2. retrieve and rerank the best evidence
3. generate a cited answer
4. rank colleges against student preferences like rank, budget, branch, and location
5. abstain when evidence is weak
6. optionally layer in Reddit/YouTube signals as secondary context

## Core Capabilities

- Official-document ingestion from URLs, PDFs, and local files
- Hybrid retrieval over lexical and dense signals
- Reranking before answer generation
- Structured answer generation with citations
- Personalized recommendation scoring for student shortlisting
- Verification and evaluation hooks
- Optional public-signals analysis kept outside the main trust path
- React 19 frontend with IvoryTower design system

## Architecture

```
app/
  api/               FastAPI routes (v1 router + health endpoints)
  dependencies.py    Shared service singletons (single instantiation)
  official/          official corpus, chunking, ingestion, retrieval, vector store
  public_signals/    optional Reddit/YouTube analysis
  verification/      claim-support verification
  models.py          API and pipeline schemas

config/
  prompts/           answer and abstain prompts
  models.yaml        provider/model settings
  retrieval.yaml     retrieval thresholds and top-k settings

data/
  official_corpus.json
  chroma/            vector index (gitignored, rebuilt per machine)

evals/
  golden_queries.jsonl

frontend/
  src/
    components/      React components (admin/, landing/, Shortlist*, Explore*, Compare*)
    styles/          global CSS + design tokens
  public/            PWA manifest + icons

sources/
  colleges/          manifest-driven seed sources
```

## Setup

### Requirements

- Python 3.11+
- Node.js 18+ (for frontend)
- `pip`
- optional: a Gemini API key for hosted answer generation and full eval runs

### Backend setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows

# Copy environment variables
copy .env.example .env
```

Key settings:

- `ANSWER_PROVIDER`: `gemini` by default, with template fallback when no key is set
- `GEMINI_API_KEY`: enables Gemini-backed answer generation and full evals
- `GEMINI_MODEL`: default hosted generator model
- `EMBEDDING_BACKEND`: `sentence_transformers` or `hash`
- `EMBEDDING_MODEL_NAME`: local embedding model
- `RERANKER_BACKEND`: `cross_encoder` or `heuristic`
- `RERANKER_MODEL_NAME`: local cross-encoder reranker
- `RETRIEVAL_TOP_K_LEXICAL`, `RETRIEVAL_TOP_K_VECTOR`, `RETRIEVAL_TOP_K_RERANK`
- `MIN_RERANK_SCORE_TO_ANSWER`
- `PUBLIC_SIGNALS_ENABLED`: keeps public signals opt-in

### Frontend setup

```bash
cd frontend
npm install
```

## Running Locally

You need **two terminals** running simultaneously.

### Terminal 1 — Backend API

```bash
uvicorn app.api.main:app --reload --port 8000
```

### Terminal 2 — Frontend Dev Server

```bash
cd frontend
npm run dev
```

Then open **http://localhost:3000** in your browser.

### How the proxy works

The Vite dev server proxies all `/v1/*`, `/health`, `/recommend`, and `/query` requests to `http://localhost:8000`. The browser only ever talks to `localhost:3000` — no CORS configuration needed in development.

### API and docs

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

All API endpoints are under `/v1/` (e.g., `/v1/recommend`, `/v1/query`, `/v1/admin/colleges`).

## Running the Streamlit Demo (deprecated)

The Streamlit frontend is no longer maintained. Use the React frontend instead.

```bash
streamlit run streamlit_app.py
```

## Example API Usage

All endpoints live under `/v1/`. Base URL: `http://localhost:8000`

### Health

```bash
curl http://localhost:8000/health
```

### Ask an official-evidence question

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How are undergraduate admissions handled at IIT Hyderabad?",
    "college_name": "IIT Hyderabad",
    "run_verification": true,
    "include_public_signals": false,
    "debug": true
  }'
```

Expected behavior:

- returns an `answered` response with citations when official evidence is strong
- returns `insufficient_evidence` when support is weak or missing

### Ingest official sources

```bash
curl -X POST http://localhost:8000/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "college_name": "IIT Hyderabad",
    "urls": ["https://www.iith.ac.in/academics/admissions/"],
    "file_paths": [],
    "title": "Admissions Page",
    "source_kind": "official"
  }'
```

### Optional public signals

```bash
curl -X POST http://localhost:8000/v1/query/college-signals \
  -H "Content-Type: application/json" \
  -d '{
    "college_name": "IIT Hyderabad",
    "focus": "hostel life and placements"
  }'
```

Public signals are treated as advisory context, not the primary source of truth.

### Get personalized recommendations

```bash
curl -X POST http://localhost:8000/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "entrance_exam": "JEE Main",
    "rank": 5000,
    "budget_lakh": 8,
    "preferred_branches": ["Computer Science and Engineering"],
    "max_results": 5
  }'
```

## Quality Gates

The repo is structured around two evaluation layers.

### Fast deterministic PR gate

Runs on every PR and push:

- unit tests
- API smoke coverage
- deterministic retrieval/evidence checks
- structured-output validation
- citation consistency checks

### Full offline quality eval

Runs on schedule or manually:

- golden eval dataset
- RAGAS-backed `faithfulness`, `answer_relevancy`, `context_precision`, and `context_recall`
- Gemini judge model plus local Hugging Face embeddings for offline scoring
- report artifacts for inspection

This split keeps PR checks stable and fast while preserving a richer offline evaluation path.

## CI Workflows

- `ci.yml`: install, test, run the fast evaluation gate, upload artifacts
- `nightly_eval.yml`: scheduled/manual full eval with `GEMINI_API_KEY`

## Development Commands

```bash
pip install -e .[dev]
pytest
python -m app.evals.fast_eval --dataset evals/golden_queries.jsonl
python -m app.evals.full_eval --dataset evals/golden_queries.jsonl --report evals/full_eval_report.json --markdown-report evals/full_eval_report.md
python -m app.ingest.sync_college --college "IIT Hyderabad"
python -m app.ingest.sync_all
```

## Frontend Tech Stack

- **React 19** + **Vite 8** — fast dev server and optimized production builds
- **React Router v7** — client-side routing with routes for `/`, `/shortlist`, `/results`, `/explore/:name`, `/compare`, `/admin/colleges`, `/admin/corpus`
- **Framer Motion 12** — page transitions, card animations, expand/collapse
- **Lucide React** — consistent icon set
- **PWA** — service worker + offline caching via `vite-plugin-pwa`
- **IvoryTower design** — warm cream (#FDFCF9), gold accent (#B8963E), Playfair Display + DM Sans

### Frontend production build

```bash
cd frontend
npm run build    # outputs to frontend/dist/
npm run preview  # serve the built files locally
```

## Public Signals Positioning

This repo intentionally centers **official-document RAG**.

Reddit and YouTube analysis remain in the codebase because they are useful for:

- lived-experience context
- recurring student concerns
- spotting likely promotional content

But they are not part of the primary trust path and they do not define whether the core RAG system is correct.

## What Makes This Production-Style

- official evidence first
- recommendation output grounded in student constraints
- explicit abstention path
- config-managed prompts and models
- evaluation dataset committed in repo
- CI gating on quality regressions
- retrieval and generation treated as separate subsystems
- single shared service instantiation (no duplicate models in memory)

## Notes

- `data/chroma/` is gitignored so local vector indexes are rebuilt per machine
- seeded corpus data is committed for reproducibility
- `app/dependencies.py` provides a single shared instance of each service to avoid duplicate model loading
- Admin endpoints (`/v1/admin/*`) have no auth — add JWT/API key middleware before production exposure
