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
**Status:** not started

- Implement `define(word: str) -> str` in `src/tools/dictionary.py`
- Use the Free Dictionary API (dictionaryapi.dev, no key required)
- Return: word, phonetic, part of speech, top 2-3 definitions, and an
  example sentence if available
- Format as plain text suitable for TTS
- Register a `ToolDefinition` (Approach A, `default_enabled=True`,
  `min_tier="trivial_ollama"`)
- Add unit tests in `tests/test_dictionary.py` (mock HTTP calls)

### T19.16 — Wikipedia Summary Tool
**Status:** not started

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
**Status:** not started

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
**Status:** not started

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
**Status:** not started

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
**Status:** not started

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
| 19 | Tools | T19.1 → T19.20 | in progress (T19.1–T19.14 complete) |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
