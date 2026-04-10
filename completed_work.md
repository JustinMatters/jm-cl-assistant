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


---

## Phase 20 -- Extended Tools

### Overview

Seven new capabilities.  **T20.1 should be done first** -- it replaces the
default local model and may simplify the vision routing in later tickets.
T20.2 and T20.3 are enabling tickets that later tools depend on; the
remaining four (T20.4-T20.7) can be built in any order once those two are
in place.

**Shared image output mechanism (T20.3):** Tools that produce images
(flowcharts, data plots, generated images) return their output as a
`bytes` object tagged with the prefix `__IMAGE__:` followed by a
base64-encoded PNG.  The orchestrator detects this sentinel and routes the
payload to a `gr.Image` output component added to the Gradio UI, leaving
the normal text path unchanged for tools that return strings.

**New dependencies required:**

| Package | Purpose | Ticket |
|---------|---------|--------|
| `pypdf` | PDF text extraction | T20.2 |
| `python-docx` | DOCX text extraction | T20.2 |
| `graphviz` (Python + system binary) | DOT to PNG rendering | T20.4 |
| `polars` | DataFrame reads / summary stats | T20.6 |
| `matplotlib` | Plot generation | T20.6 |
| `openpyxl` | Excel file support for polars | T20.6 |
| `diffusers` | Local diffusion image generation | T20.7 |
| `transformers` | Model loading for diffusers | T20.7 |
| `accelerate` | Diffusers performance layer | T20.7 |

`torch` is already declared; `trafilatura` (HTML extraction) is already present.

---

### T20.1 -- Gemma 4 Model Evaluation and Migration
**Status:** complete

Adopted model: `gemma4:e4b` replaces `sam860/deepseek-r1-0528-qwen3:8b` as the
`simple_ollama` model. Natively multimodal (text + vision). Changes: `src/app.py`
`OLLAMA_MODEL_DEFAULT`, `src/router.py` `OLLAMA_MODEL`, README.md, CLAUDE.md updated.

---

### T20.2 -- File Reader Tool (local path + URL)
**Status:** complete

`src/tools/file_reader.py` -- Approach B tool. Reads PDF (pypdf), DOCX (python-docx),
TXT (stdlib), HTML (trafilatura) from local path or URL. Truncates at 4000 chars.
Reuses `_validate_url()` from url_reader. Tests in `tests/test_file_reader.py`.
Dependencies: `pypdf`, `python-docx`.

---

### T20.3 -- Image Output Infrastructure
**Status:** complete

`src/tools/image_utils.py` -- `encode_image()`, `decode_image()`, `is_image_sentinel()`.
Sentinel format: `b"__IMAGE__:" + base64(png)`. Orchestrator stores decoded PIL Image in
`_pending_image`; Gradio `gr.Image` output component shows it. Tests in `tests/test_image_utils.py`.

---

### T20.4 -- Flowchart Generation Tool
**Status:** complete

`src/tools/flowchart.py` -- Approach B. LLM emits Graphviz DOT; `graphviz.Source.pipe(format="png")`
renders to PNG returned via sentinel. Handles `ExecutableNotFound` with install instructions.
Tests in `tests/test_flowchart.py`. Dependency: `graphviz` (Python + system binary).

---

### T20.5 -- Vision API Support
**Status:** complete

Image attachment via `gr.Image(type="pil")` input. Threaded through `handle_text` /
`handle_audio` -> `process_text` / `process_audio` -> `orchestrator.respond(image=)`.
Non-vision Ollama tiers escalate to `complex_sonnet`. `_OLLAMA_VISION_MODELS` frozenset.
Ollama: `images` key in message dict. OpenRouter: `image_url` content block.
Tests in `tests/test_vision.py`.

---

### T20.6 -- Data Analysis Tool (Polars + Matplotlib)
**Status:** complete

`src/tools/data_analysis.py` -- Approach B. Actions: `summarise` (shape, dtypes, describe,
head 5) and `plot` (bar/line/scatter/histogram via Matplotlib Agg backend, returned as sentinel).
Loads CSV (`polars.read_csv`) and Excel (`polars.read_excel`/fastexcel). Tests in
`tests/test_data_analysis.py`. Dependencies: `polars`, `matplotlib`, `fastexcel`.

---

### T20.7 -- Image Generation Tool
**Status:** complete

