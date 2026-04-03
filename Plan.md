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
**Status:** not started

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
**Status:** not started

- Create `src/memory/__init__.py` (empty, makes `memory` a package)
- Create `src/memory/store.py` implementing a `MemoryStore` class:

  ```python
  class MemoryStore:
      def __init__(self, persist_dir: str = "./chroma_db",
                   ollama_url: str = "http://localhost:11434",
                   collection: str = "assistant_memory",
                   k: int = 5,
                   similarity_threshold: float = 0.7): ...

      def add(
          self,
          text: str,
          source: str,
          session_id: str,
          keywords: str = "",
          url: str = "",
          title: str = "",
      ) -> str:
          """Store a record. Returns the generated document ID."""

      def search(
          self,
          query: str,
          k: int | None = None,
          source_filter: str | None = None,
      ) -> list[dict]:
          """Return up to k records with distance < threshold.
          Each dict has keys: id, text, source, session_id,
          timestamp, keywords, url, title, distance."""

      def get_context_block(self, query: str) -> str:
          """Return a formatted prompt-ready string of retrieved memories,
          or empty string if nothing passes the similarity threshold."""
  ```

- In `__init__`, verify that `nomic-embed-text` is available in the local
  Ollama instance before proceeding. Use `ollama.list()` (or equivalent) to
  check installed models and raise a clear `RuntimeError` with a helpful
  message (e.g. `"nomic-embed-text not found — run: ollama pull nomic-embed-text"`)
  if it is missing. This surfaces the missing model immediately at startup
  rather than producing a cryptic HTTP error mid-conversation.
- Document IDs are generated as `f"{source}_{timestamp}_{uuid4().hex[:8]}"` —
  human-readable and collision-resistant
- `get_context_block()` formats retrieved records as:
  ```
  [PAST MEMORIES]
  - [2026-01-15 | conversation] User asked about Whisper model sizes...
  - [2026-01-20 | web_search | title: "Open-Meteo API"] Forecast API returns...
  [END MEMORIES]
  ```
  Include `title` and `url` fields when present. Omit empty fields silently.
- Add unit tests in `tests/test_memory_store.py` using a temporary ChromaDB
  directory (use `tmp_path` pytest fixture). Mock the Ollama embedding call
  so tests do not require a running Ollama instance. Test: add → search →
  get_context_block round-trip, similarity threshold filtering, source
  filtering, empty-store behaviour (returns empty string, not an error).

### T18.3 — Session ID Generation
**Status:** not started

- Add session ID generation to `src/app.py`: generate a UUID once at app
  startup (not per message) and pass it to the `Orchestrator`
- Update `Orchestrator.__init__` to accept and store a `session_id: str`
  parameter; default to `uuid4().hex` if not provided so existing tests
  that construct `Orchestrator` directly continue to work
- The session ID is used as metadata on every memory write; it lets future
  queries filter to a specific session if needed
- Update `tests/test_orchestrator.py` to pass an explicit `session_id` in
  test fixtures

### T18.4 — Conversation Recording
**Status:** not started

- Instantiate `MemoryStore` in `Orchestrator.__init__`; add a
  `memory_enabled: bool = True` constructor parameter so tests can disable it
- After each complete exchange (user message + assistant response), call
  `memory.add()` with the combined text:
  ```python
  text = f"User: {user_message}\nAssistant: {response}"
  memory.add(text, source="conversation", session_id=self.session_id)
  ```
- Prepend `search_document:` to the stored text before embedding, as
  recommended for nomic-embed-text instruction-aware retrieval
- Writing to memory is fire-and-forget from the user's perspective — do not
  block the response on memory writes. If the ChromaDB write fails (e.g.
  Ollama is not running), log a warning and continue; memory failures must
  never prevent a response from being returned
- Add integration test (marked `@pytest.mark.integration`) that writes a
  turn and reads it back using a live ChromaDB instance
- Update unit tests to pass `memory_enabled=False` where memory is not
  relevant to what is being tested

### T18.5 — Context Injection
**Status:** not started

- At the start of each call to `Orchestrator.respond()`, before constructing
  the message list, call `memory.get_context_block(user_message)`
