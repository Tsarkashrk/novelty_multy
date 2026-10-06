from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentMessage:
    task_id: str
    sender: str
    recipient: str
    message_type: str
    payload: dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentError(RuntimeError):
    """Raised when an agent cannot complete its assigned task."""


class BaseAgent:
    name = "base_agent"
    role = "Base agent"
    tools: list[str] = []

    def run(self, message: AgentMessage, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
