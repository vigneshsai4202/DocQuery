import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.db.base import get_db
from app.models.orm import Conversation, Message
from app.models.schemas import ConversationDetail, ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """List all conversations for the current user, newest first."""
    return (
        db.query(Conversation)
        .filter(Conversation.owner_id == user_id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a conversation with all its messages and source citations."""
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = []
    for msg in conv.messages:
        sources = json.loads(msg.sources) if msg.sources else None
        messages.append(
            MessageOut(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                sources=sources,
                created_at=msg.created_at,
            )
        )

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        messages=messages,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