- If the returned string is non-empty, prepend it to the system prompt:
  ```python
  system = f"{base_system}\n\n{context_block}" if context_block else base_system
  ```
- The context block is only injected on messages where the user has said
  something (not on empty or whitespace-only messages)
- Prepend `search_query:` to the query text before searching, as recommended
  for nomic-embed-text instruction-aware retrieval
- Do not inject the current turn's own exchange (it hasn't been stored yet
  at inject time — this is by design; the current turn goes into memory
  after the response is returned, per T18.4)
- Context injection failures (Ollama down, ChromaDB unavailable) must be
  handled gracefully: log a warning and proceed with no injected context
- Add tests verifying: injection when memories exist and pass threshold,
  no injection when store is empty, no injection when all results exceed the
  similarity threshold distance cutoff

### T18.6 — Memory Toggle and Status Indicator
**Status:** not started

- Add a `gr.Checkbox` (label: `"Memory"`, value: `True`) to the Gradio UI,
  placed alongside the existing mode controls so it is visually grouped with
  other session settings
- Wire the checkbox to a `gr.State` variable `memory_enabled` that is passed
  into each `Orchestrator.respond()` call
- `Orchestrator.respond()` already accepts `memory_enabled` as a constructor
  parameter (T18.4); update the app to pass the live UI state value on each
  call instead so the user can toggle mid-session without restarting
- When `memory_enabled` is `False`: skip both context injection (T18.5) and
  conversation recording (T18.4) for that turn — the store is neither read
  from nor written to
- Add a read-only `gr.Textbox` or `gr.Markdown` status label next to the
  checkbox showing the current record count (e.g. `"Memory: on · 42 records"`
  or `"Memory: off"`); update it after each turn via the existing Gradio
  output chain
- The record count is retrieved cheaply via `collection.count()` on the
  ChromaDB collection — no embedding call required
- When memory is toggled off, the status label shows `"Memory: off"` so the
  user has a clear visual confirmation that the store is not being used
- Add tests verifying that passing `memory_enabled=False` suppresses both
  read and write calls to `MemoryStore`

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
computation. Phase 19 replaces that with dedicated tools so deterministic
tasks are solved reliably and cheaply without involving a large model.

### T19.1 — Calculator Tool
**Status:** not started

- Implement a `calculate(expression: str) -> str` tool in `src/tools/calculator.py`
  that evaluates arithmetic expressions safely (no `eval` on arbitrary code)
- Use the `simple_eval` or `asteval` library, or implement a safe AST-based
  evaluator, to support basic arithmetic: `+`, `-`, `*`, `/`, `**`, `%`,
  parentheses, and common maths functions (`sqrt`, `abs`, `round`, etc.)
- Return the result as a formatted string, or a clear error message if the
  expression is invalid
- Add unit tests in `tests/test_calculator.py`

### T19.2 — Integrate Calculator into Orchestrator
**Status:** not started

- Add a `maths` classification tier to the router system prompt so arithmetic
  and calculation queries are routed to `maths` instead of `simple_ollama`
- In `Orchestrator.respond()`, intercept the `maths` classification and call
  the calculator tool instead of an LLM
- Update `_backend_labels` to include a `"maths"` entry (e.g. `"Tool: calculator"`)
- Update tests in `test_orchestrator.py` and `test_router.py`

### T19.3 — Unit Conversion Tool (stretch)
**Status:** not started

- Implement a `convert(value, from_unit, to_unit) -> str` tool in
  `src/tools/converter.py` using the `pint` library
- Cover common categories: length, mass, temperature, volume, speed, time
- Integrate into orchestrator similarly to the calculator
- Add unit tests in `tests/test_converter.py`

### T19.4 — Web Search Tool
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

### T19.5 — Location Tool (IP Lookup)
**Status:** not started

- Implement a `get_location() -> dict` tool in `src/tools/location.py`
  that resolves the user's approximate location from their public IP address
- Use a free IP geolocation API (e.g. `ip-api.com` — no key required) returning
  city, region, country, latitude, and longitude
- Cache the result for the session to avoid repeated lookups
- Expose a `get_location_str() -> str` helper that returns a human-readable
  location string (e.g. `"London, England, GB"`) for use by other tools
