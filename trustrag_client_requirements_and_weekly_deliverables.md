# TrustRAG: Enterprise AI Knowledge Assistant

## Client Requirements & 4-Week Delivery Plan

**Project Type:** Enterprise GenAI / AI Engineering Project  
**Timeline:** 4 weeks  
**Delivery Model:** Weekly working deliverables  
**Deployment Target:** AWS using Docker, CI/CD, and CloudFormation

---

# 1. Project Overview

The client requires an enterprise AI knowledge assistant that can answer questions from approved internal documents, cite sources, calculate trustworthiness of retrieved content, route risky answers for human review, maintain audit logs, and be deployable to AWS.

The system must be designed as a production-style backend application with API access, containerized local development, automated CI/CD checks, and infrastructure-as-code deployment support.

---

# 2. Business Requirement

The client has internal knowledge spread across policies, SOPs, FAQs, operational notes, business rules, and other enterprise documents.

The client needs a trusted AI assistant that can:

- Reduce manual search time.
- Provide accurate answers from approved sources.
- Show which documents were used.
- Avoid unsupported answers.
- Route uncertain or risky responses to human approval.
- Maintain traceability through logs.
- Be deployed and maintained through standard engineering practices.

---

# 3. Project Name

**TrustRAG: Enterprise AI Knowledge Assistant**

---

# 4. High-Level Solution

TrustRAG will be a backend AI application using Retrieval-Augmented Generation, agent orchestration, trust scoring, human-in-the-loop review, audit logging, and AWS deployment.

High-level flow:

```text
User Question
    ↓
FastAPI Backend
    ↓
Document Retrieval / Vector Search
    ↓
Trust Score Calculation
    ↓
LLM Answer Generation
    ↓
Agent Workflow
    ↓
Confidence / Risk Decision
    ↓
Final Answer OR Human Review
    ↓
Audit Logging
```

---

# 5. Technology Requirements

## 5.1 Application Stack

### Backend

| Area                 | Required Technology                          |
| -------------------- | -------------------------------------------- |
| Programming Language | Python 3.11+                                 |
| Backend API          | FastAPI                                      |
| Server               | Uvicorn                                      |
| Data Validation      | Pydantic                                     |
| LLM Integration      | OpenAI / Anthropic / compatible LLM provider |
| Agent Workflow       | LangGraph                                    |
| RAG Support          | LangChain optional                           |
| Vector Search        | Pinecone                                     |
| Database             | PostgreSQL or SQLite for local development   |
| Testing              | pytest                                       |
| Configuration        | `.env` / environment variables               |
| Logging              | Python logging / structured logs             |

### Frontend

| Area              | Required Technology |
| ----------------- | ------------------- |
| Framework         | React               |
| Build Tool        | Vite                |
| Styling           | Tailwind CSS        |
| Component Library | shadcn/ui           |

## 5.2 DevOps & Cloud Stack

| Area                   | Required Technology                                           |
| ---------------------- | ------------------------------------------------------------- |
| Containerization       | Docker                                                        |
| Local Orchestration    | Docker Compose                                                |
| CI/CD                  | GitHub Actions                                                |
| Container Registry     | AWS ECR                                                       |
| Cloud Runtime          | AWS ECS Fargate or equivalent AWS container service           |
| Infrastructure as Code | AWS CloudFormation                                            |
| Logs                   | AWS CloudWatch                                                |
| Networking             | Security Groups, Load Balancer or API Gateway                 |
| Secrets                | AWS Secrets Manager or secure environment-based configuration |

---

# 6. Functional Requirements

## FR-1: Health Check API

The system must expose a health check endpoint.

```http
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "TrustRAG API"
}
```

Acceptance criteria:

- Endpoint returns HTTP 200.
- Response confirms service status.
- Endpoint can be used for local, Docker, and cloud health checks.

---

## FR-2: Document Ingestion

The system must allow approved documents to be ingested.

```http
POST /ingest
```

Example input:

```json
{
  "documents": [
    {
      "id": "policy_001",
      "title": "Employee Travel Policy",
      "source_type": "policy",
      "department": "HR",
      "text": "Full document text here..."
    }
  ]
}
```

