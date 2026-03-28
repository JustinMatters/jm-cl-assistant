# CLAUDE.md — jm-cl-assistant

## Project Overview
Hybrid AI chatbot that routes queries between a local Ollama model and Claude
(Sonnet/Opus) via the Anthropic API. Gradio UI with Whisper STT and Kokoro TTS.

## Architecture
- `src/router.py` — OllamaRouter: classifies query complexity (simple /
  complex_sonnet / complex_opus)
- `src/claude_client.py` — ClaudeClient: wraps anthropic SDK, targets
  claude-sonnet-4-6 and claude-opus-4-6
- `src/orchestrator.py` — Orchestrator: composes router + clients, manages
  conversation history
- `src/speech_input.py` — WhisperTranscriber: STT via openai-whisper
- `src/speech_output.py` — KokoroSpeaker: TTS via kokoro-onnx
- `src/app.py` — Gradio Blocks UI, mode switching, wires all components
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

## Runtime Configuration (argparse — see T4.6)
The following are currently hardcoded defaults pending argparse implementation:
- Whisper model: `medium` (hardcoded in `src/speech_input.py`)
- Ollama model: `sam860/deepseek-r1-0528-qwen3:8b` (hardcoded in `src/router.py`)
These will become `--whisper-model` and `--ollama-model` CLI arguments in T4.6.

## Claude Skills to Use
- Do NOT use the `claude-api` skill for `src/claude_client.py` — OpenRouter
  uses an OpenAI-compatible REST API, not the Anthropic SDK directly
- Invoke `update-config` skill when modifying hooks or settings

## Commands
```bash
uv sync                          # install dependencies
uv run python src/app.py         # run the app
uv run pytest                    # run unit tests
uv run pytest -m integration     # run integration tests
uv run ruff check .              # lint
uv run ruff format .             # format
```
