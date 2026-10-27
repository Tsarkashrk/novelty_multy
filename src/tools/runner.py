from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from src.agents.base import AgentError, ExecutionTimeout, TransientAgentError
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore


class ToolRunner:
    def __init__(
        self,
        task_id: str,
        agent: str,
        allowed: list[str],
        attempt: int,
        deadline: float,
        state_store: StateStore,
        logger: AgentLogger,
    ) -> None:
        self.task_id = task_id
        self.agent = agent
        self.allowed = set(allowed)
        self.attempt = attempt
        self.deadline = deadline
        self.state_store = state_store
        self.logger = logger

    def call(self, name: str, function: Callable[..., Any], *args: Any) -> Any:
        if name not in self.allowed:
            raise AgentError(f"Tool {name} is not allowed for {self.agent}.")
        if time.monotonic() >= self.deadline:
            raise ExecutionTimeout("Task time limit exceeded.")

        started = time.perf_counter()
        status = "OK"
        error = None
        try:
            return function(*args)
        except ExecutionTimeout as exc:
            status, error = "TIMEOUT", str(exc)
            raise
        except (OSError, TimeoutError) as exc:
            status, error = "ERROR", str(exc)
            raise TransientAgentError(f"Tool {name} failed: {exc}") from exc
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            status, error = "ERROR", str(exc)
            raise AgentError(f"Tool {name} received invalid data: {exc}") from exc
        except AgentError as exc:
            status, error = "ERROR", str(exc)
            raise
        except Exception as exc:
            status, error = "ERROR", str(exc)
            raise
        finally:
            event = {
                "task_id": self.task_id,
                "agent": self.agent,
                "event_type": "TOOL",
                "name": name,
                "status": status,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "attempt": self.attempt,
                "error": error,
            }
            self.state_store.save_call_event(event)
            self.logger.log(event)
