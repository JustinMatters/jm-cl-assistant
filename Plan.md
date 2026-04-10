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
*Archived to completed_work.md.*

- T0.1 — Create GitHub Repository — complete
- T0.2 — Initialize UV Project — complete
- T0.3 — Configure Ruff — complete
- T0.4 — Configure pytest — complete
- T0.5 — Configure Claude Code Skills & Hooks — complete

---

## Phase 1 — Dependency Installation & CI
*Archived to completed_work.md.*

- T1.1 — Add Core Dependencies via UV — complete
- T1.2 — Add Dev Dependencies via UV — complete
- T1.3 — Verify Ollama is Running Locally — complete
- T1.4 — GitHub Actions CI (`.github/workflows/ci.yml`) — complete

---

## Phase 2 — Tests
*Archived to completed_work.md.*

- T2.1 — Router Unit Tests (`tests/test_router.py`) — complete
- T2.2 — Orchestrator Unit Tests (`tests/test_orchestrator.py`) — complete
- T2.3 — Claude Client Unit Tests (`tests/test_openrouter_client.py`) — complete (renamed from `test_claude_client.py`)
- T2.4 — Speech Module Unit Tests (`tests/test_speech.py`) — complete
- T2.5 — Integration Smoke Test (`tests/test_integration.py`) — complete

---

## Phase 3 — Core Backend Modules
*Archived to completed_work.md.*

- T3.1 — Ollama Router (`src/router.py`) — complete
- T3.2 — Claude API Client (`src/openrouter_client.py`) — complete (renamed from `claude_client.py`)
- T3.3 — Chat Orchestrator (`src/orchestrator.py`) — complete

---

## Phase 4 — Speech I/O Modules
*Archived to completed_work.md.*

- T4.1 — Speech Input: Whisper (`src/speech_input.py`) — complete
- T4.2 — Speech Output: Kokoro (`src/speech_output.py`) — complete

---

## Phase 5 — Gradio Interface
*Archived to completed_work.md.*

- T5.1 — App Skeleton (`src/app.py`) — complete
- T5.2 — Text Input Flow — complete
- T5.3 — Speech Input Flow — complete
- T5.4 — Speech Output Flow — complete
- T5.5 — Mode Switching Logic — complete
- T5.6 — Argparse Runtime Configuration (`src/app.py`) — complete

---

## Phase 6 — Quality Gate
*Archived to completed_work.md.*

- T6.1 — Ruff Lint & Format Pass — complete

---

## Phase 7 — Refinements
*Archived to completed_work.md.*

- T7.1 — Dark / Light Mode Toggle — complete
- T7.2 — Scale Chat Panel to Fit Viewport — complete
- T7.3 — Rename Chat Panel to "Previous Conversation" — complete
- T7.4 — Prefix Each Reply with Model Name in Bold — complete
- T7.5 — Toggle to Show/Hide `<think>` Tag Content — complete
- T7.6 — Lint and Test — complete
- T7.7 — Add Google-Style Docstrings — complete
- T7.8 — Lint and Test Again — complete
- T7.9 — Update README — complete

---

## Phase 8 — Text to Speech Debugging
*Archived to completed_work.md.*

- T8.1 — Fix Kokoro TTS Initialisation — complete
- T8.2 — Fix Speech Not Obeying `<think>` Tag Toggle — complete
- T8.3 — Fix Float32 Audio Warning from Gradio — complete
- T8.4 — Strip Markdown Before TTS Synthesis — complete
- T8.5 — Manual Check of TTS and Resolve Any Bugs — complete
- T8.6 — Manual Check of Dual Mode and Resolve Any Bugs — complete
- T8.7 — Simplify Output Mode Radio to Two Options — complete
- T8.8 — Voice Selection Dropdown — complete

---

## Phase 9 — Routing Tiers
*Archived to completed_work.md.*

- T9.1 — Identify Fast Small Local Model — complete
- T9.2 — Add Trivial Routing Tier (Small Fast Model) — complete
- T9.3 — Update Tests and README for New Routing Tiers — complete
- T9.4 — Use Fast Model for Routing/Classification — complete

---

## Phase 10 — Speech to Text Debugging
*Archived to completed_work.md.*

- T10.1 — Check STT via Whisper Works End-to-End — complete
- T10.2 — Display Transcribed Text Before Response — complete
- T10.3 — Handle Unused `sample_rate` Parameter — complete
- T10.4 — Audio Input Validation — complete
- T10.5 — Wrap STT in Error Handling — complete
- T10.6 — STT Confidence and Empty Transcription Handling — complete
- T10.7 — Add Unit Tests for Audio Handler Logic — complete

---

## Phase 11 — Error Handling
*Archived to completed_work.md.*

- T11.1 — Ollama Call Protection — complete
- T11.2 — OpenRouter Call Protection — complete
- T11.3 — Friendly Missing API Key Error — complete
- T11.4 — Kokoro Model File Check — complete
- T11.5 — Gradio Handler Crash Protection — complete
- T11.6 — Startup Health Checks — complete

---

## Phase 12 — Unused `sample_rate` Parameter
*Archived to completed_work.md.*

