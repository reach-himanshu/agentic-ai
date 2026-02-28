import os
import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship

# Database URL - Enforce PostgreSQL (asyncpg)
# Falls back to a default postgres URL if not provided, but assumes postgres is the target
DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://opsiq:opsiqpassword@localhost:5432/opsiq_sessions")

# Engine & Session
engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)  # custom session id
    user_id = Column(String, index=True)
    title = Column(String, default="New Chat")
    model_id = Column(String)
    state = Column(JSON, nullable=True)     # For agent state serialization
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role = Column(String)  # 'user', 'assistant', 'system'
    content = Column(Text)
    type = Column(String)  # 'text', 'manifest', 'pills', etc.
    manifest = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")

class UserCredential(Base):
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String, index=True) # e.g. 'servicenow'
    user_email = Column(String, index=True)
    access_token = Column(Text)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class TimeEntry(Base):
    """Time entry for tracking billable and non-billable hours."""
    __tablename__ = "time_entries"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, index=True)
    
    # Week and date
    week_start = Column(DateTime(timezone=True))  # Monday of the week
    entry_date = Column(DateTime(timezone=True))  # Specific date
    
    # Project info (nullable for internal codes like FIRM-MTG)
    project_id = Column(String, nullable=True)
    project_name = Column(String)
    
    # Time classification
    time_code = Column(String)  # CONSULT-BILL, FIRM-MTG, etc.
    
    # Hours and notes
    hours = Column(String)  # Store as string for flexibility (e.g., "2.5")
    notes = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String, default="draft")  # draft, saved, submitted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
