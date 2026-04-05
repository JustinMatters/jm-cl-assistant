"""Text query processing pipeline for the JM Assistant.

Dispatches a text query to the orchestrator, applies think-tag filtering,
and optionally synthesises a spoken response.  Extracted from the Gradio
event handler so the logic can be unit-tested without Gradio.
"""

from src.helpers import strip_markdown, strip_think_tags, to_wav_bytes


def process_text(
    query: str,
    history: list,
    out_mode: str,
    show: bool,
    voice: str,
    orchestrator,
    speaker,
    last_backend_fn,
    memory_enabled: bool = True,
    enabled_tools: set | None = None,
) -> tuple[list, list, bytes | None]:
    """Dispatch a text query and return updated history and optional audio.

    Wraps all downstream calls in a broad exception handler so any crash
    surfaces as an error bubble in the chat rather than breaking the UI.

    Args:
        query: The user's typed message.
        history: Current conversation history.
        out_mode: Output mode — ``"text"`` or ``"text and speech"``.
        show: Whether to show ``<think>`` tags in the response.
        voice: Kokoro voice ID for TTS synthesis.
        orchestrator: ``Orchestrator`` instance.
        speaker: ``KokoroSpeaker`` instance.
        last_backend_fn: Zero-argument callable that returns the backend
          label string used to prefix the assistant reply (e.g.
          ``lambda: orchestrator.last_backend``).

    Returns:
        ``(display_history, history_state, audio_out)`` — the same tuple
        shape as the ``submit_btn.click`` outputs in ``build_app``.
        On error, ``history_state`` is the original unchanged history and
        ``audio_out`` is ``None``.
    """
    try:
        response, updated_history = orchestrator.respond(
            query,
            history,
            memory_enabled=memory_enabled,
            enabled_tools=enabled_tools,
        )
        content = response if show else strip_think_tags(response)
        display_history = list(updated_history)
        display_history[-1] = {
            "role": "assistant",
            "content": f"**{last_backend_fn()}:** {content}",
        }
        audio_out = None
        if out_mode == "text and speech":
            speech_text = response if show else strip_think_tags(response)
            arr, sr = speaker.synthesize(
                strip_markdown(speech_text), voice=voice
            )
            audio_out = to_wav_bytes(arr, sr)
        return display_history, updated_history, audio_out
    except Exception as exc:  # noqa: BLE001
        err_display = list(history) + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": f"(Error: {exc})"},
        ]
        return err_display, history, None
