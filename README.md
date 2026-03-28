# jm-cl-assistant

A hybrid AI chatbot interface that routes queries intelligently between a local Ollama model and Claude (Sonnet/Opus) via the Anthropic API.

## Architecture

```
User Input (text | Whisper speech)
        ↓
   Gradio UI
        ↓
   Ollama Router (local model)
   ├── simple query → Ollama answer
   └── complex query → Claude Sonnet / Claude Opus
        ↓
   Output (text | Kokoro speech | dual)
```

## Features

- **Typed or spoken input** — switch between keyboard and microphone (Whisper STT)
- **Intelligent routing** — local Ollama model classifies query complexity and dispatches accordingly
- **Claude API integration** — Sonnet for moderately complex queries, Opus for the hardest ones
- **Flexible output** — text, speech (Kokoro TTS), or dual mode

## Requirements

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) for package management
- [Ollama](https://ollama.com/) running locally with a routing model pulled (e.g. `llama3.2:3b`)
- `ANTHROPIC_API_KEY` environment variable set

## Setup

```bash
# Install dependencies
uv sync

# Pull the local routing model
ollama pull llama3.2:3b

# Run the app
uv run python src/app.py
```

## Development

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Tests
uv run pytest

# Integration tests (requires live Ollama)
uv run pytest -m integration
```

## Stack

| Concern | Tool |
|---------|------|
| UI | Gradio |
| STT | Whisper |
| TTS | Kokoro |
| Local model / routing | Ollama |
| Cloud LLM | Anthropic Claude (Sonnet 4.6 / Opus 4.6) |
| Package management | UV |
| Linting / formatting | Ruff |
| Testing | pytest |
