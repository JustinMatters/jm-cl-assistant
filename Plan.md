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
**Status:** complete

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
**Status:** in progress

- Verify the browser can access the microphone via the `gr.Audio` component
- Verify audio is captured and passed correctly to `WhisperTranscriber.transcribe()`
- Verify Whisper converts speech to text without error
- Verify the transcribed text is displayed correctly as the user message in the chat
- Identify and fix any bugs found at each stage

**Finding:** Gradio shows a "No microphone found" warning as soon as speech
input mode is selected — before the record button is pressed. This is
Gradio's placeholder state; the browser only requests microphone permission
when record is pressed. Confirmed on both Chrome and Firefox on Windows 11.
Documented in README under "Using Speech Input".

### T10.2 — Display Transcribed Text Before Response
**Status:** complete

- When speech mode is active, the user cannot see what Whisper thought they said
  before the query is sent to the orchestrator — there is no confirmation step
- Display the transcribed text in the chat history as the user message so the
  user can see exactly what was heard
- Consider adding a brief "You said: ..." indicator or showing the transcription
  in the text input box before clearing it

**Implementation:** Split `handle_audio` into two steps. Step 1: transcribe
and populate `text_input` (made visible) plus `submit_btn` so the user can
review and edit the transcription. Step 2: user presses Send — the existing
`handle_text` handler sends to the orchestrator as normal (handling TTS if
output mode is "text and speech"). After submit in speech mode, `text_input`
and `submit_btn` are hidden again so the UI returns to the audio recorder
ready for the next query. Re-recording replaces the text in the box.

### T10.3 — Handle Unused `sample_rate` Parameter
**Status:** complete

- `WhisperTranscriber.transcribe()` accepts `sample_rate` but never uses it;
  Whisper internally resamples all audio to 16 kHz
- Either remove the parameter and update all callers, or resample the input
  audio to 16 kHz explicitly before passing to Whisper (more robust if the
  browser provides audio at a non-standard sample rate)
- Decide which approach is correct and implement it; update tests accordingly

**Implementation:** Added `scipy.signal.resample` to `speech_input.py` to
explicitly resample audio to `_WHISPER_SR` (16 kHz) when the input sample
rate differs. This was the root cause of poor transcription quality — browser
microphones typically record at 44.1 kHz or 48 kHz, which Whisper was
interpreting as 16 kHz (3× too fast). `scipy` added as a project dependency.

### T10.4 — Audio Input Validation
**Status:** complete

- `handle_audio()` in `app.py` assumes `audio_data` is always a
  `(sample_rate, audio_array)` tuple with int16 dtype — no validation
- Add checks for: unexpected `None` values within the tuple, unexpected
  array dtypes (e.g. float32 from some browsers), zero-length audio,
  unreasonable sample rates
- Return a user-friendly chat message if audio is invalid rather than
  crashing the handler

**Implementation:** Added validation in `handle_audio()`: guards for `None`
components and zero-length arrays (silent return), invalid sample rate (error
message in chat display only — `history_state` unchanged to keep conversation
clean). Added dtype-aware normalisation: float32/float64 passed through as-is,
int32 scaled by 2^31, int16 and others scaled by 32768.

### T10.5 — Wrap STT in Error Handling
**Status:** complete

- If `whisper.load_model()` fails at startup (missing cache, OOM, network
  error during download), the app crashes with no user guidance
- If `transcribe()` fails at runtime (corrupted audio, internal Whisper
  error), the Gradio handler crashes
