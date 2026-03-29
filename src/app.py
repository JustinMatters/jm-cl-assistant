import argparse

import gradio as gr
import numpy as np

from src.orchestrator import Orchestrator
from src.speech_input import WhisperTranscriber
from src.speech_output import KokoroSpeaker

OLLAMA_MODEL_DEFAULT = "sam860/deepseek-r1-0528-qwen3:8b"
WHISPER_MODEL_DEFAULT = "medium"


def build_app(whisper_model: str, ollama_model: str) -> gr.Blocks:
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
                choices=["text", "speech", "dual"],
                value="text",
                label="Output Mode",
            )
            height_selector = gr.Dropdown(
                choices=["3 lines", "5 lines", "10 lines", "20 lines"],
                value="3 lines",
                label="Conversation Height",
            )

        _LINE_HEIGHTS = {
            "3 lines": 120,
            "5 lines": 200,
            "10 lines": 320,
            "20 lines": 620,
        }

        chatbot = gr.Chatbot(label="Previous Conversation", height=120)

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
            return gr.update(visible=mode in ("speech", "dual"))

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

        def _prefix_last_reply(history: list, response: str) -> list:
            display = list(history)
            display[-1] = {
                "role": "assistant",
                "content": f"**{orchestrator.last_backend}:** {response}",
            }
            return display

        def handle_text(query, history, out_mode):
            if not query.strip():
                return history, history, "", None
            response, updated_history = orchestrator.respond(query, history)
            display_history = _prefix_last_reply(updated_history, response)
            audio_out = None
            if out_mode in ("speech", "dual"):
                arr, sr = speaker.synthesize(response)
                audio_out = (sr, arr)
            return display_history, updated_history, "", audio_out

        submit_btn.click(
            handle_text,
            inputs=[text_input, history_state, output_mode],
            outputs=[chatbot, history_state, text_input, audio_output],
        )
        text_input.submit(
            handle_text,
            inputs=[text_input, history_state, output_mode],
            outputs=[chatbot, history_state, text_input, audio_output],
        )

        # ── Speech input flow ───────────────────────────────────────────────

        def handle_audio(audio_data, history, out_mode):
            if audio_data is None:
                return history, history, None
            sample_rate, audio_array = audio_data
            float_audio = audio_array.astype(np.float32) / 32768.0
            query = transcriber.transcribe(float_audio, sample_rate)
            response, updated_history = orchestrator.respond(query, history)
            display_history = _prefix_last_reply(updated_history, response)
            audio_out = None
            if out_mode in ("speech", "dual"):
                arr, sr = speaker.synthesize(response)
                audio_out = (sr, arr)
            return display_history, updated_history, audio_out

        audio_input.change(
            handle_audio,
            inputs=[audio_input, history_state, output_mode],
            outputs=[chatbot, history_state, audio_output],
        )

    return demo


def main():
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
    demo = build_app(args.whisper_model, args.ollama_model)
    demo.launch()
