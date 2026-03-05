# MiniHarutoAI

MiniHarutoAI is a compact ChatGPT/Gemini-style assistant app.
It focuses on practical product skills for interviews:

- chat UX
- conversation memory
- lightweight RAG
- multi-provider LLM integration

## Why This Project

This project is designed as a portfolio MVP to show:

1. backend architecture and API design
2. data modeling with SQLite
3. retrieval + generation flow
4. production-minded tradeoff explanations

## Core Features

- Web chat UI (`web/index.html`, `web/app.js`)
- Session and message persistence with SQLite (`app/db.py`)
- Provider switch: `mock`, `openai`, `gemini` (`app/providers.py`)
- Lightweight RAG from local text files in `knowledge/*.txt` (`app/rag.py`)
- Japanese-aware tokenization (CJK block + bigram) for better local retrieval
- Citation ids returned in chat API response

## Architecture

```text
Browser UI
  -> /api/chat
  -> ChatService
      -> ChatRepository (SQLite)
      -> KnowledgeBase (RAG retrieval)
      -> Provider (Mock/OpenAI/Gemini)
```

## Tech Stack

- Python 3.11+
- Standard library HTTP server (`http.server`)
- SQLite (`sqlite3`)
- Vanilla HTML/CSS/JavaScript

## Quick Start

```powershell
cd C:\Users\Haruto\Documents\Playground\mini_haruto_ai
$env:LLM_PROVIDER="mock"
$env:LLM_MODEL="gpt-4.1-mini"
python .\run.py
```

Open: `http://127.0.0.1:8080`

## Provider Setup

### Mock

```powershell
$env:LLM_PROVIDER="mock"
```

### OpenAI

```powershell
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="YOUR_OPENAI_KEY"
$env:LLM_MODEL="gpt-4.1-mini"
```

### Gemini

```powershell
$env:LLM_PROVIDER="gemini"
$env:GEMINI_API_KEY="YOUR_GEMINI_KEY"
$env:LLM_MODEL="gemini-2.0-flash"
```

## API Endpoints

- `GET /api/health`
- `GET /api/sessions`
- `GET /api/messages?session_id=<id>`
- `POST /api/chat`

Request body for `POST /api/chat`:

```json
{
  "session_id": "optional-session-id",
  "message": "hello"
}
```

## Interview Talking Points

- Why provider abstraction was used: avoid vendor lock-in and reduce integration cost.
- Why SQLite was chosen first: fastest path to MVP with persistent memory.
- Why RAG was kept lightweight: validate retrieval flow before vector DB complexity.
- Why `mock` mode exists: local testing without API key cost.
- Why Japanese bigram tokenization was chosen first: no extra dependency and fast iteration.

## Next Improvements

- Streaming responses (Server-Sent Events)
- Auth and per-user data separation
- Automated tests for service and repository layers
- Vector search backend for larger knowledge bases
