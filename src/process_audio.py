"""Audio input processing pipeline for the JM Assistant.

Validates, normalises, and transcribes a browser microphone recording,
then dispatches to the orchestrator and optionally synthesises a spoken
response.  Extracted from the Gradio event handler so the logic can be
unit-tested without Gradio.
"""

from collections.abc import Iterator

import numpy as np

from src.helpers import strip_markdown, strip_think_tags, to_wav_bytes
from src.process_text import stream_process_text


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
    memory_enabled: bool = True,
    enabled_tools: set | None = None,
    image=None,
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
        memory_enabled: When ``False``, memory reads and writes are
          skipped for this call.
        enabled_tools: Set of tool names currently active in the UI.
          ``None`` falls back to per-tool ``default_enabled`` flags.

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
    try:
        response, updated_history = orchestrator.respond(
            query,
            history,
            memory_enabled=memory_enabled,
            enabled_tools=enabled_tools,
            image=image,
        )
    except ConnectionError:
        return (
            _audio_err(
                history,
                "Ollama is not running — please start it with `ollama serve`",
            ),
            history,
            None,
        )
    content = response if show else strip_think_tags(response)
    display_history = list(updated_history)
    display_history[-1] = {
        "role": "assistant",
        "content": f"**{orchestrator.last_backend}:** {content}",
    }

    audio_out = None
    if speaker is not None and out_mode == "text and speech":
        speech_text = response if show else strip_think_tags(response)
        arr, sr = speaker.synthesize(strip_markdown(speech_text), voice=voice)
        audio_out = to_wav_bytes(arr, sr)

    return display_history, updated_history, audio_out


def stream_process_audio(
    audio_data,
    history: list,
    out_mode: str,
    show: bool,
    voice: str,
    transcriber,
    orchestrator,
    speaker,
    memory_enabled: bool = True,
    enabled_tools: set | None = None,
) -> Iterator[tuple[list, list | None, bytes | None]]:
    """Validate, transcribe, and stream a response to audio input.

    Performs the same validation and normalisation as ``process_audio``,
    then delegates to ``stream_process_text`` for the LLM streaming path.
    Yields nothing on silent or invalid input.  Error yields produce a
    single final tuple with the original history unchanged.

    Args:
        audio_data: ``(sample_rate, audio_array)`` tuple from
          ``gr.Audio``, or ``None`` if no recording is present.
        history: Current conversation history.
        out_mode: Output mode — ``"text"`` or ``"text and speech"``.
        show: Whether to show ``<think>`` tags in the response.
        voice: Kokoro voice ID for TTS synthesis.
        transcriber: ``WhisperTranscriber`` instance.
        orchestrator: ``Orchestrator`` instance.
        speaker: ``KokoroSpeaker`` instance.
        memory_enabled: When ``False``, memory reads/writes are skipped.
        enabled_tools: Set of tool names currently active in the UI.
          ``None`` falls back to per-tool ``default_enabled`` flags.

    Yields:
        ``(display_history, updated_history_or_none, audio_out)`` —
        same contract as ``stream_process_text``.  Yields nothing when
        ``audio_data`` is ``None`` or the audio array is empty.
    """
    if audio_data is None:
        return

    sample_rate, audio_array = audio_data
    if audio_array is None or sample_rate is None or len(audio_array) == 0:
        return

    is_numeric = isinstance(sample_rate, (int, float))
    sr_val = int(sample_rate) if is_numeric else 0
    if sr_val <= 0:
        yield (
            _audio_err(history, "invalid sample rate — please try again"),
            history,
            None,
        )
        return

    if audio_array.dtype in (np.float32, np.float64):
        float_audio = audio_array.astype(np.float32)
    elif audio_array.dtype == np.int32:
        float_audio = audio_array.astype(np.float32) / 2_147_483_648.0
    else:
        float_audio = audio_array.astype(np.float32) / 32_768.0

    try:
        query = transcriber.transcribe(float_audio, sr_val)
    except Exception as exc:
        yield (
            _audio_err(history, f"transcription failed: {exc}"),
            history,
            None,
        )
        return

    if not query.strip():
        yield (
            _audio_err(
                history,
                "could not understand audio — please try again",
            ),
            history,
            None,
        )
        return

    yield from stream_process_text(
        query,
        history,
        out_mode,
        show,
        voice,
        orchestrator,
        speaker,
        lambda: orchestrator.last_backend,
        memory_enabled=memory_enabled,
        enabled_tools=enabled_tools,
    )
