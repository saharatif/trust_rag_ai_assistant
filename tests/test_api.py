from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "TrustRAG API"}


def test_ingest_accepts_valid_documents():
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
