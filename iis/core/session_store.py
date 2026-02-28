from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import ChatSession, ChatMessage
import json

class SessionStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(self, session_id: str, user_id: str, model_id: str = None) -> ChatSession:
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        
        if not session:
            session = ChatSession(id=session_id, user_id=user_id, model_id=model_id)
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            # Enforce retention policy after creating new session to ensure strict limit
            await self.enforce_retention_policy(user_id)
        
        return session

    async def enforce_retention_policy(self, user_id: str):
        """
        Keeps only the last 20 sessions AND ensures none are older than 5 days.
        """
        from datetime import datetime, timedelta
        from sqlalchemy import delete, desc
        
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        
        # 1. Delete sessions older than 5 days
        # We find IDs first to delete messages, then sessions
        old_sessions = await self.db.execute(
            select(ChatSession.id)
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.updated_at < five_days_ago)
        )
        old_ids = [s[0] for s in old_sessions.all()]
        
        if old_ids:
            # Delete messages first (SQLAlchemy bulk delete doesn't always cascade)
            await self.db.execute(
                delete(ChatMessage).where(ChatMessage.session_id.in_(old_ids))
            )
            await self.db.execute(
                delete(ChatSession).where(ChatSession.id.in_(old_ids))
            )
        
        # 2. Limit to last 20 sessions
        latest_sessions = await self.db.execute(
            select(ChatSession.id)
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
            .limit(20)
        )
        keep_ids = [s[0] for s in latest_sessions.all()]
        
        if keep_ids:
            # Find IDs that are NOT in the keep list
            to_delete_res = await self.db.execute(
                select(ChatSession.id)
                .where(ChatSession.user_id == user_id)
                .where(ChatSession.id.not_in(keep_ids))
            )
            to_delete_ids = [s[0] for s in to_delete_res.all()]
            
            if to_delete_ids:
                # Delete messages first
                await self.db.execute(
                    delete(ChatMessage).where(ChatMessage.session_id.in_(to_delete_ids))
                )
                await self.db.execute(
                    delete(ChatSession).where(ChatSession.id.in_(to_delete_ids))
                )
        
        await self.db.commit()

    async def update_session_title(self, session_id: str, title: str):
        """Update the human-readable title of a session."""
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.title = title
            await self.db.commit()

    async def add_message(self, session_id: str, role: str, content: str, msg_type: str = "text", manifest: dict = None):
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            type=msg_type,
            manifest=manifest
        )
        self.db.add(msg)
        await self.db.commit()

    async def get_history(self, session_id: str) -> List[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return result.scalars().all()

    async def save_agent_state(self, session_id: str, state: dict):
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.state = state
            await self.db.commit()

    async def load_agent_state(self, session_id: str) -> Optional[dict]:
        result = await self.db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        return session.state if session else None

    async def delete_session(self, session_id: str, user_id: str):
        """Delete a chat session and its messages."""
        from sqlalchemy import delete
        
        # 1. Verify ownership before deleting
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()
        
        if session:
            # 2. Delete messages first
            await self.db.execute(
                delete(ChatMessage).where(ChatMessage.session_id == session_id)
            )
            # 3. Delete the session
            await self.db.execute(
                delete(ChatSession).where(ChatSession.id == session_id)
            )
            await self.db.commit()
            return True
        return False
