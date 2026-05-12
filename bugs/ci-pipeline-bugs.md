# Bug Report — GitHub Actions CI Pipeline

| Field    | Value                        |
| -------- | ---------------------------- |
| Reporter | Team Lead                    |
| Date     | 2026-05-12                   |
| Week     | Week 4 / Week 5              |

---

## Issues

### YAML-SYNTAX-INLINE-PYTHON

| Field     | Value                                          |
| --------- | ---------------------------------------------- |
| Severity  | critical                                       |
| File      | `.github/workflows/ci.yml:101`                 |
| Status    | fixed                                          |

**Description:**
A multi-line Python script was embedded inside a `run:` block using `python -c "..."`. The indented Python code at column 0 broke YAML parsing — the parser expected a `:` after what it read as a mapping key.

**Steps to Reproduce:**
1. Push to `main`
2. GitHub Actions reports: `Invalid workflow file: .github/workflows/ci.yml#L101 — You have an error in your yaml syntax on line 101`

**Expected:** CI pipeline starts and runs all jobs.

**Actual:** Workflow file rejected entirely; no jobs run.

**Suggested Fix:**
Replaced the inline Python block with a single `find ... | xargs python -m py_compile` shell command. Alternatively, a heredoc using `<<'EOF'` would work but `<<` is parsed as a YAML merge key unless the entire `run:` value is a quoted string.

**Fix applied:** Replaced with `find src tests -name "*.py" | xargs python -m py_compile`.

---

### GLOB-EXPANSION-BASH

| Field     | Value                                       |
| --------- | ------------------------------------------- |
| Severity  | major                                       |
| File      | `.github/workflows/ci.yml:40`               |
| Status    | fixed                                       |

**Description:**
The lint step used `python -m py_compile src/**/*.py tests/**/*.py`. The `**` glob pattern requires `globstar` to be enabled in bash (`shopt -s globstar`). GitHub Actions runners use bash without globstar by default, so the shell interprets `**` as a single `*`, resulting in `[Errno 2] No such file or directory: 'tests/**/*.py'`.

**Steps to Reproduce:**
1. Push to `main`
2. CI lint step fails with: `[Errno 2] No such file or directory: 'tests/**/*.py'`

**Expected:** All `.py` files in `src/` and `tests/` are syntax-checked.

**Actual:** Process exits with code 1 on first glob mismatch.

**Suggested Fix:**
Use `find` instead of glob patterns: `find src tests -name "*.py" | xargs python -m py_compile`.

**Fix applied:** Replaced glob with `find` command.

---

### MISSING-PYTEST-COV

| Field     | Value                                       |
| --------- | ------------------------------------------- |
| Severity  | major                                       |
| File      | `requirements.txt`, `.github/workflows/ci.yml` |
| Status    | fixed                                       |

**Description:**
The CI pytest step used `--cov`, `--cov-report=xml`, and `--cov-report=term-missing` flags which require the `pytest-cov` plugin. This package was not in `requirements.txt` and not installed before the test step, so pytest rejected all three flags as unrecognised arguments.

**Steps to Reproduce:**
1. Push to `main`
2. pytest step fails: `pytest: error: unrecognized arguments: --cov=src --cov-report=xml`

**Expected:** Tests run with coverage reporting.

**Actual:** pytest exits with code 1 before running any tests.

**Suggested Fix:**
Add `pytest-cov` to `requirements.txt`. Additionally bump the pip cache key so the stale cache (built before the fix) is discarded.

**Fix applied:** Added `pytest-cov==5.0.0` to `requirements.txt`, bumped cache key to `pip-v2-`, added explicit `pip install pytest-cov` in the install step as a safety net.

---

### LANGCHAIN-DEPENDENCY-CONFLICT

| Field     | Value                                |
| --------- | ------------------------------------ |
| Severity  | critical                             |
| File      | `requirements.txt`                   |
| Status    | fixed                                |

