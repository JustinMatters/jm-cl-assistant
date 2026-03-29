# Project Plan: `jm-cl-assistant` — Hybrid AI Chatbot

## Architecture Overview

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

---

## Permissible Ticket Statuses
`not started` | `in progress` | `complete`

---

## Phase 0 — Project Bootstrap

### T0.1 — Create GitHub Repository
**Status:** complete

- Create a new public/private GitHub repo named `jm-cl-assistant`
- Clone locally to `C:\Users\justi\Documents\GitHub\jm-cl-assistant`
- Add `.gitignore` (Python template), `LICENSE`, `README.md`
- **Skill:** none — standard `gh repo create` workflow

### T0.2 — Initialize UV Project
**Status:** complete

- Run `uv init` to create `pyproject.toml`
- Set `requires-python = ">=3.13"`
- Define project metadata (name, version, description)
- Add `uv.lock` to version control; add `.venv/` to `.gitignore`

### T0.3 — Configure Ruff
**Status:** complete

- Add `[tool.ruff]` section to `pyproject.toml`
- Enable rules: `E`, `F`, `I` (isort), `UP` (pyupgrade), `B` (bugbear)
- Set `line-length = 80`, `target-version = "py313"`
- Add `[tool.ruff.format]` for formatter config

### T0.4 — Configure pytest
**Status:** complete

- Add `[tool.pytest.ini_options]` to `pyproject.toml`
- Set `testpaths = ["tests"]`, `addopts = "-v --tb=short"`
- Create `tests/__init__.py` and `tests/conftest.py`

### T0.5 — Configure Claude Code Skills & Hooks
**Status:** complete

- Create `CLAUDE.md` at repo root documenting architecture decisions and conventions
- Use the **`update-config`** skill to add pre-commit hooks: `ruff check` and `ruff format --check`

---

## Phase 1 — Dependency Installation & CI

### T1.1 — Add Core Dependencies via UV
**Status:** complete

Install all runtime dependencies:
```
uv add gradio
uv add ollama
uv add openai
uv add openai-whisper
uv add kokoro-onnx
uv add sounddevice numpy
```

### T1.2 — Add Dev Dependencies via UV
**Status:** complete

```
uv add --dev ruff pytest pytest-mock pytest-asyncio
```

### T1.3 — Verify Ollama is Running Locally
**Status:** complete

- Document in `README.md`: required Ollama setup and recommended local model
- Recommended: DeepSeek R1 0528 Qwen3 8B (`ollama run sam860/deepseek-r1-0528-qwen3:8b`) for general use and routing
- Recommended: NVIDIA Nemotron Nano 9B v2 (`ollama run mirage335/NVIDIA-Nemotron-Nano-9B-v2-virtuoso`) for coding questions
- Default Whisper model: `medium`

### T1.4 — GitHub Actions CI (`.github/workflows/ci.yml`)
**Status:** complete

- Trigger on `push` and `pull_request` to `main`
- Jobs: `lint` (ruff check + format check), `test` (pytest, excluding integration marks)
- Use `astral-sh/setup-uv` action for UV installation
- Cache `.venv` between runs

---

## Phase 2 — Tests

### T2.1 — Router Unit Tests (`tests/test_router.py`)
**Status:** complete

- Mock Ollama client responses
- Assert correct classification for sample queries
- Test edge cases: ambiguous, empty input, non-English

### T2.2 — Orchestrator Unit Tests (`tests/test_orchestrator.py`)
**Status:** complete

- Mock `OllamaRouter` and `ClaudeClient`
- Verify correct backend is called for each classification
- Verify history is threaded correctly

### T2.3 — Claude Client Unit Tests (`tests/test_claude_client.py`)
**Status:** complete

- Mock `openai.OpenAI` using `pytest-mock`
- Verify correct model IDs are sent to OpenRouter
- Verify messages format

### T2.4 — Speech Module Unit Tests (`tests/test_speech.py`)
**Status:** complete

- Mock Whisper and Kokoro models
- Test transcription returns a string
- Test synthesis returns `(ndarray, int)`

### T2.5 — Integration Smoke Test (`tests/test_integration.py`)
**Status:** complete

- Spin up orchestrator against a live local Ollama instance (mark with `@pytest.mark.integration`)
- Excluded from default test run; run explicitly with `-m integration`

---

## Phase 3 — Core Backend Modules

### T3.1 — Ollama Router (`src/router.py`)
**Status:** complete

- `OllamaRouter` class wrapping the `ollama` Python client
- `classify(query: str) -> Literal["simple", "complex_sonnet", "complex_opus"]`
- Prompt the local model with a structured classification prompt
- Parse response into one of three routing decisions
- Default model: `sam860/deepseek-r1-0528-qwen3:8b` (hardcoded constant until T5.6)
- Unit testable in isolation (mock the Ollama client)

### T3.2 — Claude API Client (`src/claude_client.py`)
**Status:** complete

- `ClaudeClient` class using OpenRouter's OpenAI-compatible REST API (`openai` SDK)
- `ask(query: str, model: Literal["sonnet", "opus"], history: list) -> str`
- Map `"sonnet"` → `anthropic/claude-sonnet-4-6`, `"opus"` → `anthropic/claude-opus-4-6`
- Support conversation history (messages list)
- Read API key from environment variable `OPENROUTER_API_KEY`
- Base URL: `https://openrouter.ai/api/v1`

### T3.3 — Chat Orchestrator (`src/orchestrator.py`)
**Status:** complete

- `Orchestrator` class composing `OllamaRouter` + `ClaudeClient` + Ollama direct client
- `respond(query: str, history: list) -> tuple[str, list]`
- Routes based on classifier output → dispatches to correct backend
- Returns response text and updated history

