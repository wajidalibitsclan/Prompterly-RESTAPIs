"""
Public Chatbot Service
Handles the public website chatbot functionality with RAG support
"""
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from sqlalchemy.orm import Session
import logging
import uuid

from app.db.models.public_chatbot import PublicChatbotConfig, PublicChatMessage
from app.services.ai_service import ai_service
from app.services.knowledge_base_service import knowledge_base_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class PublicChatbotService:
    """Service for managing public chatbot with RAG support"""

    def __init__(self):
        self.ai_service = ai_service
        self.kb_service = knowledge_base_service

    # ============== Config Operations ==============

    async def get_config(self, db: Session) -> Optional[PublicChatbotConfig]:
        """Get the chatbot configuration"""
        return db.query(PublicChatbotConfig).first()

    async def update_config(
        self,
        db: Session,
        data: Dict[str, Any]
    ) -> PublicChatbotConfig:
        """Update or create chatbot configuration with embedding generation"""
        config = await self.get_config(db)

        # Filter out empty strings for required fields (let DB defaults apply)
        required_fields_with_defaults = {'name', 'welcome_message', 'input_placeholder'}
        # Nullable fields should convert empty string to None
        nullable_fields = {'system_prompt', 'header_subtitle', 'avatar_url'}

        filtered_data = {}
        for k, v in data.items():
            if k in required_fields_with_defaults and v == '':
                # Skip empty required fields to use DB defaults
                continue
            elif k in nullable_fields and v == '':
                # Convert empty strings to None for nullable fields
                filtered_data[k] = None
            else:
                filtered_data[k] = v

        if not config:
            # Create new config with filtered data
            config = PublicChatbotConfig(**filtered_data)
            db.add(config)
        else:
            # Update existing config
            for key, value in filtered_data.items():
                if value is not None and hasattr(config, key):
                    setattr(config, key, value)

        # Generate embedding for system prompt if it was updated
        system_prompt = data.get('system_prompt') or (config.system_prompt if config else None)
        if system_prompt:
            try:
                embedding = await self.ai_service.create_embedding(system_prompt)
                config.system_prompt_embedding = embedding
                config.embedding_model = settings.EMBEDDING_MODEL
                logger.info("Generated embedding for public chatbot system prompt")
            except Exception as e:
                logger.error(f"Failed to generate embedding for system prompt: {e}")

        db.commit()
        db.refresh(config)
        return config

    # ============== RAG Operations ==============

    async def get_rag_context(
        self,
        db: Session,
        query: str,
        similarity_threshold: float = 0.7
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Get RAG context for the query using knowledge base"""
        try:
            context, sources = await self.kb_service.get_rag_context(
                db=db,
                query=query,
                max_items=5,
                entity_types=None,  # Search all types
                lounge_id=None,  # Use global KB
                include_global=True,
                similarity_threshold=similarity_threshold
            )
            logger.info(f"RAG context retrieved: {len(sources)} sources found")
            return context, sources
        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            return "", []

    def _build_system_prompt_with_rag(
        self,
        base_prompt: str,
        rag_context: str
    ) -> str:
        """Build system prompt with RAG context injected"""
        if not rag_context:
            return base_prompt

        return f"""{base_prompt}

=== RELEVANT KNOWLEDGE ===
Use the following information to help answer the user's questions. If the information is relevant, incorporate it into your response naturally.

{rag_context}

=== END OF KNOWLEDGE ===

Remember: Use the knowledge above when relevant, but also rely on your general capabilities to provide helpful responses. If the user asks about something not covered in the knowledge base, provide the best response you can."""

    # ============== Chat Operations ==============

    def generate_session_id(self) -> str:
        """Generate a unique session ID for anonymous users"""
        return str(uuid.uuid4())

    async def get_conversation_history(
        self,
        session_id: str,
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        messages = db.query(PublicChatMessage).filter(
            PublicChatMessage.session_id == session_id
        ).order_by(
            PublicChatMessage.created_at.desc()
        ).limit(limit).all()

        # Reverse to get chronological order
        messages = list(reversed(messages))

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        db: Session
    ) -> PublicChatMessage:
        """Save a message to the database"""
        message = PublicChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    async def send_message(
        self,
        session_id: str,
        content: str,
        db: Session
    ) -> Dict[str, Any]:
        """Send a message and get AI response with RAG"""
        # Get config
        config = await self.get_config(db)
        if not config or not config.is_enabled:
            raise ValueError("Chatbot is currently disabled")

        # Save user message
        await self.save_message(session_id, "user", content, db)

        # Get conversation history
        history = await self.get_conversation_history(session_id, db)

        # Build base system prompt
        base_prompt = config.system_prompt or "You are a helpful assistant for Prompterly."

        # Get RAG context if enabled
        rag_context = ""
        sources = []
        if getattr(config, 'use_rag', True):
            similarity_threshold = getattr(config, 'rag_similarity_threshold', 70) / 100.0
            rag_context, sources = await self.get_rag_context(
                db, content, similarity_threshold
            )

        # Build final system prompt with RAG context
        system_prompt = self._build_system_prompt_with_rag(base_prompt, rag_context)

        # Generate AI response
        try:
            ai_response, metadata = await self.ai_service.generate_chat_response(
                messages=history,
                context=system_prompt,
                use_anthropic=False
            )

            # Save AI response
            await self.save_message(session_id, "assistant", ai_response, db)

            return {
                "response": ai_response,
                "session_id": session_id,
                "sources": sources if sources else None
            }
        except Exception as e:
            logger.error(f"Error generating chatbot response: {str(e)}")
            raise ValueError(f"Failed to generate response: {str(e)}")

    async def send_message_stream(
        self,
        session_id: str,
        content: str,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message and stream AI response with RAG"""
        # Get config
        config = await self.get_config(db)
        if not config or not config.is_enabled:
            yield {
                "event": "error",
                "data": {"error": "Chatbot is currently disabled"}
            }
            return

        # Save user message
        user_msg = await self.save_message(session_id, "user", content, db)

        # Yield user message event
        yield {
            "event": "user_message",
            "data": {
                "id": user_msg.id,
                "role": "user",
                "content": content
            }
        }

        # Get conversation history
        history = await self.get_conversation_history(session_id, db)

        # Build base system prompt
        base_prompt = config.system_prompt or "You are a helpful assistant for Prompterly."

        # Get RAG context if enabled
        rag_context = ""
        sources = []
        if getattr(config, 'use_rag', True):
            similarity_threshold = getattr(config, 'rag_similarity_threshold', 70) / 100.0
            rag_context, sources = await self.get_rag_context(
                db, content, similarity_threshold
            )

        # Yield RAG sources if found
        if sources:
            yield {
                "event": "rag_sources",
                "data": {"sources": sources}
            }

        # Build final system prompt with RAG context
        system_prompt = self._build_system_prompt_with_rag(base_prompt, rag_context)

        try:
            # Stream AI response
            full_response = ""
            async for chunk in self.ai_service.generate_chat_response_stream(
                messages=history,
                context=system_prompt
            ):
                full_response += chunk
                yield {
                    "event": "ai_chunk",
                    "data": {"content": chunk}
                }

            # Save AI response after streaming completes
            ai_msg = await self.save_message(session_id, "assistant", full_response, db)

            # Yield completion event
            yield {
                "event": "ai_complete",
                "data": {
                    "id": ai_msg.id,
                    "role": "assistant",
                    "content": full_response,
                    "sources": sources if sources else None
                }
            }

        except Exception as e:
            logger.error(f"Error streaming chatbot response: {str(e)}")
            yield {
                "event": "error",
                "data": {"error": str(e)}
            }

    async def clear_session(self, session_id: str, db: Session) -> bool:
        """Clear all messages for a session"""
        db.query(PublicChatMessage).filter(
            PublicChatMessage.session_id == session_id
        ).delete()
        db.commit()
        return True


# Singleton instance
public_chatbot_service = PublicChatbotService()
