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
- Use the **`claude-api`** skill when writing any Anthropic SDK code (invoked in T2.2)

---

## Phase 1 — Dependency Installation

### T1.1 — Add Core Dependencies via UV
**Status:** not started

Install all runtime dependencies:
```
uv add gradio
uv add ollama
uv add anthropic
uv add openai-whisper
uv add kokoro
uv add sounddevice numpy
```

### T1.2 — Add Dev Dependencies via UV
**Status:** complete

```
uv add --dev ruff pytest pytest-mock pytest-asyncio
```

### T1.3 — Verify Ollama is Running Locally
**Status:** not started

- Document in `README.md`: required Ollama setup and recommended local model (e.g. `llama3.2:3b` or `mistral:7b` for routing)
- Add `ollama pull <model>` to setup instructions

---

## Phase 2 — Core Backend Modules

### T2.1 — Ollama Router (`src/router.py`)
**Status:** not started

- `OllamaRouter` class wrapping the `ollama` Python client
- `classify(query: str) -> Literal["simple", "complex_sonnet", "complex_opus"]`
- Prompt the local model with a structured classification prompt
- Parse response into one of three routing decisions
- Unit testable in isolation (mock the Ollama client)

### T2.2 — Claude API Client (`src/claude_client.py`)
**Status:** not started

- `ClaudeClient` class using OpenRouter's OpenAI-compatible REST API (`openai` SDK)
- `ask(query: str, model: Literal["sonnet", "opus"], history: list) -> str`
- Map `"sonnet"` → `anthropic/claude-sonnet-4-6`, `"opus"` → `anthropic/claude-opus-4-6`
- Support conversation history (messages list)
- Read API key from environment variable `OPENROUTER_API_KEY`
- Base URL: `https://openrouter.ai/api/v1`

### T2.3 — Chat Orchestrator (`src/orchestrator.py`)
**Status:** not started

- `Orchestrator` class composing `OllamaRouter` + `ClaudeClient` + Ollama direct client
- `respond(query: str, history: list) -> tuple[str, list]`
- Routes based on classifier output → dispatches to correct backend
- Returns response text and updated history

---

## Phase 3 — Speech I/O Modules

### T3.1 — Speech Input: Whisper (`src/speech_input.py`)
**Status:** not started

- `WhisperTranscriber` class loading a Whisper model (default `base`)
- `transcribe(audio_array: np.ndarray, sample_rate: int) -> str`
- Accept raw numpy audio from Gradio's audio component
- Model size configurable via environment variable `WHISPER_MODEL`

### T3.2 — Speech Output: Kokoro (`src/speech_output.py`)
**Status:** not started

- `KokoroSpeaker` class wrapping the Kokoro pipeline
- `synthesize(text: str) -> tuple[np.ndarray, int]` — returns audio array + sample rate
- Voice and speed configurable
- Lazy-load model on first call to avoid startup delay

---

## Phase 4 — Gradio Interface

### T4.1 — App Skeleton (`src/app.py`)
**Status:** not started

- Gradio `Blocks` layout
- Top-level mode toggles: **Input Mode** (`text` | `speech`) and **Output Mode** (`text` | `speech` | `dual`)
- Chat history component (`gr.Chatbot`)
- Submit/record controls

### T4.2 — Text Input Flow
**Status:** not started

- `gr.Textbox` for typed input
- On submit: `Orchestrator.respond()` → display in chatbot
- Show routing decision as a subtle label (e.g. "Answered by: Ollama / Sonnet / Opus")

### T4.3 — Speech Input Flow
**Status:** not started

- `gr.Audio(source="microphone")` component shown when input mode = speech
- On audio captured: `WhisperTranscriber.transcribe()` → feed transcript to orchestrator
- Display transcript in chatbot as user message

### T4.4 — Speech Output Flow
**Status:** not started

- When output mode = `speech` or `dual`: pipe response text through `KokoroSpeaker.synthesize()`
- Play via `gr.Audio(autoplay=True)`
- `dual` mode renders both text in chatbot and audio playback simultaneously

### T4.5 — Mode Switching Logic
**Status:** not started

- `gr.Radio` components for input/output mode
- Gradio `visible` updates to show/hide `gr.Textbox` vs `gr.Audio` input
- All state managed through `gr.State`

---

## Phase 5 — Tests

### T5.1 — Router Unit Tests (`tests/test_router.py`)
**Status:** not started

- Mock Ollama client responses
- Assert correct classification for sample queries
- Test edge cases: ambiguous, empty input, non-English

### T5.2 — Orchestrator Unit Tests (`tests/test_orchestrator.py`)
**Status:** not started

- Mock `OllamaRouter` and `ClaudeClient`
- Verify correct backend is called for each classification
- Verify history is threaded correctly

### T5.3 — Claude Client Unit Tests (`tests/test_claude_client.py`)
**Status:** not started

- Mock `anthropic.Anthropic` using `pytest-mock`
- Verify correct model IDs are sent
- Verify messages format

### T5.4 — Speech Module Unit Tests (`tests/test_speech.py`)
**Status:** not started

- Mock Whisper and Kokoro models
- Test transcription returns a string
- Test synthesis returns `(ndarray, int)`

### T5.5 — Integration Smoke Test (`tests/test_integration.py`)
**Status:** not started

- Spin up orchestrator against a live local Ollama instance (mark with `@pytest.mark.integration`)
- Excluded from default test run; run explicitly with `-m integration`

---

## Phase 6 — Lint, Format & CI

### T6.1 — Ruff Lint & Format Pass
**Status:** not started

- Run `uv run ruff check . --fix`
- Run `uv run ruff format .`
- Resolve all remaining violations manually

### T6.2 — GitHub Actions CI (`.github/workflows/ci.yml`)
**Status:** not started

- Trigger on `push` and `pull_request` to `main`
- Jobs: `lint` (ruff check + format check), `test` (pytest, excluding integration marks)
- Use `astral-sh/setup-uv` action for UV installation
- Cache `.venv` between runs

### T6.3 — Pre-commit Hook (local dev)
**Status:** not started

- Use **`update-config`** skill to register a hook that runs `ruff check` + `ruff format --check` before every commit
- Prevents lint regressions reaching the remote

---

## Implementation Order Summary

| Order | Phase | Tickets | Status |
|-------|-------|---------|--------|
| 1 | Bootstrap | T0.1 → T0.5 | not started |
| 2 | Dependencies | T1.1 → T1.3 | not started |
| 3 | Backend core | T2.1 → T2.3 | not started |
| 4 | Speech I/O | T3.1 → T3.2 | not started |
| 5 | Gradio UI | T4.1 → T4.5 | not started |
| 6 | Tests | T5.1 → T5.5 | not started |
| 7 | CI/Lint | T6.1 → T6.3 | not started |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
| T6.3 | `update-config` | Finalize hook configuration |
