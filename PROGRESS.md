# TrustRAG — Project Progress

## Current Week: Week 4

## Last Updated: 2026-05-11

---

## Week 1 — Core API Foundation

- [x] Project scaffold: `README.md`, `requirements.txt`, `.env`
- [x] FastAPI app entry point: `src/api/main.py`
- [x] Config via environment variables: `src/utils/config.py`
- [x] Structured logging setup: `src/utils/logging.py`
- [x] Health check endpoint: `GET /health`
- [x] Document ingestion endpoint: `POST /ingest`
- [x] Document chunking logic: `src/rag/chunking.py`
- [x] Sample document data: `data/sample_docs.json`
- [x] Chunking automated tests: `tests/test_chunking.py`
- [x] README includes local setup and run instructions
- [x] Basic API rate limiting: `src/api/rate_limit.py`

**Status:** Complete

---

## Week 2 — RAG MVP

- [x] Embedding generation: `src/rag/embeddings.py`
- [x] Vector store setup (in-memory local store)
- [x] Retrieval logic: `src/rag/retriever.py`
- [x] Retrieval endpoint: `POST /retrieve`
- [x] Prompt builder: `src/rag/prompt_builder.py`
- [x] LLM answer generator: `src/rag/generator.py`
- [x] Chat endpoint: `POST /chat`
- [x] Evaluation script: `src/eval/run_eval.py`
- [x] Evaluation dataset (10+ questions): `data/eval_questions.json`
- [x] Retriever tests: `tests/test_retriever.py`

**Status:** Complete

---

## Week 3 — Agentic Workflow, Trust Score, and Human Review

- [x] Agent state schema: `src/agents/state.py`
- [x] Agent node functions: `src/agents/nodes.py`
- [x] LangGraph workflow graph: `src/agents/graph.py`
- [x] Trust score calculator: `src/trust/trust_score.py`
- [x] Database schema: `src/db/schema.sql`
- [x] Database connection: `src/db/database.py`
- [x] DB query helpers: `src/db/queries.py`
- [x] Human review endpoints: `src/api/routes_review.py`
- [x] Trust score tests: `tests/test_trust_score.py`
- [x] Architecture document: `docs/ARCHITECTURE.md`
- [x] Demo script draft: `docs/DEMO_SCRIPT.md`

**Status:** Complete

---

## Week 4 — Productionization, CI/CD, Docker, and AWS Deployment

- [ ] Dockerfile
- [ ] Docker Compose: `docker-compose.yml`
- [ ] `.dockerignore`
- [ ] GitHub Actions CI pipeline: `.github/workflows/ci.yml`
- [ ] CloudFormation template: `infra/cloudformation/template.yml`
- [ ] CloudFormation dev parameters: `infra/cloudformation/parameters.dev.json`
- [ ] AWS deployment guide: `docs/AWS_DEPLOYMENT.md`
- [ ] Final demo script: `docs/DEMO_SCRIPT.md`
- [ ] API tests: `tests/test_api.py`
- [ ] Final README polish

**Status:** Not Started

---

## Blockers

- None currently

## Known Issues

- External OpenAI/Pinecone provider wiring is still reserved for a later hardening pass; Week 2 runs locally with deterministic embeddings and an in-memory vector store.

## Notes

- Plans for each week saved to `.agent/plans/` (`1.WEEK1.md` through `4.WEEK4.md`)
- Bug reports go in `bugs/` — use `bugs/TEMPLATE.md` as the starting format
- Update this file at the end of every working session
- Week 1 verified with `pytest`, `GET /health`, and `POST /ingest` using `data/sample_docs.json`.
- Added configurable per-client rate limits for `GET /health` and `POST /ingest`.
- Week 2 verified with `pytest` and `python -m src.eval.run_eval` at 10/10 top-1 retrieval accuracy.
