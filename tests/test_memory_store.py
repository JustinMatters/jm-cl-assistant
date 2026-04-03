"""Unit tests for MemoryStore.

Ollama calls are mocked so tests run without a live Ollama instance.
ChromaDB uses a temporary directory via the tmp_path pytest fixture.
"""

import math
from unittest.mock import MagicMock

import pytest

store_module = pytest.importorskip("src.memory.store")
MemoryStore = store_module.MemoryStore

# --- Embedding fixtures ---
# Two orthogonal unit vectors in 768-dim space:
#   EMBED_A: uniform normalised  (all components equal)
#   EMBED_B: standard basis e_0  (first component = 1, rest = 0)
# Cosine distance between them = 1 - dot(A,B) = 1 - 1/sqrt(768) ≈ 0.964
# So a query embedded as EMBED_A will retrieve EMBED_A records (distance ≈ 0)
# but NOT EMBED_B records (distance ≈ 0.964 > threshold 0.7).

DIM = 768
EMBED_A = [1.0 / math.sqrt(DIM)] * DIM
EMBED_B = [1.0] + [0.0] * (DIM - 1)


def _make_embed_response(embeddings: list[list[float]]) -> MagicMock:
    r = MagicMock()
    r.embeddings = embeddings
    return r


def _make_list_response() -> MagicMock:
    """Return a fake ollama.list() response showing nomic-embed-text."""
    model = MagicMock()
    model.model = "nomic-embed-text:latest"
    resp = MagicMock()
    resp.models = [model]
    return resp


@pytest.fixture
def store(tmp_path, mocker):
    """A MemoryStore backed by a temp ChromaDB dir with mocked Ollama."""
    mock_client = MagicMock()
    mock_client.list.return_value = _make_list_response()
    # Default embed: always return EMBED_A
    mock_client.embed.return_value = _make_embed_response([EMBED_A])
    mocker.patch("src.memory.store.ollama.Client", return_value=mock_client)
    return MemoryStore(persist_dir=str(tmp_path))


class TestModelCheck:
    def test_raises_if_model_missing(self, tmp_path, mocker):
        mock_client = MagicMock()
        mock_client.list.return_value = MagicMock(models=[])
        mocker.patch("src.memory.store.ollama.Client", return_value=mock_client)
        with pytest.raises(RuntimeError, match="ollama pull nomic-embed-text"):
            MemoryStore(persist_dir=str(tmp_path))

    def test_succeeds_if_model_present(self, store):
        assert store is not None


class TestAddAndSearch:
    def test_add_returns_id_with_source_prefix(self, store):
        doc_id = store.add(
            "User asked about Whisper.",
            source="conversation",
            session_id="sess-1",
        )
        assert doc_id.startswith("conversation_")

    def test_search_returns_stored_record(self, store):
        store.add(
            "User asked about Whisper.",
            source="conversation",
            session_id="sess-1",
        )
        results = store.search("Whisper model sizes")
        assert len(results) == 1
        assert "Whisper" in results[0]["text"]
        assert results[0]["source"] == "conversation"
        assert results[0]["session_id"] == "sess-1"
        assert "distance" in results[0]

    def test_search_returns_all_metadata_keys(self, store):
        store.add(
            "Forecast API info.",
            source="web_search",
            session_id="sess-1",
            keywords="weather, api",
            url="https://example.com",
            title="Open-Meteo API",
        )
        results = store.search("weather")
        assert results[0]["keywords"] == "weather, api"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["title"] == "Open-Meteo API"

    def test_count_reflects_added_records(self, store):
        assert store.count() == 0
        store.add("First.", source="conversation", session_id="s1")
        store.add("Second.", source="conversation", session_id="s1")
        assert store.count() == 2


class TestSimilarityThreshold:
    def test_below_threshold_record_included(self, store):
        # EMBED_A vs EMBED_A → distance ≈ 0, well below threshold 0.7
        store.add("Relevant.", source="conversation", session_id="s1")
        results = store.search("query")
        assert len(results) == 1

    def test_above_threshold_record_excluded(self, tmp_path, mocker):
        # Store record with EMBED_B; query with EMBED_A → distance ≈ 0.964
        mock_client = MagicMock()
        mock_client.list.return_value = _make_list_response()
        call_count = 0

        def embed_side_effect(model, input):
            nonlocal call_count
            call_count += 1
            # First call (add): return EMBED_B
            # Second call (search): return EMBED_A
            vec = EMBED_B if call_count == 1 else EMBED_A
            return _make_embed_response([vec])

        mock_client.embed.side_effect = embed_side_effect
        mocker.patch("src.memory.store.ollama.Client", return_value=mock_client)
        s = MemoryStore(persist_dir=str(tmp_path))
        s.add("Unrelated.", source="conversation", session_id="s1")
        results = s.search("query")
        assert results == []


class TestSourceFilter:
    def test_source_filter_excludes_other_sources(self, store):
        store.add("Conv turn.", source="conversation", session_id="s1")
        store.add("Web result.", source="web_search", session_id="s1")
        results = store.search("query", source_filter="conversation")
        assert all(r["source"] == "conversation" for r in results)
        assert len(results) == 1


class TestGetContextBlock:
    def test_empty_store_returns_empty_string(self, store):
        assert store.get_context_block("anything") == ""

    def test_format_contains_memory_markers(self, store):
        store.add("Some fact.", source="conversation", session_id="s1")
        block = store.get_context_block("query")
        assert block.startswith("[PAST MEMORIES]")
        assert block.strip().endswith("[END MEMORIES]")

    def test_format_includes_date_and_source(self, store):
        store.add("Some fact.", source="conversation", session_id="s1")
        block = store.get_context_block("query")
        assert "conversation" in block

    def test_format_includes_title_when_present(self, store):
        store.add(
            "API info.",
            source="web_search",
            session_id="s1",
            title="Open-Meteo API",
        )
        block = store.get_context_block("query")
        assert 'title: "Open-Meteo API"' in block

    def test_format_omits_empty_optional_fields(self, store):
        store.add("Plain conv.", source="conversation", session_id="s1")
        block = store.get_context_block("query")
        assert "title:" not in block
        assert "url:" not in block
