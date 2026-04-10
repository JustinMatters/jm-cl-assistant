"""Persistent conversation memory backed by ChromaDB + nomic-embed-text."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import chromadb
import ollama

from src.model_config import load_models

_EMBED_MODEL = load_models()["vector_db_embedding"].model_id


class MemoryStore:
    """Stores and retrieves conversation memory using ChromaDB.

    Embeddings are generated locally via nomic-embed-text through Ollama.
    Instruction-aware prefixes (``search_document:`` / ``search_query:``)
    are applied at embed time so stored text remains clean and readable.

    Args:
        persist_dir: Directory path for ChromaDB's local persistence.
        ollama_url: Base URL of the local Ollama server.
        collection: ChromaDB collection name for this store.
        k: Maximum number of results to retrieve per search query.
        similarity_threshold: Cosine distance cutoff — records with
          distance >= this value are excluded from results (0.0 = identical,
          1.0 = completely dissimilar).

    Attributes:
        _k: Maximum results per search.
        _threshold: Similarity distance cutoff.
        _collection: The underlying ChromaDB collection.

    Raises:
        RuntimeError: If nomic-embed-text is not pulled in Ollama.
    """

    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        ollama_url: str = "http://localhost:11434",
        collection: str = "assistant_memory",
        k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> None:
        self._client = ollama.Client(host=ollama_url)
        self._check_model()
        self._k = k
        self._threshold = similarity_threshold
        chroma = chromadb.PersistentClient(path=persist_dir)
        self._collection = chroma.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )

    def _check_model(self) -> None:
        """Raise RuntimeError if nomic-embed-text is not pulled locally."""
        names = [m.model for m in self._client.list().models]
        if not any(n.startswith(_EMBED_MODEL) for n in names):
            raise RuntimeError(
                f"{_EMBED_MODEL} not found in Ollama — "
                f"run: ollama pull {_EMBED_MODEL}"
            )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed(model=_EMBED_MODEL, input=texts).embeddings

    def add(
        self,
        text: str,
        source: str,
        session_id: str,
        keywords: str = "",
        url: str = "",
        title: str = "",
    ) -> str:
        """Embed and store a text record with associated metadata.

        Args:
            text: The content to store and embed (e.g. a conversation turn).
            source: Origin label for the record, e.g. ``"conversation"``
              or ``"web_search"``.
            session_id: UUID string identifying the current app session.
            keywords: Optional comma-separated keywords for the record.
            url: Optional source URL associated with the record.
            title: Optional human-readable title for the record.

        Returns:
            The generated document ID string, composed of source, timestamp,
            and a short random hex suffix.
        """
        timestamp = datetime.now(UTC).isoformat()
        doc_id = f"{source}_{timestamp}_{uuid4().hex[:8]}"
        embedding = self._embed([f"search_document: {text}"])[0]
        self._collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[
                {
                    "source": source,
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "keywords": keywords,
                    "url": url,
                    "title": title,
                }
            ],
            ids=[doc_id],
        )
        return doc_id

    def search(
        self,
        query: str,
        k: int | None = None,
        source_filter: str | None = None,
    ) -> list[dict]:
        """Return stored records semantically similar to the query.

        Embeds the query and retrieves the nearest neighbours from
        ChromaDB, then filters out any with cosine distance >= the
        configured threshold.

        Args:
            query: The search query text to embed and match against.
            k: Maximum number of results to return. Defaults to the
              instance ``_k`` value when ``None``.
            source_filter: If provided, only records with a matching
              ``source`` metadata field are considered.

        Returns:
            A list of dicts, each with keys: ``id``, ``text``,
            ``source``, ``session_id``, ``timestamp``, ``keywords``,
            ``url``, ``title``, ``distance``. Returns an empty list if
            the store is empty or no records pass the threshold.
        """
        count = self._collection.count()
        if count == 0:
            return []
        n = min(k if k is not None else self._k, count)
        embedding = self._embed([f"search_query: {query}"])[0]
        kwargs: dict = {
            "query_embeddings": [embedding],
            "n_results": n,
            "include": ["documents", "metadatas", "distances"],
        }
        if source_filter:
            kwargs["where"] = {"source": source_filter}
        results = self._collection.query(**kwargs)
        records = []
        for i, (doc, meta, dist) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
                strict=False,
            )
        ):
            if dist < self._threshold:
                records.append(
                    {
                        "id": results["ids"][0][i],
                        "text": doc,
                        "distance": dist,
                        **meta,
                    }
                )
        return records

    def get_context_block(self, query: str) -> str:
        """Return a formatted prompt-ready block of retrieved memories.

        Searches for records relevant to the query and formats them as a
        ``[PAST MEMORIES] … [END MEMORIES]`` block suitable for injection
        as a system message. Callers can check truthiness before injecting
        — an empty string is returned when nothing passes the threshold.

        Args:
            query: The current user query used to retrieve relevant memories.

        Returns:
            A multi-line string delimited by ``[PAST MEMORIES]`` and
            ``[END MEMORIES]``, or an empty string if no relevant records
            were found.
        """
        records = self.search(query)
        if not records:
            return ""
        lines = []
        for r in records:
            date = r["timestamp"][:10]
            parts = [date, r["source"]]
            if r.get("title"):
                parts.append(f'title: "{r["title"]}"')
            if r.get("url"):
                parts.append(f"url: {r['url']}")
            prefix = " | ".join(parts)
            lines.append(f"- [{prefix}] {r['text']}")
        return "[PAST MEMORIES]\n" + "\n".join(lines) + "\n[END MEMORIES]"

    def count(self) -> int:
        """Return the total number of stored records."""
        return self._collection.count()
