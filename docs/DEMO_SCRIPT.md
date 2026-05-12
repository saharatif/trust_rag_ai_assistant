# TrustRAG Demo Script — Week 3

**Date:** 2026-05-11  
**Status:** Draft for Week 3 completion  
**Audience:** Client stakeholders, team leads, technical reviewers

---

## Overview

This demo script walks through **TrustRAG's end-to-end workflow**, showcasing:

1. Document ingestion and vector search
2. RAG-based answer generation
3. Trust scoring and confidence assessment
4. Human review workflow for flagged responses
5. Audit logging and compliance tracking

---

## Pre-Demo Setup

### Requirements

- Python 3.11+
- FastAPI running on `http://localhost:8000`
- Sample documents in `data/sample_docs.json`
- `.env` configured with OpenAI API key (or fallback mode)

### Start the Server

```bash
# Terminal 1: Start FastAPI backend
python -m uvicorn src.api.main:app --reload --port 8000
```

Check health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

## Demo Scenario

**Scenario:** HR team member queries the system about PTO policy, expense reimbursement, and a sensitive topic (performance reviews).

---

## Part 1: Document Ingestion (Minutes 1-2)

**Goal:** Show how documents are chunked and embedded.

### Step 1.1: Ingest HR Policy Documents

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "hr-policy-001",
        "title": "2026 HR Policy Handbook",
        "source_type": "policy",
        "department": "HR",
        "text": "PTO Policy: All full-time employees receive 20 days of PTO annually. PTO accrues monthly starting January 1st. Employees can roll over up to 5 days to the next calendar year. Any unused days beyond the carryover limit are forfeited. To request PTO, submit a request at least 2 weeks in advance through the HR portal..."
      },
      {
        "id": "expense-guide-001",
        "title": "Expense Reimbursement Guide",
        "source_type": "manual",
        "department": "Finance",
        "text": "Expense Reimbursement: Employees can be reimbursed for approved business expenses. Common reimbursable items include airfare, hotel, meals (up to $50/day), ground transportation, and conference fees. To be reimbursed, submit receipts and a completed expense report within 30 days of the expense date. Manager approval is required before submission..."
      },
      {
        "id": "handbook-sensitive-001",
        "title": "Performance Management Framework",
        "source_type": "policy",
        "department": "HR",
        "text": "Performance reviews are conducted annually. Managers assess employees on competency, collaboration, and goal achievement. Reviews are confidential and stored securely. Employees have the right to discuss feedback with HR..."
      }
    ]
  }'
```

**Expected Response:**

```json
{
  "documents_received": 3,
  "chunks_created": 8,
  "status": "success"
}
```

**Talking Points:**

- ✓ Documents classified by `source_type` (policy, manual, etc.)
- ✓ Owned by departments for audit tracking
- ✓ Large documents automatically chunked for better retrieval
- ✓ Ready for vector embedding and search

---

## Part 2: Basic Retrieval (Minutes 3-4)

**Goal:** Show vector search in action.

### Step 2.1: Retrieve Documents

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How much PTO do I get?",
    "top_k": 3
  }'
```

**Expected Response:**

```json
{
  "query": "How much PTO do I get?",
  "matches": [
    {
      "chunk_id": "...",
      "document_id": "hr-policy-001",
      "document_title": "2026 HR Policy Handbook",
      "source_type": "policy",
      "department": "HR",
      "similarity_score": 0.94,
      "chunk_text": "PTO Policy: All full-time employees receive 20 days of PTO annually. PTO accrues monthly starting January 1st..."
    },
    {
      "chunk_id": "...",
      "document_id": "expense-guide-001",
      "document_title": "Expense Reimbursement Guide",
      "source_type": "manual",
      "department": "Finance",
      "similarity_score": 0.61,
      "chunk_text": "..."
    }
  ]
}
```

**Talking Points:**

- ✓ Semantic search finds relevant documents even without exact keyword match
- ✓ Similarity scores show confidence in retrieval (0.94 = very relevant, 0.61 = less relevant)
- ✓ Source type is tracked for trust scoring
- ✓ Top-k parameter limits results to most relevant

---

## Part 3: Chat with Trust Scoring (Minutes 5-8)

**Goal:** Demonstrate full RAG pipeline with trust scoring and confidence levels.

### Step 3.1: Ask a High-Confidence Question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How much PTO do I get annually?",
    "top_k": 5
  }'
