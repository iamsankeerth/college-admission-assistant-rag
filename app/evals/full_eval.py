from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from app.config import settings
from app.evals.fast_eval import _load_records, run_fast_eval
from app.models import GoldenQueryRecord
from app.official.service import OfficialEvidenceService


FULL_EVAL_THRESHOLDS = {
    "faithfulness": 0.80,
    "answer_relevancy": 0.80,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_markdown_path(report_path: str | Path) -> Path:
    return Path(report_path).with_suffix(".md")


def _coerce_metric(value: Any) -> float | None:
    try:
        metric = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(metric) or math.isinf(metric):
        return None
    return metric


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if hasattr(value, "value"):
        return getattr(value, "value")
    metric = _coerce_metric(value)
    if metric is not None:
        return metric
    return value


def _reference_text(record: GoldenQueryRecord) -> str:
    if not record.expected_answer_points:
        return "Use only cited official evidence and abstain when support is missing."
    sentences = [point.rstrip(".") for point in record.expected_answer_points if point]
    return ". ".join(sentences) + "."


def build_evaluation_dataset(
    records: list[GoldenQueryRecord],
    service: OfficialEvidenceService | None = None,
):
    from ragas.dataset_schema import EvaluationDataset, SingleTurnSample

    rag_service = service or OfficialEvidenceService()
    samples: list[SingleTurnSample] = []
    sample_rows: list[dict[str, Any]] = []

    for record in records:
        if record.should_abstain:
            continue

        status, answer, citations, official_answer, _ = rag_service.answer_question(
            record.question,
            record.college_name,
            top_k=settings.retrieval_top_k_rerank,
        )
        retrieved_contexts = [chunk.content for chunk in official_answer.retrieved_chunks]
        sample = SingleTurnSample(
            user_input=record.question,
            response=answer,
            retrieved_contexts=retrieved_contexts,
            reference=_reference_text(record),
        )
        samples.append(sample)
        sample_rows.append(
            {
                "id": record.id,
                "college_name": record.college_name,
                "question": record.question,
                "status": status.value,
                "citation_count": len(citations),
                "retrieved_chunk_count": len(official_answer.retrieved_chunks),
            }
        )

    return EvaluationDataset(samples=samples), sample_rows


def _build_ragas_runtime():
    from google import genai
    from ragas.embeddings import HuggingFaceEmbeddings
    from ragas.llms import llm_factory
    from ragas.metrics.collections.answer_relevancy import AnswerRelevancy
    from ragas.metrics.collections.context_precision import ContextPrecision
    from ragas.metrics.collections.context_recall import ContextRecall
    from ragas.metrics.collections.faithfulness import Faithfulness

    client = genai.Client(api_key=settings.gemini_api_key)
    llm = llm_factory(
        settings.gemini_model,
        provider="google",
        client=client,
    )
    embeddings = HuggingFaceEmbeddings(
        model=settings.embedding_model_name,
        use_api=False,
        device="cpu",
    )
    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=embeddings),
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
    ]
    return llm, embeddings, metrics


def _aggregate_metrics(rows: list[dict[str, Any]], metric_names: list[str]) -> dict[str, float | None]:
    aggregated: dict[str, float | None] = {}
    for name in metric_names:
        values = [
            metric
            for row in rows
            if (metric := _coerce_metric(row.get(name))) is not None
        ]
        aggregated[name] = round(mean(values), 4) if values else None
    return aggregated


def _threshold_failures(metrics: dict[str, float | None]) -> dict[str, str]:
    failures: dict[str, str] = {}
    for name, threshold in FULL_EVAL_THRESHOLDS.items():
        value = metrics.get(name)
        if value is None:
            failures[name] = "metric missing"
        elif value < threshold:
            failures[name] = f"{value:.3f} < {threshold:.2f}"
    return failures


def _top_regressions(rows: list[dict[str, Any]], metric_name: str, limit: int = 5) -> list[dict[str, Any]]:
    sortable = [
        row
        for row in rows
        if _coerce_metric(row.get(metric_name)) is not None
    ]
    sortable.sort(key=lambda row: _coerce_metric(row.get(metric_name)) or 0.0)
    return sortable[:limit]


