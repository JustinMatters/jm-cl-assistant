"""Image generation tool — SDXL-Turbo local inference or CC0 web search.

Approach B tool — the LLM decides when to call it.  Two paths:

  * Local generation (primary) — uses ``stabilityai/sdxl-turbo`` via the
    ``diffusers`` library when CUDA is available.  First call downloads
    ~6.7 GB of model weights; subsequent calls reuse the cached pipeline.
  * CC0 web search (fallback) — queries the Openverse API for a freely
    licensed image when CUDA is unavailable or local generation fails.

The tool returns the image as an ``__IMAGE__:`` sentinel so the orchestrator
can route it to the Gradio image output component.

.. note::
    Set ``default_enabled=False``; local inference requires a GPU with ~7 GB
    VRAM.  Users who want this tool must enable it explicitly in settings.
"""

from __future__ import annotations

import io
import json
import logging
import urllib.parse
import urllib.request

from PIL import Image

from src.model_config import load_models
from src.tools.image_utils import encode_image
from src.tools.registry import REGISTRY, ToolDefinition

_IMAGE_GEN_CONFIG = load_models()["diffusers_image_gen_model"]
_SDXL_MODEL = _IMAGE_GEN_CONFIG.model_id
_OPENVERSE_SEARCH = "https://api.openverse.org/v1/images/"
_MAX_IMG_DIM = _IMAGE_GEN_CONFIG.diffusers_max_image_dimension

_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "Text description of the image to generate.",
        },
        "mode": {
            "type": "string",
            "enum": ["auto", "local", "search"],
            "description": (
                "'auto' tries local GPU generation first, falls back to CC0 "
                "web search. 'local' forces GPU generation. 'search' forces "
                "CC0 image search via Openverse."
            ),
        },
    },
    "required": ["prompt"],
    "additionalProperties": False,
}

# Module-level pipeline cache so the model is only loaded once per process.
_pipeline = None


def _cuda_available() -> bool:
    """Return True if PyTorch can see a CUDA device."""
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


def _generate_local(prompt: str) -> bytes:
    """Generate an image with SDXL-Turbo and return sentinel bytes.

    Downloads the model on first call (~6.7 GB).  Subsequent calls reuse
    the cached pipeline stored in the module-level ``_pipeline`` variable.

    Args:
        prompt: The text prompt to generate an image from.

    Returns:
        ``__IMAGE__:`` sentinel bytes wrapping a 512×512 PNG.

    Raises:
        RuntimeError: If CUDA is unavailable.
        Exception: On model load or inference failure.
    """
    import torch
    from diffusers.pipelines.auto_pipeline import AutoPipelineForText2Image

    global _pipeline  # noqa: PLW0603

    if not _cuda_available():
        raise RuntimeError(
            "SDXL-Turbo requires a CUDA GPU. "
            "No CUDA device found on this machine."
        )

    if _pipeline is None:
        logging.info("Loading SDXL-Turbo pipeline (first call; ~6.7 GB)…")
        _pipeline = AutoPipelineForText2Image.from_pretrained(
            _SDXL_MODEL,
            torch_dtype=torch.float16,
            variant="fp16",
        )
        _pipeline.to("cuda")

    result = _pipeline(
        prompt=prompt,
        num_inference_steps=4,
        guidance_scale=0.0,
    )
    img: Image.Image = result.images[0]
    return encode_image(img)


def _search_cc0(prompt: str) -> bytes:
    """Search Openverse for a CC0-licensed image matching the prompt.

    Args:
        prompt: The search query sent to the Openverse API.

    Returns:
        ``__IMAGE__:`` sentinel bytes wrapping the first result's PNG/JPEG.

    Raises:
        ValueError: If no results are found for the prompt.
        Exception: On network or decode failure.
    """
    params = urllib.parse.urlencode({"q": prompt, "license": "cc0"})
    url = f"{_OPENVERSE_SEARCH}?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "jm-cl-assistant/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        data = json.loads(resp.read())

    results = data.get("results", [])
    if not results:
        raise ValueError(f"No CC0 images found for prompt: {prompt!r}")

    image_url = results[0]["url"]
    img_req = urllib.request.Request(
        image_url,
        headers={"User-Agent": "jm-cl-assistant/1.0"},
    )
    with urllib.request.urlopen(img_req, timeout=20) as img_resp:  # noqa: S310
        raw = img_resp.read()

    img = Image.open(io.BytesIO(raw)).convert("RGB")
    # Resize if very large to keep response size reasonable.
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    return encode_image(img)


def _image_gen_callable(args_json: str) -> bytes | str:
    """Approach B callable — parse JSON args and generate or search for image.

    Args:
        args_json: JSON string with at least ``prompt``; optionally ``mode``.

    Returns:
        ``__IMAGE__:`` sentinel bytes, or an error string.
    """
    try:
        args = json.loads(args_json)
    except (json.JSONDecodeError, AttributeError):
        return "Error: invalid arguments for image_gen tool."

    prompt = args.get("prompt", "").strip()
    mode = args.get("mode", "auto").strip()

    if not prompt:
        return "Error: prompt is required."
    if mode not in ("auto", "local", "search"):
        return (
            f"Error: mode must be 'auto', 'local', or 'search'. Got {mode!r}."
        )

    if mode == "local":
        try:
            return _generate_local(prompt)
        except Exception as exc:
            logging.warning("Local image generation failed: %s", exc)
            return f"Error: local generation failed — {exc}"

    if mode == "search":
        try:
            return _search_cc0(prompt)
        except Exception as exc:
            logging.warning("CC0 image search failed: %s", exc)
            return f"Error: CC0 image search failed — {exc}"

    # mode == "auto": try local first, fall back to search.
    if _cuda_available():
        try:
            return _generate_local(prompt)
        except Exception as exc:
            logging.warning(
                "Local generation failed, falling back to CC0 search: %s", exc
            )
    else:
        logging.info(
            "No CUDA device; using CC0 image search for prompt: %r", prompt
        )

    try:
        return _search_cc0(prompt)
    except Exception as exc:
        logging.warning("CC0 image search also failed: %s", exc)
        return (
            f"Could not generate or find an image for {prompt!r}. "
            f"CC0 search error: {exc}"
        )


REGISTRY.register(
    ToolDefinition(
        name="image_gen",
        router_tier="image_gen",
        label="Tool: Image generation",
        description=(
            "generate an image from a text prompt using SDXL-Turbo (GPU) "
            "or find a free CC0-licensed image via Openverse search"
        ),
        examples=[
            "generate an image of a sunset over the mountains",
            "create a picture of a robot reading a book",
            "find a CC0 image of a cat",
            "draw a forest at night",
        ],
        default_enabled=False,
        min_tier="advanced_llm",
        approach="B",
        callable=_image_gen_callable,
        category="visual",
        parameters_schema=_PARAMETERS_SCHEMA,
    )
)