`src/tools/image_gen.py` -- Approach B, `default_enabled=False`. Three modes: `local`
(SDXL-Turbo, CUDA required, ~6.7 GB first-use download), `search` (Openverse CC0 API,
no key), `auto` (local first, search fallback). Pipeline cached at module level.
gr.Markdown VRAM warning in Tools accordion. Tests in `tests/test_image_gen.py`.
Dependencies: `diffusers`, `transformers`, `accelerate`.


---

## Phase 21 — Runtime Feature Switches

### Overview

Add CLI flags and matching UI toggles to disable TTS, STT, and tool use at
startup.  The goal is to allow the assistant to run on minimal hardware where
loading Whisper, Kokoro, or the full tool registry is undesirable (e.g. a
low-RAM machine, a headless server, or a quick demo environment).

Each switch is independent — any combination of the three can be disabled.
When a component is disabled it must be gracefully absent from the UI and
must not be imported or initialised, saving the associated memory and startup
time.

### T21.1 — Disable TTS (`--no-tts`)
**Status:** complete

Add a `--no-tts` CLI flag to `src/app.py`.  When set:

- Skip instantiation of `KokoroSpeaker` and `check_kokoro_files()`.
- Hide the audio output component (`gr.Audio`) and the voice selector
  (`gr.Dropdown`) from the UI — they should not be rendered at all, not
  just disabled.
- Remove the "text and speech" option from the output mode selector; default
  to "text" only.
- `process_text` and `process_audio` already accept a `speaker` argument;
  pass `None` and guard the TTS call path with `if speaker is not None`.
- Add unit tests in `tests/test_app_startup.py` (or a new
  `tests/test_feature_switches.py`) confirming that with `--no-tts` the
  speaker is `None` and the voice selector is hidden.

### T21.2 — Disable STT (`--no-stt`)
**Status:** complete

Add a `--no-stt` CLI flag to `src/app.py`.  When set:

- Skip instantiation of `WhisperTranscriber`.
- Hide the microphone / audio input row and the speech mode radio button
  entirely — the UI renders in text-only mode with no way to switch to
  speech input.
- `process_audio` becomes unreachable; no need to guard it separately.
- Add unit tests confirming that with `--no-stt` the transcriber is `None`
  and the audio input is absent from the component tree.

Note: the `--whisper-model` flag is **not** replaced here — it is removed
entirely in T22.2, where Whisper model size moves to `models.json`.

### T21.3 — Disable Tool Use (`--no-tools`)
**Status:** complete

Add a `--no-tools` CLI flag to `src/app.py`.  When set:

- Do not import `src.tools` (prevents all tool modules from registering).
- Pass an empty enabled-tools set to the orchestrator so no Approach A or
  Approach B tools are dispatched.
- Hide the Tools accordion from the UI entirely.
- The orchestrator's `_make_b_executor` still exists but receives an empty
  tool list, so the LLM never issues a tool call.
- Add unit tests confirming that with `--no-tools` the registry contributes
  no tools to the orchestrator and the accordion is absent.

---

## Phase 22 — Model Configuration File

### Overview

Model identities and several user-facing settings are currently hardcoded
across multiple source files: `src/router.py` (`OLLAMA_MODEL`,
`OLLAMA_FAST_MODEL`), `src/openrouter_client.py` (`SONNET_MODEL_ID`,
`OPUS_MODEL_ID`), `src/app.py` (`OLLAMA_MODEL_DEFAULT`,
`WHISPER_MODEL_DEFAULT`), `src/memory/store.py` (`_EMBED_MODEL`), and
`src/tools/image_gen.py` (`_SDXL_MODEL`, `_MAX_IMG_DIM`).  Changing any of
these requires editing source code.

This phase moves all of them into a single JSON file (`models.json`) at the
project root so users can swap models and tune key parameters without
touching Python.  The file is read at startup; the application falls back to
safe built-in defaults if the file is absent or malformed.

As part of this phase the `--whisper-model` CLI flag is removed — the
Whisper model size is now set in `models.json` instead.  The only
STT-related CLI flag that remains is `--no-stt` (Phase 21).

The internal router tier names (`trivial_ollama`, `simple_ollama`,
`complex_sonnet`, `complex_opus`) are also renamed to provider-neutral names
(`trivial_llm`, `simple_llm`, `advanced_llm`, `complex_llm`) throughout the
codebase, including all tool `min_tier` fields, `registry.py` rank table,
`orchestrator.py`, and `app.py`.