Required behavior:

- Validate document input.
- Reject invalid or empty documents.
- Clean document text.
- Split documents into chunks.
- Preserve document metadata.
- Prepare chunks for retrieval.
- Return ingestion summary.

Expected response:

```json
{
  "documents_received": 1,
  "chunks_created": 8,
  "status": "success"
}
```

Acceptance criteria:

- Empty documents are rejected cleanly.
- Large documents are chunked.
- Metadata is preserved.
- Ingestion errors are logged.

---

## FR-3: Document Chunking

The system must split large documents into smaller searchable chunks.

Required behavior:

- Use configurable chunk size.
- Use configurable chunk overlap.
- Attach document ID and metadata to each chunk.
- Assign unique chunk IDs.

Acceptance criteria:

- Chunks are not empty.
- Chunk metadata is preserved.
- Chunking settings can be configured.
- Chunking behavior is covered by automated tests.

---

## FR-4: Embedding Generation

The system must generate vector embeddings for document chunks.

Required behavior:

- Generate embeddings using the selected provider/model.
- Store embeddings in Pinecone.
- Handle provider failures gracefully.

Acceptance criteria:

- Document chunks can be embedded and stored in Pinecone.
- Embeddings can be searched via Pinecone similarity query.
- Embedding and Pinecone failures return clean errors and are logged.

---

## FR-5: Retrieval API

The system must retrieve relevant document chunks for a user query.

```http
POST /retrieve
```

Example input:

```json
{
  "query": "What is the employee travel reimbursement policy?",
  "top_k": 5
}
```

Expected response:

```json
{
  "query": "What is the employee travel reimbursement policy?",
  "matches": [
    {
      "chunk_id": "policy_001_chunk_003",
      "document_id": "policy_001",
      "title": "Employee Travel Policy",
      "score": 0.87,
      "text": "Relevant text..."
    }
  ]
}
```

Acceptance criteria:

- Returns top relevant chunks.
- Includes similarity scores.
- Includes source metadata.
- Handles no-match scenarios.

---

## FR-6: RAG Chat API

The system must answer user questions using retrieved document context.

```http
POST /chat
```

Example input:

```json
{
  "question": "Can employees book business class flights?",
  "top_k": 5
}
```

Expected response:

```json
{
  "answer": "According to the travel policy, employees may book business class flights only when...",
  "sources": [
    {
      "document_id": "policy_001",
      "title": "Employee Travel Policy",
      "chunk_id": "policy_001_chunk_003"
    }
  ],
  "confidence": "medium",
  "status": "answered"
}
```

Required behavior:

- Retrieve relevant document chunks.
- Generate grounded answers using retrieved context.
- Include source citations.
- Avoid answering when evidence is missing.
- Log chat requests and responses.

Acceptance criteria:

- Answers include sources.
- Unsupported answers are safely rejected or escalated.
- Missing information returns a controlled response.
- Chat requests are traceable in logs.

---

## FR-7: Trust Score Calculation

The system must calculate a trust score for retrieved content.

Purpose:

The client requires answers to be based on trusted, current, and properly governed information.

Trust score may include:

- Source type
- Metadata completeness
- Freshness / last updated date
- Department ownership
- Retrieval relevance
- Evaluation performance
- Manual approval status

Example formula:

```text
trust_score =
  metadata_score * 0.30
+ freshness_score * 0.30
+ source_quality_score * 0.20
+ eval_score * 0.20
```

Required behavior:

- Calculate trust score for documents or chunks.
- Use trust score during answer decisioning.
- Escalate low-trust answers to human review.

Acceptance criteria:

- Trust score logic is implemented.
- Trust score is explainable.
- Trust score appears in logs or API response.
- Low-trust answers are not finalized automatically.

---

## FR-8: Agentic Workflow

The system must orchestrate the RAG workflow using an agentic graph-based flow.

Required workflow:

```text
Receive Question
    ↓
Retrieve Context
    ↓
Calculate Trust Score
    ↓
Draft Answer
    ↓
Evaluate Confidence
    ↓
Decision:
    - High confidence + high trust → Final Answer
    - Low confidence or low trust → Human Review
```

