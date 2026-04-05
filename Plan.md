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

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
