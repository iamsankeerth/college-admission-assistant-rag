from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from statistics import mean

from app.config import settings
from app.official.service import OfficialEvidenceService


QUERY_SET = [
    "What are the placement statistics for IIT Hyderabad?",
    "What is the admission process for IIT Delhi?",
    "How are hostel facilities at IIT Bombay?",
    "What are the fees for NIT Warangal?",
    "Tell me about the faculty at IIT Madras.",
    "What is the cutoff rank for computer science at IIT Kanpur?",
    "How are labs and infrastructure at BITS Pilani?",
    "What placement support exists at VIT Vellore?",
]


def run_latency_check(max_p50_ms: float = 2000.0, max_p95_ms: float = 5000.0) -> dict:
    service = OfficialEvidenceService()
    latencies: list[float] = []
    errors = 0

    for question in QUERY_SET:
        college_name = None
        if "IIT" in question:
            parts = question.split("for")[-1].strip().split()
            if len(parts) >= 2:
                college_name = f"{parts[0]} {parts[1]}"
            elif len(parts) == 1:
                college_name = parts[0]
        elif "NIT" in question:
            college_name = question.split("for")[-1].strip()
        elif "BITS" in question:
            college_name = question.split("for")[-1].strip()
        elif "VIT" in question:
            college_name = question.split("for")[-1].strip()

        start = time.time()
        try:
            service.answer_question(question, college_name)
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)
        except Exception:
            errors += 1

    if not latencies:
        return {
            "status": "no_data",
            "message": "No successful queries completed",
            "p50_ms": None,
            "p95_ms": None,
        }

    sorted_latencies = sorted(latencies)
    p50_idx = int(len(sorted_latencies) * 0.5)
    p95_idx = int(len(sorted_latencies) * 0.95)

    p50 = round(sorted_latencies[p50_idx], 2)
    p95 = round(sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else sorted_latencies[-1], 2)
    avg_ms = round(mean(latencies), 2)

    p50_pass = p50 <= max_p50_ms
    p95_pass = p95 <= max_p95_ms

    failing_metrics: list[str] = []
    if not p50_pass:
        failing_metrics.append(f"p50_latency: {p50}ms > {max_p50_ms}ms threshold")
    if not p95_pass:
        failing_metrics.append(f"p95_latency: {p95}ms > {max_p95_ms}ms threshold")
    if errors > 0:
        failing_metrics.append(f"query_errors: {errors} queries failed")

    return {
        "status": "pass" if (p50_pass and p95_pass) else "fail",
        "queries_run": len(latencies),
        "errors": errors,
        "p50_ms": p50,
        "p95_ms": p95,
        "avg_ms": avg_ms,
        "threshold_p50_ms": max_p50_ms,
        "threshold_p95_ms": max_p95_ms,
        "p50_pass": p50_pass,
        "p95_pass": p95_pass,
        "failing_metrics": failing_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run latency budget check.")
    parser.add_argument("--max-p50-ms", type=float, default=2000.0)
    parser.add_argument("--max-p95-ms", type=float, default=5000.0)
    parser.add_argument("--report", default=str(Path(settings.eval_report_dir) / "latency_check.json"))
    args = parser.parse_args()

    result = run_latency_check(max_p50_ms=args.max_p50_ms, max_p95_ms=args.max_p95_ms)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))

    if result["status"] == "fail":
        print(f"\nFailing metrics ({len(result['failing_metrics'])}):")
        for fm in result["failing_metrics"]:
            print(f"  - {fm}")
        raise SystemExit(f"Latency budget failed: p50={result['p50_ms']}ms, p95={result['p95_ms']}ms")


if __name__ == "__main__":
    main()
