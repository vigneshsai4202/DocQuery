"""
FAISS vector store with a JSON metadata sidecar.

Layout on disk:
  {VECTOR_STORE_DIR}/index.faiss   – the FAISS flat L2 index
  {VECTOR_STORE_DIR}/meta.json     – list of {faiss_id, chunk_id, document_id}

Thread-safety: a simple threading.Lock guards mutations.
"""
import json
import threading
from pathlib import Path

import faiss
import numpy as np

from app.core.config import settings

_INDEX_PATH = Path(settings.VECTOR_STORE_DIR) / "index.faiss"
_META_PATH = Path(settings.VECTOR_STORE_DIR) / "meta.json"


class VectorStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._index, self._meta = self._load()

    # ── persistence ──────────────────────────────────────────────────────────

    def _load(self) -> tuple[faiss.IndexFlatL2, list[dict]]:
        _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        if _INDEX_PATH.exists() and _META_PATH.exists():
            index = faiss.read_index(str(_INDEX_PATH))
            meta = json.loads(_META_PATH.read_text())
        else:
            index = faiss.IndexFlatL2(settings.EMBEDDING_DIMENSION)
            meta = []
        return index, meta

    def _save(self):
        faiss.write_index(self._index, str(_INDEX_PATH))
        _META_PATH.write_text(json.dumps(self._meta))

    # ── public API ────────────────────────────────────────────────────────────

    def add(self, vectors: np.ndarray, chunk_ids: list[str], document_id: str) -> list[int]:
        """Add vectors and return the assigned FAISS integer IDs."""
        with self._lock:
            start_id = self._index.ntotal
            self._index.add(vectors.astype("float32"))
            new_ids = list(range(start_id, self._index.ntotal))
            for faiss_id, chunk_id in zip(new_ids, chunk_ids):
                self._meta.append({"faiss_id": faiss_id, "chunk_id": chunk_id, "document_id": document_id})
            self._save()
        return new_ids

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[str, float]]:
        """Return [(chunk_id, score), ...] ordered by ascending L2 distance."""
        with self._lock:
            if self._index.ntotal == 0:
                return []
            k = min(top_k, self._index.ntotal)
            distances, indices = self._index.search(query_vector.reshape(1, -1).astype("float32"), k)
            id_to_chunk = {m["faiss_id"]: m["chunk_id"] for m in self._meta}
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue
                chunk_id = id_to_chunk.get(int(idx))
                if chunk_id:
                    results.append((chunk_id, float(dist)))
        return results

    def delete_by_document(self, document_id: str):
        """Remove all vectors belonging to a document and rebuild the index."""
        with self._lock:
            keep = [m for m in self._meta if m["document_id"] != document_id]
            if len(keep) == len(self._meta):
                return  # nothing to remove

            # Rebuild: collect surviving chunk_ids in order, re-add their vectors
            # We can't remove from IndexFlatL2 directly, so we rebuild.
            # Fetch all vectors first.
            if keep:
                surviving_ids = [m["faiss_id"] for m in keep]
                all_vectors = faiss.rev_swig_ptr(self._index.get_xb(), self._index.ntotal * settings.EMBEDDING_DIMENSION)
                all_vectors = np.array(all_vectors, dtype="float32").reshape(self._index.ntotal, settings.EMBEDDING_DIMENSION)
                surviving_vectors = all_vectors[surviving_ids]

                new_index = faiss.IndexFlatL2(settings.EMBEDDING_DIMENSION)
                new_index.add(surviving_vectors)
                new_meta = [
                    {"faiss_id": new_id, "chunk_id": m["chunk_id"], "document_id": m["document_id"]}
                    for new_id, m in enumerate(keep)
                ]
            else:
                new_index = faiss.IndexFlatL2(settings.EMBEDDING_DIMENSION)
                new_meta = []

            self._index = new_index
            self._meta = new_meta
            self._save()

    def total(self) -> int:
        return self._index.ntotal


# Module-level singleton
_store: VectorStore | None = None


def vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
