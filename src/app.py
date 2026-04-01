"""Gradio web interface for the JM Assistant chatbot.

Provides a Blocks-based UI with text and speech input/output modes,
dark/light theme toggle, configurable conversation height, and a toggle
to show or hide LLM chain-of-thought ``<think>`` tags.
"""

import argparse
import subprocess
import time

import gradio as gr
import ollama

from src.helpers import (
    strip_markdown,
    strip_think_tags,
    suppress_connection_reset_errors,
    to_wav_bytes,
)
from src.orchestrator import Orchestrator
from src.process_audio import process_audio
from src.speech_input import WhisperTranscriber
from src.speech_output import KokoroSpeaker

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
    orchestrator = Orchestrator(ollama_model=ollama_model)
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

        def _prefix_last_reply(
            history: list, response: str, show: bool
        ) -> list:
            """Prepend the backend label to the last assistant message.

            Args:
                history: Updated history returned by the orchestrator,
                  whose last entry is the raw assistant response.
                response: The raw assistant response text.
                show: If ``False``, ``<think>`` blocks are stripped before
                  display.

            Returns:
                A copy of ``history`` with the last entry's content
                replaced by a labelled, optionally filtered string.
            """
            content = response if show else strip_think_tags(response)
            display = list(history)
            display[-1] = {
                "role": "assistant",
                "content": f"**{orchestrator.last_backend}:** {content}",
            }
            return display

        def handle_text(query, history, out_mode, show, voice):
            """Handle a text query submitted via the text input or send button.

            Args:
                query: The user's typed message.
                history: Current conversation history.
                out_mode: Output mode — ``"text"`` or ``"text and speech"``.
                show: Whether to show ``<think>`` tags in the response.
                voice: Kokoro voice ID for TTS synthesis.

            Returns:
                A tuple of ``(display_history, history_state, cleared_input,
                audio_out)`` suitable for Gradio's ``outputs`` list.
            """
            if not query.strip():
                return history, history, "", None
            try:
                response, updated_history = orchestrator.respond(query, history)
            except ConnectionError:
                err = (
                    "Ollama is not running — "
                    "please start it with `ollama serve`"
                )
                err_display = list(history) + [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": f"(Error: {err})"},
                ]
                return err_display, history, "", None
            display_history = _prefix_last_reply(
                updated_history, response, show
            )
            audio_out = None
            if out_mode == "text and speech":
                speech_text = response if show else strip_think_tags(response)
                arr, sr = speaker.synthesize(
                    strip_markdown(speech_text), voice=voice
                )
                audio_out = to_wav_bytes(arr, sr)
            return display_history, updated_history, "", audio_out

        submit_btn.click(
            handle_text,
            inputs=[
                text_input,
                history_state,
                output_mode,
                show_think,
                voice_selector,
            ],
            outputs=[chatbot, history_state, text_input, audio_output],
        )
        text_input.submit(
            handle_text,
            inputs=[
                text_input,
                history_state,
                output_mode,
                show_think,
                voice_selector,
            ],
            outputs=[chatbot, history_state, text_input, audio_output],
        )

        # ── Speech input flow ───────────────────────────────────────────────
        # Transcribe the recording and dispatch to the orchestrator immediately.
        # The transcribed query appears in the chat as the user message.
        # audio_input is reset to None after processing so the record button
        # becomes available again immediately.  The re-fired change event
        # (audio_data=None) returns gr.update() for audio_output so playback
        # is not interrupted.

        def handle_audio(audio_data, history, out_mode, show, voice):
            if audio_data is None:
                # Re-fired by our own reset — leave everything unchanged.
                return (
                    gr.update(),
                    history,
                    gr.update(),
                    gr.update(),
                )
            display_history, updated_history, audio_out = process_audio(
                audio_data,
                history,
                out_mode,
                show,
                voice,
                transcriber,
                orchestrator,
                speaker,
            )
            return (
                display_history,
                updated_history,
                audio_out,
                gr.update(value=None),  # reset recorder
            )

        audio_input.change(
            handle_audio,
            inputs=[
                audio_input,
                history_state,
                output_mode,
                show_think,
                voice_selector,
            ],
            outputs=[chatbot, history_state, audio_output, audio_input],
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
    warning = _ensure_ollama()
    if warning:
        print(f"Warning: {warning}")
    demo = build_app(args.whisper_model, args.ollama_model, warning)
    demo.launch()