**JSON schema (one entry per logical role):**
```json
{
  "models": [
    {
      "role": "trivial_llm",
      "provider": "ollama",
      "model_id": "qwen3:1.7b",
      "display_name": "Qwen3 1.7B",
      "vision": false
    },
    {
      "role": "simple_llm",
      "provider": "ollama",
      "model_id": "gemma4:e4b",
      "display_name": "Gemma 4 (4B)",
      "vision": true
    },
    {
      "role": "advanced_llm",
      "provider": "openrouter",
      "model_id": "anthropic/claude-sonnet-4-6",
      "display_name": "Claude Sonnet 4.6",
      "vision": true
    },
    {
      "role": "complex_llm",
      "provider": "openrouter",
      "model_id": "anthropic/claude-opus-4-6",
      "display_name": "Claude Opus 4.6",
      "vision": true
    },
    {
      "role": "vector_db_embedding",
      "provider": "ollama",
      "model_id": "nomic-embed-text",
      "display_name": "Nomic Embed Text",
      "vision": false
    },
    {
      "role": "whisper_stt_model",
      "provider": "local",
      "model_id": "medium",
      "display_name": "Whisper medium",
      "vision": false
    },
    {
      "role": "diffusers_image_gen_model",
      "provider": "local",
      "model_id": "stabilityai/sdxl-turbo",
      "display_name": "SDXL-Turbo",
      "vision": false,
      "diffusers_max_image_dimension": 512
    }
  ]
}
```

**Fields (all roles):**
- `role` — one of `trivial_llm`, `simple_llm`, `advanced_llm`,
  `complex_llm`, `vector_db_embedding`, `whisper_stt_model`,
  `diffusers_image_gen_model`
- `provider` — `"ollama"`, `"openrouter"`, or `"local"` (local Python
  library, not an API)
- `model_id` — the identifier passed to the provider (Ollama model name,
  OpenRouter model string, Whisper size, or HuggingFace repo ID)
- `display_name` — human-readable label shown in the UI
- `vision` — whether this model accepts image inputs (replaces the hardcoded
  `_OLLAMA_VISION_MODELS` frozenset in `orchestrator.py`)

**Fields (diffusers_image_gen_model only):**
- `diffusers_max_image_dimension` — maximum pixel size of generated images
  (replaces `_MAX_IMG_DIM`); images are thumbnailed to this size after
  generation or download

### T22.1 — `models.json` and loader module
**Status:** complete

- Create `models.json` at the project root with the seven default entries
  above.
- Create `src/model_config.py` with a `ModelConfig` dataclass and a
  `load_models(path: str = "models.json") -> dict[str, ModelConfig]`
  function that:
  - Reads and validates the JSON (all required fields present, role is one
    of the seven known values, provider is `"ollama"`, `"openrouter"`, or
    `"local"`).
  - Returns a dict keyed by role.
  - Falls back to hardcoded defaults and logs a warning if the file is
    missing or invalid — the app must still start cleanly.
- Add `models.json` to `.gitignore` so user customisations are not
  committed; ship a tracked `models.json.example` with the same content.
- Add unit tests in `tests/test_model_config.py` covering: valid file loads
  correctly, missing file uses defaults, invalid JSON uses defaults, missing
  required field uses defaults, unknown role is ignored,
  `diffusers_max_image_dimension` defaults to 512 when absent.

### T22.2 — Wire loader into application code
**Status:** complete

Replace all hardcoded model constants with values read from `load_models()`
and rename internal tier names throughout the codebase:

**Tier rename** (touches `router.py`, `registry.py`, `orchestrator.py`,
`app.py`, and all tool files with a `min_tier` field):

| Old name | New name |
|---|---|
| `trivial_ollama` | `trivial_llm` |
| `simple_ollama` | `simple_llm` |
| `complex_sonnet` | `advanced_llm` |
| `complex_opus` | `complex_llm` |

**Constants replaced:**
- `src/router.py` — `OLLAMA_MODEL` and `OLLAMA_FAST_MODEL` sourced from
  `simple_llm` and `trivial_llm` roles respectively.
- `src/openrouter_client.py` — `SONNET_MODEL_ID` and `OPUS_MODEL_ID`
  sourced from `advanced_llm` and `complex_llm` roles.
