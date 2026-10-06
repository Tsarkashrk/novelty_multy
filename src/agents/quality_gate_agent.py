from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent


class QualityGateAgent(BaseAgent):
    name = "quality_gate_agent"
    role = "Check final readiness and explain decision"
    tools = ["policy_checklist", "state_summary_reader"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        outputs = context["agent_outputs"]
        profile = outputs["topic_intake_agent"]["topic_profile"]
        novelty = outputs["novelty_assessment_agent"]["novelty_report"]
        duplication = outputs["duplication_control_agent"]["duplication_report"]
        supervisors = outputs["supervisor_matching_agent"]["supervisor_recommendations"]
        plan = outputs["completion_cycle_monitor_agent"]["completion_plan"]

        issues = []
        next_actions = [
            "Submit architecture diagram.",
            "Submit agent specification table.",
            "Run prototype and attach logs.",
        ]

        issues.extend(profile["warnings"])
        if novelty["interpretation"] == "LOW_NOVELTY":
            issues.append("Novelty score is low; topic contribution must be rewritten.")
        if duplication["status"] == "BLOCKED":
            issues.append("Topic is too close to archived work and cannot proceed as is.")
        elif duplication["status"] == "REVISION_REQUIRED":
            issues.append("Topic needs clearer differentiation from archived works.")
        if not supervisors["ranked_supervisors"]:
            issues.append("No supervisor candidate was found.")
        issues.extend(supervisors["warnings"])

        if duplication["status"] == "BLOCKED":
            decision = "BLOCK_TOPIC"
        elif issues:
            decision = "REVISE_BEFORE_TEACHER_REVIEW"
        else:
            decision = "APPROVE_FOR_TEACHER_REVIEW"

        return {
            "quality_gate_report": {
                "decision": decision,
                "issues": issues,
                "next_actions": next_actions,
                "overall_risk": plan["overall_risk"],
            }
        }
