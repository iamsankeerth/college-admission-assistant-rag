# College Admission Assistant RAG

Production-style RAG and recommendation backend for answering college questions with **official evidence first**, optional public signals second, and a Streamlit demo for personalized college shortlisting.

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
- Streamlit demo for student-facing exploration

## Architecture

```text
app/
  api/               FastAPI routes
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

evals/
  golden_queries.jsonl

sources/
  colleges/          manifest-driven seed sources
```

## Retrieval and Generation Flow

1. Normalize and chunk official documents.
2. Retrieve hybrid candidates from BM25-style lexical search and dense embeddings.
3. Rerank the merged candidate pool.
4. Reject weak evidence below threshold.
5. Generate a structured answer from the final retrieved chunks only.
6. Validate citations against retrieved chunks.
7. Optionally attach public signals if explicitly requested.

## Setup

### Requirements

- Python 3.11+
- `pip`
- optional: a Gemini API key for hosted answer generation and full eval runs

### Local install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

### Environment

Copy `.env.example` to `.env` and set the values you need.

```bash
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

## Running the API

```bash
uvicorn app.api.main:app --reload
```

Open:

- API: `http://127.0.0.1:8000`
- docs: `http://127.0.0.1:8000/docs`

## Running the Streamlit Demo

```bash
streamlit run streamlit_app.py
```

The Streamlit app calls local Python services directly, so you do not need to run the FastAPI server in a separate terminal just to try the recommendation experience.

## Example API Usage

### Health

```bash
curl http://127.0.0.1:8000/health
```

### Ask an official-evidence question

```bash
curl -X POST http://127.0.0.1:8000/query \
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
curl -X POST http://127.0.0.1:8000/admin/ingest \
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
curl -X POST http://127.0.0.1:8000/query/college-signals \
  -H "Content-Type: application/json" \
  -d '{
    "college_name": "IIT Hyderabad",
    "focus": "hostel life and placements"
  }'
```

Public signals are treated as advisory context, not the primary source of truth.

### Student recommendation demo

The Streamlit experience is designed for the exact use case of:

- exam + rank aware shortlisting
- budget filtering
- branch preference matching
- location preference matching
- hostel-sensitive recommendations
- RAG-backed official evidence snapshots for each college

See [docs/student_preference_guide.md](docs/student_preference_guide.md) for the input guidance that accompanies the demo.

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
streamlit run streamlit_app.py
```

The full eval writes both JSON and Markdown artifacts. If `GEMINI_API_KEY` is not configured, it writes a skipped report while still including the deterministic fast-gate metrics.

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

## Notes

- `data/chroma/` is ignored so local vector indexes are rebuilt per machine
- seeded corpus data is committed for reproducibility
- API-first by design; UI is intentionally out of scope for this phase