Required behavior:

- Maintain workflow state.
- Route between retrieval, trust scoring, answer drafting, and review.
- Support conditional routing.
- Support human review state.

Acceptance criteria:

- Workflow executes end-to-end.
- Conditional routing works.
- Low-confidence or low-trust answers enter review.
- Workflow behavior is documented.

---

## FR-9: Human-in-the-Loop Review

The system must allow human approval for risky or uncertain answers.

Example endpoints:

```http
POST /review/{answer_id}/approve
POST /review/{answer_id}/reject
POST /review/{answer_id}/edit
```

Required behavior:

- Place risky answers into pending review.
- Allow reviewer to approve, reject, or edit answers.
- Save review decision.
- Return final answer only after approval where required.

Acceptance criteria:

- Pending review state exists.
- Approval decision is logged.
- Rejection decision is logged.
- Edited answer is saved.
- Review flow works in the final demo.

---

## FR-10: Audit Logging

The system must maintain traceability for key actions.

Events to log:

- User question
- Retrieved chunks
- Similarity scores
- Trust scores
- LLM response
- Confidence level
- Human review decision
- Errors
- Latency where practical

Suggested database tables:

```text
documents
chunks
queries
answers
retrieval_logs
approval_logs
eval_results
```

Acceptance criteria:

- Logs are stored in database or structured log files.
- Logs can be queried.
- Errors are readable.
- Demo includes showing logged records.

---

## FR-11: Evaluation Module

The system must include a basic evaluation process.

Example evaluation dataset:

```json
[
  {
    "question": "What is the travel reimbursement policy?",
    "expected_source": "policy_001"
  }
]
```

Required behavior:

- Run evaluation questions.
- Check whether expected sources are retrieved.
- Save evaluation results.
- Produce basic retrieval success metrics.

Acceptance criteria:

- Evaluation script exists.
- At least 10 evaluation questions are included.
- Evaluation results are saved.
- Evaluation process is documented.

---

## FR-12: Dockerization

The system must be containerized.

Required files:

```text
Dockerfile
docker-compose.yml
.dockerignore
```

Required behavior:

- Build API as Docker image.
- Run API using Docker Compose.
- Include database service (Pinecone is cloud-hosted and does not require a local container).
- Use environment variables safely.

Acceptance criteria:

- Docker image builds successfully.
- Docker Compose starts the app.
- `/health` works inside the container.
- Docker instructions are documented.

---

## FR-13: CI/CD Pipeline

The system must include an automated CI/CD workflow.

Required file:

```text
.github/workflows/ci.yml
```

Required pipeline:

```text
Checkout repo
Install dependencies
Run tests
Build Docker image
```

Optional deployment steps:

```text
Authenticate with AWS
Push image to ECR
Deploy CloudFormation stack
```

Acceptance criteria:

- Pipeline runs on push or pull request.
- Tests run automatically.
- Docker image build is validated.
- Failed tests fail the pipeline.

---

## FR-14: AWS Deployment with CloudFormation

The system must include AWS deployment support using infrastructure as code.

Target AWS architecture:

```text
GitHub Actions
    ↓
Docker Build
    ↓
Push Image to AWS ECR
    ↓
CloudFormation Deploy
    ↓
ECS Fargate Service
    ↓
Application Load Balancer / API Gateway
    ↓
CloudWatch Logs
```

Required AWS components:

- ECR repository
- ECS cluster
- ECS task definition
- ECS service
- IAM execution role
- CloudWatch log group
- Security group
- Load balancer or API Gateway
- Environment variable configuration

Required files:

```text
infra/cloudformation/template.yml
infra/cloudformation/parameters.dev.json
docs/AWS_DEPLOYMENT.md
```

Acceptance criteria:

- CloudFormation template is included.
- AWS architecture is documented.
- Deployment steps are documented.
- Application can be prepared for deployment through the documented process.

---

# 7. Non-Functional Requirements

## NFR-1: Security

- No API keys committed to Git.
- Use `.env.example` for configuration examples.
- Do not expose secrets in logs.
- Human review required for risky answers.
- Production secrets must use secure configuration.

## NFR-2: Reliability

