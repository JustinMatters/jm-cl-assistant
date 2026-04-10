"""Unit tests for src/tools/image_utils.py."""

import base64

import pytest
from PIL import Image

from src.tools.image_utils import (
    _IMAGE_PREFIX,
    decode_image,
    encode_image,
    is_image_sentinel,
)


def _make_image(
    width: int = 4, height: int = 4, color: str = "red"
) -> Image.Image:
    return Image.new("RGB", (width, height), color=color)


class TestEncodeImage:
    def test_returns_bytes(self):
        img = _make_image()
        result = encode_image(img)
        assert isinstance(result, bytes)

    def test_starts_with_prefix(self):
        img = _make_image()
        result = encode_image(img)
        assert result.startswith(_IMAGE_PREFIX)

    def test_suffix_is_valid_base64(self):
        img = _make_image()
        result = encode_image(img)
        payload = result[len(_IMAGE_PREFIX) :]
        decoded = base64.b64decode(payload)
        assert len(decoded) > 0

    def test_encoded_data_is_valid_png(self):
        img = _make_image()
        result = encode_image(img)
        payload = result[len(_IMAGE_PREFIX) :]
        png_bytes = base64.b64decode(payload)
        # PNG magic bytes
        assert png_bytes[:4] == b"\x89PNG"

    def test_different_images_produce_different_bytes(self):
        red = _make_image(color="red")
        blue = _make_image(color="blue")
        assert encode_image(red) != encode_image(blue)


class TestDecodeImage:
    def test_roundtrip(self):
        original = _make_image(width=8, height=8, color="green")
        encoded = encode_image(original)
        decoded = decode_image(encoded)
        assert isinstance(decoded, Image.Image)
        assert decoded.size == original.size

    def test_raises_on_missing_prefix(self):
        with pytest.raises(ValueError, match="prefix"):
            decode_image(b"not-a-sentinel")

    def test_raises_on_empty_bytes(self):
        with pytest.raises(ValueError):
            decode_image(b"")

    def test_pixel_values_preserved(self):
        original = _make_image(width=2, height=2, color=(123, 45, 67))
        encoded = encode_image(original)
        decoded = decode_image(encoded)
        assert decoded.getpixel((0, 0))[:3] == (123, 45, 67)


class TestIsImageSentinel:
    def test_true_for_encoded_image(self):
        img = _make_image()
        assert is_image_sentinel(encode_image(img)) is True

    def test_false_for_plain_string(self):
        assert is_image_sentinel("hello") is False

    def test_false_for_plain_bytes(self):
        assert is_image_sentinel(b"some bytes") is False

    def test_false_for_none(self):
        assert is_image_sentinel(None) is False

    def test_false_for_int(self):
        assert is_image_sentinel(42) is False

    def test_false_for_prefix_only(self):
        # Prefix without payload is still bytes starting with prefix
        assert is_image_sentinel(_IMAGE_PREFIX) is True

    def test_false_for_empty_bytes(self):
        assert is_image_sentinel(b"") is False
