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
**Status:** complete

- Add a dark/light mode toggle to the Gradio UI
- Use Gradio's built-in theme support or a `gr.Radio`/`gr.Button` toggle
- Persist selection within the session via `gr.State`

### T7.2 — Scale Chat Panel to Fit Viewport
**Status:** complete

- Adjust the `gr.Chatbot` height so the full app (chat + input + send button) is
  visible without scrolling
- Chat panel must show at least 5 lines of conversation before scrolling internally
- Use Gradio's `height` parameter or custom CSS as needed

### T7.3 — Rename Chat Panel to "Previous Conversation"
**Status:** complete

- Change the `gr.Chatbot` label from `"Chat"` to `"Previous Conversation"`

### T7.4 — Prefix Each Reply with Model Name in Bold
**Status:** complete

- Prepend the responding model name in bold to every assistant reply before
  displaying it in the chatbot (e.g. `**Ollama:** ...`, `**Claude Sonnet:** ...`)
- Source the label from `orchestrator.last_backend`

### T7.5 — Toggle to Show/Hide `<think>` Tag Content
**Status:** complete

- Add a checkbox toggle next to the Conversation Height dropdown
- When enabled (default: hidden), strip any text between `<think>` and `</think>`
  tags from the LLM response before displaying it in the chatbot
- When disabled, show the full response including chain-of-thought content
- Apply stripping to the display history only; the clean response (without tags)
  is already stored in API history

### T7.6 — Lint and Test
**Status:** complete

- `uv run ruff check . --fix`
- `uv run ruff format .`
- `uv run pytest -m "not integration"`

### T7.7 — Add Google-Style Docstrings
**Status:** complete

