"""Gradio web interface for the JM Assistant chatbot.

Provides a Blocks-based UI with text and speech input/output modes,
dark/light theme toggle, configurable conversation height, and a toggle
to show or hide LLM chain-of-thought ``<think>`` tags.
"""

import argparse
import os
import subprocess
import tempfile
import time
from uuid import uuid4

import gradio as gr
import ollama

from src.helpers import (
    format_history_as_markdown,
    suppress_connection_reset_errors,
)
from src.model_config import load_models
from src.orchestrator import Orchestrator
from src.process_audio import stream_process_audio
from src.process_text import stream_process_text
from src.router import OLLAMA_FAST_MODEL
from src.sessions import (
    delete_session,
    list_sessions,
    load_session,
    save_session,
)
from src.speech_input import WhisperTranscriber
from src.speech_output import KokoroSpeaker, check_kokoro_files
from src.tools.registry import _TIER_RANK, REGISTRY
from src.tools.reminders import REMINDER_STORE

_APP_MODEL_CONFIG = load_models()
OLLAMA_MODEL_DEFAULT = _APP_MODEL_CONFIG["simple_llm"].model_id

_MODAL_CSS = """
#code-confirm-modal {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 1000 !important;
    background: var(--background-fill-primary) !important;
    border: 2px solid var(--border-color-primary) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 48px rgba(0, 0, 0, 0.7) !important;
    padding: 1.5rem !important;
    width: 680px !important;
    max-width: 92vw !important;
    max-height: 80vh !important;
    overflow-y: auto !important;
}
"""


def _ensure_ollama(max_wait: int = 10) -> str | None:
    """Start Ollama if it is not reachable, then wait for it to come up.

    Args:
        max_wait: Maximum seconds to wait after launching the server process.

    Returns:
        A warning string if Ollama could not be reached or started, or
        ``None`` if Ollama is available.
    """
    try:
        ollama.list()
        return None
    except ConnectionError:
        pass
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return (
            "Ollama is not installed. "
            "Download it from https://ollama.com/download"
        )
    for _ in range(max_wait):
        time.sleep(1)
        try:
            ollama.list()
            return None
        except ConnectionError:
            continue
    return (
        "Ollama was found but did not start within "
        f"{max_wait} seconds. Try running `ollama serve` manually."
    )


def _check_ollama_models(*models: str) -> str | None:
    """Check that required Ollama models are available locally.

    Silently returns ``None`` if Ollama is unreachable — that failure is
    already reported by ``_ensure_ollama``.

    Args:
        *models: Model name strings to verify are pulled.

    Returns:
        A warning string listing any missing models with pull commands,
        or ``None`` if all models are present or Ollama is unreachable.
    """
    try:
        available = {m.model for m in ollama.list().models}
    except Exception:
        return None
    missing = [model for model in models if model not in available]
    if missing:
        pull_cmds = " && ".join(f"ollama pull {m}" for m in missing)
        return (
            f"Ollama models not pulled: {', '.join(missing)}. Run: {pull_cmds}"
        )
    return None


def _check_api_key() -> str | None:
    """Check that OPENROUTER_API_KEY is set in the environment.

    Returns:
        A warning string if the key is absent, or ``None`` if it is set.
    """
    if not os.environ.get("OPENROUTER_API_KEY"):
        return (
            "OPENROUTER_API_KEY is not set — "
            "Claude (Sonnet/Opus) will be unavailable"
        )
    return None


WHISPER_MODEL_DEFAULT = _APP_MODEL_CONFIG["whisper_stt_model"].model_id

VOICES = [
    ("American Female", "af_heart"),
    ("American Male", "am_michael"),
    ("British Female", "bf_emma"),
    ("British Male", "bm_george"),
]


