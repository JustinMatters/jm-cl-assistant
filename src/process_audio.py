"""Audio input processing pipeline for the JM Assistant.

Validates, normalises, and transcribes a browser microphone recording,
then dispatches to the orchestrator and optionally synthesises a spoken
response.  Extracted from the Gradio event handler so the logic can be
unit-tested without Gradio.
"""

import numpy as np

from src.helpers import strip_markdown, strip_think_tags, to_wav_bytes


def _audio_err(history: list, msg: str) -> list:
    """Append an error note to the display history only.

    The underlying ``history_state`` is left unchanged so the error does
    not pollute the conversation history passed to the LLM.

    Args:
        history: Current conversation history.
        msg: Short error description shown to the user.

    Returns:
        A new list with an assistant error bubble appended.
    """
    return list(history) + [
        {"role": "assistant", "content": f"(Audio error: {msg})"}
    ]


def process_audio(
    audio_data,
    history: list,
    out_mode: str,
    show: bool,
    voice: str,
    transcriber,
    orchestrator,
    speaker,
) -> tuple[list, list, bytes | None]:
    """Validate, transcribe, and respond to audio input.

    Args:
        audio_data: ``(sample_rate, audio_array)`` tuple from ``gr.Audio``,
          or ``None`` if no recording is present.
        history: Current conversation history.
        out_mode: Output mode — ``"text"`` or ``"text and speech"``.
        show: Whether to show ``<think>`` tags in the response.
        voice: Kokoro voice ID for TTS synthesis.
        transcriber: ``WhisperTranscriber`` instance.
        orchestrator: ``Orchestrator`` instance.
        speaker: ``KokoroSpeaker`` instance.

    Returns:
        ``(display_history, history_state, audio_out)`` — the same tuple
        shape as the ``audio_input.change`` outputs in ``build_app``.
    """
    if audio_data is None:
        return history, history, None

    sample_rate, audio_array = audio_data

    # ── Input validation ─────────────────────────────────────────────────
    if audio_array is None or sample_rate is None:
        return history, history, None

    if len(audio_array) == 0:
        return history, history, None

    is_numeric = isinstance(sample_rate, (int, float))
    sr_val = int(sample_rate) if is_numeric else 0
    if sr_val <= 0:
        return (
            _audio_err(history, "invalid sample rate — please try again"),
            history,
            None,
        )

    # ── Normalise to float32 [-1, 1] ─────────────────────────────────────
    # Browsers typically send int16; some may send float32 already
    # normalised.  Dividing float32 by 32768 would produce near-silence
    # so we check dtype before scaling.
    if audio_array.dtype in (np.float32, np.float64):
        float_audio = audio_array.astype(np.float32)
    elif audio_array.dtype == np.int32:
        float_audio = audio_array.astype(np.float32) / 2_147_483_648.0
    else:
        # int16 (most common) and any other integer dtype
        float_audio = audio_array.astype(np.float32) / 32_768.0

    # ── Transcription ─────────────────────────────────────────────────────
    try:
        query = transcriber.transcribe(float_audio, sr_val)
    except Exception as exc:
        return (
            _audio_err(history, f"transcription failed: {exc}"),
            history,
            None,
        )

    if not query.strip():
        return (
            _audio_err(
                history,
                "could not understand audio — please try again",
            ),
            history,
            None,
        )

    # ── Orchestrator dispatch ─────────────────────────────────────────────
    response, updated_history = orchestrator.respond(query, history)
    content = response if show else strip_think_tags(response)
    display_history = list(updated_history)
    display_history[-1] = {
        "role": "assistant",
        "content": f"**{orchestrator.last_backend}:** {content}",
    }

    audio_out = None
    if out_mode == "text and speech":
        speech_text = response if show else strip_think_tags(response)
        arr, sr = speaker.synthesize(strip_markdown(speech_text), voice=voice)
        audio_out = to_wav_bytes(arr, sr)

    return display_history, updated_history, audio_out
