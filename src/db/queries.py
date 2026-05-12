# Database query helpers for TrustRAG.
# Provides a clean, typed interface for common CRUD operations.

import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.db.database import get_db

logger = logging.getLogger(__name__)


# ============================================================================
# Conversations
# ============================================================================


def create_conversation(user_id: str, title: str | None = None) -> str:
    """Create a new conversation."""
    conversation_id = str(uuid4())
    db = get_db()
    db.execute(
        """
        INSERT INTO conversations (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (conversation_id, user_id, title, datetime.now(), datetime.now()),
    )
    db.commit()
    logger.info(f"Created conversation {conversation_id} for user {user_id}")
    return conversation_id


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    """Retrieve a conversation by ID."""
    db = get_db()
    return db.execute_one(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    )


def list_conversations(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """List all conversations for a user, ordered by most recent."""
    db = get_db()
    return db.execute_all(
        """
        SELECT * FROM conversations
        WHERE user_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )


# ============================================================================
# Messages
# ============================================================================


def create_message(
    conversation_id: str, role: str, content: str
) -> str:
    """Create a new message in a conversation."""
    message_id = str(uuid4())
    db = get_db()
    db.execute(
        """
        INSERT INTO messages (id, conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (message_id, conversation_id, role, content, datetime.now()),
    )
    db.commit()
    logger.debug(f"Created message {message_id} in conversation {conversation_id}")
    return message_id


def get_message(message_id: str) -> dict[str, Any] | None:
    """Retrieve a message by ID."""
    db = get_db()
    return db.execute_one("SELECT * FROM messages WHERE id = ?", (message_id,))


def list_messages(conversation_id: str) -> list[dict[str, Any]]:
    """List all messages in a conversation, ordered by creation time."""
    db = get_db()
    return db.execute_all(
        """
        SELECT * FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,),
    )


# ============================================================================
# AI Responses
# ============================================================================


def create_ai_response(
    message_id: str,
    question: str,
    answer: str,
    confidence: str,
    answer_status: str,
    trust_score: float,
    sources_used: int,
    retrieved_doc_ids: list[str] | None = None,
) -> str:
    """Create a new AI response record."""
    response_id = str(uuid4())
    db = get_db()

    retrieved_doc_ids_json = (
        json.dumps(retrieved_doc_ids) if retrieved_doc_ids else None
    )

    db.execute(
        """
        INSERT INTO ai_responses
        (id, message_id, question, answer, confidence, answer_status,
         trust_score, sources_used, retrieved_doc_ids, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            response_id,
            message_id,
            question,
            answer,
            confidence,
            answer_status,
            trust_score,
            sources_used,
            retrieved_doc_ids_json,
            datetime.now(),
        ),
    )
    db.commit()
    logger.debug(f"Created AI response {response_id}")
    return response_id


def get_ai_response(response_id: str) -> dict[str, Any] | None:
    """Retrieve an AI response by ID."""
    db = get_db()
    response = db.execute_one(
        "SELECT * FROM ai_responses WHERE id = ?", (response_id,)
    )
    if response and response.get("retrieved_doc_ids"):
        response["retrieved_doc_ids"] = json.loads(response["retrieved_doc_ids"])
    return response


def get_ai_response_by_message(message_id: str) -> dict[str, Any] | None:
    """Retrieve an AI response by message ID (1:1 relationship)."""
    db = get_db()
    response = db.execute_one(
        "SELECT * FROM ai_responses WHERE message_id = ?", (message_id,)
    )
    if response and response.get("retrieved_doc_ids"):
        response["retrieved_doc_ids"] = json.loads(response["retrieved_doc_ids"])
    return response


# ============================================================================
# Review Queue
# ============================================================================


def create_review_item(
    response_id: str, review_reason: str, trust_score: float
) -> str:
    """Add a response to the review queue."""
    review_id = str(uuid4())
    db = get_db()

    db.execute(
        """
        INSERT INTO review_queue
        (id, response_id, review_reason, trust_score, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (review_id, response_id, review_reason, trust_score, "pending", datetime.now()),
    )
    db.commit()
    logger.info(f"Added response {response_id} to review queue ({review_reason})")
    return review_id


def list_pending_reviews(limit: int = 50) -> list[dict[str, Any]]:
    """List all pending reviews, ordered by oldest first (FIFO)."""
    db = get_db()
    return db.execute_all(
        """
        SELECT * FROM review_queue
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT ?
        """,
        (limit,),
    )


def update_review(
    review_id: str,
    status: str,
    reviewer_id: str | None = None,
    reviewer_notes: str | None = None,
) -> None:
    """Update a review item with reviewer feedback."""
    db = get_db()
    db.execute(
        """
        UPDATE review_queue
        SET status = ?, reviewer_id = ?, reviewer_notes = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (status, reviewer_id, reviewer_notes, datetime.now(), review_id),
    )
    db.commit()
    logger.info(f"Updated review {review_id} to status {status}")


def get_review(review_id: str) -> dict[str, Any] | None:
    """Retrieve a review item by ID."""
    db = get_db()
    return db.execute_one("SELECT * FROM review_queue WHERE id = ?", (review_id,))


# ============================================================================
# Audit Log
# ============================================================================


def log_audit(
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_type: str | None = None,
    actor_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> int:
    """Write an immutable audit log entry."""
    db = get_db()
    details_json = json.dumps(details) if details else None

    cursor = db.execute(
        """
        INSERT INTO audit_log
        (action, resource_type, resource_id, actor_type, actor_id, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            action,
            resource_type,
            resource_id,
            actor_type,
            actor_id,
            details_json,
            datetime.now(),
        ),
    )
    db.commit()

    # Return the last inserted row ID
    return cursor.lastrowid or 0


def list_audit_logs(
    action: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    """Retrieve audit logs, optionally filtered by action."""
    db = get_db()

    if action:
        logs = db.execute_all(
            """
            SELECT * FROM audit_log
            WHERE action = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (action, limit),
        )
    else:
        logs = db.execute_all(
            """
            SELECT * FROM audit_log
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

    # Parse JSON details field
    for log in logs:
        if log.get("details"):
            log["details"] = json.loads(log["details"])

    return logs