- API must handle invalid inputs.
- LLM failures must return clean errors.
- Retrieval failures must be logged.
- Application must not crash on empty documents.

## NFR-3: Observability

- Important events must be logged.
- Errors must be readable.
- Request flow must be traceable.
- Logs must contain enough context to debug issues.

## NFR-4: Maintainability

- Code must be modular.
- Core behavior must be covered by tests.
- Setup instructions must be clear.
- Architecture must be documented.

## NFR-5: Explainability

- Answers must include sources.
- Trust score must be explainable.
- Human approval decisions must be logged.
- System decisions must be traceable.

---

# 8. Repository Structure

```text
trustrag-enterprise-assistant/
│
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── requirements.txt
│
├── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes_chat.py
│   │   ├── routes_ingest.py
│   │   ├── routes_retrieve.py
│   │   └── routes_review.py
│   │
│   ├── rag/
│   │   ├── ingest.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   ├── prompt_builder.py
│   │   └── generator.py
│   │
│   ├── agents/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── nodes.py
│   │
│   ├── trust/
│   │   └── trust_score.py
│   │
│   ├── db/
│   │   ├── schema.sql
│   │   ├── database.py
│   │   └── queries.py
│   │
│   ├── eval/
│   │   └── run_eval.py
│   │
│   └── utils/
│       ├── config.py
│       └── logging.py
│
├── tests/
│   ├── test_chunking.py
│   ├── test_retriever.py
│   ├── test_trust_score.py
│   └── test_api.py
│
├── data/
│   ├── sample_docs.json
│   └── eval_questions.json
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AWS_DEPLOYMENT.md
│   └── DEMO_SCRIPT.md
│
├── infra/
│   └── cloudformation/
│       ├── template.yml
│       └── parameters.dev.json
│
└── .github/
    └── workflows/
        └── ci.yml
```

---

# 9. Weekly Delivery Plan

---

# Week 1: Core API Foundation

## Client Requirement

The client needs the initial backend foundation for the AI assistant.

By the end of Week 1, the system must provide a working FastAPI backend that can run locally, expose a health check, accept document ingestion requests, clean and chunk documents, and include basic tests.

## Required Working Outcome by End of Week 1

The client should be able to:

1. Run the backend locally.
2. Call the health check endpoint.
3. Submit sample documents through the ingestion endpoint.
4. See documents split into chunks.
5. See basic validation for invalid or empty documents.
6. Run automated tests for the initial functionality.

## Required Endpoints

```http
GET /health
POST /ingest
```

## Required Files/Components

```text
README.md
.env.example
requirements.txt
src/api/main.py
src/rag/ingest.py
src/rag/chunking.py
src/utils/config.py
src/utils/logging.py
tests/test_chunking.py
data/sample_docs.json
```

## Week 1 Acceptance Criteria

Week 1 is complete when:

- Application runs locally.
- `/health` returns success.
- `/ingest` accepts sample documents.
- Invalid/empty documents are handled cleanly.
- Documents are split into chunks.
- At least basic automated tests pass.
- README includes local setup and run instructions.

---

# Week 2: RAG MVP

## Client Requirement

The client needs the assistant to answer questions using approved internal documents and show which sources were used.

By the end of Week 2, the system must support document retrieval, RAG-based answer generation, source citations, and basic evaluation.

## Required Working Outcome by End of Week 2

The client should be able to:

1. Ingest multiple sample documents.
2. Ask a question through the chat API.
3. Receive an answer generated from retrieved document context.
4. See source documents/chunks used in the answer.
5. Receive a safe fallback when the answer is not supported by documents.
6. Run a basic evaluation set to check retrieval quality.

## Required Endpoints

```http
POST /retrieve
POST /chat
```

## Required Files/Components

```text
src/rag/embeddings.py
src/rag/retriever.py
src/rag/prompt_builder.py
src/rag/generator.py
src/api/routes_retrieve.py
src/api/routes_chat.py
src/eval/run_eval.py
data/eval_questions.json
tests/test_retriever.py
```

## Example `/chat` Response

