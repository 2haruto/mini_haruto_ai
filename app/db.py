from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
import uuid


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    created_at: str


class ChatRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
                """
            )

    def create_session(self, title: str | None = None) -> str:
        session_id = str(uuid.uuid4())
        created_at = _now_iso()
        if not title:
            title = "New chat"

        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions(session_id, title, created_at) VALUES (?, ?, ?)",
                (session_id, title, created_at),
            )
        return session_id

    def session_exists(self, session_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1", (session_id,)
            ).fetchone()
        return row is not None

    def list_sessions(self, limit: int = 20) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, title, created_at
                FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "session_id": row["session_id"],
                "title": row["title"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages(session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, _now_iso()),
            )

    def get_messages(self, session_id: str, limit: int = 16) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY message_id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        rows = list(reversed(rows))
        return [
            Message(role=row["role"], content=row["content"], created_at=row["created_at"])
            for row in rows
        ]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
