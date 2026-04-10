"""Unit tests for src/model_config.py (T22.1)."""

import json

import pytest

model_config_module = pytest.importorskip("src.model_config")
load_models = model_config_module.load_models
ModelConfig = model_config_module.ModelConfig
_DEFAULTS = model_config_module._DEFAULTS
_KNOWN_ROLES = model_config_module._KNOWN_ROLES

_ALL_ROLES = list(_KNOWN_ROLES)

_VALID_JSON = {
    "models": [
        {
            "role": "trivial_llm",
            "provider": "ollama",
            "model_id": "qwen3:1.7b",
            "display_name": "Qwen3 1.7B",
            "vision": False,
        },
        {
            "role": "simple_llm",
            "provider": "ollama",
            "model_id": "gemma4:e4b",
            "display_name": "Gemma 4 (4B)",
            "vision": True,
        },
        {
            "role": "advanced_llm",
            "provider": "openrouter",
            "model_id": "anthropic/claude-sonnet-4-6",
            "display_name": "Claude Sonnet 4.6",
            "vision": True,
        },
        {
            "role": "complex_llm",
            "provider": "openrouter",
            "model_id": "anthropic/claude-opus-4-6",
            "display_name": "Claude Opus 4.6",
            "vision": True,
        },
        {
            "role": "vector_db_embedding",
            "provider": "ollama",
            "model_id": "nomic-embed-text",
            "display_name": "Nomic Embed Text",
            "vision": False,
        },
        {
            "role": "whisper_stt_model",
            "provider": "local",
            "model_id": "medium",
            "display_name": "Whisper medium",
            "vision": False,
        },
        {
            "role": "diffusers_image_gen_model",
            "provider": "local",
            "model_id": "stabilityai/sdxl-turbo",
            "display_name": "SDXL-Turbo",
            "vision": False,
            "diffusers_max_image_dimension": 512,
        },
    ]
}


def _write_json(tmp_path, data):
    p = tmp_path / "models.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


# ── Happy path ────────────────────────────────────────────────────────────────


