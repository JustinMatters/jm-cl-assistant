# jm-cl-assistant

A hybrid AI chatbot interface that routes queries intelligently between local
Ollama models and Claude (Sonnet/Opus) via OpenRouter's OpenAI-compatible API.

## About This Project

This project is an experiment in using [Claude Code](https://claude.ai/code)
as the primary development tool. The entire codebase — architecture,
implementation, tests, and documentation — has been built through an
interactive session with Claude Code, with the human developer providing
direction and requirements while Claude Code writes and reviews the code.

The goal is to explore how far an AI coding assistant can take a non-trivial
project: routing logic, speech I/O, a Gradio UI, CI, and a full test suite,
all developed conversationally.

## Architecture

```
User Input (text | Whisper speech)
        ↓
   Gradio UI
        ↓
   Ollama Router (local model classifies query)
   ├── trivial_ollama → qwen3:1.7b (fast local model)
   ├── simple_ollama  → gemma4:e4b (local multimodal model)
   ├── complex_sonnet → Claude Sonnet 4.6 via OpenRouter
   └── complex_opus   → Claude Opus 4.6 via OpenRouter
        ↓
   Output (text | text and speech via Kokoro TTS)
```

## Features

- **Typed or spoken input** — switch between keyboard and microphone (Whisper STT)
- **Intelligent routing** — local Ollama model classifies query complexity and dispatches accordingly
- **Claude API integration** — Sonnet for moderately complex queries, Opus for the hardest ones
- **Flexible output** — text only, or text and speech (Kokoro TTS)
- **Runtime tools** — deterministic answers for maths, unit conversion, currency rates, date/time, weather, dictionary definitions, web search, Wikipedia summaries, URL reading, and reminders; each tool can be toggled on/off in the UI
- **Code execution sandbox** — LLM-drafted Python snippets run via a restricted asteval interpreter; a confirmation modal shows the code before anything executes so you can approve or deny
- **RAG memory** — past conversations stored in a local ChromaDB vector store and injected as context on relevant queries; toggleable per session

## Requirements

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) for package management
- [Ollama](https://ollama.com/) running locally with local models pulled (see below)
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

This app uses two local models. Pull both before running the app:

```bash
# Trivial queries — fast, low-VRAM
ollama run qwen3:1.7b

# Simple queries, query routing, and vision (multimodal)
ollama run gemma4:e4b
```

> **Note:** Ollama loads one model at a time. The fast model (~2 GB VRAM)
> and Gemma 4 (~8 GB VRAM) are loaded on demand as queries arrive.
> On a 16 GB GPU with Whisper medium loaded (~5 GB), there is sufficient
> headroom for either model.

### 3. Model Reference

| Model | Routing tier | VRAM (approx) |
|-------|-------------|---------------|
| `qwen3:1.7b` | `trivial_ollama` — greetings, facts a schoolchild would know | ~2 GB |
| `gemma4:e4b` | `simple_ollama` — factual lookups, routing classifier, vision | ~8 GB |
| Claude Sonnet 4.6 (OpenRouter) | `complex_sonnet` — analysis, essays, reasoning | cloud |
| Claude Opus 4.6 (OpenRouter) | `complex_opus` — research, expert proofs | cloud |

Speech recognition uses **Whisper medium** by default (~5 GB VRAM on CUDA).
The Whisper model and Ollama model can be overridden at runtime:

```bash
uv run python assistant.py --whisper-model tiny --ollama-model llama3.2
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--whisper-model` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `--ollama-model` | `gemma4:e4b` | Ollama model name for routing and simple queries |

> **First run note:** If the Whisper model has not been used before, it will
> be downloaded automatically (~1.5 GB for `medium`) on first launch and
> cached in `~/.cache/whisper/`. Subsequent starts are instant.

## Using Speech Input

Switch the **Input Mode** radio button to `speech` to reveal the microphone
recorder.

**Browser microphone permission is not requested until you press the record
button.** Before you press it, the UI may show a "No microphone found"
warning — this is Gradio's placeholder state and does not mean your microphone
is absent or blocked. Press the record button and the browser will prompt you
to grant microphone access; the warning clears once permission is given.

This behaviour has been observed on both Chrome and Firefox on Windows 11 and
is a property of how Gradio requests the microphone, not a browser-specific
issue.

If you dismiss the permission prompt or previously blocked the site, grant
access via your browser's site settings for `localhost` and reload the page.

## Setup

```bash
# 1. Install Python dependencies
uv sync

# 2. Pull Ollama models (see Ollama Setup above)
ollama run qwen3:1.7b
ollama run gemma4:e4b

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
| Memory / vector store | ChromaDB |
| Web search | DuckDuckGo (ddgs) |
| URL content extraction | trafilatura |
| Code sandbox | asteval |
| Package management | UV |
| Linting / formatting | Ruff |
| Testing | pytest |
