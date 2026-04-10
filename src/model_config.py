"""Model configuration loader for the JM Assistant.

Reads ``models.json`` at the project root and exposes a typed ``ModelConfig``
dataclass for each logical model role.  Falls back to safe built-in defaults
if the file is absent, unreadable, or structurally invalid so the application
always starts cleanly.

Seven roles are defined:

- ``trivial_llm`` — fast local model for routing and trivial queries
- ``simple_llm`` — capable local model for simple queries
- ``advanced_llm`` — cloud model for analysis and structured writing
- ``complex_llm`` — cloud model for expert / multi-domain problems
- ``vector_db_embedding`` — embedding model for the RAG memory store
- ``whisper_stt_model`` — Whisper model size for speech-to-text
- ``diffusers_image_gen_model`` — diffusers model for image generation
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

_KNOWN_ROLES = frozenset(
    {
        "trivial_llm",
        "simple_llm",
        "advanced_llm",
        "complex_llm",
        "vector_db_embedding",
        "whisper_stt_model",
        "diffusers_image_gen_model",
    }
)

_KNOWN_PROVIDERS = frozenset({"ollama", "openrouter", "local"})

_REQUIRED_FIELDS = frozenset(
    {"role", "provider", "model_id", "display_name", "vision"}
)


@dataclass
class ModelConfig:
    """Configuration for a single model role.

    Args:
        role: Logical role identifier, e.g. ``"trivial_llm"``.
        provider: Where the model runs — ``"ollama"``, ``"openrouter"``,
          or ``"local"`` (a local Python library).
        model_id: Identifier passed to the provider, e.g. an Ollama model
          name, an OpenRouter model string, a Whisper size, or a
          HuggingFace repo ID.
        display_name: Human-readable label shown in the UI.
        vision: Whether this model accepts image inputs.
        diffusers_max_image_dimension: For ``diffusers_image_gen_model``
          only — maximum pixel size for generated or downloaded images.
          Defaults to 512.

    Attributes:
        role: Logical role identifier.
        provider: Provider name.
        model_id: Provider-specific model identifier.
        display_name: Human-readable label.
        vision: True if the model accepts image inputs.
        diffusers_max_image_dimension: Max image dimension in pixels.
    """

    role: str
    provider: str
    model_id: str
    display_name: str
    vision: bool
    diffusers_max_image_dimension: int = field(default=512)


# Hardcoded defaults — used when models.json is absent or malformed.
_DEFAULTS: dict[str, ModelConfig] = {
    "trivial_llm": ModelConfig(
        role="trivial_llm",
        provider="ollama",
        model_id="qwen3:1.7b",
        display_name="Qwen3 1.7B",
        vision=False,
    ),
    "simple_llm": ModelConfig(
        role="simple_llm",
        provider="ollama",
        model_id="gemma4:e4b",
        display_name="Gemma 4 (4B)",
        vision=True,
    ),
    "advanced_llm": ModelConfig(
        role="advanced_llm",
        provider="openrouter",
        model_id="anthropic/claude-sonnet-4-6",
        display_name="Claude Sonnet 4.6",
        vision=True,
    ),
    "complex_llm": ModelConfig(
        role="complex_llm",
        provider="openrouter",
        model_id="anthropic/claude-opus-4-6",
        display_name="Claude Opus 4.6",
        vision=True,
    ),
    "vector_db_embedding": ModelConfig(
        role="vector_db_embedding",
        provider="ollama",
        model_id="nomic-embed-text",
        display_name="Nomic Embed Text",
        vision=False,
    ),
    "whisper_stt_model": ModelConfig(
        role="whisper_stt_model",
        provider="local",
        model_id="medium",
        display_name="Whisper medium",
        vision=False,
    ),
    "diffusers_image_gen_model": ModelConfig(
        role="diffusers_image_gen_model",
        provider="local",
        model_id="stabilityai/sdxl-turbo",
        display_name="SDXL-Turbo",
        vision=False,
        diffusers_max_image_dimension=512,
    ),
}


def _parse_entry(entry: object) -> ModelConfig | None:
    """Parse and validate a single JSON entry into a ModelConfig.

    Args:
        entry: The raw JSON value for one models array element.

    Returns:
        A validated ``ModelConfig``, or ``None`` if any required field is
        missing, the role is unknown, or the provider is not recognised.
    """
    if not isinstance(entry, dict):
        return None
    missing = _REQUIRED_FIELDS - entry.keys()
    if missing:
        logging.warning(
            "models.json entry missing required fields %s; skipping",
            sorted(missing),
        )
        return None
    role = entry["role"]
    if role not in _KNOWN_ROLES:
        logging.debug("models.json: unknown role %r; ignoring", role)
        return None
    provider = entry["provider"]
    if provider not in _KNOWN_PROVIDERS:
        logging.warning(
            "models.json role %r has unknown provider %r; skipping",
            role,
            provider,
        )
        return None
    return ModelConfig(
        role=role,
        provider=provider,
        model_id=str(entry["model_id"]),
        display_name=str(entry["display_name"]),
        vision=bool(entry["vision"]),
        diffusers_max_image_dimension=int(
            entry.get("diffusers_max_image_dimension", 512)
        ),
    )


def load_models(path: str = "models.json") -> dict[str, ModelConfig]:
    """Load model configuration from a JSON file.

    Reads ``path``, validates each entry, and returns a dict keyed by role.
    If the file is absent, unreadable, or invalid, the built-in defaults are
    returned and a warning is logged so the application still starts cleanly.

    Unknown roles are silently ignored; entries with missing required fields
    or unrecognised providers fall back to defaults for that role.

    Args:
        path: Path to the JSON configuration file. Relative paths are
          resolved relative to the current working directory.

    Returns:
        A ``dict[str, ModelConfig]`` mapping each known role to its
        configuration.  Roles absent from the file use built-in defaults.
    """
    result = dict(_DEFAULTS)

    p = Path(path)
    if not p.exists():
        logging.info(
            "models.json not found at %r; using built-in defaults", path
        )
        return result

    try:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        logging.warning(
            "Could not read models.json (%s); using built-in defaults", exc
        )
        return result

    if not isinstance(data, dict) or "models" not in data:
        logging.warning(
            "models.json has no top-level 'models' array; "
            "using built-in defaults"
        )
        return result

    for entry in data["models"]:
        cfg = _parse_entry(entry)
        if cfg is not None:
            result[cfg.role] = cfg

    return result
