from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS call_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    attempt INTEGER NOT NULL,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save_task_state(self, task_id: str, state: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (task_id, state_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(task_id)
                DO UPDATE SET state_json = excluded.state_json,
                              updated_at = CURRENT_TIMESTAMP
                """,
                (task_id, json.dumps(state, ensure_ascii=False)),
            )

    def save_message(self, message: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO messages
                (message_id, task_id, sender, recipient, message_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message["message_id"],
                    message["task_id"],
                    message["sender"],
                    message["recipient"],
                    message["message_type"],
                    json.dumps(message["payload"], ensure_ascii=False),
                    message["created_at"],
                ),
            )

    def save_call_event(self, event: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO call_events
                (task_id, agent, event_type, name, status, duration_ms, attempt, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["task_id"], event["agent"], event["event_type"],
                    event["name"], event["status"], event["duration_ms"],
                    event["attempt"], event.get("error"),
                ),
            )

    def call_distribution(self, task_id: str) -> dict[str, dict[str, float]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT agent, COUNT(*)
                FROM call_events
                WHERE task_id = ? AND event_type IN ('TOOL', 'LLM')
                GROUP BY agent
                """,
                (task_id,),
            ).fetchall()
        total = sum(count for _, count in rows) or 1
        return {
            agent: {"calls": count, "share_percent": round((count / total) * 100, 1)}
            for agent, count in rows
        }