```json
{
  "answer": "Employees can claim travel reimbursement when...",
  "sources": [
    {
      "document_id": "policy_001",
      "title": "Travel Policy",
      "chunk_id": "policy_001_chunk_002"
    }
  ],
  "confidence": "medium",
  "status": "answered"
}
```

## Week 2 Acceptance Criteria

Week 2 is complete when:

- Documents can be ingested.
- Embeddings are generated.
- `/retrieve` returns relevant chunks.
- `/chat` returns an answer with sources.
- Unsupported questions produce a safe fallback.
- Evaluation script runs with at least 10 test questions.
- README explains how to run the RAG flow.

---

# Week 3: Agentic Workflow, Trust Score, and Human Review

## Client Requirement

The client needs greater control and trust before answers are finalized.

By the end of Week 3, the system must use an agentic workflow to retrieve context, calculate trust score, draft an answer, evaluate confidence, and route low-confidence or low-trust answers to human review.

## Required Working Outcome by End of Week 3

The client should be able to:

1. Ask a question through the chat endpoint.
2. See the request pass through the agentic workflow.
3. See retrieved content scored for trust.
4. Receive final answers when trust/confidence is high.
5. Route low-trust or low-confidence answers to human review.
6. Approve, reject, or edit pending answers.
7. View audit logs for questions, retrieved chunks, scores, answers, and review decisions.

## Required Workflow

```text
Receive Question
    ↓
Retrieve Context
    ↓
Calculate Trust Score
    ↓
Draft Answer
    ↓
Evaluate Confidence
    ↓
Conditional Route
    ├── High confidence + high trust → Final Answer
    └── Low confidence or low trust → Human Review
```

## Required Endpoints

```http
POST /chat
POST /review/{answer_id}/approve
POST /review/{answer_id}/reject
POST /review/{answer_id}/edit
```

## Required Files/Components

```text
src/agents/state.py
src/agents/nodes.py
src/agents/graph.py
src/trust/trust_score.py
src/db/schema.sql
src/db/database.py
src/db/queries.py
src/api/routes_review.py
tests/test_trust_score.py
docs/ARCHITECTURE.md
docs/DEMO_SCRIPT.md
```

## Suggested Database Tables

```text
documents
chunks
queries
answers
retrieval_logs
approval_logs
eval_results
```

## Week 3 Acceptance Criteria

Week 3 is complete when:

- Agentic workflow runs end-to-end.
- Trust score is calculated.
- Low-confidence or low-trust answers are routed to review.
- Human approval, rejection, and edit flows work.
- Audit logs are saved.
- Database records can be inspected.
- Architecture document explains the workflow.

---

# Week 4: Productionization, CI/CD, Docker, and AWS Deployment

## Client Requirement

The client needs the system packaged and prepared for production-style deployment.

By the end of Week 4, the application must run in containers, include automated CI checks, provide AWS CloudFormation deployment support, and include final project documentation.

## Required Working Outcome by End of Week 4

The client should be able to:

1. Run the full application through Docker Compose.
2. Confirm the service is healthy inside the container.
3. Run automated tests through CI/CD.
4. Build a Docker image through the pipeline.
5. Review AWS deployment architecture.
6. Review CloudFormation infrastructure template.
7. Follow documented deployment steps.
8. Watch a full end-to-end demo of the application.

## Required DevOps Components

```text
Dockerfile
docker-compose.yml
.dockerignore
.github/workflows/ci.yml
```

## Required AWS Components

```text
infra/cloudformation/template.yml
infra/cloudformation/parameters.dev.json
docs/AWS_DEPLOYMENT.md
```

## CI/CD Pipeline Requirements

The pipeline must:

```text
1. Checkout code
2. Set up Python
3. Install dependencies
4. Run tests
5. Build Docker image
```

Optional deployment steps:

```text
6. Authenticate with AWS
7. Push image to ECR
8. Deploy CloudFormation stack
```

## CloudFormation Template Scope

The template should include or prepare the following:

- ECR repository
- ECS cluster
- ECS task definition
- ECS service
- IAM execution role
- CloudWatch log group
- Security group
- Load balancer or API Gateway placeholder
- Environment variable configuration

## Week 4 Acceptance Criteria

Week 4 is complete when:

