"""Persistência do histórico de conversas em SQLite, indexado por usuário.

Cada usuário (admin/usuario/...) possui sua própria conversa, que sobrevive a
reinicializações do servidor. O acesso é serializado por um lock e usa uma
conexão por operação, evitando problemas de concorrência entre threads
(gunicorn gthread).
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional


class HistoryStore:
    """Armazena e recupera mensagens de chat por usuário."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = str(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._lock, self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_username ON messages(username, id)"
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS privacy_consents (
                    username TEXT PRIMARY KEY,
                    notice_version TEXT NOT NULL,
                    history_enabled INTEGER NOT NULL DEFAULT 1,
                    accepted_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )

    def append(self, username: str, role: str, content: str) -> None:
        """Acrescenta uma mensagem ao histórico do usuário."""
        if not username:
            return
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO messages (username, role, content) VALUES (?, ?, ?)",
                (username, role, content),
            )

    def get(self, username: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Retorna as mensagens do usuário em ordem cronológica.

        Se ``limit`` for informado, retorna apenas as ``limit`` mais recentes
        (ainda em ordem cronológica).
        """
        if not username:
            return []
        with self._lock, self._connect() as con:
            if limit and limit > 0:
                rows = con.execute(
                    "SELECT role, content FROM messages WHERE username = ? "
                    "ORDER BY id DESC LIMIT ?",
                    (username, limit),
                ).fetchall()
                rows = list(reversed(rows))
            else:
                rows = con.execute(
                    "SELECT role, content FROM messages WHERE username = ? ORDER BY id ASC",
                    (username,),
                ).fetchall()
        return [{"role": role, "content": content} for role, content in rows]

    def clear(self, username: str) -> None:
        """Remove todo o histórico do usuário."""
        if not username:
            return
        with self._lock, self._connect() as con:
            con.execute("DELETE FROM messages WHERE username = ?", (username,))

    def get_consent(self, username: str) -> Optional[Dict[str, str | int]]:
        if not username:
            return None
        with self._lock, self._connect() as con:
            row = con.execute(
                "SELECT notice_version, history_enabled, accepted_at "
                "FROM privacy_consents WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            return None
        return {
            "notice_version": row[0],
            "history_enabled": bool(row[1]),
            "accepted_at": row[2],
        }

    def save_consent(self, username: str, notice_version: str, history_enabled: bool) -> None:
        if not username:
            return
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO privacy_consents "
                "(username, notice_version, history_enabled) VALUES (?, ?, ?) "
                "ON CONFLICT(username) DO UPDATE SET notice_version=excluded.notice_version, "
                "history_enabled=excluded.history_enabled, accepted_at=datetime('now')",
                (username, notice_version, int(history_enabled)),
            )

    def export_user_data(self, username: str) -> Dict[str, object]:
        if not username:
            return {"consentimento": None, "mensagens": []}
        with self._lock, self._connect() as con:
            messages = con.execute(
                "SELECT role, content, created_at FROM messages "
                "WHERE username = ? ORDER BY id ASC",
                (username,),
            ).fetchall()
            consent_row = con.execute(
                "SELECT notice_version, history_enabled, accepted_at "
                "FROM privacy_consents WHERE username = ?",
                (username,),
            ).fetchone()
        consent = (
            {
                "notice_version": consent_row[0],
                "history_enabled": bool(consent_row[1]),
                "accepted_at": consent_row[2],
            }
            if consent_row
            else None
        )
        return {
            "consentimento": consent,
            "mensagens": [
                {"role": role, "content": content, "created_at": created_at}
                for role, content, created_at in messages
            ],
        }

    def delete_user_data(self, username: str) -> None:
        if not username:
            return
        with self._lock, self._connect() as con:
            con.execute("DELETE FROM messages WHERE username = ?", (username,))
            con.execute("DELETE FROM privacy_consents WHERE username = ?", (username,))

    def purge_older_than(self, retention_days: int) -> int:
        """Remove mensagens antigas; zero mantém a retenção atual indefinida."""
        if retention_days <= 0:
            return 0
        with self._lock, self._connect() as con:
            cursor = con.execute(
                "DELETE FROM messages WHERE created_at < datetime('now', ?)",
                (f"-{retention_days} days",),
            )
            return cursor.rowcount
