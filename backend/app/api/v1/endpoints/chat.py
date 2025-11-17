"""Chat endpoints with SSE streaming."""
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....models.conversation import Conversation, Message
from ....models.user import User
from ....schemas.conversation import ChatRequest, MessageResponse
from ....services.rag_service import ScholarRAGService
from ...deps import get_current_user

router = APIRouter()


@router.post("/query")
def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Non-streaming chat endpoint.
    Processes the question and returns the complete response.
    """
    # Get or create conversation
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Get conversation history
    history = []
    for msg in conversation.messages:
        history.append({
            "role": msg.role,
            "content": msg.content
        })

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        citations=[]
    )
    db.add(user_message)
    db.commit()

    # Process with RAG service
    try:
        rag_service = ScholarRAGService()
        result = rag_service.process_question(
            question=request.message,
            user_id=current_user.id,
            paper_ids=request.paper_ids if request.paper_ids else None,
            conversation_history=history
        )
    except Exception as e:
        # Rollback user message on error
        db.delete(user_message)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        citations=result["citations"]
    )
    db.add(assistant_message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant_message)

    return {
        "message": {
            "id": str(assistant_message.id),
            "conversation_id": str(conversation.id),
            "role": assistant_message.role,
            "content": assistant_message.content,
            "citations": assistant_message.citations,
            "created_at": assistant_message.created_at.isoformat()
        },
        "conversation_id": str(conversation.id),
        "citations": result["citations"]
    }


@router.post("")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Streaming chat endpoint using Server-Sent Events.
    Returns chunks of the response as they are generated.
    """
    # Get or create conversation
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Get conversation history
    history = []
    for msg in conversation.messages:
        history.append({
            "role": msg.role,
            "content": msg.content
        })

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        citations=[]
    )
    db.add(user_message)
    db.commit()

    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            # Send conversation ID first
            yield f"data: {json.dumps({'type': 'conversation_id', 'id': str(conversation.id)})}\n\n"

            # Process with RAG service (non-streaming for now)
            rag_service = ScholarRAGService()
            result = rag_service.process_question(
                question=request.message,
                user_id=current_user.id,
                paper_ids=request.paper_ids if request.paper_ids else None,
                conversation_history=history
            )

            # Simulate streaming by sending chunks
            answer = result["answer"]
            chunk_size = 10  # Characters per chunk

            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

            # Send citations
            yield f"data: {json.dumps({'type': 'citations', 'citations': result['citations']})}\n\n"

            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                citations=result["citations"]
            )
            db.add(assistant_message)
            conversation.updated_at = datetime.utcnow()
            db.commit()

            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
