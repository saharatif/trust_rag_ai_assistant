# TrustRAG: Enterprise AI Knowledge Assistant

TrustRAG is a production-style FastAPI backend for an enterprise retrieval-augmented AI assistant. Week 2 adds local RAG retrieval, grounded chat responses with citations, a safe unsupported-answer fallback, and a basic retrieval evaluation set.

## Requirements

- Python 3.11+
- pip

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Environment variables are optional for local development because safe defaults are provided.

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `TrustRAG API` | Service name returned by `/health` |
| `APP_ENV` | `local` | Runtime environment label |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `CHUNK_SIZE` | `800` | Maximum characters per document chunk |
| `CHUNK_OVERLAP` | `120` | Character overlap between adjacent chunks |
| `INGEST_RATE_LIMIT_PER_MINUTE` | `10` | Maximum ingestion requests per client per minute |
| `OPENAI_API_KEY` | empty | Reserved for provider-backed generation and embeddings |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Reserved embedding model setting |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Reserved chat model setting |
| `PINECONE_API_KEY` | empty | Reserved vector store setting |
| `PINECONE_INDEX_NAME` | `trustrag` | Reserved Pinecone index name |

Do not commit `.env` files or secrets. `.env` is ignored by git.

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

1. Start the API with `uvicorn src.api.main:app --reload`.
2. Ingest documents with `curl -X POST http://127.0.0.1:8000/ingest -H "Content-Type: application/json" --data-binary @data/sample_docs.json`.
3. Query retrieved chunks with `POST /retrieve`.
4. Ask grounded questions with `POST /chat`.

The current Week 2 implementation uses deterministic local embeddings and an in-memory vector store so it runs without external API keys.

## Evaluation

```bash
python -m src.eval.run_eval
```

The eval script ingests `data/sample_docs.json`, runs the 10-question dataset in `data/eval_questions.json`, and reports top-1 retrieval accuracy.

## Tests

```bash
pytest
```

Current coverage focuses on chunking behavior, metadata preservation, validation failures, rate limiting, retrieval ranking, and the Week 2 API endpoints.
