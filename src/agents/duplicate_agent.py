from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent


class DuplicationControlAgent(BaseAgent):
    name = "duplication_control_agent"
    role = "Classify duplication risk and decide whether the topic must be revised"
    tools = ["archive_topics_dataset", "text_similarity_tool", "duplication_threshold_policy"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        novelty_report = context["agent_outputs"]["novelty_assessment_agent"][
            "novelty_report"
        ]
        max_similarity = novelty_report["max_similarity"]
        evidence = novelty_report["top_matches"]

        if max_similarity >= 0.78:
            status = "BLOCKED"
            risk_level = "HIGH"
            action = "Choose a substantially different topic or scope."
        elif max_similarity >= 0.55:
            status = "REVISION_REQUIRED"
            risk_level = "MEDIUM"
            action = "Clarify novelty and differentiate the contribution."
        else:
            status = "CLEAR"
            risk_level = "LOW"
            action = "Topic can continue to supervisor matching."

        return {
            "duplication_report": {
                "status": status,
                "risk_level": risk_level,
                "max_similarity": max_similarity,
                "evidence": evidence,
                "recommended_action": action,
            }
        }
