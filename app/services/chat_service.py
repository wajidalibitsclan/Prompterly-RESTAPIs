"""
Chat service for managing conversations and AI responses
Includes RAG (Retrieval Augmented Generation) support
"""
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.db.models.chat import ChatThread, ChatMessage, SenderType, ThreadStatus
from app.db.models.note import Note
from app.db.models.lounge import Lounge, LoungeMembership
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat threads and messages"""
    
    def __init__(self):
        """Initialize chat service"""
        self.ai_service = ai_service
    
    async def create_thread(
        self,
        user_id: int,
        db: Session,
        lounge_id: Optional[int] = None,
        title: Optional[str] = None
    ) -> ChatThread:
        """
        Create new chat thread
        
        Args:
            user_id: User ID
            db: Database session
            lounge_id: Optional lounge ID
            title: Optional thread title
            
        Returns:
            ChatThread instance
        """
        # Verify lounge access if lounge_id provided
        if lounge_id:
            membership = db.query(LoungeMembership).filter(
                LoungeMembership.lounge_id == lounge_id,
                LoungeMembership.user_id == user_id,
                LoungeMembership.left_at.is_(None)
            ).first()
            
            if not membership:
                raise ValueError("User is not a member of this lounge")
        
        # Generate title if not provided
        if not title:
            thread_count = db.query(func.count(ChatThread.id)).filter(
                ChatThread.user_id == user_id
            ).scalar()
            title = f"Conversation {thread_count + 1}"
        
        thread = ChatThread(
            user_id=user_id,
            lounge_id=lounge_id,
            title=title,
            status=ThreadStatus.OPEN
        )
        
        db.add(thread)
        db.commit()
        db.refresh(thread)
        
        return thread
    
    async def send_message(
        self,
        thread_id: int,
        user_id: int,
        content: str,
        db: Session,
        generate_ai_response: bool = True,
        use_rag: bool = True,
        use_anthropic: bool = False
    ) -> Tuple[ChatMessage, Optional[ChatMessage]]:
        """
        Send message and optionally generate AI response
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            content: Message content
            db: Database session
            generate_ai_response: Whether to generate AI response
            use_rag: Whether to use RAG for context
            use_anthropic: Use Anthropic Claude instead of OpenAI
            
        Returns:
            Tuple of (user_message, ai_message or None)
        """
        # Verify thread access
        thread = db.query(ChatThread).filter(
            ChatThread.id == thread_id,
            ChatThread.user_id == user_id
        ).first()
        
        if not thread:
            raise ValueError("Thread not found or access denied")
        
        if thread.status == ThreadStatus.ARCHIVED:
            raise ValueError("Cannot send messages to archived thread")
        
        # Create user message
        user_message = ChatMessage(
            thread_id=thread_id,
            sender_type=SenderType.USER,
            user_id=user_id,
            content=content
        )
        
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        ai_message = None
        
        if generate_ai_response:
            try:
                # Get conversation history
                history = await self._get_conversation_history(thread_id, db)
                
                # Get RAG context if enabled
                context = None
                if use_rag:
                    context = await self._get_rag_context(user_id, content, db)
                
                # Generate AI response
                ai_response, metadata = await self.ai_service.generate_chat_response(
                    messages=history,
                    context=context,
                    use_anthropic=use_anthropic
                )
                
                # Create AI message
                ai_message = ChatMessage(
                    thread_id=thread_id,
                    sender_type=SenderType.AI,
                    content=ai_response,
                    message_metadata=metadata
                )
                
                db.add(ai_message)
                db.commit()
                db.refresh(ai_message)
                
            except Exception as e:
                logger.error(f"Error generating AI response: {str(e)}")
                # Continue even if AI response fails
        
        return user_message, ai_message
    
    async def _get_conversation_history(
        self,
        thread_id: int,
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for AI context
        
        Args:
            thread_id: Thread ID
            db: Database session
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries for AI
        """
        messages = db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread_id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        history = []
        for msg in messages:
            if msg.sender_type == SenderType.USER:
                history.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.sender_type == SenderType.AI:
                history.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        return history
    
    async def _get_rag_context(
        self,
        user_id: int,
        query: str,
        db: Session,
        top_k: int = 3
    ) -> Optional[str]:
        """
        Get RAG context from user's notes
        
        Args:
            user_id: User ID
            query: Query text
            db: Database session
            top_k: Number of top results to include
            
        Returns:
            Context string or None
        """
        try:
            # Get user's notes that are included in RAG
            notes = db.query(Note).filter(
                Note.user_id == user_id,
                Note.is_included_in_rag == True
            ).all()
            
            if not notes:
                return None
            
            # Create query embedding
            query_embedding = await self.ai_service.create_embedding(query)
            
            # For now, use simple keyword matching
            # In production, you'd use vector database like Pinecone, Weaviate, etc.
            relevant_notes = []
            query_lower = query.lower()
            
            for note in notes:
                # Simple relevance scoring based on keyword matching
                content_lower = (note.title + " " + note.content).lower()
                score = sum(1 for word in query_lower.split() if word in content_lower)
                
                if score > 0:
                    relevant_notes.append((note, score))
            
            # Sort by relevance
            relevant_notes.sort(key=lambda x: x[1], reverse=True)
            
            # Take top_k most relevant notes
            top_notes = relevant_notes[:top_k]
            
            if not top_notes:
                return None
            
            # Build context string
            context_parts = []
            for note, score in top_notes:
                context_parts.append(
                    f"Note: {note.title}\n{note.content[:500]}"  # Limit length
                )
            
            context = "\n\n---\n\n".join(context_parts)
            
            return context
        
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return None
    
    async def get_thread_messages(
        self,
        thread_id: int,
        user_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Get messages in a thread
        
        Args:
            thread_id: Thread ID
            user_id: User ID (for authorization)
            db: Database session
            skip: Number of messages to skip
            limit: Maximum number of messages
            
        Returns:
            List of ChatMessage instances
        """
        # Verify thread access
        thread = db.query(ChatThread).filter(
            ChatThread.id == thread_id,
            ChatThread.user_id == user_id
        ).first()
        
        if not thread:
            raise ValueError("Thread not found or access denied")
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.thread_id == thread_id
        ).order_by(
            ChatMessage.created_at.asc()
        ).offset(skip).limit(limit).all()
        
        return messages
    
    async def update_thread(
        self,
        thread_id: int,
        user_id: int,
        db: Session,
        title: Optional[str] = None,
        status: Optional[ThreadStatus] = None
    ) -> ChatThread:
        """
        Update thread details
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            db: Database session
            title: New title
            status: New status
            
        Returns:
            Updated ChatThread instance
        """
        thread = db.query(ChatThread).filter(
            ChatThread.id == thread_id,
            ChatThread.user_id == user_id
        ).first()
        
        if not thread:
            raise ValueError("Thread not found or access denied")
        
        if title is not None:
            thread.title = title
        
        if status is not None:
            thread.status = status
        
        db.commit()
        db.refresh(thread)
        
        return thread
    
    async def delete_thread(
        self,
        thread_id: int,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Delete thread and all messages
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            db: Database session
            
        Returns:
            True if successful
        """
        thread = db.query(ChatThread).filter(
            ChatThread.id == thread_id,
            ChatThread.user_id == user_id
        ).first()
        
        if not thread:
            raise ValueError("Thread not found or access denied")
        
        db.delete(thread)
        db.commit()
        
        return True


# Singleton instance
chat_service = ChatService()
