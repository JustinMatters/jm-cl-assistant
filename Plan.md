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

### Overview

Six new capabilities grouped by the infrastructure they share.  T20.1 and
T20.2 are enabling tickets that later tools depend on; the remaining four
can be built in any order once those two are in place.

**Shared image output mechanism (T20.2):** Tools that produce images
(flowcharts, data plots, generated images) return their output as a
`bytes` object tagged with the prefix `__IMAGE__:` followed by a
base64-encoded PNG.  The orchestrator detects this sentinel and routes the
payload to a `gr.Image` output component added to the Gradio UI, leaving
the normal text path unchanged for tools that return strings.

**New dependencies required:**

| Package | Purpose | Ticket |
|---------|---------|--------|
| `pypdf` | PDF text extraction | T20.1 |
| `python-docx` | DOCX text extraction | T20.1 |
| `graphviz` (Python + system binary) | DOT → PNG rendering | T20.3 |
| `polars` | DataFrame reads / summary stats | T20.5 |
| `matplotlib` | Plot generation | T20.5 |
| `openpyxl` | Excel file support for polars | T20.5 |
| `diffusers` | Local diffusion image generation | T20.6 |
| `transformers` | Model loading for diffusers | T20.6 |
| `accelerate` | Diffusers performance layer | T20.6 |

`torch` is already declared; `trafilatura` (HTML extraction) is already
present.

---

### T20.1 — File Reader Tool (local path + URL)
**Status:** not started

Implement `src/tools/file_reader.py` — a single Approach B tool that reads
the text content of a file supplied either as a local filesystem path or a
remote URL.

**Supported formats:**

| Format | Local path | URL |
|--------|-----------|-----|
| PDF | `pypdf` | download then parse |
| DOCX | `python-docx` | download then parse |
| TXT | stdlib `open()` | `urllib.request` |
| HTML | `trafilatura` (already present) | `trafilatura` |

**Design notes:**
- Detect format from the file extension (`.pdf`, `.docx`, `.txt`, `.htm`,
  `.html`); fall back to attempting HTML extraction for unknown extensions
  when given a URL.
- For remote non-HTML files (e.g. a PDF URL), download to a `tempfile`
  then parse; clean up the temp file after reading.
- Reuse `_validate_url()` from `url_reader.py` for scheme validation before
  any network call.
- Sanitise and truncate extracted text using the same control-character
  stripping pattern used in `url_reader.py` and `wikipedia.py`, capped at
  `_MAX_CONTENT = 4000` characters.
- Return the text framed as `"Content from <source>:\n\n{text}\n\n(Source:
  <source>)"` so the LLM knows it is reading external material.
- Register a `ToolDefinition` (Approach B, `default_enabled=True`,
  `min_tier="complex_sonnet"`, `category="files"`).
- Parameters schema: `{"path_or_url": {"type": "string"}}`.
- Add unit tests in `tests/test_file_reader.py` (mock file I/O and HTTP).

**Dependencies to add via UV:** `pypdf`, `python-docx`

---

### T20.2 — Image Output Infrastructure
**Status:** not started

All tools that produce images need a shared mechanism to deliver them to
the Gradio UI.  This ticket establishes that mechanism so T20.3–T20.6 each
have a clean, consistent path.

**Return value convention:**
- Image-producing tool callables return a `bytes` object encoded as:
  `b"__IMAGE__:" + base64.b64encode(png_bytes)`
- All other tools continue to return plain strings; the orchestrator
  ignores the sentinel for them.

**Orchestrator changes (`src/orchestrator.py`):**
- After a B-tool executor returns a value, check for the `__IMAGE__:`
  prefix.
- If detected: decode the base64 payload, store the PNG bytes in
  `self._pending_image`, and return a human-readable text description
  to the LLM (e.g. `"Image generated successfully."`).
- `self._pending_image: bytes | None = None` — reset to `None` on each
  `respond()` call.

**Gradio UI changes (`src/app.py`):**
- Add a `gr.Image(visible=False, label="Output image")` component.
- After `handle_text` / `handle_audio` call `orchestrator.respond()`,
  check `orchestrator._pending_image`:
  - If set: call `gr.update(visible=True, value=…)` to show the image.
  - If not: call `gr.update(visible=False, value=None)` to hide it.
