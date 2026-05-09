# Basic retrieval evaluation for the Week 2 RAG MVP.
#
# Ingests sample documents, runs eval questions against the retriever,
# and saves results to data/eval_results.json for inspection and comparison.
#
# Run with:
#   python -m src.eval.run_eval

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.api.schemas import DocumentIngestItem
from src.rag.ingest import ingest_documents
from src.rag.retriever import index_chunks, reset_retriever, retrieve
from src.utils.config import get_settings

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DOCS = ROOT / "data" / "sample_docs.json"
EVAL_QUESTIONS = ROOT / "data" / "eval_questions.json"
EVAL_RESULTS = ROOT / "data" / "eval_results.json"


def main() -> None:
    settings = get_settings()
    reset_retriever()

    # Ingest sample documents into the configured store (Pinecone or in-memory)
    sample_payload = json.loads(SAMPLE_DOCS.read_text())
    documents = [DocumentIngestItem(**doc) for doc in sample_payload["documents"]]
    chunks, _ = ingest_documents(documents, settings)
    index_chunks(chunks, settings)

    questions = json.loads(EVAL_QUESTIONS.read_text())
    results = []
    correct = 0

    for item in questions:
        matches = retrieve(item["question"], top_k=1, settings=settings)
        actual_document_id = matches[0].document_id if matches else None
        passed = actual_document_id == item["expected_document_id"]
        correct += int(passed)

        result = {
            "question": item["question"],
            "expected_document_id": item["expected_document_id"],
            "actual_document_id": actual_document_id,
            "passed": passed,
        }
        results.append(result)

        marker = "PASS" if passed else "FAIL"
        print(f"{marker}: {item['question']} — expected={item['expected_document_id']} actual={actual_document_id}")

    total = len(questions)
    accuracy = correct / total if total else 0.0
    print(f"\nRetrieval accuracy: {correct}/{total} ({accuracy:.0%})")

    # Save results to file so they can be tracked across runs
    output = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "results": results,
    }
    EVAL_RESULTS.write_text(json.dumps(output, indent=2))
    print(f"Results saved to {EVAL_RESULTS}")


if __name__ == "__main__":
    main()
