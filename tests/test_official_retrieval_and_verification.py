import asyncio

from app.official.corpus import OfficialCorpus
from app.official.ingestion import OfficialIngestionService
from app.official.retrieval import HybridRetriever
from app.official.service import OfficialEvidenceService
from app.official.vector_store import OfficialVectorStore
from app.verification.service import FinalAnswerVerifier


def test_hybrid_retriever_returns_iith_sources():
    corpus = OfficialCorpus()
    vector_store = OfficialVectorStore()
    vector_store.upsert_chunks(corpus.chunks)
    retriever = HybridRetriever(corpus, vector_store)
    results = retriever.retrieve("What do official sources say about IIT Hyderabad fees?", "IIT Hyderabad")
    assert results
    assert any("IIT Hyderabad" in item.title for item in results)


def test_official_service_returns_retrieved_chunks():
    service = OfficialEvidenceService()
    answer = service.get_official_answer("How are IIT Hyderabad admissions handled?", "IIT Hyderabad", None)
    assert answer.retrieved_chunks
    assert answer.sources
    assert "official sources" in answer.summary.lower()


def test_final_answer_verifier_marks_unsupported_claim():
    verifier = FinalAnswerVerifier()
    report = verifier.verify(
        "Official Recommendation\n- The institute has a Mars campus.\n- Admissions are handled through national counselling.",
        ["Admissions are handled through national counselling such as JoSAA and CSAB."],
    )
    assert report.unsupported_count >= 1
    assert any(check.supported is False for check in report.checks)


def test_ingestion_service_indexes_local_file(tmp_path):
    source_file = tmp_path / "fees.txt"
    source_file.write_text(
        "IIT Hyderabad released an official hostel fee notice for the current semester.",
        encoding="utf-8",
    )
    registry_path = tmp_path / "registry.json"
    persist_dir = tmp_path / "chroma"
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