```

**Expected Response:**

```json
{
  "answer": "All full-time employees receive 20 days of PTO annually. PTO accrues monthly starting January 1st. You can roll over up to 5 days to the next calendar year, and any unused days beyond that are forfeited.",
  "confidence": "high",
  "answer_status": "answered",
  "trust_score": 0.92,
  "sources_used": 1,
  "retrieved_doc_ids": ["hr-policy-001"],
  "needs_review": false
}
```

**Talking Points:**

- ✓ LLM grounds answer in retrieved documents
- ✓ High trust score (0.92) because:
  - Source is a **policy** (most credible, weight=1.0)
  - Very high relevance (0.94)
  - High LLM confidence
- ✓ Answer delivered directly, no review needed

### Step 3.2: Ask a Medium-Confidence Question

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can I expense my lunch at a client meeting?",
    "top_k": 5
  }'
```

**Expected Response:**

```json
{
  "answer": "Yes, meals are reimbursable up to $50 per day when on approved business travel or attending client meetings. You'll need to submit receipts and a completed expense report within 30 days.",
  "confidence": "medium",
  "answer_status": "answered",
  "trust_score": 0.68,
  "sources_used": 1,
  "retrieved_doc_ids": ["expense-guide-001"],
  "needs_review": false
}
```

**Talking Points:**

- ✓ Medium trust score (0.68) because:
  - Source is a **manual** (less authoritative, weight=0.9)
  - Medium relevance (0.72)
  - Medium LLM confidence
- ✓ Still above review threshold (0.5), delivered directly
- ✓ Confidence level helps users assess reliability

### Step 3.3: Ask a Question Requiring Review

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Will I get a bonus this year?",
    "top_k": 5
  }'
```

**Expected Response:**

```json
{
  "answer": "I don't have enough information in the approved documents to answer that.",
  "confidence": "low",
  "answer_status": "unsupported",
  "trust_score": 0.15,
  "sources_used": 0,
  "retrieved_doc_ids": [],
  "needs_review": true,
  "review_reason": "insufficient_context"
}
```

**Talking Points:**

- ✓ Low trust score (0.15) because:
  - No relevant documents found
  - LLM explicitly said "unsupported"
- ✓ Automatically routed for human review
- ✓ Review reason explains why: insufficient context
- ✓ Never returns an unsupported answer — always safe

### Step 3.4: Ask a Sensitive Question (Policy Edge Case)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does the performance review process work?",
    "top_k": 5
  }'
```

**Expected Response:**

```json
{
  "answer": "Performance reviews are conducted annually. Managers assess employees on competency, collaboration, and goal achievement. Reviews are confidential and stored securely. Employees have the right to discuss feedback with HR.",
  "confidence": "high",
  "answer_status": "answered",
  "trust_score": 0.88,
  "sources_used": 1,
  "retrieved_doc_ids": ["handbook-sensitive-001"],
  "needs_review": false
}
```

**Talking Points:**

- ✓ Sensitive topic covered by **policy** documents
- ✓ High trust score, delivered safely
- ✓ Audit log tracks that this sensitive question was asked and answered
- ✓ Future enhancement: Could flag sensitive topics for optional additional review

---

## Part 4: Human Review Workflow (Minutes 9-12)

**Goal:** Show the review queue and approval/rejection/modification workflow.

### Step 4.1: Check Pending Reviews

```bash
curl http://localhost:8000/review/pending
```

**Expected Response:**

```json
{
  "total": 1,
  "items": [
    {
      "review_id": "rev-uuid-1",
      "response_id": "resp-uuid-1",
      "question": "Will I get a bonus this year?",
      "answer": "I don't have enough information in the approved documents to answer that.",
      "confidence": "low",
      "trust_score": 0.15,
      "review_reason": "insufficient_context",
      "created_at": "2026-05-11T10:45:32"
    }
  ]
}
```

**Talking Points:**

- ✓ Review queue shows all flagged responses
- ✓ Reviewer can see full context (question, answer, confidence, reason)
- ✓ FIFO ordering ensures oldest pending requests are addressed first
- ✓ Trust score visible to help reviewers prioritize

### Step 4.2: Reviewer Approves the Response

```bash
curl -X POST http://localhost:8000/review/rev-uuid-1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "reviewer-jane",
    "notes": "Confirmed: no bonus data in system. Response appropriate."
  }'
```

**Expected Response:**

```json
{
  "review_id": "rev-uuid-1",
  "response_id": "resp-uuid-1",
  "status": "approved",
  "message": "Response approved and will be delivered to user."
}
```

**Talking Points:**

- ✓ Human reviewer authenticates with `reviewer_id`
- ✓ Can add contextual notes for future reference
- ✓ Audit log automatically records: action, reviewer, timestamp, notes

### Step 4.3: Reviewer Rejects a Response (Demo Scenario)

**Simulate a different response that needs rejection:**

```bash
curl -X POST http://localhost:8000/review/rev-uuid-2/reject \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "reviewer-jane",
    "reason": "Contains inaccurate information about expense limits."
  }'
```

**Expected Response:**

```json
{
  "review_id": "rev-uuid-2",
  "response_id": "resp-uuid-2",
  "status": "rejected",
  "message": "Response rejected and will not be delivered."
}
```

