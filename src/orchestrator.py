from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.agents.base import AgentError, AgentMessage, BaseAgent
from src.agents.cycle_monitor_agent import CompletionCycleMonitorAgent
from src.agents.duplicate_agent import DuplicationControlAgent
from src.agents.intake_agent import TopicIntakeAgent
from src.agents.novelty_agent import NoveltyAssessmentAgent
from src.agents.quality_gate_agent import QualityGateAgent
from src.agents.supervisor_agent import SupervisorMatchingAgent
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Orchestrator:
    def __init__(
        self,
        state_store: StateStore | None = None,
        logger: AgentLogger | None = None,
        max_agent_retries: int = 1,
        max_steps: int = 10,
    ) -> None:
        self.state_store = state_store or StateStore(PROJECT_ROOT / "runtime" / "state.db")
        self.logger = logger or AgentLogger(PROJECT_ROOT / "runtime" / "agent_calls.jsonl")
        self.max_agent_retries = max_agent_retries
        self.max_steps = max_steps
        self.agents: list[BaseAgent] = [
            TopicIntakeAgent(),
            NoveltyAssessmentAgent(),
            DuplicationControlAgent(),
            SupervisorMatchingAgent(),
            CompletionCycleMonitorAgent(),
            QualityGateAgent(),
        ]

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        task_id = str(uuid4())
        context: dict[str, Any] = {
            "task_id": task_id,
            "request": request,
            "agent_outputs": {},
            "errors": [],
        }

        if len(self.agents) > self.max_steps:
            raise RuntimeError("Configured route exceeds max step limit.")

        previous_sender = "user"
        for step_index, agent in enumerate(self.agents, start=1):
            message = AgentMessage(
                task_id=task_id,
                sender=previous_sender,
                recipient=agent.name,
                message_type="RUN_AGENT",
                payload={"request": request, "previous_outputs": context["agent_outputs"]},
            )
            self.state_store.save_message(message.to_dict())

            output = self._execute_agent(agent, message, context, step_index)
            context["agent_outputs"][agent.name] = output
            self.state_store.save_task_state(task_id, context)
            previous_sender = agent.name

        distribution = self.state_store.call_distribution(task_id)
        final_report = {
            "task_id": task_id,
            "final_decision": context["agent_outputs"]["quality_gate_agent"][
                "quality_gate_report"
            ]["decision"],
            "agent_outputs": context["agent_outputs"],
            "call_distribution": distribution,
            "balanced_load": all(
                item["share_percent"] <= 40.0 for item in distribution.values()
            ),
        }
        self.state_store.save_task_state(task_id, final_report)
        return final_report

    def _execute_agent(
        self,
        agent: BaseAgent,
        message: AgentMessage,
        context: dict[str, Any],
        step_index: int,
    ) -> dict[str, Any]:
        last_error = None
        for attempt in range(1, self.max_agent_retries + 2):
            started = time.perf_counter()
            try:
                output = agent.run(message, context)
                duration_ms = int((time.perf_counter() - started) * 1000)
                call = {
                    "task_id": message.task_id,
                    "agent": agent.name,
                    "role": agent.role,
                    "status": "OK",
                    "duration_ms": duration_ms,
                    "tools": agent.tools,
                    "step_index": step_index,
                    "attempt": attempt,
                }
                self.state_store.save_agent_call(call)
                self.logger.log(call)
                return output
            except AgentError as exc:
                last_error = str(exc)
                duration_ms = int((time.perf_counter() - started) * 1000)
                self.logger.log(
                    {
                        "task_id": message.task_id,
                        "agent": agent.name,
                        "status": "ERROR",
                        "duration_ms": duration_ms,
                        "tools": agent.tools,
                        "step_index": step_index,
                        "attempt": attempt,
                        "error": last_error,
                    }
                )

        raise RuntimeError(f"{agent.name} failed after retries: {last_error}")
