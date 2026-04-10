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

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
