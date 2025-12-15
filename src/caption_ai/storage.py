"""SQLite storage for transcript segments."""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from caption_ai.bus import Segment
from caption_ai.config import config


class Storage:
    """SQLite storage manager for segments."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize storage with database path."""
        self.db_path = db_path or config.storage_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    text TEXT NOT NULL,
                    speaker TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON segments(timestamp)
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_session
                ON conversations(session_id, created_at)
                """
            )
            await db.commit()

    async def append(self, segment: Segment) -> None:
        """Append a segment to storage."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO segments (timestamp, text, speaker)
                VALUES (?, ?, ?)
                """
                ,
                (
                    segment.timestamp.isoformat(),
                    segment.text,
                    segment.speaker,
                ),
            )
            await db.commit()

    async def fetch_recent(
        self, limit: int = 10, since: datetime | None = None
    ) -> AsyncIterator[Segment]:
        """Fetch recent segments."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT timestamp, text, speaker FROM segments"
            params: list = []

            if since:
                query += " WHERE timestamp >= ?"
                params.append(since.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    yield Segment(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        text=row["text"],
                        speaker=row["speaker"],
                    )

    async def append_summary(self, summary: str) -> None:
        """Append a summary to storage."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO summaries (summary)
                VALUES (?)
                """,
                (summary,),
            )
            await db.commit()

    async def get_latest_summary(self) -> str | None:
        """Get the latest summary."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT summary FROM summaries ORDER BY created_at DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row["summary"]
                return None

    async def save_conversation(
        self, session_id: str, role: str, message: str
    ) -> None:
        """Save a conversation message."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO conversations (session_id, role, message)
                VALUES (?, ?, ?)
                """,
                (session_id, role, message),
            )
            await db.commit()

    async def get_conversation_history(
        self, session_id: str, limit: int = 50
    ) -> list[dict[str, str]]:
        """Get conversation history for a session."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT role, message, created_at
                FROM conversations
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (session_id, limit),
            ) as cursor:
                conversations = []
                async for row in cursor:
                    conversations.append({
                        "role": row["role"],
                        "message": row["message"],
                        "created_at": row["created_at"],
                    })
                return conversations

    async def get_all_conversations(
        self, limit: int = 100
    ) -> list[dict[str, str]]:
        """Get recent conversations from all sessions."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT session_id, role, message, created_at
                FROM conversations
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ) as cursor:
                conversations = []
                async for row in cursor:
                    conversations.append({
                        "session_id": row["session_id"],
                        "role": row["role"],
                        "message": row["message"],
                        "created_at": row["created_at"],
                    })
                return list(reversed(conversations))

    async def get_conversation_sessions(self) -> list[str]:
        """Get list of unique session IDs."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT DISTINCT session_id
                FROM conversations
                ORDER BY MAX(created_at) DESC
                """
            ) as cursor:
                sessions = []
                async for row in cursor:
                    sessions.append(row["session_id"])
                return sessions

