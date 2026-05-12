# TrustRAG — Project Progress

## Current Week: Week 5 (Complete)

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

- [x] Dockerfile
- [x] Docker Compose: `docker-compose.yml`
- [x] `.dockerignore`
- [x] GitHub Actions CI pipeline: `.github/workflows/ci.yml`
- [x] CloudFormation template: `infra/cloudformation/template.yml`
- [x] CloudFormation dev parameters: `infra/cloudformation/parameters.dev.json`
- [x] AWS deployment guide: `docs/AWS_DEPLOYMENT.md`
- [x] Final demo script: `docs/DEMO_SCRIPT.md`
- [x] API tests: `tests/test_api.py`
- [x] Final README polish

**Status:** Complete

---

## Week 5 — Frontend UI (React + Vite + Tailwind + shadcn/ui)

- [x] Vite + React + TypeScript scaffold: `frontend/`
- [x] Tailwind CSS + shadcn/ui setup
- [x] API client: `frontend/src/lib/api.ts`
- [x] App layout + routing: `frontend/src/App.tsx`
- [x] Chat page with trust score badges: `frontend/src/pages/Chat.tsx`
- [x] Ingest page with PDF uploader: `frontend/src/pages/Ingest.tsx`
- [x] Review Queue page: `frontend/src/pages/Review.tsx`
- [x] Chat history persistence across tabs: `frontend/src/lib/ChatContext.tsx`
- [x] CORS middleware added to FastAPI: `src/api/main.py`
- [x] CI pipeline fully fixed (10 bugs resolved): `bugs/ci-pipeline-bugs.md`
- [x] AWS experimental deployment validated and torn down: `docs/AWS_EXPERIMENT.md`

**Status:** Complete

---

## Blockers

- None

## Known Issues

- AWS deployment torn down after validation to avoid charges (~$33/month). Re-deploy anytime using `docs/AWS_DEPLOYMENT.md`.
- Frontend not yet hosted on AWS (runs locally via `npm run dev`). S3 + CloudFront deployment planned for production.

## Notes

- Plans for each week saved to `.agent/plans/` (`1.WEEK1.md` through `5.WEEK5.md`)
- Bug reports in `bugs/` — CI bugs: `bugs/ci-pipeline-bugs.md`, AWS bugs: `docs/AWS_EXPERIMENT.md`
- Week 1 verified with `pytest`, `GET /health`, and `POST /ingest` using `data/sample_docs.json`.
- Week 2 verified with `pytest` and `python -m src.eval.run_eval` at 10/10 top-1 retrieval accuracy.
- Week 3 trust score bug fixed: division normalised by match count not sum of weights.
- Week 4 CI pipeline fixed across 10 separate issues (see `bugs/ci-pipeline-bugs.md`).
- Week 5 AWS deployment confirmed live at `trustrag-alb-dev-902053372.us-east-1.elb.amazonaws.com` then torn down.
