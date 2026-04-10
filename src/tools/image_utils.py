"""Shared image encoding/decoding utilities for image-producing tools.

All tools that produce images use the ``__IMAGE__:`` sentinel convention
so the orchestrator can detect image results, extract the PNG payload,
and route them to the Gradio image output component.
"""

from __future__ import annotations

import base64
import io

from PIL import Image

_IMAGE_PREFIX = b"__IMAGE__:"


def encode_image(img: Image.Image) -> bytes:
    """Encode a PIL Image as the ``__IMAGE__:`` sentinel bytes.

    Args:
        img: A PIL Image object to encode as PNG.

    Returns:
        Bytes of the form ``b"__IMAGE__:" + base64(png_bytes)``.
    """
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return _IMAGE_PREFIX + base64.b64encode(buf.getvalue())


def decode_image(data: bytes) -> Image.Image:
    """Decode sentinel bytes produced by ``encode_image`` back to a PIL Image.

    Args:
        data: Bytes starting with ``b"__IMAGE__:"`` followed by
          base64-encoded PNG data.

    Returns:
        The decoded PIL Image.

    Raises:
        ValueError: If ``data`` does not start with the expected prefix.
    """
    if not data.startswith(_IMAGE_PREFIX):
        raise ValueError("data does not start with the __IMAGE__: prefix")
    png_bytes = base64.b64decode(data[len(_IMAGE_PREFIX) :])
    return Image.open(io.BytesIO(png_bytes))


def is_image_sentinel(value: object) -> bool:
    """Return True if ``value`` is a bytes image sentinel.

    Args:
        value: The value returned by a tool callable.

    Returns:
        True if ``value`` is bytes starting with ``b"__IMAGE__:"``.
    """
    return isinstance(value, bytes) and value.startswith(_IMAGE_PREFIX)
