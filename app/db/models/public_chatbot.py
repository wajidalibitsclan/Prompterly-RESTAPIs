"""
Public Chatbot Configuration model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from datetime import datetime
from app.db.session import Base


class PublicChatbotConfig(Base):
    """Configuration for the public website chatbot"""

    __tablename__ = "public_chatbot_config"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Chatbot identity
    name = Column(String(100), default="Prompterly Assistant", nullable=False)
    welcome_message = Column(Text, default="Hi! How can I help you today?", nullable=False)

    # System prompt for AI behavior
    system_prompt = Column(Text, nullable=True)

    # Embedding for RAG
    system_prompt_embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(100), nullable=True)

    # Placeholder text for input
    input_placeholder = Column(String(255), default="What's on your mind?", nullable=False)

    # Header subtitle/description
    header_subtitle = Column(Text, default="Lorem ipsum dolor sit amet, consectetur adipiscing elit.", nullable=True)

    # Enable/disable the chatbot
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Avatar image URL (optional)
    avatar_url = Column(String(500), nullable=True)

    # RAG settings
    use_rag = Column(Boolean, default=True, nullable=False)
    rag_similarity_threshold = Column(Integer, default=70, nullable=False)  # 0-100 percentage

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PublicChatbotConfig(id={self.id}, name={self.name}, enabled={self.is_enabled})>"


class PublicChatMessage(Base):
    """Store public chatbot conversation messages"""

    __tablename__ = "public_chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Session identifier (for anonymous users)
    session_id = Column(String(100), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PublicChatMessage(id={self.id}, session={self.session_id}, role={self.role})>"
