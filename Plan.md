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
| 11 | Error Handling | T11.1 → T11.6 | complete |
| 12 | Unused `sample_rate` Parameter | T12.1 | complete |
| 13 | Documentation Refresh | T13.1 → T13.4 | complete |
| 14 | Testing Gaps | T14.1 | complete |
| 15 | Dependency Management | T15.1 → T15.3 | complete |
| 16 | Portability | T16.1 | complete |
| 17 | Minor Code Quality | T17.1 → T17.2 | complete |
| 18 | Tools | T18.1 → T18.14 | not started |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
