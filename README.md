# TrustRAG: Enterprise AI Knowledge Assistant

TrustRAG is a production-ready FastAPI backend for an enterprise retrieval-augmented AI assistant. It ingests internal documents, retrieves relevant context, generates grounded answers, scores each response for trustworthiness, routes low-confidence answers for human review, and maintains a full audit log — all deployable to AWS with a single command.

## Architecture

```
POST /ingest  →  Chunking  →  Embeddings  →  Vector Store (Pinecone)
                                                      │
POST /chat    →  Retrieval  →  Prompt Builder  →  LLM (GPT-4o-mini)
                                                      │
                              Trust Score  →  Route for Review?
                                                      │
                                            Human Review Queue
                                                      │
                                              Audit Log (DB)
```

## Requirements

- Python 3.11+
- Docker (for containerized runs)
- OpenAI API key
- Pinecone API key (index: `trustrag`, dimension: 512, metric: cosine)
- AWS CLI + account (for cloud deployment)

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```bash
APP_NAME=TrustRAG API
APP_ENV=local
LOG_LEVEL=INFO
CHUNK_SIZE=800
CHUNK_OVERLAP=120
INGEST_RATE_LIMIT_PER_MINUTE=10
RETRIEVE_RATE_LIMIT_PER_MINUTE=30
CHAT_RATE_LIMIT_PER_MINUTE=20

# OpenAI
OPENAI_API_KEY=your-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini

# Pinecone
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=trustrag
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_DIMENSIONS=512
```

`.env` is gitignored and never committed.

## Run the API

```bash
uvicorn src.api.main:app --reload
```

API available at `http://127.0.0.1:8000`.

## Run with Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest
```

## Endpoints

### Health Check

```http
GET /health
```

### Document Ingestion

```http
POST /ingest
```

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  --data-binary @data/sample_docs.json
```

### Retrieval

```http
POST /retrieve
```

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "PTO policy", "top_k": 3}'
```

### Chat (full RAG pipeline)

```http
POST /chat
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How much PTO do employees get?", "top_k": 5}'
```

Response includes `trust_score` (0.0–1.0), `needs_review` flag, and `answer_status` (`answered` or `unsupported`).

### Human Review

```http
GET  /review/pending
POST /review/{id}/approve
POST /review/{id}/reject
POST /review/{id}/modify
```

## Trust Scoring

Each response receives a trust score based on:

| Factor | Weight |
|---|---|
| Source credibility | `policy`/`contract` = 1.0, `manual` = 0.9, `report` = 0.8, `faq` = 0.6 |
| Retrieval relevance | Embedding similarity score |
| LLM confidence | `high` = 1.0×, `medium` = 0.85×, `low` = 0.5× |

Responses scoring below **0.5** are automatically routed to the human review queue.

## Evaluation

```bash
python -m src.eval.run_eval
```

Runs the 10-question evaluation dataset in `data/eval_questions.json`. Week 2 result: **10/10 top-1 retrieval accuracy**.

## AWS Deployment

See [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md) for the full deployment guide.

Quick summary:

```bash
# Push image to ECR
docker build -t trustrag:latest .
docker tag trustrag:latest <ECR_URI>:latest
docker push <ECR_URI>:latest

# Deploy all infrastructure
aws cloudformation deploy \
  --template-file infra/cloudformation/template.yml \
  --stack-name trustrag-dev \
  --parameter-overrides file://infra/cloudformation/parameters.dev.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Provisions: ECR, ECS Fargate, ALB, IAM roles, CloudWatch logs, security groups.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push to `main`:

1. Install dependencies
2. Run `pytest` — fails fast on test failures
3. Build Docker image
4. Push to ECR and redeploy CloudFormation (requires `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `ECR_REPOSITORY` secrets)

## Project Structure

```
src/
├── api/          # FastAPI routes, schemas, rate limiting
├── rag/          # Chunking, embeddings, retriever, prompt builder, generator
├── agents/       # LangGraph agent graph, state, nodes
├── trust/        # Trust score calculator
├── db/           # Database schema, connection, query helpers
└── eval/         # Retrieval evaluation script

tests/            # pytest test suites
data/             # Sample documents and evaluation dataset
docs/             # Architecture, demo script, AWS deployment guide
infra/            # CloudFormation template and parameters
.github/          # CI/CD pipeline
```

## Demo

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for a step-by-step walkthrough of all features.
