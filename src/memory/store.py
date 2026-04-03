"""Persistent conversation memory backed by ChromaDB + nomic-embed-text."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import chromadb
import ollama

_EMBED_MODEL = "nomic-embed-text"


class MemoryStore:
    """Stores and retrieves conversation memory using ChromaDB.

    Embeddings are generated locally via nomic-embed-text through Ollama.
    Instruction-aware prefixes (search_document:/search_query:) are applied
    at embed time so stored text remains clean and readable.
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
        """Store a record. Returns the generated document ID."""
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
        """Return up to k records with cosine distance < threshold.

        Each dict has keys: id, text, source, session_id, timestamp,
        keywords, url, title, distance.
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
        """Return a formatted prompt-ready string of retrieved memories.

        Returns an empty string if nothing passes the similarity threshold,
        so callers can safely check truthiness before injecting into prompt.
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
