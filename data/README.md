# Data Assets

This folder now contains two complementary data layers for the college admission agent:

- `official_corpus.json`: seeded official-document RAG corpus used for grounded answers and citations
- `college_profiles.json`: structured recommendation dataset used for rank, budget, branch, and location matching

## `college_profiles.json` schema

Each profile includes:

- `college_name`, `short_name`, `category`, `college_type`
- `city`, `state`, `zone`, `is_metro`
- `hostel_available`, `campus_style`
- `accepted_exams`
- `official_admissions_url`
- `annual_cost_lakh`
  - `tuition`
  - `hostel_mess`
  - `other`
  - `total`
- `branches`
  - `name`
  - `exam`
  - `metric`
  - `value`
- `strength_tags`
- `notes`

## Intended use

`college_profiles.json` is designed for:

- rank and eligibility matching
- budget filtering
- location preference filtering
- branch-aware recommendation ranking
- Streamlit demo recommendations

The colleges in this file intentionally match the 15 institutions already present in the seeded official RAG corpus so that recommendation output can be paired with official-evidence explanations.
