from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.data_loader import load_json_dataset


class CompletionCycleMonitorAgent(BaseAgent):
    name = "completion_cycle_monitor_agent"
    role = "Build a basic milestone plan and estimate completion risk"
    tools = ["completion_template_dataset", "milestone_planner"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        duplication = context["agent_outputs"]["duplication_control_agent"][
            "duplication_report"
        ]
        template = load_json_dataset("completion_template.json")

        if duplication["status"] == "BLOCKED":
            overall_risk = "HIGH"
        elif duplication["status"] == "REVISION_REQUIRED":
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        milestones = []
        for item in template:
            status = "TODO"
            if item["code"] == "M2":
                status = "IN_PROGRESS"
            if duplication["status"] == "BLOCKED" and item["code"] != "M1":
                status = "WAITING_TOPIC_REVISION"

            milestones.append(
                {
                    "code": item["code"],
                    "name": item["name"],
                    "week": item["week"],
                    "expected_artifact": item["expected_artifact"],
                    "status": status,
                }
            )

        return {
            "completion_plan": {
                "milestones": milestones,
                "overall_risk": overall_risk,
                "monitoring_note": "Milestones follow the assignment schedule and can be expanded in Assignment 4.",
            }
        }