- `src/orchestrator.py` — `_OLLAMA_VISION_MODELS` frozenset replaced by
  checking `ModelConfig.vision` on the loaded configs; display name strings
  sourced from `display_name` field.
- `src/app.py` — `OLLAMA_MODEL_DEFAULT` sourced from `simple_llm` role;
  `WHISPER_MODEL_DEFAULT` sourced from `whisper_stt_model` role;
  `--whisper-model` CLI flag removed entirely (Whisper size is now
  config-only).
- `src/memory/store.py` — `_EMBED_MODEL` sourced from `vector_db_embedding`
  role.
- `src/tools/image_gen.py` — `_SDXL_MODEL` sourced from
  `diffusers_image_gen_model` role; `_MAX_IMG_DIM` sourced from
  `diffusers_max_image_dimension` field.
- All existing constants become module-level variables initialised from the
  loader so the rest of each module's code is unchanged.

### T22.3 — UI model status display
**Status:** complete

- Show the active model for each role in the UI — inside a collapsible
  "Models" accordion listing each role's `display_name` and `provider`.
- This gives users immediate visual confirmation that their `models.json`
  changes have taken effect without inspecting logs.
- Update `tests/test_app_startup.py` to confirm the Models accordion is
  rendered when the app is built.


---

## Phase 23 — Streaming Responses

### Overview

Currently the orchestrator waits for the full LLM response before returning
it to Gradio, which creates a noticeable lag for longer Claude replies.
Gradio supports `yield`-based streaming — the generator produces response
chunks as they arrive and Gradio updates the chat panel incrementally.

### T23.1 — Stream Ollama responses
**Status:** complete

Modify `_ollama_respond` in `src/orchestrator.py` to accept a `stream=True`
parameter and yield content chunks from the `ollama.chat` streaming API.
Non-streaming callers (tests, tool loop) must continue to work unchanged.

### T23.2 — Stream OpenRouter responses
**Status:** complete

Modify `OpenRouterClient.ask` in `src/openrouter_client.py` to accept a
`stream=True` parameter and yield content chunks from the OpenAI-compatible
streaming API (`stream=True` on the completions call).  Ensure the tool-use
agentic loop (which needs the full response to detect tool calls) still
operates in non-streaming mode.

### T23.3 — Wire streaming into the Gradio UI
**Status:** complete

Update `process_text` and `process_audio` in `src/process_text.py` and
`src/process_audio.py` to accept a `stream` flag and `yield` intermediate
history states when streaming is active.  Update the Gradio event wiring in
`src/app.py` to use streaming outputs (`submit_btn.click(..., streaming=True)`
or equivalent).  TTS synthesis must only be triggered on the final complete
response, not on partial chunks.

### T23.4 — Unit tests for streaming
**Status:** complete

Add tests covering: streamed chunks are concatenated correctly, TTS is called
only once with the full response, tool-use path bypasses streaming, and
non-streaming callers are unaffected.

---

## Phase 24 — Context Window Trimming

### Overview

Conversation history is passed to the LLM on every turn and grows
unboundedly.  Long sessions will eventually exceed the model's context window,
causing silent truncation or API errors.  This phase adds a trimming strategy
that keeps the history within a per-model token budget by summarising or
dropping the oldest turns.

### T24.1 — Per-model context window in `models.json`
**Status:** complete

Add an optional `context_tokens` integer field to `ModelConfig` in
`src/model_config.py` (and the `models.json.example` schema).  This
represents the usable history budget for that model in tokens — distinct from
the model's advertised context window, which is typically much larger but
includes the system prompt, tools schema, and current query.  Sensible
defaults: `trivial_llm` 4000, `simple_llm` 6000, `advanced_llm` 16000,
`complex_llm` 32000.  Update `_DEFAULTS` and the loader; add tests in
`tests/test_model_config.py`.

### T24.2 — Token counting utility
**Status:** complete

Add a `count_tokens(messages: list[dict]) -> int` helper to `src/helpers.py`
that estimates token count from message content length (a simple
characters-divided-by-four heuristic is sufficient; no tiktoken dependency).
The orchestrator reads the active model's `context_tokens` from `_MODEL_CONFIG`
to determine the budget for the current turn.

### T24.3 — Trim history when budget is exceeded
**Status:** complete

