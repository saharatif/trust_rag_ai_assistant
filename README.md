# TrustRAG: Enterprise AI Knowledge Assistant

TrustRAG is a production-style FastAPI backend for an enterprise retrieval-augmented AI assistant. Week 2 adds Pinecone vector storage, OpenAI embeddings and chat, grounded answers with source citations, a safe unsupported-answer fallback, and a basic retrieval evaluation set.

## Requirements

- Python 3.11+
- pip
- OpenAI API key
- Pinecone API key (index: `trustrag`, dimension: 512, metric: cosine)

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your keys:

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

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `TrustRAG API` | Service name returned by `/health` |
| `APP_ENV` | `local` | Runtime environment label |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `CHUNK_SIZE` | `800` | Maximum characters per document chunk |
| `CHUNK_OVERLAP` | `120` | Character overlap between adjacent chunks |
| `INGEST_RATE_LIMIT_PER_MINUTE` | `10` | Max ingest requests per client per minute |
| `RETRIEVE_RATE_LIMIT_PER_MINUTE` | `30` | Max retrieve requests per client per minute |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `20` | Max chat requests per client per minute |
| `OPENAI_API_KEY` | — | Required for embeddings and answer generation |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat model |
| `PINECONE_API_KEY` | — | Required for vector storage and retrieval |
| `PINECONE_INDEX_NAME` | `trustrag` | Pinecone index name |
| `PINECONE_CLOUD` | `aws` | Cloud provider of the Pinecone index |
| `PINECONE_REGION` | `us-east-1` | Region of the Pinecone index |
| `PINECONE_DIMENSIONS` | `512` | Must match the index dimension |

## Run the API

```bash
uvicorn src.api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Endpoints

### Health Check

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

### Document Ingestion

```http
POST /ingest
```

Run with the sample data:

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  --data-binary @data/sample_docs.json
```

Expected response shape:

```json
{
  "documents_received": 2,
  "chunks_created": 2,
  "status": "success"
}
```

### Retrieval

```http
POST /retrieve
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query":"Can employees book business class flights?","top_k":3}'
```

Expected response shape:

```json
{
  "query": "Can employees book business class flights?",
  "matches": [
    {
      "chunk_id": "policy_001_chunk_001",
      "document_id": "policy_001",
      "title": "Employee Travel Policy",
      "score": 0.78,
      "text": "Relevant text..."
    }
  ]
}
```

### Chat

```http
POST /chat
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Can employees book business class flights?","top_k":3}'
```

Expected response shape:

```json
{
  "answer": "Business class flights require director approval...",
  "sources": [
    {
      "document_id": "policy_001",
      "title": "Employee Travel Policy",
      "chunk_id": "policy_001_chunk_001"
    }
  ],
  "confidence": "medium",
  "status": "answered"
}
```

For unsupported questions, `/chat` returns `status: "unsupported"`, `confidence: "low"`, and no sources.

## Run the RAG Flow

1. Start the API: `uvicorn src.api.main:app --reload`
2. Ingest documents: `curl -X POST http://127.0.0.1:8000/ingest -H "Content-Type: application/json" --data-binary @data/sample_docs.json`
3. Query chunks: `POST /retrieve`
4. Ask questions: `POST /chat`

## Evaluation

```bash
python -m src.eval.run_eval
```

Ingests `data/sample_docs.json`, runs the 10-question dataset in `data/eval_questions.json`, reports top-1 retrieval accuracy, and saves results to `data/eval_results.json`.

## Tests

```bash
pytest
```

Current coverage: chunking, validation, config, logging, rate limiting, retrieval ranking, generator, prompt builder, and all API endpoints (unit + Pinecone/OpenAI integration).
