from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from src.tools.data_loader import DATA_DIR, load_json_dataset, load_topic_archive
from src.tools.domain_tools import (
    build_topic_profile,
    check_quality,
    classify_duplication,
    extract_keywords,
    interpret_novelty,
    plan_milestones,
    rank_archive,
    rank_supervisors,
    validate_request,
)


SOURCE = DATA_DIR / "openalex_thesis_topics.csv"
OUTPUT = DATA_DIR / "openalex_projects_enriched.csv"
EDITABLE_FIELDS = ["student", "department", "current_week", "completed_milestones"]
DEMO_FIELDS = [
    "demo_nearest_topic_id", "demo_nearest_similarity", "demo_novelty_score",
    "demo_duplication_status", "demo_recommended_supervisor_id",
    "demo_recommended_supervisor_name", "demo_recommended_supervisor_score",
    "demo_supervisor_alternatives", "demo_completion_risk", "demo_milestone_plan",
    "demo_quality_decision", "demo_quality_issues", "demo_assumptions",
]


def build_enriched_csv(source_path: Path, output_path: Path) -> int:
    if source_path.resolve() == output_path.resolve():
        raise ValueError("Source and output CSV must be different files")

    archive = load_topic_archive(csv_path=str(source_path))
    supervisors = load_json_dataset("supervisors.json")
    template = load_json_dataset("completion_template.json")
    existing_inputs: dict[str, dict[str, str]] = {}
    if output_path.exists():
        with output_path.open("r", encoding="utf-8-sig", newline="") as file:
            existing_inputs = {
                row["id"]: {field: row.get(field, "") for field in EDITABLE_FIELDS}
                for row in csv.DictReader(file)
            }
    with source_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        source_fields = reader.fieldnames or []
        rows = list(reader)
    fieldnames = source_fields + [field for field in EDITABLE_FIELDS + DEMO_FIELDS if field not in source_fields]
    enriched = []
    for row in rows:
        editable = existing_inputs.get(row["id"], {field: row.get(field, "") for field in EDITABLE_FIELDS})
        department = editable["department"] or "Computer Science"
        week = int(editable["current_week"]) if editable["current_week"] else 5
        completed = [item.strip() for item in re.split(r"[,;]", editable["completed_milestones"]) if item.strip()] or ["M1"]
        assumptions = (
            f"department={department};week={week};completed={','.join(completed)};"
            f"{archive['records_used']} nonsynthetic archive rows;self excluded;demo supervisor roster"
        )
        request = {
            "raw_topic": row["title"],
            "student": editable["student"] or "Dataset demo",
            "department": department,
            "keywords": [item.strip() for item in (row["keywords"] or "").split(";") if item.strip()],
            "current_week": week,
            "completed_milestones": completed,
        }
        validated = validate_request(request)
        keywords = extract_keywords(validated["title"], request["keywords"])
        profile = build_topic_profile(validated, keywords)
        matches = rank_archive(profile, archive["topics"], exclude_id=row["id"])
        max_similarity = matches[0]["similarity"] if matches else 0.0
        novelty_score = round((1.0 - max_similarity) * 100, 1)
        novelty = {
            "novelty_score": novelty_score,
            "interpretation": interpret_novelty(novelty_score),
            "max_similarity": max_similarity,
            "top_matches": matches,
        }
        duplicate = classify_duplication(max_similarity)
        duplicate.update({"max_similarity": max_similarity, "evidence": matches})
        recommendations = rank_supervisors(profile, supervisors)
        plan = plan_milestones(template, duplicate["status"], request)
        outputs = {
            "topic_intake_agent": {"topic_profile": profile},
            "novelty_assessment_agent": {"novelty_report": novelty},
            "duplication_control_agent": {"duplication_report": duplicate},
            "supervisor_matching_agent": {"supervisor_recommendations": recommendations},
            "completion_cycle_monitor_agent": {"completion_plan": plan},
        }
        quality = check_quality(outputs)
        top_supervisor = recommendations["ranked_supervisors"][0] if recommendations["ranked_supervisors"] else {}
        enriched.append({
            **row,
            **editable,
            "demo_nearest_topic_id": matches[0]["id"] if matches else "",
            "demo_nearest_similarity": max_similarity,
            "demo_novelty_score": novelty_score,
            "demo_duplication_status": duplicate["status"],
            "demo_recommended_supervisor_id": top_supervisor.get("id", ""),
            "demo_recommended_supervisor_name": top_supervisor.get("name", ""),
            "demo_recommended_supervisor_score": top_supervisor.get("score", ""),
            "demo_supervisor_alternatives": ";".join(item["id"] for item in recommendations["ranked_supervisors"][1:]),
            "demo_completion_risk": plan["overall_risk"],
            "demo_milestone_plan": ";".join(f'{item["code"]}:{item["status"]}' for item in plan["milestones"]),
            "demo_quality_decision": quality["decision"],
            "demo_quality_issues": " | ".join(quality["issues"]),
            "demo_assumptions": assumptions,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)
    return len(enriched)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an enriched, runnable OpenAlex project CSV.")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    count = build_enriched_csv(args.source, args.output)
    print(f"Saved {count} enriched project rows to {args.output}")


if __name__ == "__main__":
    main()
