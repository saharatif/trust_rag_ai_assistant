# TrustRAG: Enterprise AI Knowledge Assistant

TrustRAG is a production-style FastAPI backend for an enterprise retrieval-augmented AI assistant. Week 1 delivers the API foundation: health checks, document ingestion, configurable chunking, structured logging, and automated tests.

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
| `HEALTH_RATE_LIMIT_PER_MINUTE` | `120` | Maximum health check requests per client per minute |
| `INGEST_RATE_LIMIT_PER_MINUTE` | `10` | Maximum ingestion requests per client per minute |

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

## Tests

```bash
pytest
```

Current coverage focuses on chunking behavior, metadata preservation, validation failures, and the Week 1 API endpoints.
