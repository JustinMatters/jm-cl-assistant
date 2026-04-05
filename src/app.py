"""Gradio web interface for the JM Assistant chatbot.

Provides a Blocks-based UI with text and speech input/output modes,
dark/light theme toggle, configurable conversation height, and a toggle
to show or hide LLM chain-of-thought ``<think>`` tags.
"""

import argparse
import os
import subprocess
import time
from uuid import uuid4

import gradio as gr
import ollama

from src.helpers import suppress_connection_reset_errors
from src.orchestrator import Orchestrator
from src.process_audio import process_audio
from src.process_text import process_text
from src.router import OLLAMA_FAST_MODEL
from src.speech_input import WhisperTranscriber
from src.speech_output import KokoroSpeaker, check_kokoro_files
from src.tools.registry import _TIER_RANK, REGISTRY
from src.tools.reminders import REMINDER_STORE

OLLAMA_MODEL_DEFAULT = "sam860/deepseek-r1-0528-qwen3:8b"


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


WHISPER_MODEL_DEFAULT = "medium"

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

    Returns:
        A configured ``gr.Blocks`` instance ready to launch.
    """
    session_id = uuid4().hex
    orchestrator = Orchestrator(
        ollama_model=ollama_model, session_id=session_id
    )
    transcriber = WhisperTranscriber(model=whisper_model)
    speaker = KokoroSpeaker()

    with gr.Blocks(title="JM Assistant") as demo:
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
                choices=["text", "speech"],
                value="text",
                label="Input Mode",
            )
            output_mode = gr.Radio(
                choices=["text", "text and speech"],
                value="text",
                label="Output Mode",
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
        )

        audio_output = gr.Audio(
            label="Response audio",
            autoplay=True,
            visible=False,
        )

        history_state = gr.State([])

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

        # ── Tools accordion ─────────────────────────────────────────────────
        _all_tools = REGISTRY.all()
        _max_rank = (
            _TIER_RANK["complex_opus"]
            if os.environ.get("OPENROUTER_API_KEY")
            else _TIER_RANK["simple_ollama"]
        )
        _TIER_DISPLAY = {
            "trivial_ollama": "Ollama (fast)",
            "simple_ollama": "Ollama",
            "complex_sonnet": "Claude Sonnet",
            "complex_opus": "Claude Opus",
        }

        def _achievable(tool) -> bool:
            return _TIER_RANK.get(tool.min_tier, 0) <= _max_rank

        _init_enabled = {
            t.name for t in _all_tools if t.default_enabled and _achievable(t)
        }
        _tool_count = len(_all_tools)
        tools_state = gr.State(_init_enabled)

        with gr.Accordion("Tools", open=False):
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
            text_vis = mode == "text"
            speech_vis = mode == "speech"
            return (
                gr.update(visible=text_vis),
                gr.update(visible=text_vis),
                gr.update(visible=speech_vis),
            )

        def toggle_output_mode(mode):
            return gr.update(visible=mode == "text and speech")

        input_mode.change(
            toggle_input_mode,
            inputs=input_mode,
            outputs=[text_input, submit_btn, audio_input],
        )

        def set_chatbot_height(choice):
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

        # ── Text input flow ─────────────────────────────────────────────────

        def handle_text(
            query, history, out_mode, show, voice, mem_enabled, tools
        ):
            """Handle a text query submitted via the text input or send button.

            Args:
                query: The user's typed message.
                history: Current conversation history.
                out_mode: Output mode — ``"text"`` or ``"text and speech"``.
                show: Whether to show ``<think>`` tags in the response.
                voice: Kokoro voice ID for TTS synthesis.
                mem_enabled: Whether memory reads/writes are active.
                tools: Set of currently enabled tool names from the UI.

            Returns:
                A tuple of ``(display_history, history_state, cleared_input,
                audio_out, memory_status)`` suitable for Gradio's outputs.
            """
            if not query.strip():
                return history, history, "", None, _memory_status(mem_enabled)
            display_history, updated_history, audio_out = process_text(
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
            )
            return (
                display_history,
                updated_history,
                "",
                audio_out,
                _memory_status(mem_enabled),
            )

        submit_btn.click(
            handle_text,
            inputs=[
                text_input,
                history_state,
                output_mode,
                show_think,
                voice_selector,
                memory_checkbox,
                tools_state,
            ],
            outputs=[
                chatbot,
                history_state,
                text_input,
                audio_output,
                memory_status,
            ],
        )
        text_input.submit(
            handle_text,
            inputs=[
                text_input,
                history_state,
                output_mode,
                show_think,
                voice_selector,
                memory_checkbox,
                tools_state,
            ],
            outputs=[
                chatbot,
                history_state,
                text_input,
                audio_output,
                memory_status,
            ],
        )

        # ── Speech input flow ───────────────────────────────────────────────
        # Transcribe the recording and dispatch to the orchestrator immediately.
        # The transcribed query appears in the chat as the user message.
        # audio_input is reset to None after processing so the record button
        # becomes available again immediately.  The re-fired change event
        # (audio_data=None) returns gr.update() for audio_output so playback
        # is not interrupted.

        def handle_audio(
            audio_data, history, out_mode, show, voice, mem_enabled, tools
        ):
            """Handle a microphone recording submitted via the audio input.

            Ignores ``None`` audio (re-fired after recorder reset). On
            success delegates to ``process_audio`` and resets the recorder.
            On failure appends an error bubble and still resets the recorder
            so the UI remains usable.

            Args:
                audio_data: ``(sample_rate, audio_array)`` tuple from
                  ``gr.Audio``, or ``None`` when the recorder is reset.
                history: Current conversation history.
                out_mode: Output mode — ``"text"`` or ``"text and speech"``.
                show: Whether to show ``<think>`` tags in the response.
                voice: Kokoro voice ID for TTS synthesis.
                mem_enabled: Whether memory reads/writes are active.
                tools: Set of currently enabled tool names from the UI.

            Returns:
                A tuple of ``(chatbot, history_state, audio_output,
                audio_input, memory_status)`` suitable for Gradio's outputs.
            """
            if audio_data is None:
                # Re-fired by our own reset — leave everything unchanged.
                return (
                    gr.update(),
                    history,
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )
            try:
                display_history, updated_history, audio_out = process_audio(
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
                )
                return (
                    display_history,
                    updated_history,
                    audio_out,
                    gr.update(value=None),  # reset recorder
                    _memory_status(mem_enabled),
                )
            except Exception as exc:  # noqa: BLE001
                err_display = list(history) + [
                    {
                        "role": "assistant",
                        "content": f"(Error: {exc})",
                    }
                ]
                return (
                    err_display,
                    history,
                    None,
                    gr.update(value=None),  # reset recorder
                    _memory_status(mem_enabled),
                )

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
            ],
            outputs=[
                chatbot,
                history_state,
                audio_output,
                audio_input,
                memory_status,
            ],
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

        reminder_timer = gr.Timer(value=10, active=True)
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
        "--whisper-model",
        default=WHISPER_MODEL_DEFAULT,
        help="Whisper model size (default: medium)",
    )
    parser.add_argument(
        "--ollama-model",
        default=OLLAMA_MODEL_DEFAULT,
        help="Ollama model name",
    )
    args = parser.parse_args()
    suppress_connection_reset_errors()
    startup_warnings = []
    for warn in (
        _ensure_ollama(),
        _check_ollama_models(OLLAMA_FAST_MODEL, args.ollama_model),
        _check_api_key(),
        check_kokoro_files(),
    ):
        if warn:
            print(f"Warning: {warn}")
            startup_warnings.append(warn)
    startup_warning = "\n\n".join(startup_warnings) or None
    demo = build_app(args.whisper_model, args.ollama_model, startup_warning)
    demo.launch()
