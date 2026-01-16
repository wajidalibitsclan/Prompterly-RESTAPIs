"""
Public Chatbot API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from app.db.session import get_db
from app.services.public_chatbot_service import public_chatbot_service

router = APIRouter(prefix="/public-chatbot", tags=["Public Chatbot"])


# ============== Schemas ==============

class ChatbotConfigPublic(BaseModel):
    """Public chatbot config response (limited fields)"""
    name: str
    welcome_message: str
    input_placeholder: str
    header_subtitle: Optional[str]
    is_enabled: bool
    avatar_url: Optional[str]


class ChatMessageRequest(BaseModel):
    """Request to send a chat message"""
    session_id: Optional[str] = None
    message: str


class ChatMessageResponse(BaseModel):
    """Response from chat message"""
    response: str
    session_id: str


class SessionResponse(BaseModel):
    """Response with session ID"""
    session_id: str


# ============== Endpoints ==============

@router.get("/config", response_model=ChatbotConfigPublic)
async def get_chatbot_config(db: Session = Depends(get_db)):
    """
    Get public chatbot configuration

    Returns the chatbot settings for display on the frontend
    """
    config = await public_chatbot_service.get_config(db)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot configuration not found"
        )

    return ChatbotConfigPublic(
        name=config.name,
        welcome_message=config.welcome_message,
        input_placeholder=config.input_placeholder,
        header_subtitle=config.header_subtitle,
        is_enabled=config.is_enabled,
        avatar_url=config.avatar_url
    )


@router.post("/session", response_model=SessionResponse)
async def create_session():
    """
    Create a new chat session

    Returns a unique session ID for the conversation
    """
    session_id = public_chatbot_service.generate_session_id()
    return SessionResponse(session_id=session_id)


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to the chatbot

    Returns the AI response
    """
    # Generate session if not provided
    session_id = request.session_id or public_chatbot_service.generate_session_id()

    try:
        result = await public_chatbot_service.send_message(
            session_id=session_id,
            content=request.message,
            db=db
        )

        return ChatMessageResponse(
            response=result["response"],
            session_id=session_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/message/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message and stream the response via SSE
    """
    # Generate session if not provided
    session_id = request.session_id or public_chatbot_service.generate_session_id()

    async def event_generator():
        async for event in public_chatbot_service.send_message_stream(
            session_id=session_id,
            content=request.message,
            db=db
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id
        }
    )


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear chat history for a session
    """
    await public_chatbot_service.clear_session(session_id, db)
    return {"message": "Session cleared successfully"}