**Description:**
`langgraph==0.0.52` requires `langchain-core>=0.2,<0.3` but `langchain==0.1.20` requires `langchain-core>=0.1.52,<0.2.0`. These constraints are irreconcilable — pip cannot resolve a version of `langchain-core` that satisfies both at the same time.

**Steps to Reproduce:**
1. Push to `main`
2. Install dependencies step fails: `ERROR: ResolutionImpossible ... langchain 0.1.20 depends on langchain-core<0.2.0`

**Expected:** All packages install without conflict.

**Actual:** pip exits with `ResolutionImpossible` error; no packages installed.

**Suggested Fix:**
`langchain` is not imported anywhere in the codebase — only `langgraph.graph.StateGraph` and `END` are used. Remove `langchain` from `requirements.txt` entirely.

**Fix applied:** Removed `langchain==0.1.20` from `requirements.txt`.

---

### CHAT-RESPONSE-FIELD-MISMATCH

| Field     | Value                                              |
| --------- | -------------------------------------------------- |
| Severity  | major                                              |
| File      | `src/api/schemas.py`, `src/api/routes_chat.py`    |
| Status    | fixed                                              |

**Description:**
`ChatResponse` schema used field names `status` and `sources` (a list of citation objects). Tests and the frontend expected `answer_status`, `sources_used` (integer count), `trust_score`, `needs_review`, and `review_reason`. Every chat-related test assertion failed with `KeyError` or `AssertionError`.

**Steps to Reproduce:**
1. Run `pytest tests/test_api.py::TestChatEndpoint`
2. Tests fail: `assert 'answer_status' in {'answer': ..., 'status': 'unsupported', 'sources': []}`

**Expected:** Response includes `answer_status`, `trust_score`, `sources_used`, `needs_review`.

**Actual:** Response includes `status` and `sources` (wrong field names, wrong types).

**Suggested Fix:**
Update `ChatResponse` to use the correct field names and add missing fields. Wire `calculate_trust_score`, `should_route_for_review`, and `get_review_reason` into the chat route handler.

**Fix applied:** Updated `schemas.py` and `routes_chat.py` accordingly.

---

### REVIEW-ROUTER-NOT-REGISTERED

| Field     | Value                                  |
| --------- | -------------------------------------- |
| Severity  | critical                               |
| File      | `src/api/main.py`                      |
| Status    | fixed                                  |

**Description:**
`src/api/routes_review.py` was created in Week 3 but never registered in `main.py` with `app.include_router()`. All review endpoints returned `404 Not Found`.

**Steps to Reproduce:**
1. Run `pytest tests/test_api.py::TestReviewEndpoint`
2. All tests fail: `assert 404 == 200`

**Expected:** `GET /review/pending` returns 200 with empty list.

**Actual:** All `/review/*` routes return 404.

**Suggested Fix:**
Add `from src.api.routes_review import router as review_router` and `app.include_router(review_router)` to `main.py`.

**Fix applied:** Router registered in `main.py`.

---

### REVIEW-QUERY-PARAM-FIELD-ANNOTATION

| Field     | Value                                      |
| --------- | ------------------------------------------ |
| Severity  | critical                                   |
| File      | `src/api/routes_review.py:86`              |
| Status    | fixed                                      |

**Description:**
The `list_pending_reviews` route declared its `limit` query parameter using Pydantic's `Field()`. FastAPI only accepts `Query()`, `Path()`, `Header()`, or `Cookie()` for non-body parameters. Using `Field()` caused an `AssertionError` at app startup, preventing the entire test suite from collecting.

**Steps to Reproduce:**
1. Run `pytest tests/test_api.py`
2. Collection fails: `AssertionError: non-body parameters must be in path, query, header or cookie: limit`

**Expected:** App starts and all tests are collected.

**Actual:** pytest cannot collect any tests due to startup error.

