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
        gr.Markdown("# JM Assistant")

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

        chatbot = gr.Chatbot(label="Chat")
        backend_label = gr.Markdown("")

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
        output_mode.change(
            toggle_output_mode,
            inputs=output_mode,
            outputs=audio_output,
        )

        # ── Text input flow ─────────────────────────────────────────────────

        def handle_text(query, history, out_mode):
            if not query.strip():
                return history, history, "", None, ""
            response, updated_history = orchestrator.respond(query, history)
            backend = f"*Answered by: {orchestrator.last_backend}*"
            audio_out = None
            if out_mode in ("speech", "dual"):
                arr, sr = speaker.synthesize(response)
                audio_out = (sr, arr)
            return updated_history, updated_history, "", audio_out, backend

        submit_btn.click(
            handle_text,
            inputs=[text_input, history_state, output_mode],
            outputs=[
                chatbot,
                history_state,
                text_input,
                audio_output,
                backend_label,
            ],
        )
        text_input.submit(
            handle_text,
            inputs=[text_input, history_state, output_mode],
            outputs=[
                chatbot,
                history_state,
                text_input,
                audio_output,
                backend_label,
            ],
        )

        # ── Speech input flow ───────────────────────────────────────────────

        def handle_audio(audio_data, history, out_mode):
            if audio_data is None:
                return history, history, None, ""
            sample_rate, audio_array = audio_data
            float_audio = audio_array.astype(np.float32) / 32768.0
            query = transcriber.transcribe(float_audio, sample_rate)
            response, updated_history = orchestrator.respond(query, history)
            backend = f"*Answered by: {orchestrator.last_backend}*"
            audio_out = None
            if out_mode in ("speech", "dual"):
                arr, sr = speaker.synthesize(response)
                audio_out = (sr, arr)
            return updated_history, updated_history, audio_out, backend

        audio_input.change(
            handle_audio,
            inputs=[audio_input, history_state, output_mode],
            outputs=[chatbot, history_state, audio_output, backend_label],
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