- App runs with Docker Compose.
- `/health` works inside the container.
- Tests run locally.
- CI pipeline runs tests.
- CI pipeline builds Docker image.
- CloudFormation template exists.
- AWS deployment flow is documented.
- Final demo can be completed end-to-end.

---

# 10. Final Project Acceptance Criteria

The full project is complete when:

## Application

- FastAPI backend runs locally.
- Documents can be ingested.
- Documents are chunked.
- Embeddings are generated.
- Relevant chunks can be retrieved.
- Chat endpoint answers using retrieved context.
- Answers include sources.
- Unsupported answers are handled safely.
- Agent workflow orchestrates the process.
- Trust score is calculated.
- Human review is supported.
- Logs are stored.

## Testing

- Core functions have automated tests.
- API has basic tests.
- Evaluation script runs.
- CI executes tests automatically.

## DevOps

- Dockerfile exists.
- Docker Compose runs the app.
- CI workflow exists.
- Docker image builds successfully.
- AWS deployment architecture is documented.
- CloudFormation template exists.

## Documentation

- README is complete.
- Architecture document is complete.
- AWS deployment guide is complete.
- Demo script is complete.

---

# 11. Final Demo Flow

The final project demo must show:

1. Project overview.
2. Architecture overview.
3. Local application startup.
4. `/health` endpoint.
5. Document ingestion.
6. Retrieval endpoint.
7. RAG chat endpoint.
8. Source-cited answer.
9. Unsupported question fallback.
10. Trust score calculation.
11. Low-confidence answer routed to review.
12. Human approval/rejection/edit flow.
13. Audit logs.
14. Evaluation script.
15. Docker Compose startup.
16. CI/CD workflow.
17. AWS CloudFormation deployment plan.

---

# 12. Production Risks to Address

The implementation and documentation should address these risks:

## AI Risks

- Hallucination
- Prompt injection
- Poor retrieval quality
- Outdated documents
- Low-quality source data
- Unsupported answers

## Engineering Risks

- Missing tests
- Secrets leakage
- Poor error handling
- Lack of observability
- Database failures
- Vector store failures
- LLM provider downtime

## Deployment Risks

- Incorrect IAM permissions
- Exposed endpoints
- Missing environment variables
- No rollback plan
- Cloud cost surprises
- Logs containing sensitive data

---

# 13. PROGRESS.md — Instructions

A `PROGRESS.md` file must be maintained at the root of the repository throughout the project. It is the single source of truth for what has been built, what is in progress, and what is blocked.

## Purpose

- Track completion status week by week.
- Give the team lead and client a quick view of where the project stands.
- Surface blockers and known issues early.

## Structure

```markdown
# TrustRAG — Project Progress

## Current Week: [Week Number]
## Last Updated: [Date]

---

## Week 1 — Core API Foundation
- [ ] Task or requirement
- [x] Completed task
...
Status: In Progress / Complete

## Week 2 — RAG MVP
...

## Week 3 — Agentic Workflow, Trust Score, and Human Review
...

## Week 4 — Productionization, CI/CD, Docker, and AWS Deployment
...

---

## Blockers
- [Description of any blocker and which week/feature it affects]

## Known Issues
- [Any known bugs or gaps, with a reference to the bugs/ folder if logged there]

## Notes
- [Any decisions made, scope changes, or context the team should know]
```

## Rules

- Update `PROGRESS.md` at the end of every working session.
- Check items off as they are completed — do not mark complete until the acceptance criteria are met.
- Any blocker that cannot be resolved within the same session must be listed under **Blockers**.
- Major bugs must also be logged in the `bugs/` folder with full detail.
- Do not delete previous weeks' entries — keep the full history intact.

---

# 14. Delivery Summary

The 4-week delivery will produce a working enterprise AI assistant backend with:

- FastAPI APIs
- Document ingestion
- RAG retrieval and chat
- Source-cited answers
- Trust scoring
- Agentic workflow
- Human review
- Audit logging
- Evaluation
- Docker Compose setup
- CI/CD pipeline
- AWS CloudFormation deployment support

The final result should be a realistic production-style GenAI system that can be demonstrated end-to-end.