In `Orchestrator.respond`, after building `augmented`, determine the budget
from the active model's `ModelConfig.context_tokens`.  If
`count_tokens(augmented)` exceeds the budget, drop the oldest non-system
turns (pairs of user+assistant messages) until the budget is met.  As a last
resort, summarise the dropped turns into a brief system note prepended to
the remaining history.

### T24.4 — UI indicator and unit tests for context trimming
**Status:** complete

When trimming occurs, append a small italic note to the assistant reply
(e.g. `*(older context was trimmed to fit the model's window)*`) so the user
is aware.  Add unit tests covering: history within budget is unchanged,
oversized history is trimmed to fit, system messages are preserved, the note
appears only when trimming occurs, and the budget is read from model config.

---

## Phase 25 — Conversation Export

### Overview

Users may want to save a chat session as a readable file.  This phase adds a
download button that serialises the current Gradio history state to a
Markdown file and offers it for download.

### T25.1 — Export formatter
**Status:** complete

Add `format_history_as_markdown(history: list[dict]) -> str` to
`src/helpers.py`.  Each turn becomes a `**User:**` / `**Assistant:**` block
separated by horizontal rules.  Include a timestamp header at the top.

### T25.2 — Download button in the Gradio UI
**Status:** complete

Add a `gr.DownloadButton` (or `gr.File`) to `src/app.py` that, when clicked,
calls the formatter and serves the result as `conversation.md`.  Wire it to
the `history_state` so it always reflects the current session.

### T25.3 — Unit tests for export
**Status:** complete

Tests covering: empty history produces a valid header-only file, user and
assistant turns are formatted correctly, special Markdown characters in
content are preserved (not double-escaped).

---

## Phase 26 — Token and Cost Display

### Overview

OpenRouter returns token usage metadata on every response.  Surfacing per-call
token counts and an approximate cost in the UI helps users understand spend,
especially for Opus which is significantly more expensive than Sonnet.

### T26.1 — Capture usage metadata from OpenRouter
**Status:** complete

Update `OpenRouterClient.ask` in `src/openrouter_client.py` to extract
`usage.prompt_tokens`, `usage.completion_tokens`, and `usage.total_tokens`
from the API response and return them alongside the text response (e.g. as
a `(text, usage_dict)` tuple or by storing on the client instance).

### T26.2 — Cost calculation
**Status:** complete

Add a `PRICING` dict to `src/openrouter_client.py` keyed by model ID with
per-million-token input and output costs (sourced from the OpenRouter pricing
page).  Add `calculate_cost(model_id, prompt_tokens, completion_tokens) -> float`.

### T26.3 — Per-response cost in the UI
**Status:** complete

After each Claude response, display token counts and estimated cost as a small
grey annotation below the assistant message (e.g. `*(523 tokens · ~$0.002)*`).
Ollama responses show token counts only (no cost).  Implement via a separate
`gr.Markdown` component updated after each turn.

### T26.4 — Session total cost tracker
**Status:** complete

Accumulate per-response costs in a session total displayed in the sidebar
(e.g. `Session cost: ~$0.014`).  Reset to zero when the conversation is
cleared.

### T26.5 — Unit tests for cost tracking
**Status:** complete

Tests covering: cost calculation is correct for known token counts, Ollama
path produces zero cost, session total accumulates correctly, display
formatting rounds to a sensible number of decimal places.

---

## Phase 27 — Session Persistence

### Overview

Gradio's `history_state` is lost when the page is refreshed or the server
restarts.  This phase adds the ability to save named sessions to disk and
reload them, complementing the existing RAG memory (which stores semantic
content) with full verbatim conversation replay.

### T27.1 — Session serialisation
**Status:** complete

Add `save_session(name: str, history: list[dict], path: str = "sessions/")`,
`load_session(name: str, path: str = "sessions/") -> list[dict]`, and
`delete_session(name: str, path: str = "sessions/")` to a new
`src/sessions.py` module.  Sessions are stored as JSON files in `sessions/`
(gitignored).  Include a `list_sessions()` helper returning saved session names.
Sanitise session names to safe filenames (alphanumeric, hyphens, underscores only).

### T27.2 — Save and load UI
**Status:** complete

Add a collapsible "Sessions" accordion to `src/app.py` containing:
- A text input for the session name
- A `Save` button that writes the current history to disk; if the name already
  exists show a warning Markdown element (`*Session already exists — save again
  to overwrite*`) and only overwrite on a second click
