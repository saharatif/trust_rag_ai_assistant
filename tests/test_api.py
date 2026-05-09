from fastapi.testclient import TestClient

from src.api.main import app
from src.rag.retriever import reset_retriever


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "TrustRAG API"}


def test_ingest_accepts_valid_documents():
    reset_retriever()
    response = client.post(
        "/ingest",
        json={
            "documents": [
                {
                    "id": "policy_001",
                    "title": "Employee Travel Policy",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "Travel reimbursement requires receipts within thirty days.",
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["documents_received"] == 1
    assert response.json()["chunks_created"] == 1
    assert response.json()["status"] == "success"


def test_ingest_rejects_blank_document_text():
    response = client.post(
        "/ingest",
        json={
            "documents": [
                {
                    "id": "policy_001",
                    "title": "Employee Travel Policy",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "   ",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_retrieve_returns_ingested_chunks():
    reset_retriever()
    client.post(
        "/ingest",
        json={
            "documents": [
                {
                    "id": "policy_001",
                    "title": "Employee Travel Policy",
                    "source_type": "policy",
                    "department": "HR",
                    "text": (
                        "Business class flights require director approval "
                        "for international trips longer than eight hours."
                    ),
                }
            ]
        },
    )

    response = client.post(
        "/retrieve",
        json={"query": "Can employees book business class flights?", "top_k": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "Can employees book business class flights?"
    assert body["matches"][0]["document_id"] == "policy_001"
    assert body["matches"][0]["title"] == "Employee Travel Policy"


def test_chat_returns_answer_with_sources():
    reset_retriever()
    client.post(
        "/ingest",
        json={
            "documents": [
                {
                    "id": "policy_001",
                    "title": "Employee Travel Policy",
                    "source_type": "policy",
                    "department": "HR",
                    "text": (
                        "Business class flights require director approval "
                        "for international trips longer than eight hours."
                    ),
                }
            ]
        },
    )

    response = client.post(
        "/chat",
        json={"question": "Can employees book business class flights?", "top_k": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert "director approval" in body["answer"]
    assert body["sources"][0]["chunk_id"] == "policy_001_chunk_001"


def test_chat_returns_safe_fallback_for_unsupported_question():
    reset_retriever()
    client.post(
        "/ingest",
        json={
            "documents": [
                {
                    "id": "faq_001",
                    "title": "IT Support FAQ",
                    "source_type": "faq",
                    "department": "IT",
                    "text": "Password resets must use identity verification.",
                }
            ]
        },
    )

    response = client.post(
        "/chat",
        json={"question": "What is the cafeteria lunch menu?", "top_k": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unsupported"
    assert body["confidence"] == "low"
    assert body["sources"] == []
