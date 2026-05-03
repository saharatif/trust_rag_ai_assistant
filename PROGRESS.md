# TrustRAG — Project Progress

## Current Week: Week 1
## Last Updated: 2026-05-02

---

## Week 1 — Core API Foundation

- [x] Project scaffold: `README.md`, `requirements.txt`, `.env.example`
- [x] FastAPI app entry point: `src/api/main.py`
- [x] Config via environment variables: `src/utils/config.py`
- [x] Structured logging setup: `src/utils/logging.py`
- [x] Health check endpoint: `GET /health`
- [x] Document ingestion endpoint: `POST /ingest`
- [x] Document chunking logic: `src/rag/chunking.py`
- [x] Sample document data: `data/sample_docs.json`
- [x] Chunking automated tests: `tests/test_chunking.py`
- [x] README includes local setup and run instructions

**Status:** Complete

---

## Week 2 — RAG MVP

- [ ] Embedding generation: `src/rag/embeddings.py`
- [ ] Vector store setup (Chroma or FAISS)
- [ ] Retrieval logic: `src/rag/retriever.py`
- [ ] Retrieval endpoint: `POST /retrieve`
- [ ] Prompt builder: `src/rag/prompt_builder.py`
- [ ] LLM answer generator: `src/rag/generator.py`
- [ ] Chat endpoint: `POST /chat`
- [ ] Evaluation script: `src/eval/run_eval.py`
- [ ] Evaluation dataset (10+ questions): `data/eval_questions.json`
- [ ] Retriever tests: `tests/test_retriever.py`

**Status:** Not Started

---

## Week 3 — Agentic Workflow, Trust Score, and Human Review

- [ ] Agent state schema: `src/agents/state.py`
- [ ] Agent node functions: `src/agents/nodes.py`
- [ ] LangGraph workflow graph: `src/agents/graph.py`
- [ ] Trust score calculator: `src/trust/trust_score.py`
- [ ] Database schema: `src/db/schema.sql`
- [ ] Database connection: `src/db/database.py`
- [ ] DB query helpers: `src/db/queries.py`
- [ ] Human review endpoints: `src/api/routes_review.py`
- [ ] Trust score tests: `tests/test_trust_score.py`
- [ ] Architecture document: `docs/ARCHITECTURE.md`
- [ ] Demo script draft: `docs/DEMO_SCRIPT.md`

**Status:** Not Started

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

- None currently

## Notes

- Plans for each week saved to `.agent/plans/` (`1.WEEK1.md` through `4.WEEK4.md`)
- Bug reports go in `bugs/` — use `bugs/TEMPLATE.md` as the starting format
- Update this file at the end of every working session
- Week 1 verified with `pytest`, `GET /health`, and `POST /ingest` using `data/sample_docs.json`.
