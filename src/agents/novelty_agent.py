from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.data_loader import load_json_dataset
from src.tools.domain_tools import rank_archive


class NoveltyAssessmentAgent(BaseAgent):
    name = "novelty_assessment_agent"
    role = "Assess topic novelty against archived diploma and master's projects"
    tools = ["archive_topics_dataset", "text_similarity_tool"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        profile = message.payload["previous_outputs"]["topic_intake_agent"]["topic_profile"]
        tools = context["tools"]
        archive = tools.call("archive_topics_dataset", load_json_dataset, "archive_topics.json")
        top_matches = tools.call("text_similarity_tool", rank_archive, profile, archive)
        max_similarity = top_matches[0]["similarity"] if top_matches else 0.0
        novelty_score = round((1.0 - max_similarity) * 100, 1)

        if novelty_score >= 70:
            interpretation = "HIGH_NOVELTY"
        elif novelty_score >= 45:
            interpretation = "MEDIUM_NOVELTY"
        else:
            interpretation = "LOW_NOVELTY"

        return {
            "novelty_report": {
                "novelty_score": novelty_score,
                "interpretation": interpretation,
                "max_similarity": max_similarity,
                "top_matches": top_matches,
            }
        }
