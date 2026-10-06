from __future__ import annotations

from src.agents.base import AgentMessage, BaseAgent
from src.tools.data_loader import load_json_dataset
from src.tools.text_similarity import tokenize


class SupervisorMatchingAgent(BaseAgent):
    name = "supervisor_matching_agent"
    role = "Recommend supervisors according to expertise, department, and capacity"
    tools = ["supervisor_dataset", "keyword_matcher", "capacity_scorer"]

    def run(self, message: AgentMessage, context: dict) -> dict:
        profile = context["agent_outputs"]["topic_intake_agent"]["topic_profile"]
        supervisors = load_json_dataset("supervisors.json")
        topic_terms = set(tokenize(" ".join([profile["title"], *profile["keywords"]])))

        ranked = []
        for supervisor in supervisors:
            expertise_terms = set(tokenize(" ".join(supervisor["expertise_keywords"])))
            overlap = len(topic_terms & expertise_terms)
            expertise_score = overlap / max(len(topic_terms), 1)
            department_score = 1.0 if supervisor["department"] == profile["department"] else 0.45
            free_slots = supervisor["capacity_total"] - supervisor["capacity_used"]
            capacity_score = max(free_slots, 0) / max(supervisor["capacity_total"], 1)
            full_capacity_penalty = 0.25 if free_slots <= 0 else 0.0
            score = (0.55 * expertise_score) + (0.25 * department_score) + (0.2 * capacity_score)
            score = max(score - full_capacity_penalty, 0)

            if free_slots <= 0:
                capacity_note = "no free capacity"
            else:
                capacity_note = f"{free_slots} free slot(s)"

            ranked.append(
                {
                    "id": supervisor["id"],
                    "name": supervisor["name"],
                    "department": supervisor["department"],
                    "score": round(score, 3),
                    "capacity_note": capacity_note,
                    "matched_keywords": sorted(topic_terms & expertise_terms),
                    "reason": "expertise, department fit, and capacity were scored separately",
                }
            )

        ranked_supervisors = sorted(ranked, key=lambda item: item["score"], reverse=True)[:3]
        warnings = []
        if ranked_supervisors and ranked_supervisors[0]["score"] < 0.35:
            warnings.append("Supervisor fit is weak; expand topic keywords or supervisor pool.")

        return {
            "supervisor_recommendations": {
                "ranked_supervisors": ranked_supervisors,
                "warnings": warnings,
            }
        }
