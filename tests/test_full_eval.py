from __future__ import annotations

import json

from app.evals.full_eval import build_evaluation_dataset, run_full_eval
from app.models import (
    GoldenQueryRecord,
    OfficialAnswer,
    QueryStatus,
    RetrievalTrace,
    RetrievedChunk,
)


class FakeOfficialEvidenceService:
    def answer_question(self, question: str, college_name: str | None, *, top_k: int | None = None):
        chunk = RetrievedChunk(
            chunk_id=f"{college_name or 'general'}::chunk-0",
            doc_id=f"{college_name or 'general'}::doc-0",
            college_name=college_name or "General",
            title=f"{college_name or 'General'} admissions",
            url="https://example.edu/admissions",
            content=f"{college_name or 'The college'} uses official counselling instructions.",
            retrieval_stage="reranked",
            rank=1,
            rerank_score=0.91,
        )
        official_answer = OfficialAnswer(
            summary=f"{college_name or 'The college'} uses official counselling instructions.",
            retrieved_chunks=[chunk],
        )
        return (
            QueryStatus.answered,
            official_answer.summary,
            [],
            official_answer,
            RetrievalTrace(),
        )


def test_build_evaluation_dataset_skips_abstain_records():
    records = [
        GoldenQueryRecord(
            id="answerable",
            college_name="IIT Hyderabad",
            question="How are admissions handled?",
            expected_answer_points=["Official counselling instructions"],
        ),
        GoldenQueryRecord(
            id="abstain",
            college_name="IIT Hyderabad",
            question="What was the 2025 exact closing rank?",
            should_abstain=True,
        ),
    ]

    dataset, sample_rows = build_evaluation_dataset(
        records,
        service=FakeOfficialEvidenceService(),
    )

    assert len(dataset.samples) == 1
    assert sample_rows[0]["id"] == "answerable"
    assert dataset.samples[0].user_input == "How are admissions handled?"
    assert dataset.samples[0].reference == "Official counselling instructions."


def test_run_full_eval_without_gemini_key_writes_skipped_report(tmp_path, monkeypatch):
    dataset_path = tmp_path / "golden.jsonl"
    dataset_path.write_text(
        "\n".join(
            [
                GoldenQueryRecord(
                    id="answerable",
                    college_name="IIT Hyderabad",
                    question="How are admissions handled?",
                    expected_answer_points=["Official counselling instructions"],
                ).model_dump_json(),
                GoldenQueryRecord(
                    id="abstain",
                    college_name="IIT Hyderabad",
                    question="What was the 2025 exact closing rank?",
                    should_abstain=True,
                ).model_dump_json(),
            ]
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "full_eval_report.json"

    monkeypatch.setattr(
        "app.evals.full_eval.run_fast_eval",
        lambda dataset_path=None: {
            "retrieval_recall_at_5": 1.0,
            "citation_coverage": 1.0,
            "abstention_precision": 1.0,
            "structured_output_validity": 1.0,
            "answer_source_consistency": 1.0,
        },
    )
    monkeypatch.setattr("app.evals.full_eval.settings.gemini_api_key", None)

    report = run_full_eval(dataset_path=dataset_path, report_path=report_path)

    assert report["status"] == "skipped"
    assert report["evaluated_records"] == 0
    assert "GEMINI_API_KEY" in report["reason"]
    assert report_path.exists()
    assert report_path.with_suffix(".md").exists()

    saved_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_report["fast_eval_metrics"]["citation_coverage"] == 1.0
