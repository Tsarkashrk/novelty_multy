from __future__ import annotations

import signal
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.agents.base import AgentError, AgentMessage, BaseAgent, ExecutionTimeout, TransientAgentError
from src.agents.cycle_monitor_agent import CompletionCycleMonitorAgent
from src.agents.duplicate_agent import DuplicationControlAgent
from src.agents.intake_agent import TopicIntakeAgent
from src.agents.novelty_agent import NoveltyAssessmentAgent
from src.agents.quality_gate_agent import QualityGateAgent
from src.agents.supervisor_agent import SupervisorMatchingAgent
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore
from src.tools.runner import ToolRunner


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def task_timer(seconds: float):
    if not hasattr(signal, "setitimer") or threading.current_thread() is not threading.main_thread():
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_remaining, previous_interval = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()

    def expire(_signum: int, _frame: Any) -> None:
        raise ExecutionTimeout("Task time limit exceeded.")

    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, min(seconds, previous_remaining) if previous_remaining else seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_remaining:
            signal.setitimer(signal.ITIMER_REAL, max(0.000001, previous_remaining - (time.monotonic() - started)), previous_interval)


class Orchestrator:
    def __init__(
        self,
        state_store: StateStore | None = None,
        logger: AgentLogger | None = None,
        max_agent_retries: int = 1,
        max_steps: int = 10,
        max_runtime_seconds: float = 10.0,
        agents: list[BaseAgent] | None = None,
    ) -> None:
        if max_steps < 1 or max_runtime_seconds <= 0 or max_agent_retries < 0:
            raise ValueError("Runtime limits must be positive; retries cannot be negative.")
        self.state_store = state_store or StateStore(PROJECT_ROOT / "runtime" / "state.db")
        self.logger = logger or AgentLogger(PROJECT_ROOT / "runtime" / "agent_calls.jsonl")
        self.max_agent_retries = max_agent_retries
        self.max_steps = max_steps
        self.max_runtime_seconds = max_runtime_seconds
        self.agents = agents if agents is not None else [
            TopicIntakeAgent(), NoveltyAssessmentAgent(), DuplicationControlAgent(),
            SupervisorMatchingAgent(), CompletionCycleMonitorAgent(), QualityGateAgent(),
        ]
        if any(len(agent.tools) > 5 for agent in self.agents):
            raise ValueError("Each agent may have at most five tools.")

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        task_id = str(uuid4())
        state: dict[str, Any] = {"task_id": task_id, "request": request, "agent_outputs": {}, "status": "RUNNING", "errors": []}
        self.state_store.save_task_state(task_id, state)
        deadline = time.monotonic() + self.max_runtime_seconds
        failed_agent = None

        try:
            with task_timer(self.max_runtime_seconds):
                for step_index, agent in enumerate(self.agents, start=1):
                    if step_index > self.max_steps:
                        raise AgentError(f"Step limit of {self.max_steps} reached.")
                    if time.monotonic() >= deadline:
                        raise ExecutionTimeout("Task time limit exceeded.")
                    failed_agent = agent.name
                    message = AgentMessage(
                        task_id=task_id, sender="orchestrator", recipient=agent.name,
                        message_type="RUN_AGENT",
                        payload={"request": request, "previous_outputs": state["agent_outputs"]},
                    )
                    self.state_store.save_message(message.to_dict())
                    output = self._execute_agent(agent, message, step_index, deadline)
                    response = AgentMessage(
                        task_id=task_id, sender=agent.name, recipient="orchestrator",
                        message_type="AGENT_RESULT", payload=output,
                    )
                    self.state_store.save_message(response.to_dict())
                    state["agent_outputs"][agent.name] = output
                    self.state_store.save_task_state(task_id, state)
        except Exception as exc:
            state["status"] = "FAILED"
            state["errors"].append({"agent": failed_agent, "type": type(exc).__name__, "message": str(exc)})
        else:
            state["status"] = "COMPLETED"

        distribution = self.state_store.call_distribution(task_id)
        report = {
            "task_id": task_id,
            "status": state["status"],
            "final_decision": state["agent_outputs"].get("quality_gate_agent", {}).get("quality_gate_report", {}).get("decision"),
            "agent_outputs": state["agent_outputs"],
            "errors": state["errors"],
            "steps_executed": len(state["agent_outputs"]),
            "call_distribution": distribution,
            "balanced_load": state["status"] == "COMPLETED" and bool(distribution) and all(item["share_percent"] <= 40.0 for item in distribution.values()),
            "load_metric": "actual TOOL and LLM calls, including failed attempts",
        }
        self.state_store.save_task_state(task_id, report)
        return report

    def _execute_agent(self, agent: BaseAgent, message: AgentMessage, step_index: int, deadline: float) -> dict[str, Any]:
        for attempt in range(1, self.max_agent_retries + 2):
            if time.monotonic() >= deadline:
                raise ExecutionTimeout("Task time limit exceeded.")
            tools = ToolRunner(message.task_id, agent.name, agent.tools, attempt, deadline, self.state_store, self.logger)
            started = time.perf_counter()
            status, error = "OK", None
            try:
                output = agent.run(message, {"tools": tools})
                if not isinstance(output, dict):
                    raise AgentError("Agent must return a JSON object.")
                return output
            except ExecutionTimeout as exc:
                status, error = "TIMEOUT", str(exc)
                raise
            except TransientAgentError as exc:
                status, error = "ERROR", str(exc)
                if attempt > self.max_agent_retries:
                    raise AgentError(f"{agent.name} failed after {attempt} attempts: {exc}") from exc
            except AgentError as exc:
                status, error = "ERROR", str(exc)
                raise
            except Exception as exc:
                status, error = "ERROR", str(exc)
                raise AgentError(f"{agent.name} failed unexpectedly: {exc}") from exc
            finally:
                event = {
                    "task_id": message.task_id, "agent": agent.name, "event_type": "AGENT",
                    "name": agent.name, "role": agent.role, "status": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    "step_index": step_index, "attempt": attempt, "error": error,
                }
                self.state_store.save_call_event(event)
                self.logger.log(event)
        raise AssertionError("Retry loop exited without a result.")
