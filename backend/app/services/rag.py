"""
RAG service with:
- Chunk deduplication (same page + similar text → keep best score)
- Query embedding cache (same question doesn't re-embed)
- stream_answer() for token-by-token streaming
- answer_question() for standard full-response usage
"""
import hashlib
from collections.abc import Generator
from functools import lru_cache

import numpy as np
from sqlalchemy.orm import Session

from app.models.orm import Chunk, Document
from app.models.schemas import ChunkOut
from app.services.embeddings import embedder
from app.services.llm_provider import llm_provider
from app.services import vector_store as vs

_SYSTEM_TEMPLATE = """\
You are a precise document assistant. Answer the user's question using ONLY the context passages provided below.
If the answer is not contained in the context, say exactly: "I don't have enough information in the provided documents to answer that."
Do not speculate or use outside knowledge. Be concise and direct.

Context:
{context}
"""

# How many prior message pairs (user+assistant) to include as history
_HISTORY_TURNS = 4


def _build_context(chunks: list[ChunkOut]) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {c.document_name}, page {c.page_number}]\n{c.text}"
        for c in chunks
    )


def _deduplicate(chunks: list[ChunkOut]) -> list[ChunkOut]:
    """
    Remove near-duplicate chunks: if two chunks share the same document + page
    and their text overlap is > 80%, keep only the one with the better score.
    """
    seen: list[ChunkOut] = []
    for chunk in chunks:
        duplicate = False
        for existing in seen:
            if existing.document_id == chunk.document_id and existing.page_number == chunk.page_number:
                words_a = set(existing.text.lower().split())
                words_b = set(chunk.text.lower().split())
                if words_a and words_b:
                    overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
                    if overlap > 0.8:
                        duplicate = True
                        break
        if not duplicate:
            seen.append(chunk)
    return seen


@lru_cache(maxsize=256)
def _cached_embed(question_hash: str, question: str) -> np.ndarray:
    """Cache embeddings by question hash to avoid re-embedding identical queries."""
    arr = embedder().embed_one(question)
    arr.flags.writeable = False
    return arr


def _embed_query(question: str) -> np.ndarray:
    h = hashlib.md5(question.encode()).hexdigest()
    return _cached_embed(h, question)


def retrieve_chunks(query: str, top_k: int, db: Session) -> list[ChunkOut]:
    """Embed query → pgvector search → hydrate from DB → deduplicate."""
    q_vec = _embed_query(query).tolist()
    hits = vs.search(db, q_vec, top_k)
    if not hits:
        return []

    chunk_ids = [cid for cid, _ in hits]
    score_map = {cid: score for cid, score in hits}

    rows = (
        db.query(Chunk, Document.original_name)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Chunk.id.in_(chunk_ids))
        .all()
    )

    results = [
        ChunkOut(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_name=doc_name,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            score=score_map.get(chunk.id, 0.0),
        )
        for chunk, doc_name in rows
    ]

    results.sort(key=lambda c: score_map.get(c.chunk_id, float("inf")))
    return _deduplicate(results)


def stream_answer(
    question: str,
    top_k: int,
    db: Session,
    history: list[dict] | None = None,
) -> tuple[list[ChunkOut], Generator[str, None, None]]:
    """
    Returns (sources, token_generator).
    Retrieval happens eagerly; LLM tokens are yielded lazily.
    history: list of {"role": "user"|"assistant", "content": str} — prior turns.
    """
    sources = retrieve_chunks(question, top_k, db)
    if not sources:
        def _empty():
            yield "I don't have enough information in the provided documents to answer that."
        return [], _empty()

    context = _build_context(sources)
    system_prompt = _SYSTEM_TEMPLATE.format(context=context)
    return sources, llm_provider().stream(system_prompt, question, history=history or [])


def answer_question(
    question: str,
    top_k: int,
    db: Session,
    history: list[dict] | None = None,
) -> tuple[str, list[ChunkOut]]:
    """Full RAG pipeline, returns complete answer string + sources."""
    sources, token_gen = stream_answer(question, top_k, db, history=history)
    answer = "".join(token_gen)
    return answer, sources


def load_history(conversation_id: str, db: Session) -> list[dict]:
    """Load the last _HISTORY_TURNS pairs from a conversation for context."""
    from app.models.orm import Message  # local import to avoid circular
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(_HISTORY_TURNS * 2)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]
