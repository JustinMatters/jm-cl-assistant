# CLAUDE.md — jm-cl-assistant

## Project Overview
Hybrid AI chatbot that routes queries between a local Ollama model and Claude
(Sonnet/Opus) via the Anthropic API. Gradio UI with Whisper STT and Kokoro TTS.

## Architecture
- `src/router.py` — OllamaRouter: classifies query complexity (trivial_ollama /
  simple_ollama / complex_sonnet / complex_opus)
- `src/openrouter_client.py` — OpenRouterClient: wraps OpenAI-compatible REST API,
  targets claude-sonnet-4-6 and claude-opus-4-6 via OpenRouter
- `src/orchestrator.py` — Orchestrator: composes router + clients, manages
  conversation history, drives Approach B tool-use loop, handles pending
  confirmation for tools that require user approval before execution
- `src/speech_input.py` — WhisperTranscriber: STT via openai-whisper
- `src/speech_output.py` — KokoroSpeaker: TTS via kokoro-onnx
- `src/app.py` — Gradio Blocks UI, mode switching, wires all components;
  includes confirmation modal for sandboxed code execution
- `src/memory/` — RAG memory store backed by ChromaDB; injects relevant past
  context into each LLM call; can be toggled on/off per session
- `src/tools/` — Runtime tool registry; each tool self-registers at import
  time via `REGISTRY.register(ToolDefinition(...))`
  - Approach A tools: router-dispatched (calculator, converter, currency,
    datetime, weather, dictionary, location, web search, Wikipedia summary,
    URL reader, reminders, system info)
  - Approach B tools: LLM function-calling (Wikipedia, URL reader, reminders,
    code execution sandbox); sandboxed code requires UI confirmation
- `tests/` — pytest unit tests (mocked) + integration tests (live Ollama,
  marked with @pytest.mark.integration)

## Conventions
- Python 3.13+
- Line length: 80 characters
- Formatting: Black-compatible via Ruff (`ruff format`)
- Linting: Ruff rules E, F, I, UP, B
- All dependencies managed via UV (`uv add`, never pip install directly)
- Tests use pytest-mock for mocking; never mock at the module level
- Integration tests excluded from default runs; invoke with `pytest -m integration`

## Environment Variables
- `OPENROUTER_API_KEY` — required for Claude API calls via OpenRouter

## Runtime Configuration
The app accepts the following CLI arguments (implemented in `src/app.py`):
- `--whisper-model` — Whisper model size (default: `medium`)
- `--ollama-model` — Ollama model for routing and simple queries
  (default: `gemma4:e4b`)

## Claude Skills to Use
- Do NOT use the `claude-api` skill for `src/openrouter_client.py` — OpenRouter
  uses an OpenAI-compatible REST API, not the Anthropic SDK directly
- Invoke `update-config` skill when modifying hooks or settings

## Commands
```bash
uv sync                          # install dependencies
uv run python assistant.py       # run the app
uv run pytest                    # run unit tests
uv run pytest -m integration     # run integration tests
uv run ruff check .              # lint
uv run ruff format .             # format
```