- Add docstrings to all public classes and functions across `src/` following the
  [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- Cover: `OllamaRouter`, `OpenRouterClient`, `Orchestrator`, `WhisperTranscriber`,
  `KokoroSpeaker`, `build_app`, `main`

### T7.8 — Lint and Test Again
**Status:** not started

- Repeat T7.6 after docstrings are added to confirm nothing was broken
- Extend integration tests to also run as part of the T7.8 gate
- Auto-start Ollama before integration tests via a session-scoped
  `ollama_server` fixture in `conftest.py` so manual pre-launch is not required
- Add `TestEnvironment.test_openrouter_api_key_is_set` integration test that
  asserts `OPENROUTER_API_KEY` is present and non-empty in the environment

### T7.9 — Update README
**Status:** complete

- Add running instructions: `uv run python assistant.py` with argparse options
- Add a note about the Whisper model download delay on first run (~1.5 GB for
  `medium`, instant on subsequent runs as it is cached in `~/.cache/whisper/`)
- Verify and document kokoro-onnx model file download requirements (model files
  are large binaries and currently gitignored — confirm exact filenames, download
  source, and placement instructions)

---

## Phase 8 — Text to Speech Debugging

### T8.1 — Fix Kokoro TTS Initialisation
**Status:** complete

The installed version of `kokoro-onnx` requires `model_path` and
`voices_path` as positional arguments to `Kokoro.__init__()`, but
`KokoroSpeaker.synthesize` currently calls `Kokoro()` with no arguments,
raising:

```
TypeError: Kokoro.__init__() missing 2 required positional arguments:
'model_path' and 'voices_path'
```

Also fixed: `Kokoro.create()` requires a `voice` argument. Added `voice`
(default: `"af_heart"`) and `speed` (default: `1.0`) as constructor args.

- Investigate the current `kokoro-onnx` API to confirm required arguments
- Update `KokoroSpeaker` to pass the correct model file paths
  (expected files: `kokoro-v1.0.onnx` and `voices-v1.0.bin` in project root
  per the README)
- Make the paths, voice, and speed configurable (constructor arguments with
  sensible defaults)
- Update or add unit tests to cover the new constructor signature

### T8.2 — Fix Speech Not Obeying `<think>` Tag Toggle
**Status:** complete

Speech synthesis was always passed the raw LLM response, ignoring the
"Show `<think>` tags" toggle. When the toggle was off, the TTS would still
read out chain-of-thought content.

- Apply the same `show` logic to speech text as to the chat display:
  `response if show else strip_think_tags(response)`
- Fix applied in both `handle_text` and `handle_audio` in `src/app.py`

### T8.3 — Fix Float32 Audio Warning from Gradio
**Status:** complete

Gradio emitted a `UserWarning` about auto-converting float32 audio to int16.
Kokoro returns float32 samples in `[-1, 1]`; Gradio's `gr.Audio` expects int16.

- Convert audio array before returning to Gradio:
  `(arr * 32767).astype(np.int16)`
- Fix applied in both `handle_text` and `handle_audio` in `src/app.py`

### T8.4 — Strip Markdown Before TTS Synthesis
**Status:** complete

Models that return Markdown-formatted responses caused TTS to vocalise
symbols (e.g. "asterisk asterisk"). Markdown should be stripped before
passing text to Kokoro; the chat display keeps the formatted version.

- Add `strip_markdown(text: str) -> str` to `src/helpers.py`
- Call `strip_markdown(speech_text)` in both `handle_text` and
  `handle_audio` in `src/app.py` before `speaker.synthesize()`
- Add unit tests in `tests/test_helpers.py`

### T8.5 — Manual Check of TTS and Resolve Any Bugs
**Status:** complete

### T8.6 — Manual Check of Dual Mode and Resolve Any Bugs
**Status:** complete

### T8.7 — Simplify Output Mode Radio to Two Options
**Status:** complete

Text is always printed to the conversation panel, making a separate "dual"
mode redundant. Simplify output mode to two options:

- `text` — response shown in chat only, no audio
- `text and speech` — response shown in chat AND spoken via Kokoro

- Change `gr.Radio` choices to `["text", "text and speech"]`, default `"text"`
- Update `toggle_output_mode` and both `handle_text` / `handle_audio` to
  check `out_mode == "text and speech"` instead of
  `out_mode in ("speech", "dual")`
- Remove any remaining references to `"speech"` and `"dual"` output modes

### T8.8 — Voice Selection Dropdown
**Status:** complete

Add a `gr.Dropdown` to the UI letting the user pick a Kokoro voice. Four
options covering the most common accent/gender combinations:

| Label | Voice ID | Description |
|-------|----------|-------------|
| American Female (default) | `af_heart` | Current default |
| American Male | `am_michael` | |
| British Female | `bf_emma` | |
| British Male | `bm_george` | |

- Add the dropdown to the controls row in `src/app.py`
- Pass the selected voice ID to `KokoroSpeaker` — either re-instantiate
  with the new voice or add a `voice` setter / update the voice attribute
  directly before synthesis
- Default selection: `af_heart` (American Female)

---

## Phase 9 — Routing Tiers

### T9.1 — Identify Fast Small Local Model
**Status:** complete

Research and select a very fast, lightweight Ollama model suitable for
handling trivial queries (e.g. simple greetings, single-fact lookups,
arithmetic). Criteria:

- Low VRAM footprint (fits alongside Whisper medium on a 16 GB GPU)
- Fast time-to-first-token (noticeably quicker than the 8B reasoning model)
- Sufficient quality for trivial responses

**Selected: `qwen3:1.7b`**
- ~1.5–2 GB VRAM (Q4_K_M), ~1.1 GB on disk
- Same Qwen model family as `sam860/deepseek-r1-0528-qwen3:8b` — consistent
  tokenizer behaviour and well-documented instruction-following precision,
  important for the one-word routing response
- Estimated 4–6× faster than the 8B model for short-context inference
- `ollama run qwen3:1.7b`

**Rejected alternatives:**

| Model | Params | Est. VRAM | Reason rejected |
|-------|--------|-----------|-----------------|
| `gemma3:1b` | 1B | ~1–1.5 GB | Slightly higher risk of malformed classification output |
| `llama3.2:1b` | 1B | ~1.5–2 GB | Outclassed by Qwen3 at similar VRAM; keep as fallback if GPU/driver issues |
| `qwen3:0.6b` | 0.6B | ~0.8 GB | Noticeable instruction-following quality dip vs 1.7B |

### T9.2 — Add Trivial Routing Tier (Small Fast Model)
**Status:** complete

Introduce a new routing classification `"trivial_ollama"` handled by the
small fast model identified in T9.1. Tier names use underscore suffixes
(`_ollama`, `_sonnet`, `_opus`) so the classifier cannot accidentally
return a plain English word that matches a valid tier.

Current routing:
```
simple         → sam860/deepseek-r1-0528-qwen3:8b
complex_sonnet → Claude Sonnet
complex_opus   → Claude Opus
```

New routing:
```
trivial_ollama → qwen3:1.7b
simple_ollama  → sam860/deepseek-r1-0528-qwen3:8b
complex_sonnet → Claude Sonnet
complex_opus   → Claude Opus
```

- Add `OLLAMA_FAST_MODEL = "qwen3:1.7b"` constant to `src/router.py`
- Rename `"simple"` → `"simple_ollama"` and add `"trivial_ollama"` to
  `_VALID`, `_FALLBACK`, type hints, and `_SYSTEM_PROMPT`
- Add `fast_model` constructor arg to `Orchestrator`; add `model` parameter
  to `_ollama_respond()`; dispatch `"trivial_ollama"` to fast model and
  `"simple_ollama"` to the deepseek model
- Updated all router and orchestrator unit tests

### T9.3 — Update Tests and README for New Routing Tiers
**Status:** complete

- Extend router unit tests to assert correct classification for trivially
  simple queries (e.g. "hi", "what is 2+2") — done as part of T9.2
- Extend orchestrator unit tests to confirm the fast model is called for
  `"trivial_ollama"` and the deepseek model for `"simple_ollama"` — done
  as part of T9.2
- Update README routing diagram and model reference table to reflect the
  four-tier routing system
- Add a project introduction section to the README explaining that this
  project is an experiment in using Claude Code as a development tool

### T9.4 — Use Fast Model for Routing/Classification
**Status:** complete

The router was using the 8B model for classification, making every query
incur a slow 8B inference call before the fast model even ran. Fixed by
switching the router to use `qwen3:1.7b` for classification too.

- Change `OllamaRouter` in `Orchestrator.__init__` to use `fast_model`
  instead of `ollama_model`
- Store `ollama_model` separately as `self._ollama_model` so `simple_ollama`
  responses still use the 8B model
- Update `_ollama_respond` call for `simple_ollama` to use
  `self._ollama_model` instead of `self._router._model`
- Update docstrings to accurately describe each model's role
- Add integration tests verifying both models are pulled and each tier
  routes to the correct model

---

## Phase 10 — Speech to Text Debugging

### T10.1 — Check STT via Whisper Works End-to-End
**Status:** not started

- Verify the browser can access the microphone via the `gr.Audio` component
- Verify audio is captured and passed correctly to `WhisperTranscriber.transcribe()`
- Verify Whisper converts speech to text without error
- Verify the transcribed text is displayed correctly as the user message in the chat
- Identify and fix any bugs found at each stage

---

## Implementation Order Summary

| Order | Phase | Tickets | Status |
|-------|-------|---------|--------|
| 0 | Bootstrap | T0.1 → T0.5 | complete |
| 1 | Dependencies & CI | T1.1 → T1.4 | complete |
| 2 | Tests | T2.1 → T2.5 | complete |
| 3 | Backend core | T3.1 → T3.3 | complete |
| 4 | Speech I/O | T4.1 → T4.2 | complete |
| 5 | Gradio UI | T5.1 → T5.6 | complete |
| 6 | Quality gate | T6.1 | complete |
| 7 | Refinements | T7.1 → T7.9 | complete |
| 8 | Text to Speech Debugging | T8.1 → T8.8 | complete |
| 9 | Routing Tiers | T9.1 → T9.4 | complete |
| 10 | Speech to Text Debugging | T10.1 | not started |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
