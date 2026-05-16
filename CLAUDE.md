# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

HRMS-AI is a FastAPI service that bridges natural language HR queries to a remote HRMS REST API. A user sends a plain-English question; the system uses a local LLM (Gemma, via llama-cpp-python) to (1) pick the right API endpoint, (2) call that endpoint, and (3) reformat the result as a conversational response.

## Commands

```bash
# Start the development server
uvicorn app.main:app --reload

# Test LLM inference directly (no FastAPI)
python test_llm.py

# Download/list quantized models from HuggingFace
python download_model.py
```

There is no automated test suite. `test_llm.py` is a manual smoke test.

## Architecture

### Request Pipeline

Every `POST /chat` request flows through three sequential steps in `app/orchestrator.py`:

1. **Tool Selection** (`app/llm/tool_selector.py`) — LLM reads the user query and the list of discovered tools, picks the best match. Falls back to fuzzy string matching with a 0.5-score threshold to avoid false positives.
2. **API Execution** (`app/tools/executor.py`) — Issues the GET/POST against the HRMS REST API with the caller's Bearer token forwarded verbatim.
3. **Response Generation** (`app/llm/response_generator.py`) — LLM takes the raw API JSON and produces a human-readable answer.

### Tool Discovery (startup)

On startup (`app/main.py` lifespan), the app:
- Fetches Swagger docs from `SWAGGER_URL` (`app/core/config.py`)
- Parses them into tool descriptors (`app/tools/swagger_parser.py`, `tool_builder.py`)
- Registers them in an in-memory list (`app/tools/registry.py`: `TOOLS`, `LLM_TOOLS`)

All tool knowledge is derived at runtime from the remote Swagger spec — there is no static tool list in the code.

### LLM Layer

`app/llm/llm.py` — singleton Llama instance, loaded lazily on first use. Config: 6 threads, batch 128, context window 1024–4096.

`app/llm/llm_service.py` — all LLM calls go through here. Two call profiles control context allocation:
- `tool_call`: small context (≥2 KB), max 128 output tokens — fast, for intent classification
- `response_generation`: full context (≥4 KB), max 2048 output tokens — for final answers

Context window is sized dynamically: input tokens are estimated at ~1 token per 4 characters, then clamped to the profile limits. All calls are protected by a `threading.Lock`.

### Authentication

The `/chat` endpoint requires a `Bearer <token>` header. The token is extracted and forwarded to every upstream HRMS API call — the service itself does not validate or cache credentials.

### Performance Instrumentation

`app/utils/timing.py` provides a `Timer` with named checkpoints. The orchestrator records latency for each pipeline step and logs them on every request.

## Key Configuration

Defined in `app/core/config.py`:
- `SWAGGER_URL` — remote Swagger JSON endpoint
- `BASE_URL` — HRMS API base URL

Model file is expected at `models/gemma/gemma-4-e2b-it-Q8_0.gguf` (relative to project root, ~4.7 GB). The path is hardcoded in `app/llm/llm.py`.
