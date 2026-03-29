# jm-cl-assistant

A hybrid AI chatbot interface that routes queries intelligently between a local Ollama model and Claude (Sonnet/Opus) via OpenRouter's OpenAI-compatible API.

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

If using a quantized model, pass the filename to `KokoroSpeaker` at
initialisation (full precision is the default).

## Ollama Setup

### 1. Install Ollama

Download and install from [ollama.com](https://ollama.com). On Windows,
Ollama runs as a background service and starts automatically.

Verify it is running:
```bash
ollama list
```

### 2. Pull the Local Models

This app uses two local models — one for general queries and routing, one
for coding questions. Pull both before running the app:

```bash
# General use, reasoning, and query routing (default)
ollama run sam860/deepseek-r1-0528-qwen3:8b

# Coding questions
ollama run mirage335/NVIDIA-Nemotron-Nano-9B-v2-virtuoso
```

> **Note:** These models require approximately 5–6 GB of VRAM each. On a
> 16 GB GPU with Whisper medium loaded (~5 GB), there is sufficient headroom
> to run either model. Only one is loaded at a time by Ollama.

### 3. Recommended Models Reference

| Model | Best for | VRAM (approx) |
|-------|----------|---------------|
| DeepSeek R1 0528 Qwen3 8B | General use, reasoning, routing | ~5 GB |
| NVIDIA Nemotron Nano 9B v2 | Coding questions | ~6 GB |

Speech recognition uses **Whisper medium** by default (~5 GB VRAM on CUDA).
The Whisper model and Ollama model can be overridden at runtime:

```bash
uv run python assistant.py --whisper-model tiny --ollama-model llama3.2
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--whisper-model` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `--ollama-model` | `sam860/deepseek-r1-0528-qwen3:8b` | Ollama model name for routing and simple queries |

> **First run note:** If the Whisper model has not been used before, it will
> be downloaded automatically (~1.5 GB for `medium`) on first launch and
> cached in `~/.cache/whisper/`. Subsequent starts are instant.

## Setup

```bash
# 1. Install Python dependencies
uv sync

# 2. Pull Ollama models (see Ollama Setup above)
ollama run sam860/deepseek-r1-0528-qwen3:8b
ollama run mirage335/NVIDIA-Nemotron-Nano-9B-v2-virtuoso

# 3. Download Kokoro model files (see Required Model File Downloads above)
#    Place kokoro-v1.0.onnx and voices-v1.0.bin in the project root

# 4. Set your OpenRouter API key
export OPENROUTER_API_KEY=your_key_here

# 5. Run the app (defaults)
uv run python assistant.py

# 5a. Or override models at launch
uv run python assistant.py --whisper-model tiny --ollama-model llama3.2
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