**Suggested Fix:**
Replace `Field(default=50, ge=1, le=500)` with `Query(default=50, ge=1, le=500)` and import `Query` from `fastapi`.

**Fix applied:** Updated `routes_review.py`.

---

### RATE-LIMITER-STATE-BLEEDING-BETWEEN-TESTS

| Field     | Value                                           |
| --------- | ----------------------------------------------- |
| Severity  | major                                           |
| File      | `tests/test_api.py`                             |
| Status    | fixed                                           |

**Description:**
The rate limiter uses a module-level singleton that persists across test cases. `TestChatEndpoint` and `TestIntegration` each call `POST /ingest` in their `setup_method`, but prior test classes had already consumed the rate limit for that client IP. Subsequent calls returned `429 Too Many Requests` instead of `200`, causing cascade failures unrelated to the feature being tested.

**Steps to Reproduce:**
1. Run full `pytest tests/test_api.py`
2. `TestIntegration::test_end_to_end_workflow` fails: `assert 429 == 200`

**Expected:** Each test starts with a clean rate limit state.

**Actual:** Rate limit counter accumulates across all test classes; later tests are throttled.

**Suggested Fix:**
Add an `autouse` pytest fixture that calls `rate_limiter.reset()` before and after each test.

**Fix applied:** Added `autouse` fixture in `tests/test_api.py`.

---

### DATABASE-NOT-INITIALISED-IN-TESTS

| Field     | Value                                   |
| --------- | --------------------------------------- |
| Severity  | major                                   |
| File      | `tests/conftest.py` (missing file)      |
| Status    | fixed                                   |

**Description:**
Review endpoints depend on `get_db()` which requires `init_db()` to have been called first. No test setup initialised the database, so every review endpoint call raised `RuntimeError: Database not initialized. Call init_db() first.` and returned `500 Internal Server Error`.

**Steps to Reproduce:**
1. Run `pytest tests/test_api.py::TestReviewEndpoint`
2. Tests fail: `assert 500 == 404` (expected 404 for unknown ID, got 500 from unhandled RuntimeError)

**Expected:** Review endpoints return correct status codes.

**Actual:** All review calls crash with 500 due to uninitialised database.

**Suggested Fix:**
Create `tests/conftest.py` with a session-scoped `autouse` fixture that calls `asyncio.get_event_loop().run_until_complete(init_db("sqlite:///:memory:"))`.

**Fix applied:** Created `tests/conftest.py`.

---

### DOCKERFILE-PACKAGE-PERMISSIONS

| Field     | Value                        |
| --------- | ---------------------------- |
| Severity  | critical                     |
| File      | `Dockerfile`                 |
| Status    | fixed                        |

**Description:**
The builder stage installed packages using `pip install --user`, placing them in `/root/.local`. The runtime stage copied `/root/.local` and set `PATH=/root/.local/bin:$PATH`, then switched to `appuser`. On Linux, `/root/.local` has `700` permissions (owner: root, no access for others), so `appuser` could not read the installed packages. Running `python -m pytest` inside the container failed with `No module named pytest`.

Additionally the `FROM ... as builder` line used lowercase `as` which does not match `FROM` casing and triggered a build warning.

**Steps to Reproduce:**
1. CI runs `docker run --rm trustrag:test python -m pytest --version`
2. Fails: `/usr/local/bin/python: No module named pytest`

**Expected:** `pytest 8.2.2` printed; container exits 0.

**Actual:** Module not found error; container exits 1.

**Suggested Fix:**
Remove `--user` from `pip install` in the builder stage so packages go to system site-packages (`/usr/local/lib/python3.11/site-packages`). In the runtime stage, copy from that path instead of `/root/.local`. Fix `as` → `AS` casing.

**Fix applied:** Rewrote Dockerfile to use system-wide install and copy `/usr/local/lib/python3.11/site-packages` + `/usr/local/bin` into the runtime stage.