- Add unit tests in `tests/test_location.py` (mock HTTP calls)

### T19.6 — Date and Time Tool
**Status:** not started

- Implement a `get_datetime(timezone: str | None = None) -> str` tool in
  `src/tools/datetime_tool.py`
- Return the current date and time formatted as a readable string
  (e.g. `"Sunday 29 March 2026, 14:35 BST"`)
- If no timezone is supplied, attempt to infer it from the location tool
  (T19.5); fall back to UTC with a note
- Use the `zoneinfo` stdlib module (Python 3.9+) — no extra dependency needed
- Add a `datetime` classification tier to the router system prompt for
  queries about the current time or date
- Integrate into `Orchestrator.respond()` with `_backend_label` `"Tool: datetime"`
- Add unit tests in `tests/test_datetime_tool.py`

### T19.7 — Weather Forecast Tool
**Status:** not started

- Implement a `get_weather(location: str, days: int = 7) -> str` tool in
  `src/tools/weather.py`
- Use the Open-Meteo API (free, no API key required) with geocoding via the
  Open-Meteo geocoding endpoint to resolve location names to coordinates
- Return a day-by-day forecast summary for up to 7 days: date, condition,
  high/low temperature (°C), precipitation probability
- If `location` is `"auto"`, call the location tool (T19.5) to resolve the
  user's current location automatically
- Format output as plain text suitable for reading aloud via TTS
- Add a `weather` classification tier to the router system prompt
- Integrate into `Orchestrator.respond()` with `_backend_label` `"Tool: weather"`
- Add unit tests in `tests/test_weather.py` (mock HTTP calls)

### T19.8 — Tool Registry and LLM Function Calling Infrastructure
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

### T19.9 — Memory Write Interface for Tools
**Status:** not started

- Extend the `ToolRegistry.execute()` dispatch mechanism (T19.8) with an
  optional `store: MemoryStore | None = None` parameter so tools can commit
  records without coupling to the Orchestrator directly
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
  when memory is disabled) into the tool registry dispatch call
- Add a unit test verifying that a mock tool receives the `store` argument
  and can call `add()` on it

### T19.10 — Currency Conversion Tool
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

### T19.11 — Dictionary / Definition Tool
**Status:** not started

- Implement `define(word: str) -> str` in `src/tools/dictionary.py`
- Use the Free Dictionary API (dictionaryapi.dev, no key required)
- Return: word, phonetic, part of speech, top 2-3 definitions, and an
  example sentence if available
- Format as plain text suitable for TTS
- Good candidate for Approach A — "define serendipity" or "what does
  ephemeral mean" are clear triggers
- Add unit tests in `tests/test_dictionary.py` (mock HTTP calls)

### T19.12 — Wikipedia Summary Tool
**Status:** not started

- Implement `wiki_summary(topic: str) -> str` in `src/tools/wikipedia.py`
- Use the Wikipedia REST API (`en.wikipedia.org/api/rest_v1/page/summary/`)
  — no key required, returns a plain-text extract
- Return the first 2-3 sentences of the article summary, plus the URL
- Good candidate for Approach B (LLM tool use) — the model can decide when
  a factual query would benefit from Wikipedia vs its own knowledge, and
  can rephrase the search term for better results
- Add unit tests in `tests/test_wikipedia.py` (mock HTTP calls)

### T19.13 — URL Content Summariser
**Status:** not started

- Implement `summarise_url(url: str) -> str` in `src/tools/url_reader.py`
- Fetch the page content, extract readable text (use `trafilatura` or
  `beautifulsoup4` + `requests`), and truncate to a reasonable length
- Pass the extracted text to the current Claude tier with a "summarise this
  page" system prompt, returning the summary
- Best suited for Approach B — the model detects a URL in the user's message
  and decides to fetch and summarise it
- Add unit tests in `tests/test_url_reader.py` (mock HTTP calls)

### T19.14 — Reminder / Timer Tool
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

### T19.15 — System Info Tool
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
| 18 | RAG Memory | T18.1 → T18.6 | not started |
| 19 | Tools | T19.1 → T19.15 | not started |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
