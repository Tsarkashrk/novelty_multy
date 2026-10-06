from __future__ import annotations

from src.agents.base import AgentError, AgentMessage, BaseAgent
from src.tools.text_similarity import normalize_text, tokenize


class TopicIntakeAgent(BaseAgent):
    name = "topic_intake_agent"
    role = "Validate and structure a submitted diploma or master's topic"
    tools = ["schema_validator", "keyword_extractor"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        request = message.payload["request"]
        title = request.get("raw_topic", "").strip()
        student = request.get("student", "").strip() or "Unknown Student"
        department = request.get("department", "").strip() or "Unknown Department"

        if not title:
            raise AgentError("Topic title is required.")

        provided_keywords = request.get("keywords") or []
        if isinstance(provided_keywords, str):
            provided_keywords = [
                item.strip() for item in provided_keywords.split(",") if item.strip()
            ]

        extracted = tokenize(title)
        keywords = list(dict.fromkeys([*provided_keywords, *extracted]))[:12]
        warnings = []
        if len(title.split()) < 5:
            warnings.append("Topic title is too short and should be clarified.")
        if len(keywords) < 3:
            warnings.append("At least 3 meaningful keywords are recommended.")

        return {
            "topic_profile": {
                "title": title,
                "normalized_title": normalize_text(title),
                "student": student,
                "department": department,
                "keywords": keywords,
                "warnings": warnings,
            }
        }
