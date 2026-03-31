from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import settings
from app.models import GoldenQueryRecord, QueryStatus
from app.official.service import OfficialEvidenceService
from app.verification.service import FinalAnswerVerifier


def _load_records(path: str | Path) -> list[GoldenQueryRecord]:
    eval_path = Path(path)
    records: list[GoldenQueryRecord] = []
    with eval_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = line.lstrip("\ufeff").strip()
            if not payload:
                continue
            records.append(GoldenQueryRecord.model_validate_json(payload))
    return records


def run_fast_eval(dataset_path: str | Path | None = None) -> dict:
    records = _load_records(dataset_path or settings.eval_dataset_path)
    service = OfficialEvidenceService()
    verifier = FinalAnswerVerifier()

    retrieval_hits = 0
    citation_hits = 0
    abstain_true_positive = 0
    abstain_predicted = 0
    abstain_expected = 0
    structured_valid = 0
    answer_source_consistency = 0
    total_supported_claims = 0
    total_unsupported_claims = 0

    per_query_details: list[dict] = []
    failing_queries: list[str] = []

    for record in records:
        status, answer, citations, official_answer, _ = service.answer_question(
            record.question,
            record.college_name,
            top_k=settings.retrieval_top_k_rerank,
        )
        retrieved_ids = {chunk.chunk_id for chunk in official_answer.retrieved_chunks}
        retrieved_urls = {chunk.url for chunk in official_answer.retrieved_chunks}
        citation_ids = {citation.chunk_id for citation in citations}

        if not record.expected_chunk_ids or retrieved_ids.intersection(record.expected_chunk_ids):
            retrieval_hits += 1

        required_urls = set(record.required_source_urls)
        if not required_urls or citation_ids:
            matched_urls = {citation.url for citation in citations}
            if not required_urls or required_urls.issubset(matched_urls):
                citation_hits += 1

        if status in {QueryStatus.answered, QueryStatus.insufficient_evidence}:
            structured_valid += 1

        if all(citation.chunk_id in retrieved_ids and citation.url in retrieved_urls for citation in citations):
            answer_source_consistency += 1

        if record.should_abstain:
            abstain_expected += 1
        if status == QueryStatus.insufficient_evidence:
            abstain_predicted += 1
            if record.should_abstain:
                abstain_true_positive += 1

        query_claims: list[dict] = []
        query_faithfulness = 1.0
        if status == QueryStatus.insufficient_evidence:
            query_faithfulness = 1.0
        else:
            evidence_texts = [chunk.content for chunk in official_answer.retrieved_chunks]
            verif_report = verifier.verify(answer, evidence_texts)
            total_supported_claims += verif_report.supported_count
            total_unsupported_claims += verif_report.unsupported_count
            for check in verif_report.checks:
                evidence_chunk_ids = [
                    chunk.chunk_id
                    for chunk in official_answer.retrieved_chunks
                    if any(ev in chunk.content for ev in check.evidence)
                ]
                query_claims.append({
                    "claim": check.claim,
                    "supported": check.supported,
                    "confidence_score": check.confidence_score,
                    "evidence_chunk_ids": evidence_chunk_ids,
                })
            total_claims = len(verif_report.checks)
            if total_claims > 0:
                query_faithfulness = verif_report.supported_count / total_claims
            else:
                query_faithfulness = 1.0

        per_query_details.append({
            "query_id": record.id,
            "question": record.question,
            "college_name": record.college_name,
            "status": status.value,
            "claims": query_claims,
            "query_faithfulness": query_faithfulness,
        })

    total = max(len(records), 1)
    total_claims_evaluated = total_supported_claims + total_unsupported_claims
    abstention_precision = (
        abstain_true_positive / abstain_predicted if abstain_predicted else 1.0
    )
    faithfulness = (
        total_supported_claims / total_claims_evaluated if total_claims_evaluated > 0 else 1.0
    )
    metrics = {
        "total": len(records),
        "retrieval_recall_at_5": retrieval_hits / total,
        "citation_coverage": citation_hits / total,
        "abstention_precision": abstention_precision,
        "structured_output_validity": structured_valid / total,
        "answer_source_consistency": answer_source_consistency / total,
        "faithfulness": faithfulness,
        "total_claims_evaluated": total_claims_evaluated,
        "supported_claims": total_supported_claims,
        "unsupported_claims": total_unsupported_claims,
        "abstentions_expected": abstain_expected,
        "abstentions_predicted": abstain_predicted,
    }

    thresholds = {
        "retrieval_recall_at_5": 0.85,
        "citation_coverage": 0.95,
        "abstention_precision": 0.90,
        "structured_output_validity": 1.00,
        "faithfulness": 0.80,
    }

    for name, threshold in thresholds.items():
        value = metrics.get(name)
        if value is not None and value < threshold:
            failing_queries.append(name)

    return {
        "metrics": metrics,
        "thresholds": thresholds,
        "per_query_details": per_query_details,
        "failing_queries": failing_queries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic RAG evaluation gate.")
    parser.add_argument(
        "--dataset",
        default=settings.eval_dataset_path,
        help="Path to the golden JSONL dataset.",
    )
    parser.add_argument(
        "--report",
        default=str(Path(settings.eval_report_dir) / "fast_eval_report.json"),
        help="Where to write the JSON metrics report.",
    )
    args = parser.parse_args()

    result = run_fast_eval(args.dataset)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    failures = {
        name: value
        for name, value in result["metrics"].items()
        if name in result["thresholds"] and value < result["thresholds"][name]
    }
    print(json.dumps(result["metrics"], indent=2))
    if failures:
        raise SystemExit(
            "Fast eval thresholds failed: "
            + ", ".join(f"{name}={value:.3f}" for name, value in failures.items())
        )


if __name__ == "__main__":
    main()