---

## Phase 4 — Speech I/O Modules

### T4.1 — Speech Input: Whisper (`src/speech_input.py`)
**Status:** complete

- `WhisperTranscriber` class loading a Whisper model
- Default model: `medium` (hardcoded constant until T5.6)
- `transcribe(audio_array: np.ndarray, sample_rate: int) -> str`
- Accept raw numpy audio from Gradio's audio component

### T4.2 — Speech Output: Kokoro (`src/speech_output.py`)
**Status:** complete

- `KokoroSpeaker` class wrapping the `kokoro-onnx` pipeline
- `synthesize(text: str) -> tuple[np.ndarray, int]` — returns audio array + sample rate
- Voice and speed configurable
- Lazy-load model on first call to avoid startup delay

---

## Phase 5 — Gradio Interface

### T5.1 — App Skeleton (`src/app.py`)
**Status:** complete

- Gradio `Blocks` layout
- Top-level mode toggles: **Input Mode** (`text` | `speech`) and **Output Mode** (`text` | `speech` | `dual`)
- Chat history component (`gr.Chatbot`)
- Submit/record controls

### T5.2 — Text Input Flow
**Status:** complete

- `gr.Textbox` for typed input
- On submit: `Orchestrator.respond()` → display in chatbot
- Show routing decision as a subtle label (e.g. "Answered by: Ollama / Sonnet / Opus")

### T5.3 — Speech Input Flow
**Status:** complete

- `gr.Audio(source="microphone")` component shown when input mode = speech
- On audio captured: `WhisperTranscriber.transcribe()` → feed transcript to orchestrator
- Display transcript in chatbot as user message

### T5.4 — Speech Output Flow
**Status:** complete

- When output mode = `speech` or `dual`: pipe response text through `KokoroSpeaker.synthesize()`
- Play via `gr.Audio(autoplay=True)`
- `dual` mode renders both text in chatbot and audio playback simultaneously

### T5.5 — Mode Switching Logic
**Status:** complete

- `gr.Radio` components for input/output mode
- Gradio `visible` updates to show/hide `gr.Textbox` vs `gr.Audio` input
- All state managed through `gr.State`

### T5.6 — Argparse Runtime Configuration (`src/app.py`)
**Status:** complete

- Add `argparse` to `src/app.py` entry point
- `--whisper-model` — Whisper model size (default: `medium`)
- `--ollama-model` — Ollama model name (default: `sam860/deepseek-r1-0528-qwen3:8b`)
- Pass parsed args down to `WhisperTranscriber` and `OllamaRouter` constructors
- Until this ticket is implemented, both values are hardcoded as module-level
  constants in their respective source files

---

## Phase 6 — Quality Gate

### T6.1 — Ruff Lint & Format Pass
**Status:** complete

- Run `uv run ruff check . --fix`
- Run `uv run ruff format .`
- Resolve all remaining violations manually
- Confirms codebase is clean before considering the project shippable

---

## Phase 7 — Refinements

### T7.1 — Dark / Light Mode Toggle
**Status:** not started

- Add a dark/light mode toggle to the Gradio UI
- Use Gradio's built-in theme support or a `gr.Radio`/`gr.Button` toggle
- Persist selection within the session via `gr.State`

### T7.2 — Scale Chat Panel to Fit Viewport
**Status:** not started

- Adjust the `gr.Chatbot` height so the full app (chat + input + send button) is
  visible without scrolling
- Chat panel must show at least 5 lines of conversation before scrolling internally
- Use Gradio's `height` parameter or custom CSS as needed

### T7.3 — Rename Chat Panel to "Previous Conversation"
**Status:** not started

- Change the `gr.Chatbot` label from `"Chat"` to `"Previous Conversation"`

### T7.4 — Prefix Each Reply with Model Name in Bold
**Status:** not started

- Prepend the responding model name in bold to every assistant reply before
  displaying it in the chatbot (e.g. `**Ollama:** ...`, `**Claude Sonnet:** ...`)
- Source the label from `orchestrator.last_backend`

### T7.5 — Lint and Test
**Status:** not started

- `uv run ruff check . --fix`
- `uv run ruff format .`
- `uv run pytest -m "not integration"`

### T7.6 — Add Google-Style Docstrings
**Status:** not started

- Add docstrings to all public classes and functions across `src/` following the
  [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- Cover: `OllamaRouter`, `ClaudeClient`, `Orchestrator`, `WhisperTranscriber`,
  `KokoroSpeaker`, `build_app`, `main`

### T7.7 — Lint and Test Again
**Status:** not started

- Repeat T7.5 after docstrings are added to confirm nothing was broken

### T7.8 — Update README
**Status:** not started

- Add running instructions: `uv run python assistant.py` with argparse options
- Add a note about the Whisper model download delay on first run (~1.5 GB for
  `medium`, instant on subsequent runs as it is cached in `~/.cache/whisper/`)
- Verify and document kokoro-onnx model file download requirements (model files
  are large binaries and currently gitignored — confirm exact filenames, download
  source, and placement instructions)

---

## Implementation Order Summary

| Order | Phase | Tickets | Status |
|-------|-------|---------|--------|
| 1 | Bootstrap | T0.1 → T0.5 | complete |
| 2 | Dependencies & CI | T1.1 → T1.4 | complete |
| 3 | Tests | T2.1 → T2.5 | complete |
| 4 | Backend core | T3.1 → T3.3 | complete |
| 5 | Speech I/O | T4.1 → T4.2 | complete |
| 6 | Gradio UI | T5.1 → T5.6 | complete |
| 7 | Quality gate | T6.1 | complete |
| 8 | Refinements | T7.1 → T7.8 | not started |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
