"""
Chat API endpoints
Handles chat threads, messages, and AI responses
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.core.jwt import get_current_active_user
from app.db.models.user import User
from app.db.models.chat import ChatThread, ChatMessage
from app.db.models.file import File as FileModel
from app.schemas.chat import (
    ChatThreadCreate,
    ChatThreadUpdate,
    ChatThreadResponse,
    MessageCreate,
    MessageResponse,
    FileUploadResponse,
    AIResponseRequest,
    ChatHistoryResponse
)
from app.services.chat_service import chat_service
from app.services.file_service import file_service

router = APIRouter()


@router.get("/threads", response_model=List[ChatThreadResponse])
async def list_threads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    lounge_id: Optional[int] = None,
    status: Optional[str] = None
):
    """
    List user's chat threads
    
    - Returns threads owned by current user
    - Supports filtering by lounge and status
    """
    query = db.query(ChatThread).filter(
        ChatThread.user_id == current_user.id
    )
    
    if lounge_id:
        query = query.filter(ChatThread.lounge_id == lounge_id)
    
    if status:
        query = query.filter(ChatThread.status == status)
    
    threads = query.order_by(
        ChatThread.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for thread in threads:
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.thread_id == thread.id
        ).scalar()
        
        last_message = db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread.id
        ).order_by(ChatMessage.created_at.desc()).first()
        
        result.append(ChatThreadResponse(
            id=thread.id,
            user_id=thread.user_id,
            lounge_id=thread.lounge_id,
            title=thread.title,
            status=thread.status,
            created_at=thread.created_at,
            message_count=message_count,
            last_message_at=last_message.created_at if last_message else None,
            lounge_title=thread.lounge.title if thread.lounge else None
        ))
    
    return result


@router.post("/threads", response_model=ChatThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    thread_data: ChatThreadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new chat thread
    
    - Creates thread for current user
    - Optionally associates with lounge
    """
    try:
        thread = await chat_service.create_thread(
            user_id=current_user.id,
            db=db,
            lounge_id=thread_data.lounge_id,
            title=thread_data.title
        )
        
        return ChatThreadResponse(
            id=thread.id,
            user_id=thread.user_id,
            lounge_id=thread.lounge_id,
            title=thread.title,
            status=thread.status,
            created_at=thread.created_at,
            message_count=0,
            last_message_at=None,
            lounge_title=thread.lounge.title if thread.lounge else None
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/threads/{thread_id}", response_model=ChatHistoryResponse)
async def get_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get thread with messages
    
    - Returns thread details and message history
    - Paginated messages
    """
    try:
        messages = await chat_service.get_thread_messages(
            thread_id=thread_id,
            user_id=current_user.id,
            db=db,
            skip=skip,
            limit=limit
        )
        
        thread = db.query(ChatThread).filter(
            ChatThread.id == thread_id
        ).first()
        
        total_messages = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.thread_id == thread_id
        ).scalar()
        
        message_responses = []
        for msg in messages:
            sender_name = None
            sender_avatar = None
            
            if msg.sender_type.value == "user" and msg.user_id:
                user = db.query(User).filter(User.id == msg.user_id).first()
                if user:
                    sender_name = user.name
                    sender_avatar = user.avatar_url
            elif msg.sender_type.value == "ai":
                sender_name = "AI Coach"
            
            attachment_count = len(msg.attachments) if msg.attachments else 0
            
            message_responses.append(MessageResponse(
                id=msg.id,
                thread_id=msg.thread_id,
                sender_type=msg.sender_type,
                user_id=msg.user_id,
                content=msg.content,
                metadata=msg.message_metadata,
                created_at=msg.created_at,
                sender_name=sender_name,
                sender_avatar=sender_avatar,
                has_attachments=attachment_count > 0,
                attachment_count=attachment_count
            ))
        
        thread_response = ChatThreadResponse(
            id=thread.id,
            user_id=thread.user_id,
            lounge_id=thread.lounge_id,
            title=thread.title,
            status=thread.status,
            created_at=thread.created_at,
            message_count=total_messages,
            lounge_title=thread.lounge.title if thread.lounge else None
        )
        
        return ChatHistoryResponse(
            thread=thread_response,
            messages=message_responses,
            total_messages=total_messages
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/threads/{thread_id}", response_model=ChatThreadResponse)
async def update_thread(
    thread_id: int,
    update_data: ChatThreadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update thread details
    
    - Can update title and status
    - Only thread owner can update
    """
    try:
        thread = await chat_service.update_thread(
            thread_id=thread_id,
            user_id=current_user.id,
            db=db,
            title=update_data.title,
            status=update_data.status
        )
        
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.thread_id == thread_id
        ).scalar()
        
        return ChatThreadResponse(
            id=thread.id,
            user_id=thread.user_id,
            lounge_id=thread.lounge_id,
            title=thread.title,
            status=thread.status,
            created_at=thread.created_at,
            message_count=message_count,
            lounge_title=thread.lounge.title if thread.lounge else None
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete thread
    
    - Deletes thread and all messages
    - Only thread owner can delete
    """
    try:
        await chat_service.delete_thread(
            thread_id=thread_id,
            user_id=current_user.id,
            db=db
        )
        return None
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def send_message(
    thread_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    generate_ai: bool = Query(True, description="Generate AI response")
):
    """
    Send message to thread
    
    - Sends user message
    - Optionally generates AI response
    - Supports RAG context
    """
    try:
        user_message, ai_message = await chat_service.send_message(
            thread_id=thread_id,
            user_id=current_user.id,
            content=message_data.content,
            db=db,
            generate_ai_response=generate_ai
        )
        
        responses = []
        
        # User message
        responses.append(MessageResponse(
            id=user_message.id,
            thread_id=user_message.thread_id,
            sender_type=user_message.sender_type,
            user_id=user_message.user_id,
            content=user_message.content,
            metadata=user_message.message_metadata,
            created_at=user_message.created_at,
            sender_name=current_user.name,
            sender_avatar=current_user.avatar_url,
            has_attachments=False,
            attachment_count=0
        ))
        
        # AI message if generated
        if ai_message:
            responses.append(MessageResponse(
                id=ai_message.id,
                thread_id=ai_message.thread_id,
                sender_type=ai_message.sender_type,
                user_id=ai_message.user_id,
                content=ai_message.content,
                metadata=ai_message.message_metadata,
                created_at=ai_message.created_at,
                sender_name="AI Coach",
                sender_avatar=None,
                has_attachments=False,
                attachment_count=0
            ))
        
        return responses
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload file
    
    - Uploads file to S3
    - Returns file metadata
    - Can be attached to messages
    """
    try:
        # Validate file type
        if not file_service.validate_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed"
            )
        
        file_record = await file_service.upload_file(
            file=file,
            user_id=current_user.id,
            db=db
        )
        
        return FileUploadResponse(
            id=file_record.id,
            storage_path=file_record.storage_path,
            mime_type=file_record.mime_type,
            size_bytes=file_record.size_bytes,
            size_mb=file_record.size_mb,
            created_at=file_record.created_at,
            is_image=file_record.is_image,
            is_video=file_record.is_video,
            is_audio=file_record.is_audio,
            is_document=file_record.is_document
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("/files/{file_id}/url")
async def get_file_url(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get file download URL
    
    - Returns presigned URL for file download
    - URL expires in 1 hour
    """
    try:
        url = await file_service.get_file_url(
            file_id=file_id,
            db=db
        )
        
        return {"url": url}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
