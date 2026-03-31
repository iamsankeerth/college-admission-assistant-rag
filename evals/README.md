# Golden Evaluation Dataset

golden_queries.jsonl contains manually curated evaluation prompts for the college RAG backend.

Each JSON line includes:

- id: stable case identifier
- college_name: institution filter passed to retrieval
- question: user query to evaluate
- expected_answer_points: key concepts that should appear in a good answer
- required_source_urls: official sources that should appear in citations
- expected_chunk_ids: expected seeded chunk ids for deterministic retrieval checks
- should_abstain: whether the system should decline to answer
- notes: reviewer guidance for manual inspection

Dataset design:

- 15 colleges
- 5 cases per college
- 4 answerable cases
- 1 abstain case

This gives 75 evaluation examples covering admissions, fees, placements, campus life, and unsupported claims.

Evaluation usage:

- `python -m app.evals.fast_eval` runs the deterministic PR gate over all 75 records.
- `python -m app.evals.full_eval` runs the RAGAS-backed offline suite on the 60 answerable records and keeps abstention quality in the fast gate.

The full eval measures:

- faithfulness
- answer relevancy
- context precision
- context recall

It writes both JSON and Markdown artifacts so CI uploads a human-readable nightly report.
