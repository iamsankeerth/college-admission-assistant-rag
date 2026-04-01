from __future__ import annotations

import asyncio

from app.evals.fast_eval import run_fast_eval
from app.ingest.manifests import load_manifest
from app.official.corpus import OfficialCorpus, chunk_text
from app.official.ingestion import OfficialIngestionService
from app.official.retrieval import HybridRetriever
from app.official.service import OfficialEvidenceService
from app.official.vector_store import OfficialVectorStore
from app.verification.service import FinalAnswerVerifier


def test_sentence_aware_chunking_preserves_overlap():
    text = " ".join(
        f"Sentence {idx} explains admissions and hostel details for a college."
        for idx in range(40)
    )
    chunks = chunk_text(text, chunk_size=40, overlap=10)
    assert len(chunks) >= 2
    assert "Sentence 0" in chunks[0]


def test_hybrid_retriever_returns_iith_sources():
    corpus = OfficialCorpus()
    vector_store = OfficialVectorStore()
    vector_store.upsert_chunks(corpus.chunks)
    retriever = HybridRetriever(corpus, vector_store)
    retriever.cache.clear()
    results, trace = retriever.retrieve(
        "What do official sources say about IIT Hyderabad fees?",
        "IIT Hyderabad",
    )
    assert results
    assert trace.reranked_candidates
    assert any("IIT Hyderabad" in item.title for item in results)


def test_official_service_returns_citations():
    service = OfficialEvidenceService()
    status, answer, citations, official_answer, trace = service.answer_question(
        "How are IIT Hyderabad admissions handled?",
        "IIT Hyderabad",
    )
    assert status == "answered"
    assert answer
    assert citations
    assert official_answer.retrieved_chunks
    assert trace.decision is not None


def test_final_answer_verifier_marks_unsupported_claim():
    verifier = FinalAnswerVerifier()
    report = verifier.verify(
        "Official Recommendation\n- The institute has a Mars campus.\n- Admissions are handled through national counselling.",
        ["Admissions are handled through national counselling such as JoSAA and CSAB."],
    )
    assert report.unsupported_count >= 1
    assert any(check.supported is False for check in report.checks)


def test_ingestion_service_indexes_local_file(workspace_tmp_path):
    source_file = workspace_tmp_path / "fees.txt"
    source_file.write_text(
        "IIT Hyderabad released an official hostel fee notice for the current semester.",
        encoding="utf-8",
    )
    registry_path = workspace_tmp_path / "registry.json"
    persist_dir = workspace_tmp_path / "chroma"
    corpus = OfficialCorpus(registry_path=registry_path)
    vector_store = OfficialVectorStore(persist_dir=persist_dir)
    ingestion = OfficialIngestionService(corpus, vector_store)

    result, errors = asyncio.run(
        ingestion.ingest(
            college_name="IIT Hyderabad",
            urls=[],
            file_paths=[str(source_file)],
            title="Local Fee Notice",
        )
    )

    assert not errors
    assert result
    query_results = vector_store.query("hostel fee notice", "IIT Hyderabad")
    assert query_results


def test_manifest_loader_reads_seed_manifest():
    manifest = load_manifest("IIT Hyderabad")
    assert manifest.college_name == "IIT Hyderabad"
    assert manifest.allowed_domains
    assert manifest.seed_urls


def test_fast_eval_returns_threshold_metrics():
    result = run_fast_eval()
    assert "metrics" in result
    assert "per_query_details" in result
    assert "thresholds" in result
    assert "failing_queries" in result
    metrics = result["metrics"]
    assert metrics["retrieval_recall_at_5"] >= 0
    assert metrics["citation_coverage"] >= 0
    assert metrics["structured_output_validity"] > 0
    assert "faithfulness" in metrics
    assert "total_claims_evaluated" in metrics
    assert "supported_claims" in metrics
    assert "unsupported_claims" in metrics
    assert 0 <= metrics["faithfulness"] <= 1
