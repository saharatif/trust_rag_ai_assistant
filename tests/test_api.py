# Comprehensive API tests for TrustRAG.
# Tests all endpoints, error handling, and workflows.

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.main import app
from src.api.schemas import DocumentIngestItem, IngestRequest, RetrieveRequest
from src.rag.retriever import reset_retriever

client = TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_returns_ok(self):
        """GET /health should return 200 with ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_check_response_structure(self):
        """Health response should have expected structure."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestIngestEndpoint:
    """Test document ingestion endpoint."""

    def setup_method(self):
        """Reset retriever before each test."""
        reset_retriever()

    def test_ingest_single_document(self):
        """POST /ingest with a single valid document."""
        payload = {
            "documents": [
                {
                    "id": "doc1",
                    "title": "Test Policy",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "This is a test policy document with substantial content.",
                }
            ]
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["documents_received"] == 1
        assert data["chunks_created"] > 0
        assert data["status"] == "success"

    def test_ingest_multiple_documents(self):
        """POST /ingest with multiple documents."""
        payload = {
            "documents": [
                {
                    "id": "doc1",
                    "title": "Policy 1",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "First policy document with substantial content.",
                },
                {
                    "id": "doc2",
                    "title": "FAQ",
                    "source_type": "faq",
                    "department": "IT",
                    "text": "Frequently asked questions about IT support systems.",
                },
            ]
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["documents_received"] == 2
        assert data["chunks_created"] >= 2
        assert data["status"] == "success"

    def test_ingest_rejects_empty_documents_list(self):
        """POST /ingest should reject empty documents list."""
        payload = {"documents": []}
        response = client.post("/ingest", json=payload)
        assert response.status_code == 422

    def test_ingest_rejects_invalid_source_type(self):
        """POST /ingest should reject invalid source_type."""
        payload = {
            "documents": [
                {
                    "id": "doc1",
                    "title": "Test",
                    "source_type": "invalid_type",
                    "department": "HR",
                    "text": "Test document.",
                }
            ]
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 422

    def test_ingest_rejects_blank_fields(self):
        """POST /ingest should reject blank fields."""
        payload = {
            "documents": [
                {
                    "id": "",
                    "title": "Test",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "Test document.",
                }
            ]
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 422

    def test_ingest_rejects_whitespace_only_fields(self):
        """POST /ingest should reject whitespace-only fields."""
        payload = {
            "documents": [
                {
                    "id": "   ",
                    "title": "Test",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "Test document.",
                }
            ]
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 422


class TestRetrieveEndpoint:
    """Test document retrieval endpoint."""

    def setup_method(self):
        """Set up test data before each test."""
        reset_retriever()
        ingest_payload = {
            "documents": [
                {
                    "id": "doc1",
                    "title": "HR Policy Handbook",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "All full-time employees receive 20 days of PTO annually.",
                }
            ]
        }
        client.post("/ingest", json=ingest_payload)

    def test_retrieve_with_valid_query(self):
        """POST /retrieve with valid query returns matches."""
        payload = {"query": "PTO policy", "top_k": 5}
        response = client.post("/retrieve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "matches" in data
        assert isinstance(data["matches"], list)

    def test_retrieve_with_default_top_k(self):
        """POST /retrieve uses default top_k=5 when not specified."""
        payload = {"query": "PTO"}
        response = client.post("/retrieve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["matches"]) <= 5

    def test_retrieve_with_custom_top_k(self):
        """POST /retrieve respects custom top_k parameter."""
        payload = {"query": "PTO", "top_k": 3}
        response = client.post("/retrieve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["matches"]) <= 3

    def test_retrieve_validates_top_k_range(self):
        """POST /retrieve validates top_k is between 1 and 20."""
        response = client.post("/retrieve", json={"query": "test", "top_k": 0})
        assert response.status_code == 422

        response = client.post("/retrieve", json={"query": "test", "top_k": 100})
        assert response.status_code == 422

    def test_retrieve_rejects_blank_query(self):
        """POST /retrieve rejects blank query."""
        response = client.post("/retrieve", json={"query": "", "top_k": 5})
        assert response.status_code == 422


class TestChatEndpoint:
    """Test chat/RAG pipeline endpoint."""

    def setup_method(self):
        """Set up test data before each test."""
        reset_retriever()
        ingest_payload = {
            "documents": [
                {
                    "id": "doc1",
                    "title": "HR Policy",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "All full-time employees receive 20 days of PTO annually. PTO accrues monthly.",
                }
            ]
        }
        client.post("/ingest", json=ingest_payload)

    def test_chat_with_answerable_question(self):
        """POST /chat returns an answer for supported question."""
        payload = {"question": "How much PTO do employees get?", "top_k": 5}
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "confidence" in data
        assert data["confidence"] in ["low", "medium", "high"]
        assert "answer_status" in data
        assert data["answer_status"] in ["answered", "unsupported"]
        assert "trust_score" in data
        assert 0.0 <= data["trust_score"] <= 1.0
        assert "sources_used" in data
        assert isinstance(data["sources_used"], int)
        assert "needs_review" in data
        assert isinstance(data["needs_review"], bool)

    def test_chat_with_unanswerable_question(self):
        """POST /chat handles questions without supporting documents."""
        payload = {
            "question": "What is the weather today?",
            "top_k": 5,
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["answer_status"] == "unsupported"
        assert "don't have enough information" in data["answer"].lower()

    def test_chat_response_structure(self):
        """POST /chat response has all required fields."""
        payload = {"question": "PTO policy", "top_k": 5}
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "answer",
            "confidence",
            "answer_status",
            "trust_score",
            "sources_used",
            "needs_review",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_chat_rejects_blank_question(self):
        """POST /chat rejects blank question."""
        response = client.post("/chat", json={"question": "", "top_k": 5})
        assert response.status_code == 422


class TestReviewEndpoint:
    """Test human review endpoints."""

    def setup_method(self):
        """Set up test data before each test."""
        reset_retriever()
        ingest_payload = {
            "documents": [
                {
                    "id": "doc1",
                    "title": "Test Policy",
                    "source_type": "policy",
                    "department": "HR",
                    "text": "This is a test policy.",
                }
            ]
        }
        client.post("/ingest", json=ingest_payload)

    def test_list_pending_reviews_returns_empty_initially(self):
        """GET /review/pending returns empty list initially."""
        response = client.get("/review/pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_pending_reviews_with_limit_parameter(self):
        """GET /review/pending respects limit parameter."""
        response = client.get("/review/pending?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data

    def test_review_endpoint_structure(self):
        """Review endpoints follow expected structure."""
        response = client.get("/review/pending")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_approve_review_with_invalid_id(self):
        """POST /review/{id}/approve rejects invalid review ID."""
        response = client.post(
            "/review/nonexistent-id/approve",
            json={"reviewer_id": "reviewer1", "notes": "Approved"},
        )
        assert response.status_code == 404

    def test_reject_review_with_invalid_id(self):
        """POST /review/{id}/reject rejects invalid review ID."""
        response = client.post(
            "/review/nonexistent-id/reject",
            json={"reviewer_id": "reviewer1", "reason": "Inaccurate"},
        )
        assert response.status_code == 404

    def test_modify_review_with_invalid_id(self):
        """POST /review/{id}/modify rejects invalid review ID."""
        response = client.post(
            "/review/nonexistent-id/modify",
            json={
                "reviewer_id": "reviewer1",
                "corrected_answer": "Corrected text",
                "notes": "Fixed",
            },
        )
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_invalid_json_returns_422(self):
        """Invalid JSON payload returns 422."""
        response = client.post(
            "/ingest",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields_returns_422(self):
        """Missing required fields returns 422."""
        response = client.post("/ingest", json={"documents": [{}]})
        assert response.status_code == 422

    def test_nonexistent_endpoint_returns_404(self):
        """Request to nonexistent endpoint returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_unsupported_method_returns_405(self):
        """Unsupported HTTP method returns 405."""
        response = client.post("/health")
        assert response.status_code == 405


class TestIntegration:
    """Integration tests for full workflows."""

    def setup_method(self):
        """Reset retriever before each test."""
        reset_retriever()

    def test_end_to_end_workflow(self):
        """Test complete workflow: ingest → retrieve → chat."""
        # Step 1: Ingest documents
        ingest_response = client.post(
            "/ingest",
            json={
                "documents": [
                    {
                        "id": "doc1",
                        "title": "Employee Handbook",
                        "source_type": "manual",
                        "department": "HR",
                        "text": "Employees work Monday through Friday. Remote work is allowed with manager approval.",
                    }
                ]
            },
        )
        assert ingest_response.status_code == 200
        assert ingest_response.json()["status"] == "success"

        # Step 2: Retrieve documents
        retrieve_response = client.post(
            "/retrieve",
            json={"query": "work schedule", "top_k": 5},
        )
        assert retrieve_response.status_code == 200
        matches = retrieve_response.json()["matches"]
        assert len(matches) > 0

        # Step 3: Chat
        chat_response = client.post(
            "/chat",
            json={"question": "What is the work schedule?", "top_k": 5},
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["answer_status"] in ["answered", "unsupported"]
        assert 0.0 <= chat_data["trust_score"] <= 1.0

    def test_multiple_document_types_workflow(self):
        """Test workflow with multiple document types."""
        # Ingest different document types
        ingest_response = client.post(
            "/ingest",
            json={
                "documents": [
                    {
                        "id": "policy1",
                        "title": "Security Policy",
                        "source_type": "policy",
                        "department": "Security",
                        "text": "All passwords must be at least 16 characters with mixed case and numbers.",
                    },
                    {
                        "id": "faq1",
                        "title": "IT FAQ",
                        "source_type": "faq",
                        "department": "IT",
                        "text": "Q: How do I reset my password? A: Use the self-service portal.",
                    },
                ]
            },
        )
        assert ingest_response.status_code == 200

        # Query for policy information
        response = client.post(
            "/chat",
            json={"question": "What are password requirements?", "top_k": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer_status"] in ["answered", "unsupported"]

