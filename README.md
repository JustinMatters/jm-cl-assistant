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

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) for package management
- [Ollama](https://ollama.com/) running locally with a routing model pulled (e.g. `llama3.2:3b`)
- `OPENROUTER_API_KEY` environment variable set

## Required Model File Downloads

The Kokoro TTS engine requires two large model files that are not included in
this repository. Download them and place them in the project root before
running the app.

| File | Size | Description |
|------|------|-------------|
| `kokoro-v1.0.onnx` | 310 MB | Full precision model (recommended) |
| `voices-v1.0.bin` | — | Voice data (26 voice profiles) |

**Download from:**
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0

Quantized alternatives (smaller, slightly lower quality):
- `kokoro-v1.0.fp16.onnx` (169 MB) — half precision
- `kokoro-v1.0.int8.onnx` (88 MB) — integer quantized

If using a quantized model, update `KOKORO_MODEL` in your environment (see below).

## Setup

```bash
# Install dependencies
uv sync

# Pull the local routing model
ollama pull llama3.2:3b

# Download Kokoro model files (see Required Model File Downloads above)
# Place kokoro-v1.0.onnx and voices-v1.0.bin in the project root

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
| Cloud LLM | Claude Sonnet 4.6 / Opus 4.6 via OpenRouter |
| Package management | UV |
| Linting / formatting | Ruff |
| Testing | pytest |
