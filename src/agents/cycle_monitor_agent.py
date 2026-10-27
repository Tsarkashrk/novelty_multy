from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.data_loader import load_json_dataset
from src.tools.domain_tools import plan_milestones


class CompletionCycleMonitorAgent(BaseAgent):
    name = "completion_cycle_monitor_agent"
    role = "Build a basic milestone plan and estimate completion risk"
    tools = ["completion_template_dataset", "milestone_planner"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        duplication = message.payload["previous_outputs"]["duplication_control_agent"][
            "duplication_report"
        ]
        tools = context["tools"]
        template = tools.call("completion_template_dataset", load_json_dataset, "completion_template.json")
        plan = tools.call("milestone_planner", plan_milestones, template, duplication["status"], message.payload["request"])
        return {"completion_plan": plan}
