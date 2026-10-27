from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.domain_tools import classify_duplication


class DuplicationControlAgent(BaseAgent):
    name = "duplication_control_agent"
    role = "Classify duplication risk and decide whether the topic must be revised"
    tools = ["duplication_threshold_policy"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        novelty_report = message.payload["previous_outputs"]["novelty_assessment_agent"][
            "novelty_report"
        ]
        max_similarity = novelty_report["max_similarity"]
        evidence = novelty_report["top_matches"]
        classification = context["tools"].call("duplication_threshold_policy", classify_duplication, max_similarity)

        return {
            "duplication_report": {
                **classification,
                "max_similarity": max_similarity,
                "evidence": evidence,
            }
        }
