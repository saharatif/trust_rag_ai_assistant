# TrustRAG Demo Script — Final

**Date:** 2026-05-11
**Status:** Final (Week 4)
**Audience:** Client stakeholders, team leads, technical reviewers

---

## Overview

This demo walks through **TrustRAG end-to-end**, covering:

1. Local setup and health check
2. Document ingestion and vector search
3. RAG-based answer generation with trust scoring
4. Human review workflow for flagged responses
5. Docker container deployment
6. AWS production deployment

---

## Part 1: Local Setup (Minutes 0-1)

### Start the API locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{ "status": "ok", "service": "TrustRAG API" }
```

---

## Part 2: Document Ingestion (Minutes 1-2)

Ingest three HR documents with different source types:

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
        "text": "PTO Policy: All full-time employees receive 20 days of PTO annually. PTO accrues monthly starting January 1st. Employees can roll over up to 5 days to the next calendar year. Any unused days beyond the carryover limit are forfeited."
      },
      {
        "id": "expense-guide-001",
        "title": "Expense Reimbursement Guide",
        "source_type": "manual",
        "department": "Finance",
        "text": "Employees can be reimbursed for approved business expenses including airfare, hotel, meals up to $50/day, ground transportation, and conference fees. Submit receipts and a completed expense report within 30 days."
      },
      {
        "id": "perf-review-001",
        "title": "Performance Management Framework",
        "source_type": "policy",
        "department": "HR",
        "text": "Performance reviews are conducted annually. Managers assess employees on competency, collaboration, and goal achievement. Reviews are confidential and stored securely."
      }
    ]
  }'
```

Expected:

```json
{ "documents_received": 3, "chunks_created": 8, "status": "success" }
```

**Talking points:**
- Documents are classified by `source_type` — this drives trust scoring later
- Large documents are auto-chunked for more precise retrieval
- Each chunk is embedded and stored in the vector index

---

## Part 3: Retrieval (Minutes 3-4)

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "How much PTO do I get?", "top_k": 3}'
```

**Talking points:**
- Semantic search — finds relevant chunks without exact keyword match
- Similarity scores (0.0–1.0) rank chunks by relevance
- Source type is attached to every result for trust scoring downstream

---

## Part 4: Chat with Trust Scoring (Minutes 5-9)

### 4.1 — High-confidence answer

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How much PTO do employees get annually?", "top_k": 5}'
```

Expected:

```json
{
  "answer": "All full-time employees receive 20 days of PTO annually...",
  "confidence": "high",
  "answer_status": "answered",
  "trust_score": 0.92,
  "sources_used": 1,
  "needs_review": false
}
```

**Talking points:** Policy source (weight 1.0) + high relevance + high LLM confidence = trust score 0.92. No human review needed.

### 4.2 — Medium-confidence answer

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I expense my lunch at a client meeting?", "top_k": 5}'
```

Expected trust score: ~0.68 (manual source, weight 0.9). Still above review threshold (0.5) — delivered automatically.

### 4.3 — Answer routed for human review

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Will I get a bonus this year?", "top_k": 5}'
```

Expected:

```json
{
  "answer": "I don't have enough information in the approved documents to answer that.",
  "answer_status": "unsupported",
  "trust_score": 0.15,
  "needs_review": true,
  "review_reason": "insufficient_context"
}
```

**Talking points:** No relevant documents → trust score 0.15 → automatically queued for human review. System never invents an answer.

---

## Part 5: Human Review Workflow (Minutes 10-13)

### 5.1 — View pending reviews

```bash
curl http://localhost:8000/review/pending
```

### 5.2 — Approve

```bash
curl -X POST http://localhost:8000/review/<review_id>/approve \
  -H "Content-Type: application/json" \
  -d '{"reviewer_id": "reviewer-jane", "notes": "No bonus data in system. Response appropriate."}'
```

### 5.3 — Reject

```bash
curl -X POST http://localhost:8000/review/<review_id>/reject \
  -H "Content-Type: application/json" \
  -d '{"reviewer_id": "reviewer-jane", "reason": "Contains inaccurate expense limits."}'
```

### 5.4 — Modify and approve

```bash
curl -X POST http://localhost:8000/review/<review_id>/modify \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "reviewer-jane",
    "corrected_answer": "Meal expenses are reimbursable up to $50/day for approved business purposes.",
    "notes": "Clarified approved business context."
  }'
```

**Talking points:** Original answer preserved in audit log. Corrected answer delivered to user. Every action timestamped with reviewer ID.

---

## Part 6: Docker Deployment (Minutes 14-15)

```bash
# Start full stack
docker compose up --build

# Verify health inside container
curl http://localhost:8000/health
```

**Talking points:** Multi-stage Dockerfile for minimal image size. Non-root user for security. No secrets baked into the image — all passed via environment variables.

Run the full test suite inside the container:

```bash
docker run --rm trustrag:latest python -m pytest tests/ -v
```

---

## Part 7: AWS Production Deployment (Minutes 16-18)

```bash
# 1. Authenticate and push image to ECR
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin <ECR_URI>
docker build -t trustrag:latest .
docker tag trustrag:latest <ECR_URI>:latest
docker push <ECR_URI>:latest

# 2. Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file infra/cloudformation/template.yml \
  --stack-name trustrag-dev \
  --parameter-overrides file://infra/cloudformation/parameters.dev.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# 3. Get the public endpoint
aws cloudformation describe-stacks \
  --stack-name trustrag-dev \
  --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
  --output text

# 4. Verify live
curl http://<ALB_DNS>/health
```

**Talking points:** Single command deploys ECR repo, ECS Fargate cluster, ALB, IAM roles, and CloudWatch logs. Rolling updates with zero downtime. All infrastructure defined as code in `infra/cloudformation/template.yml`.

---

## Part 8: CI/CD Pipeline (Minute 19)

Push to `main` → GitHub Actions automatically:

1. Runs `pytest` — pipeline fails fast if any test fails
2. Builds Docker image
3. (With AWS secrets) Pushes to ECR and redeploys CloudFormation stack

Show the `.github/workflows/ci.yml` pipeline and a passing run.

---

## Summary

| Week | Delivered |
|---|---|
| 1 | FastAPI core, ingestion, chunking, rate limiting |
| 2 | Embeddings, vector retrieval, RAG pipeline, eval (10/10) |
| 3 | LangGraph agent, trust scoring, human review, audit logs |
| 4 | Docker, CI/CD, CloudFormation, AWS Fargate deployment |

**TrustRAG is production-ready:**

- Answers grounded in approved documents only
- Every response scored for trustworthiness
- Low-confidence responses routed for human review before delivery
- Full audit trail for compliance
- One-command deployment to AWS
- Automated CI/CD on every push

---

**End of Demo**
