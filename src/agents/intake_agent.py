from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.domain_tools import extract_keywords, validate_request
from src.tools.text_similarity import normalize_text


class TopicIntakeAgent(BaseAgent):
    name = "topic_intake_agent"
    role = "Validate and structure a submitted diploma or master's topic"
    tools = ["schema_validator", "keyword_extractor"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        request = message.payload["request"]
        tools = context["tools"]
        validated = tools.call("schema_validator", validate_request, request)
        title = validated["title"]
        keywords = tools.call("keyword_extractor", extract_keywords, title, request.get("keywords"))
        warnings = []
        if len(title.split()) < 5:
            warnings.append("Topic title is too short and should be clarified.")
        if len(keywords) < 3:
            warnings.append("At least 3 meaningful keywords are recommended.")

        return {
            "topic_profile": {
                "title": title,
                "normalized_title": normalize_text(title),
                "student": validated["student"],
                "department": validated["department"],
                "keywords": keywords,
                "warnings": warnings,
            }
        }