class TestLoadModelsValid:
    def test_returns_dict_with_all_roles(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        assert set(result.keys()) == _KNOWN_ROLES

    def test_all_values_are_model_config(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        for cfg in result.values():
            assert isinstance(cfg, ModelConfig)

    def test_trivial_llm_model_id(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        assert result["trivial_llm"].model_id == "qwen3:1.7b"

    def test_simple_llm_vision_true(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        assert result["simple_llm"].vision is True

    def test_trivial_llm_vision_false(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        assert result["trivial_llm"].vision is False

    def test_advanced_llm_provider_openrouter(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        assert result["advanced_llm"].provider == "openrouter"

    def test_display_name_loaded(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        assert result["advanced_llm"].display_name == "Claude Sonnet 4.6"

    def test_diffusers_max_image_dimension_loaded(self, tmp_path):
        path = _write_json(tmp_path, _VALID_JSON)
        result = load_models(path)
        cfg = result["diffusers_image_gen_model"]
        assert cfg.diffusers_max_image_dimension == 512

    def test_custom_model_id_overrides_default(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "trivial_llm",
                    "provider": "ollama",
                    "model_id": "my-custom-model",
                    "display_name": "My Custom",
                    "vision": False,
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        assert result["trivial_llm"].model_id == "my-custom-model"


# ── Missing / invalid file ────────────────────────────────────────────────────


class TestLoadModelsFileMissing:
    def test_missing_file_returns_defaults(self, tmp_path):
        result = load_models(str(tmp_path / "nonexistent.json"))
        assert set(result.keys()) == _KNOWN_ROLES

    def test_missing_file_defaults_match_expected(self, tmp_path):
        result = load_models(str(tmp_path / "nonexistent.json"))
        expected = _DEFAULTS["trivial_llm"].model_id
        assert result["trivial_llm"].model_id == expected

    def test_invalid_json_returns_defaults(self, tmp_path):
        p = tmp_path / "models.json"
        p.write_text("not valid json", encoding="utf-8")
        result = load_models(str(p))
        assert set(result.keys()) == _KNOWN_ROLES

    def test_wrong_structure_returns_defaults(self, tmp_path):
        p = tmp_path / "models.json"
        p.write_text(json.dumps({"wrong": "structure"}), encoding="utf-8")
        result = load_models(str(p))
        expected = _DEFAULTS["simple_llm"].model_id
        assert result["simple_llm"].model_id == expected


# ── Partial / bad entries ─────────────────────────────────────────────────────


class TestLoadModelsPartialEntries:
    def test_missing_required_field_uses_default(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "trivial_llm",
                    "provider": "ollama",
                    # model_id missing
                    "display_name": "Bad entry",
                    "vision": False,
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        expected = _DEFAULTS["trivial_llm"].model_id
        assert result["trivial_llm"].model_id == expected

    def test_unknown_role_is_ignored(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "nonexistent_role",
                    "provider": "ollama",
                    "model_id": "something",
                    "display_name": "Unknown",
                    "vision": False,
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        assert "nonexistent_role" not in result
        # All known roles still present via defaults
        assert set(result.keys()) == _KNOWN_ROLES

    def test_unknown_provider_uses_default(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "trivial_llm",
                    "provider": "unknown_provider",
                    "model_id": "something",
                    "display_name": "Bad",
                    "vision": False,
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        expected = _DEFAULTS["trivial_llm"].provider
        assert result["trivial_llm"].provider == expected

    def test_diffusers_max_image_dimension_defaults_to_512(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "diffusers_image_gen_model",
                    "provider": "local",
                    "model_id": "some/model",
                    "display_name": "Some Model",
                    "vision": False,
                    # diffusers_max_image_dimension omitted
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        cfg = result["diffusers_image_gen_model"]
        assert cfg.diffusers_max_image_dimension == 512

    def test_partial_file_fills_missing_roles_from_defaults(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "trivial_llm",
                    "provider": "ollama",
                    "model_id": "override",
                    "display_name": "Override",
                    "vision": False,
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        # trivial_llm overridden, others use defaults
        assert result["trivial_llm"].model_id == "override"
        assert result["simple_llm"].model_id == _DEFAULTS["simple_llm"].model_id


# ── context_tokens field ──────────────────────────────────────────────────────


class TestContextTokens:
    def test_defaults_have_nonzero_context_tokens_for_llm_roles(self):
        for role in (
            "trivial_llm",
            "simple_llm",
            "advanced_llm",
            "complex_llm",
        ):
            assert _DEFAULTS[role].context_tokens > 0

    def test_defaults_context_tokens_values(self):
        assert _DEFAULTS["trivial_llm"].context_tokens == 4000
        assert _DEFAULTS["simple_llm"].context_tokens == 6000
        assert _DEFAULTS["advanced_llm"].context_tokens == 16000
        assert _DEFAULTS["complex_llm"].context_tokens == 32000

    def test_non_llm_roles_have_zero_context_tokens(self):
        for role in (
            "vector_db_embedding",
            "whisper_stt_model",
            "diffusers_image_gen_model",
        ):
            assert _DEFAULTS[role].context_tokens == 0

    def test_context_tokens_loaded_from_json(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "trivial_llm",
                    "provider": "ollama",
                    "model_id": "qwen3:1.7b",
                    "display_name": "Qwen3",
                    "vision": False,
                    "context_tokens": 8000,
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        assert result["trivial_llm"].context_tokens == 8000

    def test_context_tokens_defaults_to_zero_when_absent(self, tmp_path):
        data = {
            "models": [
                {
                    "role": "trivial_llm",
                    "provider": "ollama",
                    "model_id": "qwen3:1.7b",
                    "display_name": "Qwen3",
                    "vision": False,
                    # no context_tokens key
                }
            ]
        }
        path = _write_json(tmp_path, data)
        result = load_models(path)
        assert result["trivial_llm"].context_tokens == 0