**Talking Points:**

- ✓ Reviewer rejects responses with errors
- ✓ Reason captured for post-mortem analysis
- ✓ User informed: "Response could not be verified"
- ✓ Logged for compliance audits

### Step 4.4: Reviewer Modifies and Approves

```bash
curl -X POST http://localhost:8000/review/rev-uuid-3/modify \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "reviewer-jane",
    "corrected_answer": "Meal expenses are reimbursable up to $50 per day for approved business purposes. Submit receipts within 30 days to Finance.",
    "notes": "Fixed to clarify 'approved business' context."
  }'
```

**Expected Response:**

```json
{
  "review_id": "rev-uuid-3",
  "response_id": "resp-uuid-3",
  "status": "modified",
  "message": "Response modified and approved. It will be delivered to user."
}
```

**Talking Points:**

- ✓ Reviewers can edit responses before delivery
- ✓ Original answer preserved in audit log for compliance
- ✓ Corrected answer sent to user
- ✓ Tracks: original answer, corrected answer, reviewer, timestamp

---

## Part 5: Audit & Compliance Logging (Minutes 13-14)

**Goal:** Show immutable audit trail.

### Step 5.1: View Audit Log

```bash
curl "http://localhost:8000/audit/logs?action=review_approved&limit=10"
```

**Expected Response:**

```json
{
  "logs": [
    {
      "id": 1,
      "action": "review_approved",
      "resource_type": "response",
      "resource_id": "resp-uuid-1",
      "actor_type": "reviewer",
      "actor_id": "reviewer-jane",
      "details": {
        "review_id": "rev-uuid-1",
        "notes": "Confirmed: no bonus data in system. Response appropriate."
      },
      "created_at": "2026-05-11T10:47:15"
    },
    {
      "id": 2,
      "action": "review_modified",
      "resource_type": "response",
      "resource_id": "resp-uuid-3",
      "actor_type": "reviewer",
      "actor_id": "reviewer-jane",
      "details": {
        "review_id": "rev-uuid-3",
        "original_answer": "...",
        "corrected_answer": "...",
        "notes": "Fixed to clarify 'approved business' context."
      },
      "created_at": "2026-05-11T10:48:22"
    }
  ]
}
```

**Talking Points:**

- ✓ **Immutable:** Audit log is append-only, never modified or deleted
- ✓ **Complete:** Tracks every action (ingest, retrieve, review, approve, reject, modify)
- ✓ **Traceable:** Links back to users, reviewers, and original responses
- ✓ **Compliance-Ready:** Timestamps, actor IDs, details preserved for audits

---

## Part 6: Summary & Key Metrics (Minutes 15)

**Live Dashboard Display (if available):**

```
TrustRAG — Week 3 Summary
════════════════════════════════════════
Total Conversations:        12
Total Messages:             34
Answers Generated:          24
Average Trust Score:        0.71
Responses Reviewed:         4
   ├─ Approved:             2
   ├─ Rejected:             1
   └─ Modified:             1

High Confidence (≥0.75):    18 (75%)
Medium Confidence (0.5-0.75): 4 (17%)
Low Confidence (<0.5):       2 (8%)

Audit Log Entries:          42
────────────────────────────────────────
```

**Key Talking Points:**

1. **Trust Score in Action**
   - 75% of responses scored highly enough to bypass review
   - Review system caught low-confidence edge cases
   - Reviewers can quickly assess and act on flagged responses

2. **Agentic Workflow Benefits**
   - Retrieve → Generate → Score → Route happens automatically
   - Reduces manual overhead for safe answers
   - Escalates risky ones efficiently

3. **Audit & Compliance**
   - Every action tracked with timestamps and actors
   - Provides defense against liability ("we logged everything")
   - Reviewers' decisions preserved for analysis

4. **Next Steps (Week 4)**
   - Containerize with Docker
   - Deploy to AWS with CloudFormation
   - Scale to production with PostgreSQL
   - Add external provider integration (OpenAI, Pinecone)

---

## Troubleshooting

### Server Not Responding

```bash
# Check if server is running
curl http://localhost:8000/health

# If not, restart:
python -m uvicorn src.api.main:app --reload --port 8000
```

### No Documents Found

```bash
# Re-ingest sample documents
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d @data/sample_docs.json
```

### Tests Failing

```bash
pytest tests/test_trust_score.py -v
pytest tests/test_retriever.py -v
pytest tests/test_generator.py -v
```

---

## Closing

**TrustRAG Week 3 delivers:**

✅ Agentic orchestration with LangGraph  
✅ Trust scoring for confidence assessment  
✅ Human review workflow for governance  
✅ Comprehensive audit logging  
✅ Production-ready database schema

**Next week (Week 4):** Production deployment, CI/CD, AWS infrastructure.

---

**End of Demo Script**
