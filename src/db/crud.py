# src/db/crud.py
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import User, SessionLog

async def create_user(db: AsyncSession, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def create_session_log(db: AsyncSession, session_id: str, user_id: UUID | None = None) -> SessionLog:
    session_log = SessionLog(session_id=session_id, user_id=user_id)
    db.add(session_log)
    await db.commit()
    await db.refresh(session_log)
    return session_log

async def update_session_log(db: AsyncSession, session_id: str, ended_at: datetime, token_usage: dict):
    # Update session log with end time and token usage
    result = await db.execute(select(SessionLog).where(SessionLog.session_id == session_id))
    session_log = result.scalar_one_or_none()
    
    if session_log:
        session_log.ended_at = ended_at
        session_log.token_usage_json = token_usage
        await db.commit()
