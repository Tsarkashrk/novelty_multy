from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.data_loader import load_json_dataset
from src.tools.domain_tools import rank_supervisors


class SupervisorMatchingAgent(BaseAgent):
    name = "supervisor_matching_agent"
    role = "Recommend supervisors according to expertise, department, and capacity"
    tools = ["supervisor_dataset", "supervisor_ranker"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        profile = message.payload["previous_outputs"]["topic_intake_agent"]["topic_profile"]
        tools = context["tools"]
        supervisors = tools.call("supervisor_dataset", load_json_dataset, "supervisors.json")
        return {"supervisor_recommendations": tools.call("supervisor_ranker", rank_supervisors, profile, supervisors)}
