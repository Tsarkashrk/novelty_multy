from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.domain_tools import check_quality


class QualityGateAgent(BaseAgent):
    name = "quality_gate_agent"
    role = "Check final readiness and explain decision"
    tools = ["policy_checklist"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        outputs = message.payload["previous_outputs"]
        return {"quality_gate_report": context["tools"].call("policy_checklist", check_quality, outputs)}