def _write_reports(
    report: dict[str, Any],
    report_path: str | Path,
    markdown_report_path: str | Path | None = None,
) -> tuple[Path, Path]:
    json_path = Path(report_path)
    markdown_path = (
        Path(markdown_report_path)
        if markdown_report_path is not None
        else _default_markdown_path(json_path)
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown_report(report), encoding="utf-8")
    return json_path, markdown_path


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Full Evaluation Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Dataset: `{report['dataset_path']}`",
        f"- Total records: `{report['total_records']}`",
        f"- Answerable records: `{report['answerable_records']}`",
        f"- Abstain records: `{report['abstain_records']}`",
        f"- Evaluated records: `{report['evaluated_records']}`",
        "",
        "## Fast Gate Snapshot",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for name, value in report.get("fast_eval_metrics", {}).items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(
        [
            "",
            "## RAGAS Metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    ragas_metrics = report.get("ragas_metrics", {})
    if ragas_metrics:
        for name, value in ragas_metrics.items():
            lines.append(f"| `{name}` | `{value}` |")
    else:
        lines.append("| `skipped` | `true` |")

    reason = report.get("reason")
    if reason:
        lines.extend(["", "## Note", "", reason])

    regressions = report.get("lowest_faithfulness_examples", [])
    if regressions:
        lines.extend(["", "## Lowest Faithfulness Examples", ""])
        for row in regressions:
            lines.append(
                f"- `{row['id']}` ({row['college_name']}): faithfulness={row.get('faithfulness')}, "
                f"answer_relevancy={row.get('answer_relevancy')}"
            )

    failures = report.get("threshold_failures", {})
    if failures:
        lines.extend(["", "## Threshold Failures", ""])
        for name, detail in failures.items():
            lines.append(f"- `{name}`: {detail}")

    lines.append("")
    return "\n".join(lines)


def run_full_eval(
    dataset_path: str | Path | None = None,
    report_path: str | Path | None = None,
    markdown_report_path: str | Path | None = None,
) -> dict[str, Any]:
    dataset = Path(dataset_path or settings.eval_dataset_path)
    json_report_path = Path(
        report_path or (Path(settings.eval_report_dir) / "full_eval_report.json")
    )
    records = _load_records(dataset)
    answerable_records = [record for record in records if not record.should_abstain]
    fast_metrics = run_fast_eval(dataset)

    base_report = {
        "generated_at": _utc_now(),
        "dataset_path": str(dataset),
        "total_records": len(records),
        "answerable_records": len(answerable_records),
        "abstain_records": len(records) - len(answerable_records),
        "fast_eval_metrics": fast_metrics,
        "judge_model": settings.gemini_model,
        "embedding_model": settings.embedding_model_name,
    }

    if not settings.gemini_api_key:
        report = {
            **base_report,
            "status": "skipped",
            "evaluated_records": 0,
            "ragas_metrics": {},
            "threshold_failures": {},
            "reason": "Full RAGAS evaluation requires GEMINI_API_KEY. Fast gate metrics are still included.",
        }
        _write_reports(report, json_report_path, markdown_report_path)
        return report

    try:
        from ragas import evaluate
    except ModuleNotFoundError:
        report = {
            **base_report,
            "status": "skipped",
            "evaluated_records": 0,
            "ragas_metrics": {},
            "threshold_failures": {},
            "reason": "RAGAS is not installed. Install the dev dependencies with `pip install -e .[dev]`.",
        }
        _write_reports(report, json_report_path, markdown_report_path)
        return report

    try:
        evaluation_dataset, sample_rows = build_evaluation_dataset(answerable_records)
        llm, embeddings, metrics = _build_ragas_runtime()
        result = evaluate(
            dataset=evaluation_dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=False,
            show_progress=True,
        )
        try:
            ragas_rows = result.to_pandas().to_dict(orient="records")
        except Exception:
            ragas_rows = [dict(row) for row in getattr(result, "scores", [])]

        enriched_rows = [
            sample | ragas_row
            for sample, ragas_row in zip(sample_rows, ragas_rows, strict=False)
        ]
        metric_names = [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ]
        ragas_metrics = _aggregate_metrics(enriched_rows, metric_names)
        failures = _threshold_failures(ragas_metrics)
        report = {
            **base_report,
            "status": "completed" if not failures else "failed",
            "evaluated_records": len(enriched_rows),
            "ragas_metrics": ragas_metrics,
            "threshold_failures": failures,
            "run_id": str(getattr(result, "run_id", "")),
            "total_tokens": getattr(result, "total_tokens", lambda: None)(),
            "total_cost": getattr(result, "total_cost", lambda: None)(),
            "lowest_faithfulness_examples": _top_regressions(
                enriched_rows,
                "faithfulness",
            ),
            "per_example_metrics": enriched_rows,
        }
        _write_reports(report, json_report_path, markdown_report_path)
    except Exception as exc:
        report = {
            **base_report,
            "status": "failed",
            "evaluated_records": 0,
            "ragas_metrics": {},
            "threshold_failures": {"runtime": f"{type(exc).__name__}: {exc}"},
            "reason": f"Full evaluation failed during runtime: {type(exc).__name__}: {exc}",
        }
        _write_reports(report, json_report_path, markdown_report_path)
        raise

    if report["threshold_failures"]:
        failure_summary = ", ".join(
            f"{name} ({detail})" for name, detail in report["threshold_failures"].items()
        )
        raise SystemExit(f"Full eval thresholds failed: {failure_summary}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the RAGAS-backed offline evaluation suite."
    )
    parser.add_argument(
        "--dataset",
        default=settings.eval_dataset_path,
        help="Path to the golden JSONL dataset.",
    )
    parser.add_argument(
        "--report",
        default=str(Path(settings.eval_report_dir) / "full_eval_report.json"),
        help="Where to write the JSON metrics report.",
    )
    parser.add_argument(
        "--markdown-report",
        default=None,
        help="Optional path for the Markdown summary artifact.",
    )
    args = parser.parse_args()

    report = run_full_eval(
        dataset_path=args.dataset,
        report_path=args.report,
        markdown_report_path=args.markdown_report,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