def build_app(
    whisper_model: str,
    ollama_model: str,
    startup_warning: str | None = None,
    tts_enabled: bool = True,
    stt_enabled: bool = True,
    tools_enabled: bool = True,
) -> gr.Blocks:
    """Construct and return the Gradio Blocks application.

    Instantiates the orchestrator, transcriber, and speaker, then wires
    all UI components and event handlers together.

    Args:
        whisper_model: Whisper model size to load for speech input
          (e.g. ``"tiny"``, ``"base"``, ``"medium"``).
        ollama_model: Ollama model name used for routing and simple
          query responses.
        startup_warning: Optional warning shown as the first chatbot
          message, e.g. when Ollama could not be started.
        tts_enabled: When ``False``, skips KokoroSpeaker initialisation
          and hides all TTS-related UI components.
        stt_enabled: When ``False``, skips WhisperTranscriber initialisation
          and hides all STT-related UI components.
        tools_enabled: When ``False``, hides the Tools accordion and passes
          an empty enabled-tools set to every orchestrator call so no tool
          is ever dispatched.

    Returns:
        A configured ``gr.Blocks`` instance ready to launch.
    """
    session_id = uuid4().hex
    orchestrator = Orchestrator(
        ollama_model=ollama_model, session_id=session_id
    )
    transcriber = (
        WhisperTranscriber(model=whisper_model) if stt_enabled else None
    )
    speaker = KokoroSpeaker() if tts_enabled else None

    with gr.Blocks(title="JM Assistant", css=_MODAL_CSS) as demo:
        with gr.Row():
            gr.Markdown("# JM Assistant")
            dark_toggle = gr.Button("🌙 Dark / ☀️ Light", scale=0, min_width=160)

        dark_toggle.click(
            fn=None,
            inputs=None,
            outputs=None,
            js="() => document.documentElement.classList.toggle('dark')",
        )

        with gr.Row():
            input_mode = gr.Radio(
                choices=["text", "speech"] if stt_enabled else ["text"],
                value="text",
                label="Input Mode",
                visible=stt_enabled,
            )
            output_mode = gr.Radio(
                choices=(
                    ["text", "text and speech"] if tts_enabled else ["text"]
                ),
                value="text",
                label="Output Mode",
                visible=tts_enabled,
            )
            height_selector = gr.Dropdown(
                choices=["3 lines", "5 lines", "10 lines", "20 lines"],
                value="3 lines",
                label="Conversation Height",
            )
            show_think = gr.Checkbox(
                value=True,
                label="Show <think> tags",
            )
            voice_selector = gr.Dropdown(
                choices=VOICES,
                value="af_heart",
                label="Voice",
                visible=tts_enabled,
            )
            memory_checkbox = gr.Checkbox(
                value=True,
                label="Memory",
            )

        _LINE_HEIGHTS = {
            "3 lines": 120,
            "5 lines": 200,
            "10 lines": 320,
            "20 lines": 620,
        }

        _initial_history: list = []
        if startup_warning:
            _initial_history = [
                {
                    "role": "assistant",
                    "content": f"**Warning:** {startup_warning}",
                }
            ]

        chatbot = gr.Chatbot(
            label="Previous Conversation",
            height=120,
            value=_initial_history,
        )

        text_input = gr.Textbox(
            placeholder="Type your message...",
            label="Message",
            visible=True,
        )
        submit_btn = gr.Button("Send", visible=True)

        audio_input = gr.Audio(
            sources=["microphone"],
            label="Speak",
            visible=False,
            render=stt_enabled,
        )

        audio_output = gr.Audio(
            label="Response audio",
            autoplay=True,
            visible=False,
            render=tts_enabled,
        )

        image_output = gr.Image(
            label="Output image",
            visible=False,
        )

        image_input = gr.Image(
            sources=["upload", "clipboard"],
            type="pil",
            label="Attach image (optional)",
        )

        history_state = gr.State([])

        def _export_conversation(history: list) -> str | None:
            """Write history to a temp Markdown file and return its path.

            Returns:
                Path to the generated ``.md`` file, or ``None`` if the
                history is empty.
            """
            if not history:
                return None
            md = format_history_as_markdown(history)
            tmp = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".md",
                delete=False,
                encoding="utf-8",
                prefix="conversation_",
            )
            tmp.write(md)
            tmp.close()
            return tmp.name

        with gr.Row():
            gr.DownloadButton(
                label="Export conversation",
                value=_export_conversation,
                inputs=[history_state],
                variant="secondary",
                size="sm",
            )
            clear_btn = gr.Button("Clear", variant="secondary", size="sm")

        usage_md = gr.Markdown("", visible=False)
        session_cost_md = gr.Markdown("", visible=False)

        def _usage_annotation() -> gr.update:
            """Return a gr.update for the per-response usage annotation."""
            usage = orchestrator.last_usage
            if not usage:
                return gr.update(visible=False, value="")
            total = usage.get("total_tokens", 0)
            parts = [f"{total:,} tokens"]
            if orchestrator.last_cost > 0:
                parts.append(f"~${orchestrator.last_cost:.4f}")
            return gr.update(
                visible=True,
                value=f"*({' · '.join(parts)})*",
            )

        def _session_cost_update() -> gr.update:
            """Return a gr.update for the session total cost display."""
            cost = orchestrator.session_cost
            if cost <= 0:
                return gr.update(visible=False, value="")
            return gr.update(
                visible=True,
                value=f"Session cost: ~${cost:.4f}",
            )

        def _memory_status(enabled: bool) -> str:
            if not enabled or orchestrator._memory is None:
                return "Memory: off"
            return f"Memory: on · {orchestrator._memory.count()} records"

        memory_status = gr.Markdown(_memory_status(True))

        memory_checkbox.change(
            fn=_memory_status,
            inputs=memory_checkbox,
            outputs=memory_status,
        )

        # ── Models accordion ────────────────────────────────────────────────
        _model_cfg = _APP_MODEL_CONFIG
        _model_lines = "\n".join(
            f"- **{cfg.display_name}** ({cfg.provider})"
            for cfg in _model_cfg.values()
        )
        with gr.Accordion("Models", open=False):
            gr.Markdown(_model_lines)

        # ── Sessions accordion ───────────────────────────────────────────────
        _sessions_path = "sessions/"
        with gr.Accordion("Sessions", open=False):
            session_status = gr.Markdown("")
            session_name_input = gr.Textbox(
                placeholder="Session name (letters, digits, - _)",
                label="Session name",
                scale=3,
            )
            with gr.Row():
                save_session_btn = gr.Button(
                    "Save", variant="primary", size="sm"
                )
                refresh_sessions_btn = gr.Button(
                    "Refresh list", variant="secondary", size="sm"
                )
            session_dropdown = gr.Dropdown(
                choices=list_sessions(_sessions_path),
                label="Saved sessions",
                value=None,
            )
            with gr.Row():
                load_session_btn = gr.Button(
                    "Load", variant="primary", size="sm"
                )
                delete_session_btn = gr.Button(
                    "Delete", variant="stop", size="sm"
                )

            _pending_overwrite = gr.State(False)
            _pending_delete = gr.State(False)

            def _handle_save(
                name: str,
                history: list,
                pending_ow: bool,
            ) -> tuple:
                """Save current history; warn before overwriting."""
                try:
                    sessions = list_sessions(_sessions_path)
                    if name.strip() in sessions and not pending_ow:
                        return (
                            "*Session already exists — save again"
                            " to overwrite.*",
                            True,
                            gr.update(),
                            gr.update(value="Delete"),
                            False,
                        )
                    save_session(name, history, _sessions_path)
                    return (
                        f"*Saved session '{name.strip()}'.*",
                        False,
                        gr.update(
                            choices=list_sessions(_sessions_path),
                            value=name.strip(),
                        ),
                        gr.update(value="Delete"),
                        False,
                    )
                except ValueError as exc:
                    return (
                        f"*Error: {exc}*",
                        False,
                        gr.update(),
                        gr.update(value="Delete"),
                        False,
                    )

            save_session_btn.click(
                _handle_save,
                inputs=[
                    session_name_input,
                    history_state,
                    _pending_overwrite,
                ],
                outputs=[
                    session_status,
                    _pending_overwrite,
                    session_dropdown,
                    delete_session_btn,
                    _pending_delete,
                ],
            )

            def _handle_load(selected: str | None) -> tuple:
                """Replace current history with the selected session."""
                if not selected:
                    return (
                        gr.update(),
                        gr.update(),
                        "*No session selected.*",
                        gr.update(value="Delete"),
                        False,
                    )
                try:
                    hist = load_session(selected, _sessions_path)
                    return (
                        hist,
                        hist,
                        f"*Loaded session '{selected}'.*",
                        gr.update(value="Delete"),
                        False,
                    )
                except Exception as exc:  # noqa: BLE001
                    return (
                        gr.update(),
                        gr.update(),
                        f"*Error loading session: {exc}*",
                        gr.update(value="Delete"),
                        False,
                    )

            load_session_btn.click(
                _handle_load,
                inputs=[session_dropdown],
                outputs=[
                    chatbot,
                    history_state,
                    session_status,
                    delete_session_btn,
                    _pending_delete,
                ],
            )

            def _handle_delete(selected: str | None, pending: bool) -> tuple:
                """Two-step delete: first click confirms, second executes."""
                if not selected:
                    return (
                        "*No session selected.*",
                        False,
                        gr.update(value="Delete"),
                        gr.update(),
                    )
                if not pending:
                    return (
                        f"*Click Delete again to confirm"
                        f" deleting '{selected}'.*",
                        True,
                        gr.update(value="Confirm delete?"),
                        gr.update(),
                    )
                try:
                    delete_session(selected, _sessions_path)
                    remaining = list_sessions(_sessions_path)
                    return (
                        f"*Deleted session '{selected}'.*",
                        False,
                        gr.update(value="Delete"),
                        gr.update(
                            choices=remaining,
                            value=remaining[0] if remaining else None,
                        ),
                    )
                except Exception as exc:  # noqa: BLE001
                    return (
                        f"*Error: {exc}*",
                        False,
                        gr.update(value="Delete"),
                        gr.update(),
                    )

            delete_session_btn.click(
                _handle_delete,
                inputs=[session_dropdown, _pending_delete],
                outputs=[
                    session_status,
                    _pending_delete,
                    delete_session_btn,
                    session_dropdown,
                ],
            )

            # Cancel pending delete when the selected session changes.
            def _cancel_pending_delete(_selected: str | None) -> tuple:
                return gr.update(value="Delete"), False

            session_dropdown.change(
                _cancel_pending_delete,
                inputs=[session_dropdown],
                outputs=[delete_session_btn, _pending_delete],
            )

            def _refresh_sessions() -> gr.update:
                return gr.update(choices=list_sessions(_sessions_path))

            refresh_sessions_btn.click(
                _refresh_sessions,
                inputs=[],
                outputs=[session_dropdown],
            )

        # ── Tools accordion ─────────────────────────────────────────────────
        _all_tools = REGISTRY.all() if tools_enabled else []
        _max_rank = (
            _TIER_RANK["complex_llm"]
            if os.environ.get("OPENROUTER_API_KEY")
            else _TIER_RANK["simple_llm"]
        )
        _TIER_DISPLAY = {
            "trivial_llm": "Ollama (fast)",
            "simple_llm": "Ollama",
            "advanced_llm": "Claude Sonnet",
            "complex_llm": "Claude Opus",
        }

        def _achievable(tool) -> bool:
            return _TIER_RANK.get(tool.min_tier, 0) <= _max_rank

        _init_enabled: set = (
            {t.name for t in _all_tools if t.default_enabled and _achievable(t)}
            if tools_enabled
            else set()
        )
        _tool_count = len(_all_tools)
        tools_state = gr.State(_init_enabled)

        with gr.Accordion("Tools", open=False, render=tools_enabled):
            tools_status = gr.Markdown(
                f"Tools: {len(_init_enabled)} / {_tool_count} enabled"
            )
            _by_category: dict[str, list] = {}
            for _t in _all_tools:
                _by_category.setdefault(_t.category, []).append(_t)

            _checkboxes: dict[str, gr.Checkbox] = {}
            for _cat, _cat_tools in _by_category.items():
                gr.Markdown(f"**{_cat}**")
                for _tool in _cat_tools:
                    _ok = _achievable(_tool)
                    if _ok:
                        _lbl = _tool.label
                    else:
                        _tier_name = _TIER_DISPLAY.get(
                            _tool.min_tier, _tool.min_tier
                        )
                        _lbl = (
                            f"{_tool.label} — requires {_tier_name} or higher"
                        )
                    _checkboxes[_tool.name] = gr.Checkbox(
                        value=_tool.default_enabled and _ok,
                        label=_lbl,
                        interactive=_ok,
                    )
                    if _tool.name == "image_gen":
                        gr.Markdown(
                            "_Note: enabling Image generation downloads "
                            "~6.7 GB of SDXL-Turbo weights on first use "
                            "and requires a CUDA GPU with ≥7 GB VRAM._"
                        )

        def _make_tool_toggle(name: str):
            """Return a Gradio change callback for the named tool's checkbox.

            The returned function updates the enabled-tools state set and
            the tools status Markdown string when the checkbox value changes.

            Args:
                name: Tool name to add to or remove from the enabled set.

            Returns:
                A ``(val, state) -> (new_state, status_str)`` callable
                suitable for wiring to a ``gr.Checkbox.change`` event.
            """

            def _fn(val: bool, state: set) -> tuple[set, str]:
                new = (state | {name}) if val else (state - {name})
                return new, f"Tools: {len(new)} / {_tool_count} enabled"

            return _fn

        for _name, _cb in _checkboxes.items():
            _tool_def = next(t for t in _all_tools if t.name == _name)
            if _achievable(_tool_def):
                _cb.change(
                    fn=_make_tool_toggle(_name),
                    inputs=[_cb, tools_state],
                    outputs=[tools_state, tools_status],
                )

        # ── Mode switching ──────────────────────────────────────────────────

        def toggle_input_mode(mode):
            """Show text or speech input components based on selected mode.

            Args:
                mode: Input mode string — ``"text"`` or ``"speech"``.

            Returns:
                Three ``gr.update`` dicts controlling visibility of the text
                input, submit button, and audio input respectively.
            """
            text_vis = mode == "text"
            speech_vis = mode == "speech"
            return (
                gr.update(visible=text_vis),
                gr.update(visible=text_vis),
                gr.update(visible=speech_vis),
            )

        def toggle_output_mode(mode):
            """Show or hide the audio output component based on output mode.

            Args:
                mode: Output mode string — ``"text"`` or ``"text and speech"``.

            Returns:
                A ``gr.update`` dict controlling audio output visibility.
            """
            return gr.update(visible=mode == "text and speech")

        input_mode.change(
            toggle_input_mode,
            inputs=input_mode,
            outputs=[text_input, submit_btn, audio_input],
        )

        def set_chatbot_height(choice):
            """Update the chatbot panel height based on the selected size.

            Args:
                choice: One of the keys in ``_LINE_HEIGHTS``
                  (e.g. ``"compact"``, ``"standard"``, ``"large"``).

            Returns:
                A ``gr.update`` dict setting the chatbot ``height`` in pixels.
            """
            return gr.update(height=_LINE_HEIGHTS[choice])

        output_mode.change(
            toggle_output_mode,
            inputs=output_mode,
            outputs=audio_output,
        )
        height_selector.change(
            set_chatbot_height,
            inputs=height_selector,
            outputs=chatbot,
        )

        # ── Code execution confirmation modal ───────────────────────────────
        # Components are created here (before the input handlers that
        # reference them).  Both start hidden; handle_text / handle_audio
        # show them when the orchestrator has a pending code execution.

        _OVERLAY_HTML = (
            '<div style="position:fixed;inset:0;'
            'background:rgba(0,0,0,0.55);z-index:999"></div>'
        )
        modal_overlay = gr.HTML(value=_OVERLAY_HTML, visible=False)

        with gr.Column(
            visible=False, elem_id="code-confirm-modal"
        ) as modal_panel:
            gr.Markdown("### Code Execution Request")
            gr.Markdown(
                "Review the code below, then **Approve** to run it "
                "or **Deny** to cancel."
            )
            modal_code = gr.Code(
                language="python",
                interactive=False,
                label="Pending code",
            )
            with gr.Row():
                approve_btn = gr.Button("Approve", variant="primary")
                deny_btn = gr.Button("Deny", variant="stop")

        _MODAL_OUTPUTS = [modal_overlay, modal_panel, modal_code]

        def _show_modal() -> tuple:
            """Return gr.update tuples to make the modal visible.

            Returns hidden updates when no execution is pending.
            """
            pending = orchestrator._pending_execution
            if pending is None:
                return (
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(value=""),
                )
            return (
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(value=pending["code"]),
            )

        def _hide_modal() -> tuple:
            """Return gr.update tuples to hide the modal."""
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=""),
            )

        def _image_update():
            """Return a gr.update for the image output component.

            Shows the image if the orchestrator has a pending image result,
            then leaves it visible until the next query clears it.
            """
            img = orchestrator._pending_image
            if img is not None:
                return gr.update(visible=True, value=img)
            return gr.update(visible=False, value=None)

        # ── Text input flow ─────────────────────────────────────────────────

        def handle_text(
            query, history, out_mode, show, voice, mem_enabled, tools, img
        ):
            """Handle a text query, streaming the response incrementally.

            Yields intermediate display-history updates as the LLM
            streams its reply, then a final yield that updates all
            outputs (history state, cleared text input, audio, modals).

            Args:
                query: The user's typed message.
                history: Current conversation history.
                out_mode: Output mode — ``"text"`` or
                  ``"text and speech"``.
                show: Whether to show ``<think>`` tags in the response.
                voice: Kokoro voice ID for TTS synthesis.
                mem_enabled: Whether memory reads/writes are active.
                tools: Set of currently enabled tool names from the UI.
                img: Optional PIL Image attached to the query.

            Yields:
                Ten-element tuples matching ``_text_outputs`` — each
                successive yield updates the Gradio UI.
            """
            if not query.strip():
                yield (
                    history,
                    history,
                    "",
                    None,
                    _memory_status(mem_enabled),
                    gr.update(visible=False, value=None),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                ) + _hide_modal()
                return
            for (
                display_history,
                updated_history,
                audio_out,
            ) in stream_process_text(
                query,
                history,
                out_mode,
                show,
                voice,
                orchestrator,
                speaker,
                lambda: orchestrator.last_backend,
                memory_enabled=mem_enabled,
                enabled_tools=tools,
                image=img,
            ):
                if updated_history is None:
                    # Intermediate chunk — only refresh chatbot.
                    yield (
                        display_history,
                        history,
                        gr.update(),
                        gr.update(),
                        gr.update(),
                        gr.update(),
                        gr.update(),
                        gr.update(),
                        gr.update(),
                    ) + _hide_modal()
                else:
                    # Final chunk — update all outputs.
                    yield (
                        display_history,
                        updated_history,
                        "",
                        audio_out,
                        _memory_status(mem_enabled),
                        _image_update(),
                        gr.update(value=None),
                        _usage_annotation(),
                        _session_cost_update(),
                    ) + _show_modal()

        _text_inputs = [
            text_input,
            history_state,
            output_mode,
            show_think,
            voice_selector,
            memory_checkbox,
            tools_state,
            image_input,
        ]
        _text_outputs = [
            chatbot,
            history_state,
            text_input,
            audio_output,
            memory_status,
            image_output,
            image_input,
            usage_md,
            session_cost_md,
        ] + _MODAL_OUTPUTS

        submit_btn.click(
            handle_text,
            inputs=_text_inputs,
            outputs=_text_outputs,
        )
        text_input.submit(
            handle_text,
            inputs=_text_inputs,
            outputs=_text_outputs,
        )

        # ── Speech input flow ───────────────────────────────────────────────
        # Transcribe the recording and dispatch to the orchestrator immediately.
        # The transcribed query appears in the chat as the user message.
        # audio_input is reset to None after processing so the record button
        # becomes available again immediately.  The re-fired change event
        # (audio_data=None) returns gr.update() for audio_output so playback
        # is not interrupted.

        def handle_audio(
            audio_data, history, out_mode, show, voice, mem_enabled, tools, img
        ):
            """Handle a microphone recording, streaming the response.

            Ignores ``None`` audio (re-fired after recorder reset).
            Delegates to ``stream_process_audio`` for validation,
            transcription, and LLM streaming.  The recorder is reset
            on the final yield so playback is not interrupted.

            Args:
                audio_data: ``(sample_rate, audio_array)`` tuple from
                  ``gr.Audio``, or ``None`` when the recorder is reset.
                history: Current conversation history.
                out_mode: Output mode — ``"text"`` or
                  ``"text and speech"``.
                show: Whether to show ``<think>`` tags in the response.
                voice: Kokoro voice ID for TTS synthesis.
                mem_enabled: Whether memory reads/writes are active.
                tools: Set of currently enabled tool names from the UI.
                img: Optional PIL Image attached to the query.

            Yields:
                Ten-element tuples matching the audio ``outputs`` list.
            """
            if audio_data is None:
                # Re-fired by our own reset — leave everything unchanged.
                yield (
                    gr.update(),
                    history,
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                ) + _hide_modal()
                return
            try:
                for (
                    display_history,
                    updated_history,
                    audio_out,
                ) in stream_process_audio(
                    audio_data,
                    history,
                    out_mode,
                    show,
                    voice,
                    transcriber,
                    orchestrator,
                    speaker,
                    memory_enabled=mem_enabled,
                    enabled_tools=tools,
                ):
                    if updated_history is None:
                        # Intermediate chunk — only refresh chatbot.
                        yield (
                            display_history,
                            history,
                            gr.update(),
                            gr.update(),
                            gr.update(),
                            gr.update(),
                            gr.update(),
                            gr.update(),
                            gr.update(),
                        ) + _hide_modal()
                    else:
                        # Final — update all outputs and reset recorder.
                        yield (
                            display_history,
                            updated_history,
                            audio_out,
                            gr.update(value=None),
                            _memory_status(mem_enabled),
                            _image_update(),
                            gr.update(value=None),
                            _usage_annotation(),
                            _session_cost_update(),
                        ) + _show_modal()
            except Exception as exc:  # noqa: BLE001
                err_display = list(history) + [
                    {"role": "assistant", "content": f"(Error: {exc})"}
                ]
                yield (
                    err_display,
                    history,
                    None,
                    gr.update(value=None),
                    _memory_status(mem_enabled),
                    gr.update(visible=False, value=None),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                ) + _hide_modal()

        audio_input.change(
            handle_audio,
            inputs=[
                audio_input,
                history_state,
                output_mode,
                show_think,
                voice_selector,
                memory_checkbox,
                tools_state,
                image_input,
            ],
            outputs=[
                chatbot,
                history_state,
                audio_output,
                audio_input,
                memory_status,
                image_output,
                image_input,
                usage_md,
                session_cost_md,
            ]
            + _MODAL_OUTPUTS,
        )

        def handle_clear():
            """Clear the conversation and reset session cost."""
            orchestrator.reset_session_cost()
            return (
                [],
                [],
                "",
                gr.update(visible=False, value=""),
                gr.update(visible=False, value=""),
            )

        clear_btn.click(
            handle_clear,
            inputs=[],
            outputs=[
                chatbot,
                history_state,
                text_input,
                usage_md,
                session_cost_md,
            ],
        )

        # ── Modal button handlers ───────────────────────────────────────────

        def handle_approve(history: list) -> tuple:
            """Execute pending code and append the result to the chat.

            Args:
                history: Current conversation history state.

            Returns:
                Updated ``(chatbot, history_state, overlay, modal,
                code)`` tuple.
            """
            result = orchestrator.confirm_pending()
            msg = {
                "role": "assistant",
                "content": f"**Code output:**\n```\n{result}\n```",
            }
            updated = list(history) + [msg]
            return (updated, updated) + _hide_modal()

        def handle_deny(history: list) -> tuple:
            """Cancel pending code and append a cancellation notice.

            Args:
                history: Current conversation history state.

            Returns:
                Updated ``(chatbot, history_state, overlay, modal,
                code)`` tuple.
            """
            orchestrator.cancel_pending()
            msg = {
                "role": "assistant",
                "content": "Code execution cancelled.",
            }
            updated = list(history) + [msg]
            return (updated, updated) + _hide_modal()

        approve_btn.click(
            handle_approve,
            inputs=[history_state],
            outputs=[chatbot, history_state] + _MODAL_OUTPUTS,
        )
        deny_btn.click(
            handle_deny,
            inputs=[history_state],
            outputs=[chatbot, history_state] + _MODAL_OUTPUTS,
        )

        # ── Reminder timer ──────────────────────────────────────────────────
        # Poll for due reminders every 10 seconds and inject them into the
        # chat as assistant messages so the user sees them immediately.

        def _check_reminders(history: list) -> tuple:
            """Fire any due reminders into the chat history.

            Args:
                history: The current conversation history state.

            Returns:
                Updated ``(chatbot, history_state)`` tuple, or
                ``gr.update()`` if no reminders are due.
            """
            due = REMINDER_STORE.get_due(session_id)
            if not due:
                return gr.update(), history
            new_msgs = [
                {
                    "role": "assistant",
                    "content": f"\u23f0 Reminder: {r.message}",
                }
                for r in due
            ]
            updated = list(history) + new_msgs
            return updated, updated

        reminder_timer = gr.Timer(value=10, active=tools_enabled)
        reminder_timer.tick(
            fn=_check_reminders,
            inputs=[history_state],
            outputs=[chatbot, history_state],
        )

    return demo


def main():
    """Parse CLI arguments and launch the Gradio app."""
    parser = argparse.ArgumentParser(description="JM Assistant")
    parser.add_argument(
        "--ollama-model",
        default=OLLAMA_MODEL_DEFAULT,
        help="Ollama model name",
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Disable text-to-speech output",
    )
    parser.add_argument(
        "--no-stt",
        action="store_true",
        help="Disable speech-to-text input",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Disable all tool use and hide the Tools accordion",
    )
    args = parser.parse_args()
    suppress_connection_reset_errors()
    startup_warnings = []
    kokoro_warn = None if args.no_tts else check_kokoro_files()
    for warn in (
        _ensure_ollama(),
        _check_ollama_models(OLLAMA_FAST_MODEL, args.ollama_model),
        _check_api_key(),
        kokoro_warn,
    ):
        if warn:
            print(f"Warning: {warn}")
            startup_warnings.append(warn)
    startup_warning = "\n\n".join(startup_warnings) or None
    demo = build_app(
        WHISPER_MODEL_DEFAULT,
        args.ollama_model,
        startup_warning,
        tts_enabled=not args.no_tts,
        stt_enabled=not args.no_stt,
        tools_enabled=not args.no_tools,
    )
    demo.launch()
