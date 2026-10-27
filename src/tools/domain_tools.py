from __future__ import annotations

from typing import Any

from src.agents.base import AgentError
from src.tools.text_similarity import blended_similarity, tokenize, topic_to_text


def validate_request(request: dict[str, Any]) -> dict[str, Any]:
    title = request.get("raw_topic")
    if not isinstance(title, str) or not title.strip():
        raise AgentError("Topic title is required.")
    week = request.get("current_week", 5)
    if not isinstance(week, int) or isinstance(week, bool) or not 1 <= week <= 30:
        raise AgentError("current_week must be an integer from 1 to 30.")
    return {
        "title": title.strip(),
        "student": str(request.get("student") or "Unknown Student").strip(),
        "department": str(request.get("department") or "Unknown Department").strip(),
        "current_week": week,
    }


def extract_keywords(title: str, provided: Any) -> list[str]:
    if isinstance(provided, str):
        provided = [item.strip() for item in provided.split(",") if item.strip()]
    if provided is None:
        provided = []
    if not isinstance(provided, list) or not all(isinstance(item, str) for item in provided):
        raise ValueError("keywords must be a list of strings")
    return list(dict.fromkeys([*(item.strip() for item in provided if item.strip()), *tokenize(title)]))[:12]


def rank_archive(profile: dict[str, Any], archive: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate = " ".join([profile["title"], " ".join(profile["keywords"])])
    matches = [
        {
            "id": topic["id"],
            "title": topic["title"],
            "domain": topic.get("domain", topic.get("department", "")),
            "year": topic["year"],
            "language": topic.get("language", ""),
            "source": topic.get("source", ""),
            "url": topic.get("url", ""),
            "is_synthetic": topic.get("is_synthetic", False),
            "similarity": max(
                blended_similarity(profile["title"], topic["title"]),
                blended_similarity(candidate, topic_to_text(topic)),
            ),
        }
        for topic in archive
    ]
    return sorted(matches, key=lambda item: item["similarity"], reverse=True)[:3]


def classify_duplication(similarity: float) -> dict[str, str]:
    if similarity >= 0.78:
        return {"status": "BLOCKED", "risk_level": "HIGH", "recommended_action": "Choose a substantially different topic or scope."}
    if similarity >= 0.55:
        return {"status": "REVISION_REQUIRED", "risk_level": "MEDIUM", "recommended_action": "Clarify novelty and differentiate the contribution."}
    return {"status": "CLEAR", "risk_level": "LOW", "recommended_action": "Topic can continue to supervisor matching."}


def rank_supervisors(profile: dict[str, Any], supervisors: list[dict[str, Any]]) -> dict[str, Any]:
    topic_terms = set(tokenize(" ".join([profile["title"], *profile["keywords"]])))
    ranked = []
    for supervisor in supervisors:
        free_slots = supervisor["capacity_total"] - supervisor["capacity_used"]
        if free_slots <= 0:
            continue
        expertise_terms = set(tokenize(" ".join(supervisor["expertise_keywords"])))
        overlap = sorted(topic_terms & expertise_terms)
        expertise_score = len(overlap) / max(len(topic_terms), 1)
        department_score = 1.0 if supervisor["department"] == profile["department"] else 0.45
        capacity_score = free_slots / max(supervisor["capacity_total"], 1)
        score = 0.55 * expertise_score + 0.25 * department_score + 0.2 * capacity_score
        ranked.append({
            "id": supervisor["id"], "name": supervisor["name"],
            "department": supervisor["department"], "score": round(score, 3),
            "capacity_note": f"{free_slots} free slot(s)",
            "matched_keywords": overlap,
            "reason": "expertise, department fit, and capacity were scored separately",
        })
    ranked = sorted(ranked, key=lambda item: item["score"], reverse=True)[:3]
    warnings = []
    if not ranked:
        warnings.append("No supervisor has free capacity.")
    elif ranked[0]["score"] < 0.35:
        warnings.append("Supervisor fit is weak; expand topic keywords or supervisor pool.")
    return {"ranked_supervisors": ranked, "warnings": warnings}


def plan_milestones(template: list[dict[str, Any]], status: str, request: dict[str, Any]) -> dict[str, Any]:
    completed = request.get("completed_milestones") or []
    if not isinstance(completed, list) or not all(isinstance(code, str) for code in completed):
        raise ValueError("completed_milestones must be a list of codes")
    known = {item["code"] for item in template}
    if set(completed) - known:
        raise ValueError("completed_milestones contains an unknown code")
    current_week = request.get("current_week", 5)
    active = next((item["code"] for item in template if item["code"] not in completed), None)
    milestones = []
    for item in template:
        if item["code"] in completed:
            milestone_status = "DONE"
        elif status == "BLOCKED" and item["code"] != "M1":
            milestone_status = "WAITING_TOPIC_REVISION"
        elif item["week"] < current_week:
            milestone_status = "OVERDUE"
        elif item["code"] == active:
            milestone_status = "IN_PROGRESS"
        else:
            milestone_status = "TODO"
        milestones.append({**item, "status": milestone_status})
    risk = "HIGH" if status == "BLOCKED" or any(item["status"] == "OVERDUE" for item in milestones) else "MEDIUM" if status == "REVISION_REQUIRED" else "LOW"
    return {"milestones": milestones, "overall_risk": risk, "current_week": current_week}


def check_quality(outputs: dict[str, Any]) -> dict[str, Any]:
    profile = outputs["topic_intake_agent"]["topic_profile"]
    novelty = outputs["novelty_assessment_agent"]["novelty_report"]
    duplication = outputs["duplication_control_agent"]["duplication_report"]
    supervisors = outputs["supervisor_matching_agent"]["supervisor_recommendations"]
    plan = outputs["completion_cycle_monitor_agent"]["completion_plan"]
    issues = list(profile["warnings"])
    if novelty["interpretation"] == "LOW_NOVELTY":
        issues.append("Novelty score is low; topic contribution must be rewritten.")
    if duplication["status"] == "BLOCKED":
        issues.append("Topic is too close to archived work and cannot proceed as is.")
    elif duplication["status"] == "REVISION_REQUIRED":
        issues.append("Topic needs clearer differentiation from archived works.")
    if not supervisors["ranked_supervisors"]:
        issues.append("No supervisor candidate was found.")
    issues.extend(supervisors["warnings"])
    if any(item["status"] == "OVERDUE" for item in plan["milestones"]):
        issues.append("At least one milestone is overdue.")
    decision = "BLOCK_TOPIC" if duplication["status"] == "BLOCKED" else "REVISE_BEFORE_TEACHER_REVIEW" if issues else "APPROVE_FOR_TEACHER_REVIEW"
    return {
        "decision": decision,
        "issues": issues,
        "next_actions": ["Review topic evidence with a teacher.", "Confirm supervisor availability.", "Update milestone completion as work progresses."],
        "overall_risk": plan["overall_risk"],
    }
