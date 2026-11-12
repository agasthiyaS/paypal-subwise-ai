import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def generate_conversation_id() -> str:
    return f"conv_{uuid.uuid4().hex[:16]}"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True, default=generate_conversation_id, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    account_type = Column(String(32), nullable=False, default="business", index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="conversations")
    business = relationship("BusinessProfile")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at.asc()")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)  # provider, is_ai_generated, generation_model, intent, evidence_cards, actions, etc.

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