- Add `image_output` to the outputs list of both `submit_btn.click` and
  `text_input.submit` and `audio_input.change`.
- The image output component sits below the chatbot and above the text
  input row.

**Helper function in `src/tools/image_utils.py`:**
```python
import base64, io
from PIL import Image   # already available via diffusers / torch

def encode_image(img: Image.Image) -> bytes:
    """Encode a PIL Image as the __IMAGE__ sentinel bytes."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return b"__IMAGE__:" + base64.b64encode(buf.getvalue())
```

Add unit tests in `tests/test_image_utils.py`.

---

### T20.3 — Flowchart Generation Tool
**Status:** not started

Implement `src/tools/flowchart.py` — the LLM generates
[Graphviz DOT notation](https://graphviz.org/doc/info/lang.html) and the
tool renders it to a PNG image returned via the T20.2 sentinel.

**Design notes:**
- Approach B tool; parameters schema:
  `{"dot": {"type": "string", "description": "Valid Graphviz DOT source"}}`.
- Use the `graphviz` Python library (`graphviz.Source(dot).pipe(format="png")`)
  to render to PNG bytes without writing to disk.
- Pass the PNG bytes through `encode_image()` (T20.2) to produce the
  sentinel return value.
- On `graphviz.ExecutableNotFound`: return a clear error message asking
  the user to install Graphviz (`winget install graphviz` / `brew install
  graphviz` / `apt install graphviz`).
- The LLM system prompt for this tool should specify that it must emit
  valid DOT source only, no commentary — the description and examples
  guide this.
- Register a `ToolDefinition` (Approach B, `default_enabled=True`,
  `min_tier="complex_sonnet"`, `category="visual"`).
- Add unit tests in `tests/test_flowchart.py` (mock `graphviz.Source.pipe`).

**Dependencies to add via UV:** `graphviz` (Python package);
instruct user to also install the Graphviz system binary separately.

---

### T20.4 — Vision API Support
**Status:** not started

Allow the user to attach an image to a query and have it analysed by a
vision-capable model.

**UI changes (`src/app.py`):**
- Add a `gr.Image(sources=["upload", "clipboard"], type="pil",
  visible=True, label="Attach image (optional)")` component.
- The attached image is optional — if `None`, the existing text-only flow
  is unchanged.
- Thread the image through `handle_text` → `process_text` →
  `orchestrator.respond()` as an additional `image` parameter
  (defaults to `None`).

**Routing logic (`src/orchestrator.py`):**
- When `image is not None`, always route to at least `complex_sonnet`
  (Claude supports vision; small Ollama models generally do not).
- Exception: if the active Ollama model is a known vision model
  (`llava`, `moondream`, `minicpm-v`, etc.) and the tier is
  `trivial_ollama` or `simple_ollama`, send to Ollama.
- Add an `_OLLAMA_VISION_MODELS` frozenset of known vision-capable model
  name prefixes.

**OpenRouter client changes (`src/openrouter_client.py`):**
- `ask()` gains an optional `image: PIL.Image.Image | None = None`
  parameter.
- When set, encode as base64 PNG and include in the user message as an
  OpenAI vision content block:
  ```python
  {"type": "image_url",
   "image_url": {"url": f"data:image/png;base64,{b64}"}}
  ```

**Ollama client path (`src/orchestrator.py` `_ollama_respond()`):**
- Ollama vision models accept `images` in the message dict:
  `{"role": "user", "content": text, "images": [b64_bytes]}`.

**`src/process_text.py` and `src/process_audio.py`:**
- Add `image` parameter (default `None`) threading it to
  `orchestrator.respond()`.

Add unit tests in `tests/test_vision.py` (mock the API calls).

---

### T20.5 — Data Analysis Tool (Polars + Matplotlib)
**Status:** not started

Implement `src/tools/data_analysis.py` — reads a CSV or Excel file (by
local path or URL), produces a statistical summary, and optionally
generates a chart.

**Design notes:**
- Approach B tool with two operations controlled by an `action` parameter:
  - `"summarise"` — load the file and return `shape`, column types,
    `describe()` statistics, and the first 5 rows as plain text.
  - `"plot"` — generate a chart of the type specified by the `chart_type`
    parameter (`"bar"`, `"line"`, `"scatter"`, `"histogram"`), using
    columns specified by `x_col` and `y_col`.
- Parameters schema:
  ```json
  {
    "path_or_url": {"type": "string"},
    "action":      {"type": "string", "enum": ["summarise", "plot"]},
    "chart_type":  {"type": "string", "enum": ["bar","line","scatter","histogram"]},
    "x_col":       {"type": "string"},
    "y_col":       {"type": "string"},
    "title":       {"type": "string"}
  }
  ```
  (`chart_type`, `x_col`, `y_col`, `title` required only for `action="plot"`.)
- For URL inputs, download to a temp file then load with Polars.
- For Excel files (`.xlsx`, `.xls`), use `polars.read_excel()` which
  requires `openpyxl`.
- Plots use `matplotlib.figure.Figure` (non-interactive backend —
  `matplotlib.use("Agg")` at module level to avoid display dependencies);
  the resulting PNG is returned via `encode_image()` (T20.2).
- Summarise output is returned as a plain text string.
- Register a `ToolDefinition` (Approach B, `default_enabled=True`,
  `min_tier="complex_sonnet"`, `category="files"`).
- Add unit tests in `tests/test_data_analysis.py`.

**Dependencies to add via UV:** `polars`, `matplotlib`, `openpyxl`

---

### T20.6 — Image Generation Tool
**Status:** not started

Implement `src/tools/image_gen.py` — generates an image from a text
prompt, first attempting local diffusion and falling back to a CC0 image
search if the local model is unavailable.

**Local generation (primary path):**
- Use `diffusers` with `stabilityai/sdxl-turbo` as the default model:
  - 4-step generation; fast on a modern GPU (~2–5 s at 512×512).
  - ~6.7 GB VRAM in fp16.
  - Model downloaded on first use to the HuggingFace cache
    (`~/.cache/huggingface/`) — not bundled with the repo.
- Pipeline: `AutoPipelineForText2Image.from_pretrained(...,
  torch_dtype=torch.float16)`.
- If `torch.cuda.is_available()` is False, skip local generation and go
  directly to the CC0 fallback.
- If the model files are absent (cache miss on first run), raise a
  recognisable `EnvironmentError`; catch it in the callable and fall
  back.
- Generate at 512×512 with `num_inference_steps=4`, `guidance_scale=0.0`
  (SDXL-Turbo is guidance-free).
- Return the image via `encode_image()` (T20.2).

**CC0 fallback (Openverse API):**
- Query `https://api.openverse.org/v1/images/?q={prompt}&license=cc0`
  (no API key required).
- Download the first result's image URL, decode to `PIL.Image`, and
  return via `encode_image()`.
- If Openverse also fails, return a plain-text error string.

**Callable flow:**
```python
def _image_gen_callable(args_json: str) -> bytes | str:
    prompt = ...
    # 1. Try local diffusion
    try:
        return _generate_local(prompt)
    except (EnvironmentError, RuntimeError):
        pass
    # 2. Try Openverse CC0 search
    try:
        return _search_cc0(prompt)
    except Exception as exc:
        return f"Image generation failed: {exc}"
```

**Parameters schema:**
```json
{"prompt": {"type": "string",
            "description": "Descriptive text for the image to generate"}}
```

- Register a `ToolDefinition` (Approach B, `default_enabled=False`,
  `min_tier="complex_sonnet"`, `category="visual"`).
  Off by default because the first run triggers a ~7 GB model download.
- A `gr.Markdown` warning in the Tools accordion explains the download
  requirement when the tool is enabled.
- Add unit tests in `tests/test_image_gen.py` (mock both paths).

**Dependencies to add via UV:** `diffusers`, `transformers`, `accelerate`

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
| 20 | Extended Tools | T20.1 → T20.6 | not started |

---

## Claude Skills to Invoke During Build

| When | Skill | Why |
|------|-------|-----|
| T0.5 | `update-config` | Register ruff pre-commit hooks in `settings.json` |
