# Completed Work — jm-cl-assistant

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
**Status:** complete

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
**Status:** complete

- Wrap `ollama.chat()` calls in `orchestrator.py` (`_ollama_respond`) and
  `router.py` (`classify`) in try/except
- Catch `ollama.ResponseError`, `httpx.ConnectError`, and generic `Exception`
- In the orchestrator, return a user-friendly string
  (e.g. "Ollama is not responding — please check it is running")
- In the router, fall back to `trivial_ollama` on connection failure (already
  the fallback for unparseable output) and log a warning
- Add unit tests that mock `ollama.chat` raising each exception type

### T11.2 — OpenRouter Call Protection
**Status:** complete

- Wrap the `self._client.chat.completions.create()` call in
  `openrouter_client.py` in try/except
- Catch `openai.APIConnectionError`, `openai.RateLimitError` (429),
  `openai.APIStatusError` (5xx), and `openai.AuthenticationError`
- Return a descriptive error string for each case (e.g. "OpenRouter rate
  limit hit — please wait and try again")
- Add a `timeout` parameter to the `create()` call (e.g. 60 seconds)
- Add unit tests for each exception path

### T11.3 — Friendly Missing API Key Error
**Status:** complete

- `OpenRouterClient.__init__` raises a bare `KeyError` when
  `OPENROUTER_API_KEY` is not set
- Catch `KeyError` and raise `ValueError` with the message
  "Set the OPENROUTER_API_KEY environment variable before running the app"
- Update the existing test in `test_openrouter_client.py` to assert on the
  new `ValueError` and message text

### T11.4 — Kokoro Model File Check
**Status:** complete

- At startup in `build_app()`, check whether `kokoro-v1.0.onnx` and
  `voices-v1.0.bin` exist in the project root
- If missing, log a clear warning ("Kokoro model files not found — TTS will
  be unavailable") and allow the app to launch in text-only mode
- Wrap the `Kokoro()` constructor call in `speech_output.py` in try/except
  so a missing or corrupted model file produces a clear error rather than
  a crash on first TTS request

### T11.5 — Gradio Handler Crash Protection
**Status:** complete

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
**Status:** complete

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
**Status:** complete (superseded by T10.3)

- Option B (resample) was implemented in Phase 10 as part of T10.3.
  `speech_input.py` uses `scipy.signal.resample` to resample audio to
  16 kHz when the input sample rate differs from Whisper's expected rate.
  No further action required.

---

## Phase 13 — Documentation Refresh

### T13.1 — Update CLAUDE.md Runtime Configuration Section
**Status:** complete

- Rewrote section to reflect argparse implementation; removed "pending"
  language and T5.6 reference.

### T13.2 — Update CLAUDE.md Architecture Description
**Status:** complete

- Updated router description to list all four tiers: trivial_ollama /
  simple_ollama / complex_sonnet / complex_opus.

### T13.3 — Update README Model Reference Table
**Status:** complete

- Updated `trivial_ollama` description to "facts a schoolchild would know";
  arithmetic correctly attributed to `simple_ollama`.

### T13.4 — Fix Historical Filenames in Plan.md
**Status:** complete

- Updated T2.3 and T3.2 entries to reference the renamed
  `*openrouter_client*` files with a note about the rename.

---

## Phase 14 — Testing Gaps

Two of the three originally planned tickets were superseded before this phase
started: handler logic was extracted and tested in T10.7 (`process_audio`) and
T11.5 (`process_text`); error-path tests were added across all modules in
Phase 11.

### T14.1 — Integration Test API Key Guard
**Status:** complete

- `TestIntegrationOrchestrator` and `TestIntegrationRouting` in
  `test_integration.py` don't verify `OPENROUTER_API_KEY` is set before
  running; `Orchestrator.__init__` instantiates `OpenRouterClient`, which
  raises `ValueError` if the key is missing
- Add a `pytest.mark.skipif` check at the class level so a missing key
  produces a clean skip rather than a confusing `ValueError`

---

## Phase 15 — Dependency Management

Supply chain hardening strategy: `uv.lock` already contains SHA256 hashes for
every package (853 entries). The missing piece is enforcing those hashes in CI
via `--frozen`, and bounding versions in `pyproject.toml` to prevent unexpected
major-version upgrades silently entering the lockfile.

### T15.1 — Pin Major Version Bounds in `pyproject.toml`
**Status:** complete

- `~=` applied to `gradio`, `openai`, `ollama`, `kokoro-onnx`
- `openai-whisper` pinned with `==20250625` (date-based version, `~=` not valid)
- `numpy`, `scipy`, `sounddevice`, `torch` kept on `>=` (platform-sensitive)

### T15.2 — Enforce Lockfile Hash Verification in CI
**Status:** complete

- Both `uv sync` calls in `.github/workflows/ci.yml` updated to `--frozen`;
  CI now verifies committed lockfile SHA256 hashes on every build

### T15.3 — Verify `uv.lock` Is Committed and Not Gitignored
**Status:** complete

- Confirmed: `git ls-files uv.lock` returns the file; not in `.gitignore`

---

## Phase 16 — Portability

### T16.1 — Remove Absolute Path from `.claude/settings.json`
**Status:** complete

- Removed `cd C:/Users/justi/Documents/GitHub/jm-cl-assistant &&` from the
  pre-commit hook command; Claude Code hooks always run from the project root
  (the directory containing `.claude/`) so the `cd` was unnecessary.

---

## Phase 17 — Minor Code Quality

### T17.1 — Initialise `last_backend` to a Sensible Default
**Status:** complete

- `orchestrator.py:44` sets `last_backend = ""` — if `_prefix_last_reply()`
  is ever called before the first response, the chat bubble shows `**: text`
- Initialise to `"(awaiting first query)"` or guard against empty string
  in `_prefix_last_reply()`

### T17.2 — Strip List Markers in `strip_markdown()`
**Status:** complete

- `helpers.py` `strip_markdown()` does not remove `- ` bullet prefixes
  or `1. ` numbered list prefixes — TTS reads "dash" and "one dot"
- Add regex passes for unordered markers (`^[-*+]\s+`, multiline) and
  ordered markers (`^\d+\.\s+`, multiline)
- Add tests for bullet and numbered list input in `test_helpers.py`

---

## Phase 18 — RAG Memory

### Overview

This phase adds persistent, retrievable memory to the assistant using
Retrieval-Augmented Generation (RAG). Past conversation turns and externally
sourced content (web search results, Wikipedia summaries, URLs — added in
Phase 19) are embedded, stored in a local vector database, and retrieved at
query time. The top-k most semantically relevant past records are injected
into the system prompt so the assistant can reference prior context across
sessions.

### Architecture

```
src/memory/
├── __init__.py
└── store.py        ← MemoryStore: the single public interface
chroma_db/          ← ChromaDB persistence directory (gitignored)
```

**MemoryStore** wraps ChromaDB and exposes a small, stable API:
- `add(text, source, metadata)` — store any record with full metadata
- `search(query, k, filter)` → list of matching records
- `get_context_block(query)` → formatted string ready to inject into a prompt

This interface is intentionally source-agnostic. Conversation turns, tool
outputs (web search, Wikipedia, URL reader), and research documents all flow
through the same `add()` method with different `source` values. Phase 19
tools call `MemoryStore.add()` directly — no orchestrator involvement needed
for writes from tools.

**Metadata schema** (every record carries all fields; optional ones default
to empty string):

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | str | yes | `"conversation"`, `"web_search"`, `"wikipedia"`, `"url"`, `"research"` |
| `session_id` | str | yes | UUID generated at app startup |
| `timestamp` | str | yes | ISO 8601 datetime |
| `keywords` | str | no | Comma-separated keyword tags |
| `url` | str | no | Origin URL for web-sourced records |
| `title` | str | no | Document or page title |

ChromaDB metadata values must be scalar strings or numbers — lists are stored
as comma-separated strings and deserialized on read.

**Embedding**: `nomic-embed-text` via Ollama's `/api/embeddings` endpoint
(768 dimensions). Uses ChromaDB's built-in `OllamaEmbeddingFunction` — no
separate embedding step in application code. Prepend inputs with
`search_document:` on writes and `search_query:` on reads to activate
nomic-embed-text's instruction-aware retrieval improvement.

**Similarity threshold**: only inject retrieved records with cosine distance
< 0.7. When the store is sparse (new install, first few sessions), this
prevents irrelevant context from degrading responses.

**Context budget**: inject up to k=5 records by default, occupying ~20–30%
of the context window. Each record contributes roughly 512 tokens; the
majority of the context window is preserved for the current conversation.

### T18.1 — Dependencies and Embedding Model
**Status:** complete

- Add `chromadb` to project dependencies: `uv add chromadb`
- Run `uv sync` to install the new dependency and refreeze the lockfile
- Commit both `pyproject.toml` and `uv.lock` together in a single commit so
  the lockfile always reflects the declared dependencies
- Pull the embedding model: `ollama pull nomic-embed-text`
- Verify the model is available via `ollama list` and that
  `http://localhost:11434/api/embeddings` responds to a test embed call
- Add `chroma_db/` to `.gitignore` (the persistence directory must not be
  committed — it is local to each installation)
- No application code changes in this ticket; this is environment setup only

### T18.2 — MemoryStore Class
**Status:** complete

- Create `src/memory/__init__.py` (empty, makes `memory` a package)
- Create `src/memory/store.py` implementing a `MemoryStore` class with
  `add()`, `search()`, `get_context_block()`, and `count()` methods
- In `__init__`, verify that `nomic-embed-text` is available in Ollama and
  raise a clear `RuntimeError` with a pull command if it is missing
- Document IDs generated as `f"{source}_{timestamp}_{uuid4().hex[:8]}"`
- `get_context_block()` formats retrieved records as a
  `[PAST MEMORIES] … [END MEMORIES]` block with date, source, and optional
  title/url metadata
- Add unit tests in `tests/test_memory_store.py` using `tmp_path` fixture
  with mocked Ollama embedding calls

### T18.3 — Session ID Generation
**Status:** complete

- Generate a UUID once at app startup in `src/app.py` and pass it to
  `Orchestrator.__init__` as `session_id`
- Default to `uuid4().hex` when not provided so existing callers continue
  to work
- Update `tests/test_orchestrator.py` to pass an explicit `session_id`

### T18.4 — Conversation Recording
**Status:** complete

- Instantiate `MemoryStore` in `Orchestrator.__init__` with a
  `memory_enabled` constructor flag for test isolation
- After each exchange, call `memory.add()` with the combined turn text;
  failures are logged and swallowed so memory never blocks a response

### T18.5 — Context Injection
**Status:** complete

- Before each `Orchestrator.respond()` call, retrieve relevant memories via
  `get_context_block()` and prepend as a `{"role": "system"}` message
- Injected context is a local copy — never accumulated into returned history
- Failures are logged and swallowed; no response is ever blocked

### T18.6 — Memory Toggle and Status Indicator
**Status:** complete

- Add `gr.Checkbox("Memory", value=True)` and a `gr.Markdown` status label
  to the Gradio UI
- `memory_enabled` flag threaded through `process_text`, `process_audio`,
  and `Orchestrator.respond()` so the user can toggle mid-session
- Status label shows `"Memory: on · N records"` or `"Memory: off"`
- Tests verify that `memory_enabled=False` suppresses both reads and writes

---

---

## Phase 19 — Tools

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
mid-conversation, and handle ambiguous queries. Ollama also supports native
tool calling for Qwen3 variants (our current model is Qwen3-based), so Approach
B is technically available across all tiers — though the local model's
tool-calling reliability may be lower than Claude's.

**Security note for tool results:** Any tool that fetches external content
(web search, URL reader) must sanitise results before feeding them back to
the model. Indirect prompt injection — malicious instructions embedded in
web content that the model then acts on — is the most dangerous tool-use
attack vector. Validate and truncate all tool outputs before including them
in the context.

**Token cost note:** Tool definitions consume input tokens. A single
verbose MCP server can consume ~11,700 tokens of definitions. The tool
registry should support selective loading (only the tools needed for a given
query) and descriptions should be kept concise.

**Recommended hybrid approach:**
- Use **Approach A** (router-dispatched) for tools that map to obvious,
  unambiguous queries: calculator, datetime, weather. These are fast and
  don't need LLM judgement.
- Use **Approach B** (LLM tool use) for tools that benefit from model
  judgement: web search (deciding what to search for), location-aware
  follow-ups, or chaining multiple tools. Register tool schemas with the
  OpenRouterClient and handle the tool-call response loop. Qwen3 tool
  calling can be trialled for Ollama tiers once the Claude path is working.
- Start with Approach A for all tools (simpler), then migrate selected tools
  to Approach B once the basic infrastructure works.

**Registry construction — build fresh per turn:**
At the start of each `Orchestrator.respond()` call, construct the active tool
list by filtering the master registry against `(enabled_names_set,
current_route_tier)`. Never mutate a shared registry object mid-conversation.
This keeps the active catalogue immutable within a turn, avoids concurrency
bugs, and is the pattern used by production systems (e.g. Codex).

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
- Tool schemas and metadata are defined via `ToolDefinition` in
  `src/tools/registry.py`; the registry drives both the router prompt and
  LLM function calling (Approach B)
- The word "skill" is reserved for Claude Code; the app calls its own
  capabilities "tools"
- Tests for runtime tools live in `tests/test_*.py` alongside existing tests

### Current tool inventory

The router currently routes arithmetic and maths calculations to `simple_ollama`
(the 8B model) because LLMs can produce incorrect results for numerical
computation. Phase 19 replaces that with dedicated tools so deterministic
tasks are solved reliably and cheaply without involving a large model.

### T19.1 — Calculator Tool
**Status:** complete

- Implement a `calculate(expression: str) -> str` tool in `src/tools/calculator.py`
  that evaluates arithmetic expressions safely (no `eval` on arbitrary code)
- Use the `simple_eval` or `asteval` library, or implement a safe AST-based
  evaluator, to support basic arithmetic: `+`, `-`, `*`, `/`, `**`, `%`,
  parentheses, and common maths functions (`sqrt`, `abs`, `round`, etc.)
- Return the result as a formatted string, or a clear error message if the
  expression is invalid
- Add unit tests in `tests/test_calculator.py`

### T19.2 — Integrate Calculator into Orchestrator
**Status:** complete

- Add a `maths` classification tier to the router system prompt so arithmetic
  and calculation queries are routed to `maths` instead of `simple_ollama`
- In `Orchestrator.respond()`, intercept the `maths` classification and call
  the calculator tool instead of an LLM
- Update `_backend_labels` to include a `"maths"` entry (e.g. `"Tool: calculator"`)
- Update tests in `test_orchestrator.py` and `test_router.py`

### T19.3 — Unit Conversion Tool (stretch)
**Status:** complete (includes orchestrator integration with `convert` router tier)

- Implement a `convert(value, from_unit, to_unit) -> str` tool in
  `src/tools/converter.py` using the `pint` library
- Cover common categories: length, mass, temperature, volume, speed, time
- Integrate into orchestrator similarly to the calculator
- Add unit tests in `tests/test_converter.py`
- **Note:** T19.1–T19.3 use direct hardcoded integration; T19.5 migrates
  them to the registry so future tools self-register instead

---

### T19.4 — Tool Definition Protocol
**Status:** complete

Introduce the `ToolDefinition` dataclass in `src/tools/registry.py` that
carries all metadata needed for routing, UI display, and LLM function calling:

```python
@dataclass
class ToolDefinition:
    name: str           # machine identifier, e.g. "calculator"
    router_tier: str    # classification token, e.g. "maths"
    label: str          # display label, e.g. "Tool: calculator"
    description: str    # natural language description for router prompt
    examples: list[str] # example queries, used in router prompt
    default_enabled: bool
    min_tier: str       # minimum router tier allowed to invoke this tool
                        # one of: trivial_ollama / simple_ollama /
                        #         complex_sonnet / complex_opus
    approach: str       # "A" (router-dispatched) or "B" (LLM function call)
    callable: Callable  # the Python function to invoke
    category: str = "general"   # UI grouping label, e.g. "maths", "web",
                                 # "system" — used by T19.7 to group checkboxes
    is_async: bool = False       # True if callable is a coroutine — dispatch
                                 # must await it
    # Approach B only — OpenAI-compatible JSON schema for LLM function calling:
    parameters_schema: dict | None = None
```

- `min_tier` prevents small, unreliable models from being given access to
  tools with side-effects or that require careful argument construction
  (e.g. code execution should require at least `complex_sonnet`)
- `approach` determines dispatch path in the orchestrator
- `parameters_schema` is the JSON schema passed in the `tools` param for
  Approach B calls; `None` for Approach A tools. **Prefer auto-generation**
  via a Pydantic `BaseModel` subclass and `model.model_json_schema()` over
  hand-written JSON Schema — this avoids drift when signatures change
- `category` drives grouping in the tool accordion (T19.7); keep values
  short and consistent: `"maths"`, `"web"`, `"time"`, `"system"`, `"general"`
- Add unit tests in `tests/test_registry.py` verifying the dataclass fields
  and that missing required fields raise `TypeError`

### T19.5 — Tool Registry
**Status:** complete

Implement `ToolRegistry` in `src/tools/registry.py`:

- Stores `ToolDefinition` instances; tools register via `registry.register(defn)`
- `registry.enabled_tools(enabled_names: set[str]) -> list[ToolDefinition]`
  returns only definitions whose `name` is in the enabled set
- `registry.router_prompt_section(enabled_names) -> str` generates the tier
  block for the router system prompt dynamically from enabled tools only —
  each entry uses `description` and `examples` from the `ToolDefinition`
- `registry.dispatch(tier, query, enabled_names, current_route_tier) -> str | None`
  finds the matching enabled tool by `router_tier`, **enforces `min_tier` at
  execution time** (refuses to dispatch if `current_route_tier` ranks below
  `tool.min_tier` — not just at UI/schema level), and calls `callable`;
  returns `None` if no match or gated (orchestrator falls back to LLM)
- `registry.schemas(enabled_names) -> list[dict]` returns OpenAI-compatible
  tool schemas for all enabled Approach B tools (used in T19.8)
- **Migrate T19.1 (calculator) and T19.3 (converter)** to self-register
  `ToolDefinition` instances at module import time; remove hardcoded
  `if classification == "maths"` / `"convert"` branches from
  `Orchestrator.respond()` and replace with `registry.dispatch()`
- Include `strict: true` in all Approach B parameter schemas
- Add unit tests in `tests/test_registry.py`

### T19.6 — Dynamic Router
**Status:** complete

- `OllamaRouter.classify()` accepts an `enabled_tools` set and builds its
  `_VALID` set and system prompt dynamically from the registry:
  - Base tiers (`trivial_ollama`, `simple_ollama`, `complex_sonnet`,
    `complex_opus`) are always present
  - Tool tiers are appended only for enabled tools, in the order they are
    registered — disabling a tool removes its tier from the prompt entirely,
    saving tokens and preventing phantom classifications
- `Orchestrator` passes the current enabled set into `classify()` on every
  call
- Update `test_router.py` tests that previously hardcoded the tool tiers to
  use the registry fixture instead
- Add a test that disabling a tool removes its tier from the generated prompt

### T19.7 — Tool Toggle UI
**Status:** complete

- On startup, query the registry for all registered tools and build a
  per-tool `gr.Checkbox` in the Gradio UI, using `default_enabled` for the
  initial value and `label` for the display name
- Group tool checkboxes under a collapsible `gr.Accordion("Tools")`, grouped
  by `ToolDefinition.category` so related tools sit together
- Tools whose `min_tier` exceeds the current model's route tier should be
  rendered **greyed-out with an explanatory label** (e.g. "Requires Claude
  Sonnet or higher") rather than hidden — hiding confuses users who later
  upgrade the model; a visible-but-disabled state is the right UX
- Collect the enabled set as a `gr.State` and pass it into the orchestrator
  on every submit/audio event alongside the existing `memory_enabled` flag
- Add a `tools_status` `gr.Markdown` label (similar to the memory status
  indicator) showing how many tools are active: `"Tools: 3 / 5 enabled"`
- Update `handle_text()` and `handle_audio()` in `app.py` accordingly

### T19.8 — Agentic Tool Use Loop (Approach B)
**Status:** complete

Currently all tools are called *instead of* the LLM (Approach A: router
decides). Approach B lets the LLM itself decide to call a tool mid-response,
receive the result, and continue reasoning before returning to the user.

- Extend `OpenRouterClient.ask()` to accept an optional `tools` list
  (OpenAI-compatible schemas from `registry.schemas()`):
  1. Send query + tool schemas to Claude
  2. If `stop_reason == "tool_use"`, extract tool name + arguments
  3. Execute via `registry.dispatch()`, capture result
  4. Append `tool_result` message and resend to the model
  5. Repeat until `stop_reason != "tool_use"` (or a max-iteration guard)
  6. Return the final text response
- Extend the Ollama client path similarly — Qwen3 supports native tool
  calling; the Ollama `/v1` endpoint accepts the same `tools` parameter
- `Orchestrator.respond()` passes enabled Approach B tool schemas to
  whichever client is handling the request; Approach A tools are still
  router-dispatched as before
- Add a `max_tool_iterations` guard (default: 5) to prevent runaway loops
- Add unit tests covering: single tool call round-trip, multi-step chain,
  max-iterations guard, tool error propagation

---

### T19.9 — Memory Write Interface for Tools
**Status:** complete

- Extend the `ToolRegistry.dispatch()` mechanism (T19.5) with an optional
  `store: MemoryStore | None = None` parameter so tools can commit records
  without coupling to the Orchestrator directly
- Tool functions that want to write to memory declare the parameter and
  receive the live store; tools that do not need it simply omit it
- Document the expected call pattern for tools that write to memory:
  ```python
  # Example: web search tool writing its result to memory
  if store:
      store.add(
          text=result_text,
          source="web_search",
          session_id=session_id,
          keywords=", ".join(top_keywords),
          url=result_url,
          title=result_title,
      )
  ```
- Update `Orchestrator.respond()` to pass `orchestrator._memory` (or `None`
  when memory is disabled) into the registry dispatch call
- Add a unit test verifying that a mock tool receives the `store` argument
  and can call `add()` on it

### T19.10 — Web Search Tool
**Status:** complete

- Implement a `web_search(query: str) -> str` tool in `src/tools/web_search.py`
- Use the DuckDuckGo Instant Answer API (no API key required) or the
  `duckduckgo-search` library as the backend
- Return a concise summary of the top results (title + snippet + URL)
  formatted as plain text suitable for passing back to an LLM or reading aloud
- **Security:** Sanitise all result text (titles, snippets, URLs) before
  injecting into the LLM context — indirect prompt injection via search
  results is a known attack vector; truncate to a safe character limit
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_web_search.py` (mock HTTP calls)

### T19.11 — Location Tool (IP Lookup)
**Status:** complete

- Implement a `get_location() -> dict` tool in `src/tools/location.py`
  that resolves the user's approximate location from their public IP address
- Use a free IP geolocation API (e.g. `ip-api.com` — no key required) returning
  city, region, country, latitude, and longitude
- Cache the result for the session to avoid repeated lookups
- Expose a `get_location_str() -> str` helper that returns a human-readable
  location string (e.g. `"London, England, GB"`) for use by other tools
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_location.py` (mock HTTP calls)

### T19.12 — Date and Time Tool
**Status:** complete

- Implement a `get_datetime(timezone: str | None = None) -> str` tool in
  `src/tools/datetime_tool.py`
- Return the current date and time formatted as a readable string
  (e.g. `"Sunday 29 March 2026, 14:35 BST"`)
- If no timezone is supplied, attempt to infer it from the location tool
  (T19.11); fall back to UTC with a note
- Use the `zoneinfo` stdlib module (Python 3.9+) — no extra dependency needed
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_datetime_tool.py`

### T19.13 — Weather Forecast Tool
**Status:** complete

- Implement a `get_weather(location: str, days: int = 7) -> str` tool in
  `src/tools/weather.py`
- Use the Open-Meteo API (free, no API key required) with geocoding via the
  Open-Meteo geocoding endpoint to resolve location names to coordinates
- Return a day-by-day forecast summary for up to 7 days: date, condition,
  high/low temperature (°C), precipitation probability
- If `location` is `"auto"`, call the location tool (T19.11) to resolve the
  user's current location automatically
- Format output as plain text suitable for reading aloud via TTS
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_weather.py` (mock HTTP calls)

### T19.14 — Currency Conversion Tool
**Status:** complete

- Implement `convert_currency(amount, from_code, to_code) -> str` in
  `src/tools/currency.py`
- Use the free frankfurter.app API (no key required, ECB exchange rates,
  updated daily) or exchangerate.host as a fallback
- Return a formatted string (e.g. `"100.00 USD = 91.47 EUR (rate: 0.9147)"`)
- Cache exchange rates for the session to avoid repeated lookups
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_currency.py` (mock HTTP calls)

### T19.15 — Dictionary / Definition Tool
**Status:** complete

- Implement `define(word: str) -> str` in `src/tools/dictionary.py`
- Use the Free Dictionary API (dictionaryapi.dev, no key required)
- Return: word, phonetic, part of speech, top 2-3 definitions, and an
  example sentence if available
- Format as plain text suitable for TTS
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_dictionary.py` (mock HTTP calls)

### T19.16 — Wikipedia Summary Tool
**Status:** complete

- Implement `wiki_summary(topic: str) -> str` in `src/tools/wikipedia.py`
- Use the Wikipedia REST API (`en.wikipedia.org/api/rest_v1/page/summary/`)
  — no key required, returns a plain-text extract
- Return the first 2-3 sentences of the article summary, plus the URL
- Register a `ToolDefinition` (Approach B, `default_enabled=True`,
  `min_tier="simple_ollama"`) — the model decides when a factual query
  benefits from Wikipedia vs its own knowledge, and can rephrase the search
  term for better results
- Add unit tests in `tests/test_wikipedia.py` (mock HTTP calls)

### T19.17 — URL Content Summariser
**Status:** complete

- Implement `summarise_url(url: str) -> str` in `src/tools/url_reader.py`
- Fetch the page content, extract readable text (use `trafilatura` or
  `beautifulsoup4` + `requests`), and truncate to a reasonable length
- **Security:** Page content from untrusted URLs is a high-risk indirect
  injection surface — strip HTML, limit extracted length, and pass through
  a summarisation prompt that explicitly scopes the model's task before
  including in context
- Pass the extracted text to the current Claude tier with a "summarise this
  page" system prompt, returning the summary
- Register a `ToolDefinition` (Approach B, `default_enabled=True`,
  `min_tier="complex_sonnet"`) — requires a capable model to safely
  summarise and not be misled by injected content
- Add unit tests in `tests/test_url_reader.py` (mock HTTP calls)

### T19.18 — Reminder / Timer Tool
**Status:** complete

- Implement a session-scoped reminder system in `src/tools/reminders.py`
- `set_reminder(message: str, minutes: int) -> str` — schedules a callback
  that pushes a notification into the Gradio chat after the delay
- `list_reminders() -> str` — shows active reminders
- Requires Gradio's `gr.Timer` or background thread to inject messages
  into the chat after a delay — investigate feasibility
- Register a `ToolDefinition` (Approach B, `default_enabled=True`,
  `min_tier="simple_ollama"`) — the model parses natural language like
  "remind me in 10 minutes to check the oven"
- Add unit tests in `tests/test_reminders.py`

### T19.19 — System Info Tool
**Status:** complete

- Implement `system_info() -> str` in `src/tools/sysinfo.py`
- Return a summary of the host machine: OS, CPU, RAM total/available,
  GPU name and VRAM (via `torch.cuda` if available), Python version,
  loaded Ollama models
- Uses only stdlib (`platform`, `os`, `shutil`) plus optional `torch`
- Useful for debugging and for the assistant to understand its own
  environment (e.g. "how much VRAM do I have free?")
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_sysinfo.py`

### T19.20 — Code Execution Sandbox
**Status:** complete

- Implement a `run_code(code: str, language: str = "python") -> str` tool
  in `src/tools/code_exec.py` that safely executes user-supplied code and
  returns the output
- **Two implementation options to evaluate:**
  - **`asteval`** (simpler): AST-based evaluator for arithmetic and simple
    Python expressions. Safe by default — no file I/O, no imports, no
    network. Good for data manipulation, sorting, string formatting, and
    computations beyond the calculator's scope.
  - **`restrictedpython`** (more powerful): Compiles and runs arbitrary
    Python in a restricted namespace with configurable builtins and guards.
    Supports loops, comprehensions, user-defined functions, and controlled
    imports — useful if the assistant needs to run non-trivial user-provided
    scripts. Requires careful configuration of the allowed namespace and
    guard functions to prevent sandbox escapes.
- Start with `asteval` for initial implementation; leave `restrictedpython`
  as a documented upgrade path for when broader execution power is needed
- Capture stdout/stderr and return as a formatted string; enforce a
  configurable timeout to prevent runaway code
- Register a `ToolDefinition` (Approach B, `default_enabled=False`,
  `min_tier="complex_sonnet"`) — off by default given execution risk;
  requires a capable model to construct safe arguments
- Add unit tests in `tests/test_code_exec.py`

---
