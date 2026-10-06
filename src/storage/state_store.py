from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

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
                CREATE TABLE IF NOT EXISTS agent_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    tools_json TEXT NOT NULL,
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

    def save_agent_call(self, call: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_calls
                (task_id, agent, status, duration_ms, tools_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    call["task_id"],
                    call["agent"],
                    call["status"],
                    call["duration_ms"],
                    json.dumps(call.get("tools", []), ensure_ascii=False),
                ),
            )

    def call_distribution(self, task_id: str) -> dict[str, dict[str, float]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT agent, COUNT(*)
                FROM agent_calls
                WHERE task_id = ? AND status = 'OK'
                GROUP BY agent
                """,
                (task_id,),
            ).fetchall()
        total = sum(count for _, count in rows) or 1
        return {
            agent: {"calls": count, "share_percent": round((count / total) * 100, 1)}
            for agent, count in rows
        }