- Wrap model loading in try/except with a clear error message (e.g.
  "Whisper model failed to load — check your internet connection and
  available disk space")
- Wrap the `transcribe()` call in `handle_audio()` in try/except and
  return a chat error bubble rather than crashing
- Consider deferring Whisper model loading to first use (lazy loading)
  to match the KokoroSpeaker pattern and speed up app startup

**Implementation:** Converted `WhisperTranscriber` to lazy-load the model
on first `transcribe()` call (matching KokoroSpeaker's pattern), speeding
up app startup. Model load exceptions propagate naturally from `transcribe()`.
In `handle_audio()`, wrapped the `transcriber.transcribe()` call in
try/except — any failure appends an error bubble to the chat display without
crashing the handler or polluting `history_state`. Added two new tests:
`test_model_loaded_lazily_on_first_call` and
`test_model_not_reloaded_on_second_call`.

### T10.6 — STT Confidence and Empty Transcription Handling
**Status:** complete

- Whisper can return empty or near-empty strings for silent, noisy, or
  unintelligible audio — currently this is passed straight to the
  orchestrator as a query
- Detect empty or whitespace-only transcriptions and show a "Could not
  understand audio — please try again" message instead of routing an
  empty query
- Investigate whether Whisper's `no_speech_prob` or segment-level
  confidence scores can be used to warn the user about low-confidence
  transcriptions

**Implementation:** Added `_NO_SPEECH_THRESHOLD = 0.6` to `speech_input.py`.
After transcription, the average `no_speech_prob` across all segments is
checked; if it exceeds the threshold the transcription is discarded (returns
empty string). In `handle_audio()`, the silent return on empty transcription
was replaced with a user-facing message: "could not understand audio — please
try again". Three new tests cover high confidence, low confidence, and no
segments (result dict without a `"segments"` key).

### T10.7 — Add Unit Tests for Audio Handler Logic
**Status:** complete

- `handle_audio()` in `app.py` contains real logic: int16-to-float32
  conversion, transcription, orchestrator dispatch, optional TTS — none
  of this is unit-tested
- Extract the audio conversion and transcription logic into a testable
  helper (or test `handle_audio` directly with mocked dependencies)
- Add tests for: normal audio path, None audio input, empty
  transcription, TTS-enabled vs TTS-disabled output, error cases

---

## Phase 11 — Error Handling

The app currently has no protection around any external call site. If Ollama
is stopped, OpenRouter is unreachable, or a model file is missing, the user
sees a raw Python traceback instead of a helpful message. This phase adds
resilience across every boundary.

### T11.1 — Ollama Call Protection
**Status:** not started

- Wrap `ollama.chat()` calls in `orchestrator.py` (`_ollama_respond`) and
  `router.py` (`classify`) in try/except
- Catch `ollama.ResponseError`, `httpx.ConnectError`, and generic `Exception`
- In the orchestrator, return a user-friendly string
  (e.g. "Ollama is not responding — please check it is running")
- In the router, fall back to `trivial_ollama` on connection failure (already
  the fallback for unparseable output) and log a warning
- Add unit tests that mock `ollama.chat` raising each exception type

### T11.2 — OpenRouter Call Protection
**Status:** not started

- Wrap the `self._client.chat.completions.create()` call in
  `openrouter_client.py` in try/except
- Catch `openai.APIConnectionError`, `openai.RateLimitError` (429),
  `openai.APIStatusError` (5xx), and `openai.AuthenticationError`
- Return a descriptive error string for each case (e.g. "OpenRouter rate
  limit hit — please wait and try again")
- Add a `timeout` parameter to the `create()` call (e.g. 60 seconds)
- Add unit tests for each exception path

### T11.3 — Friendly Missing API Key Error
**Status:** not started

- `OpenRouterClient.__init__` raises a bare `KeyError` when
  `OPENROUTER_API_KEY` is not set
- Catch `KeyError` and raise `ValueError` with the message
  "Set the OPENROUTER_API_KEY environment variable before running the app"
- Update the existing test in `test_openrouter_client.py` to assert on the
  new `ValueError` and message text

### T11.4 — Kokoro Model File Check
**Status:** not started

- At startup in `build_app()`, check whether `kokoro-v1.0.onnx` and
  `voices-v1.0.bin` exist in the project root
- If missing, log a clear warning ("Kokoro model files not found — TTS will
  be unavailable") and allow the app to launch in text-only mode
- Wrap the `Kokoro()` constructor call in `speech_output.py` in try/except
  so a missing or corrupted model file produces a clear error rather than
  a crash on first TTS request

### T11.5 — Gradio Handler Crash Protection
**Status:** not started

- Wrap the bodies of `handle_text()` and `handle_audio()` in `app.py` in
  try/except blocks
- On exception, append an error message to the chat history as an assistant
  bubble (e.g. "Error: Ollama is not responding") instead of letting the
  handler crash
- Ensure the UI remains usable after an error — the user should be able to
  retry or switch modes without reloading the page
- Add unit tests (see also T10.7) that verify error bubbles appear when
  downstream components raise exceptions

### T11.6 — Startup Health Checks
**Status:** not started

- Add an optional startup check in `build_app()` that verifies:
  - Ollama is reachable (`ollama.list()` succeeds)
  - Required Ollama models are pulled (both `qwen3:1.7b` and the 8B model)
  - `OPENROUTER_API_KEY` is set (warn, don't block — local-only use is valid)
  - Kokoro model files are present (see T11.4)
- Log the result of each check at startup; do not block launch on failures
  but warn clearly which features will be unavailable

---

## Phase 12 — Unused `sample_rate` Parameter

### T12.1 — Resolve `sample_rate` in WhisperTranscriber
**Status:** not started

- `WhisperTranscriber.transcribe()` accepts `sample_rate` as a parameter
  but never passes it to Whisper — the model internally resamples to 16 kHz
- **Option A (remove):** Delete the parameter and update `handle_audio()` in
  `app.py` to stop passing it; simpler but less future-proof
- **Option B (resample):** Use `scipy.signal.resample` or `librosa.resample`
  to explicitly resample the input to 16 kHz before passing to Whisper;
  more robust if the browser provides audio at a non-standard rate
- Pick one approach, implement it, and update tests
- Cross-reference: overlaps with T10.3 — close whichever is addressed first
  and mark the other as superseded

---

## Phase 13 — Documentation Refresh

### T13.1 — Update CLAUDE.md Runtime Configuration Section
**Status:** not started

- Lines 32-36 say "currently hardcoded defaults pending argparse
  implementation" and reference T5.6 — argparse is already implemented in
  `app.py` with `--whisper-model` and `--ollama-model` flags
- Rewrite the section to reflect current reality; remove the "pending"
  language

### T13.2 — Update CLAUDE.md Architecture Description
**Status:** not started

- Line 8 describes the router as classifying "simple / complex_sonnet /
  complex_opus" — the router now has four tiers including `trivial_ollama`
- Update to list all four tiers

### T13.3 — Update README Model Reference Table
**Status:** not started

- Line 102 lists `trivial_ollama` as handling "greetings, arithmetic,
  one-word answers" — arithmetic was moved to `simple_ollama` and
  `trivial_ollama` now handles "facts a schoolchild would know"
- Update the table to match the current routing prompt

### T13.4 — Fix Historical Filenames in Plan.md
**Status:** not started

- T2.3 (line 121) references `tests/test_claude_client.py` and T3.2
  (line 155) references `src/claude_client.py` — both were renamed to
  `*openrouter_client*` during implementation
- Add a note to each completed ticket indicating the rename, or update
  the descriptions to use the current filenames

---

## Phase 14 — Testing Gaps

### T14.1 — Unit Tests for `app.py` Event Handlers
**Status:** not started

- `app.py` has zero unit tests — the event handlers contain real logic:
  int16-to-float32 conversion, history management, TTS gating, think-tag
  stripping
- Extract testable logic from `handle_text()` and `handle_audio()` into
  helper functions, or test the handlers directly with mocked dependencies
- Cross-reference: overlaps with T10.7 — coordinate to avoid duplication

### T14.2 — Error-Path Tests Across All Modules
**Status:** not started

- No test file exercises failure scenarios: Ollama down, OpenRouter 429,
  missing model files, corrupted audio input, empty API responses
- Add parametrised tests that mock exceptions from `ollama.chat()`,
  `openai.OpenAI.chat.completions.create()`, and `whisper.load_model()`
- Verify that the error handling added in Phase 11 returns user-friendly
  messages rather than raising unhandled exceptions

### T14.3 — Integration Test API Key Guard
**Status:** not started

- `TestIntegrationOrchestrator` and `TestIntegrationRouting` in
  `test_integration.py` don't verify `OPENROUTER_API_KEY` is set before
  running tests that exercise Claude paths
- Add a `pytest.mark.skipif` or `skipUnless` check for the API key at the
  class level so missing keys produce a clear skip rather than a confusing
  `KeyError`

---

## Phase 15 — Dependency Management

### T15.1 — Pin Major Version Bounds in `pyproject.toml`
**Status:** not started

- All dependencies use `>=` with no upper bounds — a breaking major version
  update (e.g. Gradio 7.0, OpenAI SDK 3.0) could silently break the app
- Switch to compatible-release constraints (`~=`) for key libraries:
  `gradio~=6.10`, `openai~=2.30`, `kokoro-onnx~=0.5`, `ollama~=0.6`,
  `openai-whisper~=20250625`
- Keep `numpy` and `sounddevice` on `>=` — these have stable APIs
- Run `uv sync` and `uv run pytest` after the change to verify nothing
  breaks

---

## Phase 16 — Portability

### T16.1 — Remove Absolute Path from `.claude/settings.json`
**Status:** not started

- The pre-commit hook hardcodes
  `cd C:/Users/justi/Documents/GitHub/jm-cl-assistant`
- If Claude Code hooks support `$PWD` or a relative path, use that instead
- If not, document in CLAUDE.md that the path must be updated per-machine,
  or remove the `cd` and rely on the hook running from the repo root
  (verify this is the case)

---

## Phase 17 — Minor Code Quality

### T17.1 — Initialise `last_backend` to a Sensible Default
**Status:** not started

- `orchestrator.py:44` sets `last_backend = ""` — if `_prefix_last_reply()`
  is ever called before the first response, the chat bubble shows `**: text`
- Initialise to `"(awaiting first query)"` or guard against empty string
  in `_prefix_last_reply()`

### T17.2 — Robust Backend Label Extraction
**Status:** not started

- `orchestrator.py:46-49` uses `.split('/')[-1]` to extract a display name
  from the model string — breaks for model names without a `/`
- Replace with: `name.split('/')[-1] if '/' in name else name`
- Add a test with a model name that contains no `/`

### T17.3 — Strip List Markers in `strip_markdown()`
**Status:** not started

- `helpers.py` `strip_markdown()` does not remove `- ` bullet prefixes
  or `1. ` numbered list prefixes — TTS reads "dash" and "one dot"
- Add regex passes for unordered markers (`^[-*+]\s+`, multiline) and
  ordered markers (`^\d+\.\s+`, multiline)
- Add tests for bullet and numbered list input in `test_helpers.py`

---

## Phase 18 — Tools

### Implementation Strategy

There are two approaches to giving the assistant access to tools:

**Approach A — Router-dispatched (current plan):**
The Ollama router classifies the query into a tool-specific tier (e.g. `maths`,
`weather`, `datetime`) and the orchestrator calls the tool directly without
involving an LLM. This is fast, cheap, and deterministic — but it requires the
small classification model to correctly identify every tool-worthy query, and
each new tool needs a new routing tier in the system prompt.

**Approach B — LLM tool use (function calling):**
The OpenAI-compatible API (and Claude natively) supports a `tools` parameter
where you define function schemas. The model decides when to call a tool,
generates structured arguments, and the client executes the function and feeds
the result back. This is more flexible — the model can chain tools, use tools
mid-conversation, and handle ambiguous queries — but it only works for the
Claude tiers (Sonnet/Opus via OpenRouter), not the local Ollama models which
have limited or no tool-use support.

**Recommended hybrid approach:**
- Use **Approach A** (router-dispatched) for tools that map to obvious,
  unambiguous queries: calculator, datetime, weather. These are fast and
  don't need LLM judgement.
- Use **Approach B** (LLM tool use) for tools that benefit from model
  judgement: web search (deciding what to search for), location-aware
  follow-ups, or chaining multiple tools. Register tool schemas with the
  OpenRouterClient and handle the tool-call response loop.
- Start with Approach A for all tools (simpler), then migrate selected tools
  to Approach B once the basic infrastructure works.

### Tool definitions vs Claude Code skills — keeping them separate

This project is built using Claude Code, which has its own skill/hook system
(defined in `.claude/` and invoked via slash commands during development).
The tools defined in this phase are **runtime tools for the assistant app** —
they live in `src/tools/` and are called by `Orchestrator.respond()` at
runtime. The two systems are completely separate:

| Concern | Claude Code skills | Assistant runtime tools |
|---------|-------------------|------------------------|
| Where defined | `.claude/`, `CLAUDE.md` | `src/tools/*.py` |
| When invoked | During development (by the dev) | At runtime (by the app) |
| Who calls them | Claude Code CLI | `Orchestrator.respond()` |
| Configuration | `settings.json`, slash commands | Router tiers or LLM `tools` param |

To keep the boundary clear:
- All runtime tool code lives under `src/tools/` (never in `.claude/`)
- Tool schemas for LLM function calling (Approach B) are defined in a
  `src/tools/registry.py` module, not in any Claude Code config file
- The word "skill" is reserved for Claude Code; the app calls its own
  capabilities "tools"
- Tests for runtime tools live in `tests/test_*.py` alongside existing tests

### Current tool inventory

The router currently routes arithmetic and maths calculations to `simple_ollama`
(the 8B model) because LLMs can produce incorrect results for numerical
computation. Phase 18 replaces that with dedicated tools so deterministic
tasks are solved reliably and cheaply without involving a large model.

### T18.1 — Calculator Tool
**Status:** not started

- Implement a `calculate(expression: str) -> str` tool in `src/tools/calculator.py`
  that evaluates arithmetic expressions safely (no `eval` on arbitrary code)
- Use the `simple_eval` or `asteval` library, or implement a safe AST-based
  evaluator, to support basic arithmetic: `+`, `-`, `*`, `/`, `**`, `%`,
  parentheses, and common maths functions (`sqrt`, `abs`, `round`, etc.)
- Return the result as a formatted string, or a clear error message if the
  expression is invalid
- Add unit tests in `tests/test_calculator.py`

### T18.2 — Integrate Calculator into Orchestrator
**Status:** not started

- Add a `maths` classification tier to the router system prompt so arithmetic
  and calculation queries are routed to `maths` instead of `simple_ollama`
- In `Orchestrator.respond()`, intercept the `maths` classification and call
  the calculator tool instead of an LLM
- Update `_backend_labels` to include a `"maths"` entry (e.g. `"Tool: calculator"`)
- Update tests in `test_orchestrator.py` and `test_router.py`

### T18.3 — Unit Conversion Tool (stretch)
**Status:** not started

- Implement a `convert(value, from_unit, to_unit) -> str` tool in
  `src/tools/converter.py` using the `pint` library
- Cover common categories: length, mass, temperature, volume, speed, time
- Integrate into orchestrator similarly to the calculator
- Add unit tests in `tests/test_converter.py`

### T18.4 — Web Search Tool
**Status:** not started

- Implement a `web_search(query: str) -> str` tool in `src/tools/web_search.py`
- Use the DuckDuckGo Instant Answer API (no API key required) or the
  `duckduckgo-search` library as the backend
- Return a concise summary of the top results (title + snippet + URL)
  formatted as plain text suitable for passing back to an LLM or reading aloud
- Add a `web_search` classification tier to the router system prompt for
  queries that require current information (news, recent events, live data)
- Integrate into `Orchestrator.respond()` with `_backend_label` `"Tool: web search"`
- Add unit tests in `tests/test_web_search.py` (mock HTTP calls)

### T18.5 — Location Tool (IP Lookup)
**Status:** not started

- Implement a `get_location() -> dict` tool in `src/tools/location.py`
  that resolves the user's approximate location from their public IP address
- Use a free IP geolocation API (e.g. `ip-api.com` — no key required) returning
  city, region, country, latitude, and longitude
- Cache the result for the session to avoid repeated lookups
- Expose a `get_location_str() -> str` helper that returns a human-readable
  location string (e.g. `"London, England, GB"`) for use by other tools
- Add unit tests in `tests/test_location.py` (mock HTTP calls)

### T18.6 — Date and Time Tool
**Status:** not started

- Implement a `get_datetime(timezone: str | None = None) -> str` tool in
  `src/tools/datetime_tool.py`
- Return the current date and time formatted as a readable string
  (e.g. `"Sunday 29 March 2026, 14:35 BST"`)
- If no timezone is supplied, attempt to infer it from the location tool
  (T18.5); fall back to UTC with a note
- Use the `zoneinfo` stdlib module (Python 3.9+) — no extra dependency needed
- Add a `datetime` classification tier to the router system prompt for
  queries about the current time or date
- Integrate into `Orchestrator.respond()` with `_backend_label` `"Tool: datetime"`
- Add unit tests in `tests/test_datetime_tool.py`

### T18.7 — Weather Forecast Tool
**Status:** not started

- Implement a `get_weather(location: str, days: int = 7) -> str` tool in
  `src/tools/weather.py`
- Use the Open-Meteo API (free, no API key required) with geocoding via the
  Open-Meteo geocoding endpoint to resolve location names to coordinates
- Return a day-by-day forecast summary for up to 7 days: date, condition,
  high/low temperature (°C), precipitation probability
- If `location` is `"auto"`, call the location tool (T18.5) to resolve the
  user's current location automatically
- Format output as plain text suitable for reading aloud via TTS
- Add a `weather` classification tier to the router system prompt
- Integrate into `Orchestrator.respond()` with `_backend_label` `"Tool: weather"`
- Add unit tests in `tests/test_weather.py` (mock HTTP calls)

### T18.8 — Tool Registry and LLM Function Calling Infrastructure
**Status:** not started

- Create `src/tools/registry.py` containing a `ToolRegistry` class that:
  - Stores tool definitions as OpenAI-compatible function schemas (name,
    description, parameters JSON schema)
  - Maps tool names to callable Python functions
  - Provides a `schemas()` method returning the list for the API `tools` param
  - Provides an `execute(name, arguments) -> str` method to dispatch a call
- Update `OpenRouterClient.ask()` to optionally accept a `tools` list and
  handle the tool-call response loop: send tools → receive tool_use stop
  reason → execute tool → send tool result → receive final response
- This is the foundation for Approach B tools (LLM-chosen tool use)
- Add unit tests in `tests/test_registry.py`

### T18.9 — Currency Conversion Tool
**Status:** not started

- Implement `convert_currency(amount, from_code, to_code) -> str` in
  `src/tools/currency.py`
- Use the free frankfurter.app API (no key required, ECB exchange rates,
  updated daily) or exchangerate.host as a fallback
- Return a formatted string (e.g. "100.00 USD = 91.47 EUR (rate: 0.9147)")
- Cache exchange rates for the session to avoid repeated lookups
- Good candidate for Approach A (router-dispatched) — queries like "convert
  50 euros to dollars" are unambiguous
- Add unit tests in `tests/test_currency.py` (mock HTTP calls)

### T18.10 — Dictionary / Definition Tool
**Status:** not started

- Implement `define(word: str) -> str` in `src/tools/dictionary.py`
- Use the Free Dictionary API (dictionaryapi.dev, no key required)
- Return: word, phonetic, part of speech, top 2-3 definitions, and an
  example sentence if available
- Format as plain text suitable for TTS
- Good candidate for Approach A — "define serendipity" or "what does
  ephemeral mean" are clear triggers
- Add unit tests in `tests/test_dictionary.py` (mock HTTP calls)

### T18.11 — Wikipedia Summary Tool
**Status:** not started

- Implement `wiki_summary(topic: str) -> str` in `src/tools/wikipedia.py`
- Use the Wikipedia REST API (`en.wikipedia.org/api/rest_v1/page/summary/`)
  — no key required, returns a plain-text extract
- Return the first 2-3 sentences of the article summary, plus the URL
- Good candidate for Approach B (LLM tool use) — the model can decide when
  a factual query would benefit from Wikipedia vs its own knowledge, and
  can rephrase the search term for better results
- Add unit tests in `tests/test_wikipedia.py` (mock HTTP calls)

### T18.12 — URL Content Summariser
**Status:** not started

- Implement `summarise_url(url: str) -> str` in `src/tools/url_reader.py`
- Fetch the page content, extract readable text (use `trafilatura` or
  `beautifulsoup4` + `requests`), and truncate to a reasonable length
- Pass the extracted text to the current Claude tier with a "summarise this
  page" system prompt, returning the summary
- Best suited for Approach B — the model detects a URL in the user's message
  and decides to fetch and summarise it
- Add unit tests in `tests/test_url_reader.py` (mock HTTP calls)

### T18.13 — Reminder / Timer Tool
**Status:** not started

- Implement a session-scoped reminder system in `src/tools/reminders.py`
- `set_reminder(message: str, minutes: int) -> str` — schedules a callback
  that pushes a notification into the Gradio chat after the delay
- `list_reminders() -> str` — shows active reminders
- Requires Gradio's `gr.Timer` or background thread to inject messages
  into the chat after a delay — investigate feasibility
- Good candidate for Approach B — the model parses natural language like
  "remind me in 10 minutes to check the oven"
- Add unit tests in `tests/test_reminders.py`

### T18.14 — System Info Tool
**Status:** not started

- Implement `system_info() -> str` in `src/tools/sysinfo.py`
- Return a summary of the host machine: OS, CPU, RAM total/available,
  GPU name and VRAM (via `torch.cuda` if available), Python version,
  loaded Ollama models
- Uses only stdlib (`platform`, `os`, `shutil`) plus optional `torch`
- Useful for debugging and for the assistant to understand its own
  environment (e.g. "how much VRAM do I have free?")
- Router-dispatched (Approach A) — queries like "system info" or "how
  much memory do I have" are unambiguous
- Add unit tests in `tests/test_sysinfo.py`

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
| 10 | Speech to Text Debugging | T10.1 → T10.7 | complete |
| 11 | Error Handling | T11.1 → T11.6 | not started |
| 12 | Unused `sample_rate` Parameter | T12.1 | not started |
| 13 | Documentation Refresh | T13.1 → T13.4 | not started |
| 14 | Testing Gaps | T14.1 → T14.3 | not started |
| 15 | Dependency Management | T15.1 | not started |
| 16 | Portability | T16.1 | not started |
| 17 | Minor Code Quality | T17.1 → T17.3 | not started |
| 18 | Tools | T18.1 → T18.14 | not started |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