- A `gr.Dropdown` listing saved sessions, refreshed on open
- A `Load` button that replaces the current history with the selected session

### T27.3 — Session deletion with confirmation
**Status:** complete

Add a `Delete` button alongside the session dropdown.  Deletion is a
two-step interaction: the first click changes the button label to
`Confirm delete?` and sets a pending-delete flag in `gr.State`; a second
click within the same UI interaction executes the deletion and refreshes the
dropdown.  Any other action (selecting a different session, clicking Load,
clicking Save) cancels the pending delete and resets the button label.

### T27.4 — Unit tests for session persistence
**Status:** complete

Tests covering: save writes a valid JSON file, load restores history exactly,
list returns saved names, delete removes the file, invalid names are rejected,
overwrite guard triggers on first save and clears on second.

---

## Phase 28 — Coverage Report

### Overview

The test suite has grown organically to 732 tests but coverage has not been
measured.  This phase installs `pytest-cov`, generates a baseline report, and
adds targeted tests to fill the most significant gaps.

### T28.1 — Add pytest-cov and baseline report
**Status:** complete

`uv add --dev pytest-cov`.  Run `uv run pytest --cov=src --cov-report=term-missing -m "not integration" -q`
and record the baseline line coverage percentage.  Identify the top five
uncovered modules or functions by uncovered-line count.

### T28.2 — Fill coverage gaps
**Status:** complete

Write targeted tests for the identified gaps.  Focus on branches and error
paths that are hard to hit in normal use (e.g. malformed tool arguments,
Ollama connection failures in specific code paths, edge cases in helpers).
Aim for >= 85% overall line coverage.

### T28.3 — Add coverage to CI
**Status:** complete

Update `.github/workflows/ci.yml` to run pytest with `--cov=src
--cov-fail-under=85` so coverage regressions fail the build.

---

## Phase 29 — Docker Support

### Overview

Running the assistant currently requires manually installing Ollama, Python,
UV, and all dependencies.  A `Dockerfile` and `compose.yml` package the
Python application so it can be started with a single `docker compose up`,
with Ollama running as a sidecar service.

Several runtime tools make outbound network requests (web search, weather,
currency, Wikipedia, URL reader) and some tools (image generation) require
GPU access.  The compose configuration must expose the necessary ports and
pass GPU resources through to the containers that need them.

### T29.1 — Dockerfile
**Status:** complete

Write a `Dockerfile` based on `python:3.13-slim`.  Install UV, copy
`pyproject.toml` and `uv.lock`, run `uv sync --frozen`, copy source.
Expose port 7860 (Gradio default).  Set `CMD` to `uv run python assistant.py
--no-tts --no-stt` as a sensible headless default (TTS/STT require system
audio which is unavailable in most container environments).

Network-dependent tools (web search, weather, currency, URL reader) work
without additional port configuration as they make outbound HTTP requests.
No inbound ports beyond 7860 are required for the app container itself.

### T29.2 — docker-compose.yml
**Status:** complete

Write `compose.yml` with two services:

**`ollama`** — uses the official `ollama/ollama` image.  Mount a named volume
for model weights so they persist across restarts.  For GPU inference, add an
NVIDIA runtime deploy block:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```
This requires the host to have the NVIDIA Container Toolkit installed
(`nvidia-ctk`).  Without a GPU the service still starts but Ollama runs in
CPU mode and image generation will be unavailable.

**`app`** — builds the Dockerfile above.  Set `OLLAMA_HOST=http://ollama:11434`
so it connects to the sidecar.  Mount a `./sessions` volume for session
persistence and a `./models.json` bind mount so users can supply a custom
config without rebuilding the image.  Pass through any `OPENROUTER_API_KEY`
from the host environment.  Include `depends_on: ollama` with a health-check
(`curl -f http://ollama:11434/` with retries) so the app waits for Ollama to
be ready before starting.  Expose port 7860.

### T29.3 — Documentation
**Status:** complete

Update `README.md` with a Docker quick-start section covering:
- Prerequisites: Docker, Docker Compose, and (for GPU) NVIDIA Container Toolkit
- `docker compose up` to start both services
- `docker compose exec ollama ollama pull gemma4:e4b` to pull the default model
- How to supply a custom `models.json`
- GPU pass-through note: image generation and fast Ollama inference require
  the NVIDIA runtime; the compose file includes the deploy block but it is a
  no-op on CPU-only hosts
