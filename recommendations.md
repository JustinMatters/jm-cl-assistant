# Project Review: Recommendations

*Reviewed: 2026-03-30*

---

## Overall Assessment

The project is well-structured, consistently styled, and has strong test
coverage for core logic (~130 test cases across 6 test files). The
four-tier routing design is sound, docstrings are thorough, and the
codebase follows its own conventions cleanly. The issues below are
genuine opportunities for improvement, not criticisms of what is already
a solid codebase.

---

## 1. Error Handling

The biggest gap across the project. Every external call site can fail
at runtime with no user-facing feedback.

### 1.1 Ollama unavailability

`orchestrator.py:95` and `router.py:78` call `ollama.chat()` without
any exception handling. If Ollama is stopped or unreachable, the
entire Gradio handler crashes and the user sees a generic traceback.

**Recommendation:** Wrap Ollama calls in try/except and return a
user-friendly error string (e.g. "Ollama is not responding - please
check it is running"). Consider a startup health check in `build_app()`
that verifies `ollama.list()` succeeds before launching the UI.

### 1.2 OpenRouter API failures

`openrouter_client.py:58` calls the OpenAI SDK with no timeout, no
retry, and no error handling. Network failures, rate limits (HTTP 429),
and invalid API keys at runtime all produce unhandled exceptions.

**Recommendation:** Add a timeout parameter to the `create()` call,
catch `openai.APIError` and its subclasses, and return a clear message.
Consider exponential backoff for transient errors (429, 5xx).

### 1.3 Missing API key

`openrouter_client.py:33` uses `os.environ["OPENROUTER_API_KEY"]` which
raises a bare `KeyError`. The user sees `KeyError: 'OPENROUTER_API_KEY'`
with no guidance on what to do.

**Recommendation:** Catch `KeyError` and raise a `ValueError` with a
message like "Set the OPENROUTER_API_KEY environment variable".

### 1.4 Whisper model loading

`speech_input.py:18` calls `whisper.load_model()` during `__init__`.
If the model download fails or the cache is corrupted, the app crashes
on startup.

**Recommendation:** Catch exceptions during model load and surface a
clear error to the user, or defer loading to the first `transcribe()`
call (lazy loading, matching KokoroSpeaker's pattern).

### 1.5 Kokoro model files missing

`speech_output.py:58` loads the ONNX model on first `synthesize()` call.
If the model files are missing, the error appears only when the user
first requests TTS, not at startup.

**Recommendation:** Add a startup check in `build_app()` that warns if
`kokoro-v1.0.onnx` or `voices-v1.0.bin` are not found in the project
root. The user can still launch in text-only mode.

### 1.6 Gradio event handlers

`app.py` handlers `handle_text()` (line 168) and `handle_audio()`
(line 209) have no try/except. Any exception from any downstream
component crashes the handler and Gradio shows a raw traceback.

**Recommendation:** Wrap each handler body in try/except and append an
error message to the chat history (e.g. a red "Error: ..." bubble)
rather than crashing the UI.

---

## 2. Unused Parameter

`speech_input.py:20` — `transcribe()` accepts `sample_rate` as a
parameter but never passes it to `self._model.transcribe()`. Whisper
internally resamples to 16 kHz regardless, so the parameter has no
effect.

**Recommendation:** Either remove the parameter (breaking change to
callers) or pass it through if a future Whisper version supports it.
At minimum, document that it is currently unused.

---

## 3. Documentation Staleness

### 3.1 CLAUDE.md — Runtime Configuration section

Lines 32-36 say "currently hardcoded defaults pending argparse
implementation" and reference T5.6. Argparse was implemented in Phase 5
and `app.py` already has `--whisper-model` and `--ollama-model` flags.

**Recommendation:** Update the section to reflect that argparse is
implemented. Remove the "pending" language and the T5.6 reference.

### 3.2 CLAUDE.md — Architecture section

Line 8 describes the router as classifying "simple / complex_sonnet /
complex_opus". The router now has four tiers including `trivial_ollama`.

**Recommendation:** Update to list all four tiers.

### 3.3 Plan.md — Historical naming

Lines 121 and 155 reference `test_claude_client.py` and
`src/claude_client.py`. These were renamed to `test_openrouter_client.py`
and `src/openrouter_client.py` during implementation.

**Recommendation:** Update the completed ticket descriptions to reflect
the actual filenames, or add a note that the rename happened.

### 3.4 README.md — Model Reference table

Line 102 lists `trivial_ollama` as handling "greetings, arithmetic,
one-word answers". Since the last routing prompt update, arithmetic is
now routed to `simple_ollama` and `trivial_ollama` handles "facts a
schoolchild would know".

**Recommendation:** Update the table to match the current routing prompt.

---

## 4. Testing Gaps

### 4.1 No tests for `app.py`

The Gradio UI module has zero unit tests. The event handlers contain
real logic (audio format conversion, history management, TTS gating)
that could break silently.

**Recommendation:** Extract the handler logic into testable functions
that don't depend on Gradio, then test those. For example, the
int16-to-float32 conversion in `handle_audio()` and the
`_prefix_last_reply()` helper can be tested in isolation.

### 4.2 No error-path tests

No test file exercises failure scenarios: Ollama down, OpenRouter 429,
missing model files, corrupted audio input, empty API responses.

**Recommendation:** Add parametrised tests that mock exceptions from
`ollama.chat()`, `openai.OpenAI.chat.completions.create()`, and
`whisper.load_model()` to verify graceful degradation (once error
handling from section 1 is implemented).

### 4.3 Integration test API key check

`tests/test_integration.py` — `TestIntegrationOrchestrator` and
`TestIntegrationRouting` don't verify `OPENROUTER_API_KEY` is set.
If it's missing, tests that exercise Claude paths will fail with a
confusing `KeyError` rather than a clear skip.

**Recommendation:** Add `pytest.importorskip` or a `skipUnless` check
for the API key at the top of those test classes.

---

## 5. Dependency Management

### 5.1 No upper version bounds

`pyproject.toml` uses `>=` for all dependencies with no upper bounds.
Libraries like `gradio`, `openai`, and `kokoro-onnx` are actively
developed and could ship breaking changes in a major version bump.

**Recommendation:** Use compatible-release constraints (`~=`) for at
least the major libraries: `gradio~=6.10`, `openai~=2.30`,
`kokoro-onnx~=0.5`. This allows patch/minor updates while guarding
against breaking major versions.

### 5.2 Lock file

The project uses UV with `uv.lock`, which mitigates the above risk in
practice for reproducible installs. The `~=` constraints would
additionally protect against `uv add` pulling a future breaking version.

---

## 6. Portability

### 6.1 Absolute path in settings.json

`.claude/settings.json` line 10 hardcodes
`cd C:/Users/justi/Documents/GitHub/jm-cl-assistant`. This works on
the current machine but would break on any other checkout location.

**Recommendation:** If Claude Code hooks support relative paths or
`$REPO_ROOT`, use those. Otherwise, document that the path must be
updated per-machine, or generate it with a setup script.

---

## 7. Minor Code Quality

### 7.1 `last_backend` initial state

`orchestrator.py:44` initialises `last_backend` to `""`. If
`_prefix_last_reply()` in `app.py` is called before the first response
(unlikely but possible if Gradio races), the chat bubble will show
`**: response`.

**Recommendation:** Initialise to a sensible default like
`"(not yet set)"` or guard against empty string in `_prefix_last_reply`.

### 7.2 Backend label string splitting

`orchestrator.py:46-49` uses `.split('/')[-1]` to extract a display
name from the model string. This is fine for the two current models
but would produce unexpected results for a model name with no `/`.

**Recommendation:** Add a simple fallback:
`name.split('/')[-1] if '/' in name else name`.

### 7.3 `strip_markdown` — numbered lists and bullet points

`helpers.py` `strip_markdown()` does not strip `- ` bullet prefixes or
`1. ` numbered list prefixes. TTS will read "dash item" or "one dot
item".

**Recommendation:** Add regex passes for unordered list markers
(`^[-*+]\s+`) and ordered list markers (`^\d+\.\s+`).

---

## 8. Feature Suggestions

### 8.1 Conversation export

Users may want to save a conversation to a text or JSON file. Gradio
Chatbot doesn't provide this natively.

**Recommendation:** Add a "Download conversation" button that serialises
the history state as JSON or plain text.

### 8.2 System prompt customisation

The Ollama response models currently have no system prompt — they get
raw user queries. Adding a configurable system prompt (e.g. "You are a
helpful assistant. Be concise.") would improve response quality,
especially for the fast 1.7B model.

### 8.3 Token/cost tracking

OpenRouter returns usage metadata in the API response. Tracking token
counts and estimated cost per conversation would help the user monitor
API spend.

### 8.4 Conversation history limits

`orchestrator.py` passes the full history to every LLM call. For long
conversations, this will eventually exceed context windows or become
very expensive on the Claude tiers.

**Recommendation:** Implement a sliding window or summarisation strategy
for history. At minimum, truncate to the last N turns before sending to
the API.

---

## Priority Summary

| Priority | Item | Section |
|----------|------|---------|
| High | Error handling in all external calls | 1.1-1.6 |
| High | Gradio handler crash protection | 1.6 |
| Medium | Update stale documentation | 3.1-3.4 |
| Medium | Unit tests for `app.py` handlers | 4.1 |
| Medium | Error-path tests | 4.2 |
| Medium | Conversation history limits | 8.4 |
| Low | Dependency version bounds | 5.1 |
| Low | Unused `sample_rate` parameter | 2 |
| Low | Portability of settings.json | 6.1 |
| Low | Minor code quality items | 7.1-7.3 |
| Low | Feature suggestions | 8.1-8.3 |
