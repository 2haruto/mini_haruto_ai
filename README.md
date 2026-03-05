# MiniHarutoAI

A compact ChatGPT/Gemini-style assistant app built with standard Python only.

## Features

- web chat UI
- session memory with SQLite
- provider switch (`mock`, `openai`, `gemini`)
- lightweight RAG from `knowledge/*.txt`
- citations in responses

## Quick Start

1. Install Python 3.11+.
2. Set environment variables.
3. Run the app.

```powershell
$env:LLM_PROVIDER="mock"
$env:LLM_MODEL="gpt-4.1-mini"
python .\run.py
```

Open `http://127.0.0.1:8080`.

## Provider Setup

### Mock mode

```powershell
$env:LLM_PROVIDER="mock"
```

### OpenAI mode

```powershell
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="YOUR_OPENAI_KEY"
$env:LLM_MODEL="gpt-4.1-mini"
```

### Gemini mode

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

`POST /api/chat` body:

```json
{
  "session_id": "optional-session-id",
  "message": "hello"
}
```
