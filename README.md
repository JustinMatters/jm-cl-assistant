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
- [Ollama](https://ollama.com/) running locally with a local model pulled (see below)
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

## Recommended Local Models

The local Ollama model handles query routing and answers simple queries
directly. The following are recommended for systems with ~10GB VRAM available
(e.g. after Whisper medium is loaded on a 16GB GPU):

| Model | Ollama command | Best for |
|-------|---------------|----------|
| DeepSeek R1 0528 Qwen3 8B | `ollama run sam860/deepseek-r1-0528-qwen3:8b` | General use, reasoning, routing |

Speech recognition uses **Whisper medium** by default (`WHISPER_MODEL=medium`),
which gives excellent accuracy at ~5GB VRAM on a CUDA GPU.

## Setup

```bash
# Install dependencies
uv sync

# Pull the recommended local model
ollama run sam860/deepseek-r1-0528-qwen3:8b

# Download Kokoro model files (see Required Model File Downloads above)
# Place kokoro-v1.0.onnx and voices-v1.0.bin in the project root

# Set your OpenRouter API key
export OPENROUTER_API_KEY=your_key_here

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
