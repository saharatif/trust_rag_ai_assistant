# TrustRAG Architecture

**TrustRAG** is an enterprise AI knowledge assistant that combines Retrieval-Augmented Generation (RAG), trust scoring, human-in-the-loop review, and audit logging to provide reliable, traceable answers from approved internal documents.

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Agentic Workflow](#agentic-workflow)
5. [Trust Scoring](#trust-scoring)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Deployment](#deployment)

---

## High-Level Overview

```
User Question
    ↓
FastAPI Backend
    ↓
Vector Search (Retrieval)
    ↓
Trust Score Calculation
    ↓
LLM Answer Generation
    ↓
Agent Workflow (LangGraph)
    ↓
Confidence & Risk Assessment
    ↓
[Trust Score ≥ 0.5?]
    ├─ YES → Direct Delivery
    └─ NO  → Human Review Queue
    ↓
Audit Logging
    ↓
Response to User
```

---

## System Components

### 1. **FastAPI Backend** (`src/api/`)

- **Entry Point:** `src/api/main.py`
- **Routes:**
  - `POST /ingest` — Document ingestion and chunking
  - `POST /retrieve` — Vector search for relevant documents
  - `POST /chat` — Full RAG pipeline (retrieve → generate → return)
  - `GET /review/pending` — List pending reviews
  - `POST /review/{review_id}/approve` — Approve a response
  - `POST /review/{review_id}/reject` — Reject a response
  - `POST /review/{review_id}/modify` — Edit and approve a response

- **Schemas:** `src/api/schemas.py`
  - Pydantic models for request/response validation
  - API documentation via OpenAPI (Swagger)

### 2. **RAG Pipeline** (`src/rag/`)

- **Chunking** (`chunking.py`) — Splits documents into overlapping chunks
- **Embeddings** (`embeddings.py`) — Generates vector embeddings using sentence-transformers
- **Retriever** (`retriever.py`) — In-memory vector search (local) or Pinecone (production)
- **Prompt Builder** (`prompt_builder.py`) — Constructs RAG prompts with retrieved context
- **Generator** (`generator.py`) — Calls LLM (OpenAI) or fallback extraction to generate answers

### 3. **Agentic Workflow** (`src/agents/`)

**LangGraph-based orchestration** that chains operations:

- **State** (`state.py`) — `AgentState` dataclass tracking workflow data
- **Nodes** (`nodes.py`) — Functions for each workflow step:
  - `node_retrieve` — Fetch top-k documents
  - `node_generate_answer` — LLM answer generation
  - `node_score_trust` — Calculate trust score
  - `node_route_review` — Decide if review is needed
- **Graph** (`graph.py`) — Compiled LangGraph workflow

### 4. **Trust Scoring** (`src/trust/`)

- `trust_score.py` — Calculates 0.0-1.0 trust score based on:
  - Relevance of retrieved documents
  - Source credibility (policy > contract > manual > report > faq)
  - LLM confidence level
  - Whether answer is grounded in context
- Thresholds:
  - Score < 0.5 → Route for human review
  - Score 0.5-0.75 → Medium confidence
  - Score ≥ 0.75 → High confidence

### 5. **Database** (`src/db/`)

**SQLite for local development, PostgreSQL-ready for production.**

- `schema.sql` — Database schema with tables:
  - `conversations` — User sessions
  - `messages` — User and AI messages
  - `ai_responses` — Detailed answer tracking (question, answer, confidence, trust_score)
  - `review_queue` — Responses pending human approval
  - `audit_log` — Immutable compliance log
- `database.py` — Connection management and schema initialization
- `queries.py` — CRUD helpers for all operations

### 6. **Configuration** (`src/utils/`)

- `config.py` — Loads settings from `.env` (API keys, model selection, etc.)
- `logging.py` — Structured logging with JSON output
- `rate_limit.py` — Per-client rate limiting

---

## Data Flow

### 1. **Document Ingestion**

```
POST /ingest
  ↓
[Document Validation]
  ↓
[Chunking] → 512-char chunks with 128-char overlap
  ↓
[Embedding Generation] → Sentence-transformers
  ↓
[Vector Store] → Store in-memory or Pinecone
  ↓
Response: chunks_created
```

### 2. **Chat / Answer Generation**

```
POST /chat?question="..."
  ↓
[Agent Workflow Starts]
  ├─ node_retrieve → Get top-5 documents
  ├─ node_generate_answer → LLM generates answer
  ├─ node_score_trust → Calculate trust score
  ├─ node_route_review → Decide if review needed
  │   ├─ If trust_score < 0.5 → Add to review_queue
  │   └─ If trust_score ≥ 0.5 → Ready for delivery
  └─ [Audit Log Entry]
  ↓
Response: answer, confidence, trust_score, needs_review
```

### 3. **Human Review**

```
GET /review/pending
  ↓
[Show pending responses with context]
  ↓
Reviewer chooses:
  ├─ POST /review/{id}/approve → Mark approved
  ├─ POST /review/{id}/reject → Mark rejected
  └─ POST /review/{id}/modify → Edit answer + approve
  ↓
[Audit Log Entry with reviewer_id]
  ↓
Response marked as ready or rejected
```

---

## Agentic Workflow

**LangGraph Graph Structure:**

```
┌─────────┐
│Retrieve │ — Query vector store for top-k documents
└────┬────┘
     │
     ↓
┌──────────────┐
│Generate      │ — LLM produces grounded answer
│Answer        │
└────┬─────────┘
     │
     ↓
┌──────────┐
│Score     │ — Calculate trust score (0.0-1.0)
│Trust     │
└────┬─────┘
     │
     ↓
┌──────────────┐
│Route Review  │ — Conditional: review or ready?
└────┬─────────┘
     │
     ├─ [Trust < 0.5] → Review Queue
     └─ [Trust ≥ 0.5] → Ready for Delivery
```

**State Transitions:**

- `init` → `retrieved` → `generated` → `scored` → `ready` or `review`
- Each node can transition state and add errors

---

## Trust Scoring

### Formula

```
trust_score = (weighted_avg_relevance_and_credibility) * confidence_multiplier
```

Where:

- **Relevance**: Embedding similarity score (0.0-1.0)
- **Credibility by Source**:
  - Policy: 1.0
  - Contract: 1.0
  - Manual: 0.9
  - Report: 0.8
  - FAQ: 0.6
- **Confidence Multiplier**:
  - High: 1.0
  - Medium: 0.85
  - Low: 0.5

### Example

- **Policy** document with 0.95 similarity + **high confidence** → ~0.95 score
- **FAQ** document with 0.8 similarity + **low confidence** → ~0.24 score
- **Multiple mixed sources** → Average weighted score

### Thresholds

| Score Range | Action          | Reason                 |
| ----------- | --------------- | ---------------------- |
| < 0.2       | Review          | insufficient_context   |
| 0.2 - 0.4   | Review          | low_source_confidence  |
| 0.4 - 0.5   | Review          | below_review_threshold |
| ≥ 0.5       | Direct Delivery | —                      |
| ≥ 0.75      | High Confidence | —                      |

---

## Database Schema

### Tables

#### `conversations`

Tracks user sessions.

```sql
id TEXT PRIMARY KEY
user_id TEXT NOT NULL
created_at TIMESTAMP
updated_at TIMESTAMP
title TEXT
```

#### `messages`

Individual turns in a conversation.

```sql
id TEXT PRIMARY KEY
conversation_id TEXT (FK: conversations)
role TEXT ('user' | 'assistant')
content TEXT
created_at TIMESTAMP
```

#### `ai_responses`

Detailed RAG pipeline results.

```sql
id TEXT PRIMARY KEY
message_id TEXT UNIQUE (FK: messages)
question TEXT
answer TEXT
confidence TEXT ('low' | 'medium' | 'high')
answer_status TEXT ('answered' | 'unsupported')
trust_score REAL (0.0-1.0)
sources_used INT
retrieved_doc_ids TEXT (JSON array)
created_at TIMESTAMP
```

#### `review_queue`

Responses pending human approval.

```sql
id TEXT PRIMARY KEY
response_id TEXT UNIQUE (FK: ai_responses)
review_reason TEXT
trust_score REAL
status TEXT ('pending' | 'approved' | 'rejected' | 'modified')
reviewer_id TEXT
reviewer_notes TEXT
reviewed_at TIMESTAMP
created_at TIMESTAMP
```

#### `audit_log`

Immutable compliance log.

```sql
id INT PRIMARY KEY (auto-increment)
action TEXT ('question_asked', 'answer_generated', 'review_completed', etc.)
resource_type TEXT ('response', 'review', etc.)
resource_id TEXT
actor_type TEXT ('user' | 'system' | 'reviewer')
actor_id TEXT
details TEXT (JSON)
created_at TIMESTAMP
```

---

## API Endpoints

### **Document Management**

| Method | Endpoint    | Purpose           |
| ------ | ----------- | ----------------- |
| POST   | `/ingest`   | Ingest documents  |
| POST   | `/retrieve` | Vector search     |
| POST   | `/chat`     | Full RAG pipeline |
| GET    | `/health`   | Health check      |

### **Human Review**

| Method | Endpoint               | Purpose                 |
| ------ | ---------------------- | ----------------------- |
| GET    | `/review/pending`      | List pending reviews    |
| POST   | `/review/{id}/approve` | Approve response        |
| POST   | `/review/{id}/reject`  | Reject response         |
| POST   | `/review/{id}/modify`  | Edit & approve response |

### **Request Examples**

**POST /chat**

```json
{
  "question": "What is our PTO policy?",
  "top_k": 5
}
```

**Response:**

```json
{
  "answer": "...",
  "confidence": "high",
  "answer_status": "answered",
  "trust_score": 0.92,
  "sources_used": 3,
  "needs_review": false
}
```

**GET /review/pending**

```json
{
  "total": 3,
  "items": [
    {
      "review_id": "uuid",
      "response_id": "uuid",
      "question": "...",
      "answer": "...",
      "confidence": "low",
      "trust_score": 0.35,
      "review_reason": "low_source_confidence",
      "created_at": "2026-05-11T10:30:00"
    }
  ]
}
```

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m src.db.database

# Run server
uvicorn src.api.main:app --reload --port 8000
```

### Docker (Week 4)

```bash
docker build -t trustrag .
docker run -p 8000:8000 trustrag
```

### AWS Deployment (Week 4)

- CloudFormation template for infrastructure
- ECR for Docker images
- RDS for PostgreSQL
- Lambda for serverless option
- API Gateway for public access

---

## Security & Compliance

- ✅ Secrets in `.env` (never committed)
- ✅ No API keys in logs or responses
- ✅ Immutable audit trail for all actions
- ✅ Rate limiting per client
- ✅ Input validation via Pydantic
- ✅ Human review routing for risky responses

---

## Performance Considerations

- **Chunking**: 512-char chunks with 128-char overlap balances context and efficiency
- **Vector Search**: In-memory for local, Pinecone for production scale
- **LLM Calls**: Cached embeddings, single LLM call per request
- **Database**: Indexed on frequently queried fields (user_id, created_at, status)

---

## What's Next (Week 4)

- [ ] Containerization with Docker & Docker Compose
- [ ] CI/CD pipeline with GitHub Actions
- [ ] AWS deployment with CloudFormation
- [ ] Production hardening and load testing
- [ ] External provider integration (OpenAI, Pinecone)