- T12.1 — Resolve `sample_rate` in WhisperTranscriber — complete

---

## Phase 13 — Documentation Refresh
*Archived to completed_work.md.*

- T13.1 — Update CLAUDE.md Runtime Configuration Section — complete
- T13.2 — Update CLAUDE.md Architecture Description — complete
- T13.3 — Update README Model Reference Table — complete
- T13.4 — Fix Historical Filenames in Plan.md — complete

---

## Phase 14 — Testing Gaps
*Archived to completed_work.md.*

- T14.1 — Integration Test API Key Guard — complete

---

## Phase 15 — Dependency Management
*Archived to completed_work.md.*

- T15.1 — Pin Major Version Bounds in `pyproject.toml` — complete
- T15.2 — Enforce Lockfile Hash Verification in CI — complete
- T15.3 — Verify `uv.lock` Is Committed and Not Gitignored — complete

---

## Phase 16 — Portability
*Archived to completed_work.md.*

- T16.1 — Remove Absolute Path from `.claude/settings.json` — complete

---

## Phase 17 — Minor Code Quality
*Archived to completed_work.md.*

- T17.1 — Initialise `last_backend` to a Sensible Default — complete
- T17.2 — Strip List Markers in `strip_markdown()` — complete

---

## Phase 18 — RAG Memory
*Archived to completed_work.md.*

- T18.1 — Dependencies and Embedding Model — complete
- T18.2 — MemoryStore Class — complete
- T18.3 — Session ID Generation — complete
- T18.4 — Conversation Recording — complete
- T18.5 — Context Injection — complete
- T18.6 — Memory Toggle and Status Indicator — complete

---

## Phase 19 — Tools
*Archived to completed_work.md.*

- T19.1 — Calculator Tool — complete
- T19.2 — Integrate Calculator into Orchestrator — complete
- T19.3 — Unit Conversion Tool (stretch) — complete
- T19.4 — Tool Definition Protocol — complete
- T19.5 — Tool Registry — complete
- T19.6 — Dynamic Router — complete
- T19.7 — Tool Toggle UI — complete
- T19.8 — Agentic Tool Use Loop (Approach B) — complete
- T19.9 — Memory Write Interface for Tools — complete
- T19.10 — Web Search Tool — complete
- T19.11 — Location Tool (IP Lookup) — complete
- T19.12 — Date and Time Tool — complete
- T19.13 — Weather Forecast Tool — complete
- T19.14 — Currency Conversion Tool — complete
- T19.15 — Dictionary / Definition Tool — complete
- T19.16 — Wikipedia Summary Tool — complete
- T19.17 — URL Content Summariser — complete
- T19.18 — Reminder / Timer Tool — complete
- T19.19 — System Info Tool — complete
- T19.20 — Code Execution Sandbox — complete

---

## Phase 20 — Extended Tools
*Archived to completed_work.md.*

- T20.1 — Gemma 4 Model Evaluation and Migration — complete
- T20.2 — File Reader Tool (local path + URL) — complete
- T20.3 — Image Output Infrastructure — complete
- T20.4 — Flowchart Generation Tool — complete
- T20.5 — Vision API Support — complete
- T20.6 — Data Analysis Tool (Polars + Matplotlib) — complete
- T20.7 — Image Generation Tool — complete

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
| 11 | Error Handling | T11.1 → T11.6 | complete |
| 12 | Unused `sample_rate` Parameter | T12.1 | complete |
| 13 | Documentation Refresh | T13.1 → T13.4 | complete |
| 14 | Testing Gaps | T14.1 | complete |
| 15 | Dependency Management | T15.1 → T15.3 | complete |
| 16 | Portability | T16.1 | complete |
| 17 | Minor Code Quality | T17.1 → T17.2 | complete |
| 18 | RAG Memory | T18.1 → T18.6 | complete |
| 19 | Tools | T19.1 → T19.20 | complete |
| 20 | Extended Tools | T20.1 → T20.7 | complete |
| 21 | Runtime Feature Switches | T21.1 → T21.3 | complete |
| 22 | Model Configuration File | T22.1 → T22.3 | complete |
| 23 | Streaming Responses | T23.1 → T23.4 | complete |
| 24 | Context Window Trimming | T24.1 → T24.4 | complete |
| 25 | Conversation Export | T25.1 → T25.3 | complete |
| 26 | Token and Cost Display | T26.1 → T26.5 | complete |
| 27 | Session Persistence | T27.1 → T27.4 | complete |
| 28 | Coverage Report | T28.1 → T28.3 | complete |
| 29 | Docker Support | T29.1 → T29.3 | complete |

---

## Phase 21 — Runtime Feature Switches
*Archived to completed_work.md.*

- T21.1 — Disable TTS (`--no-tts`) — complete
- T21.2 — Disable STT (`--no-stt`) — complete
- T21.3 — Disable Tool Use (`--no-tools`) — complete

---

## Phase 22 — Model Configuration File
*Archived to completed_work.md.*

- T22.1 — `models.json` and loader module — complete
- T22.2 — Wire loader into application code — complete
- T22.3 — UI model status display — complete

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
Aim for ≥ 85% overall line coverage.

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

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
