import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.db.base import get_db
from app.models.orm import Conversation, Message
from app.models.schemas import QueryRequest, QueryResponse, SearchRequest, SearchResponse
from app.services.rag import answer_question, load_history, retrieve_chunks, stream_answer

router = APIRouter(prefix="/query", tags=["query"])


def _resolve_conversation(body: QueryRequest, user_id: str, db: Session) -> Conversation:
    if body.conversation_id:
        conv = db.get(Conversation, body.conversation_id)
        if not conv or conv.owner_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv
    title = body.question[:60] + ("…" if len(body.question) > 60 else "")
    conv = Conversation(owner_id=user_id, title=title)
    db.add(conv)
    db.flush()
    return conv


@router.post("/search", response_model=SearchResponse)
def semantic_search(
    body: SearchRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Semantic search only — returns top-k chunks without calling the LLM."""
    return SearchResponse(results=retrieve_chunks(body.query, body.top_k, db, user_id=user_id))


@router.post("/ask", response_model=QueryResponse)
def ask(
    body: QueryRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Full RAG pipeline. Returns complete answer + sources in one response."""
    conv = _resolve_conversation(body, user_id, db)
    history = load_history(conv.id, db) if body.conversation_id else []
    answer, sources = answer_question(body.question, body.top_k, db, history=history, user_id=user_id)

    db.add(Message(conversation_id=conv.id, role="user", content=body.question))
    sources_payload = [s.model_dump() for s in sources]
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources_payload),
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return QueryResponse(
        answer=answer,
        sources=sources,
        conversation_id=conv.id,
        message_id=assistant_msg.id,
    )


@router.post("/ask/stream")
def ask_stream(
    body: QueryRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Streaming RAG endpoint using Server-Sent Events (SSE).

    Event types:
      data: {"type": "sources", "sources": [...]}   — sent first with retrieved chunks
      data: {"type": "token",   "token": "..."}     — one per LLM token
      data: {"type": "done",    "conversation_id": "...", "message_id": "..."}
      data: {"type": "error",   "detail": "..."}    — on failure
    """
    conv = _resolve_conversation(body, user_id, db)
    history = load_history(conv.id, db) if body.conversation_id else []
    db.add(Message(conversation_id=conv.id, role="user", content=body.question))
    db.flush()

    sources, token_gen = stream_answer(body.question, body.top_k, db, history=history, user_id=user_id)
    conv_id = conv.id
    sources_payload = [s.model_dump() for s in sources]
    db.commit()  # persist the user message before the session is closed

    def _event_stream():
        # 1. Send sources immediately so the UI can render them before the answer
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources_payload})}\n\n"

        # 2. Stream tokens
        full_answer = []
        try:
            for token in token_gen:
                full_answer.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
            return

        # 3. Persist assistant message in a fresh session and send done event
        from app.db.base import SessionLocal
        answer_text = "".join(full_answer)
        with SessionLocal() as fresh_db:
            assistant_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=answer_text,
                sources=json.dumps(sources_payload),
            )
            fresh_db.add(assistant_msg)
            fresh_db.commit()
            fresh_db.refresh(assistant_msg)
            msg_id = assistant_msg.id

        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': msg_id})}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
