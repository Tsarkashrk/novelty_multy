from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.domain_tools import build_topic_profile, extract_keywords, validate_request


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
        return {"topic_profile": build_topic_profile(validated, keywords)}
