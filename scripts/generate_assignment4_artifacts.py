from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.main import DEFAULT_TOPIC
from src.orchestrator import Orchestrator
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def request(title: str, *, week: int = 5, completed: list[str] | None = None, source: str = "openalex", include_synthetic: bool = False) -> dict:
    return {
        "raw_topic": title,
        "student": "Sample Student",
        "department": "Computer Science",
        "keywords": [],
        "current_week": week,
        "completed_milestones": completed if completed is not None else ["M1"],
        "archive_source": source,
        "include_synthetic": include_synthetic,
    }


def main() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    cases = [
        ("normal", request(DEFAULT_TOPIC)),
        ("exact_openalex_duplicate", request("Artificial intelligence, education and music : the use of artificial intelligence to encourage and facilitate music composition by novices")),
        ("short_title", request("AI System")),
        ("overdue", request(DEFAULT_TOPIC, week=11)),
        ("completed_milestones", request(DEFAULT_TOPIC, week=10, completed=["M1", "M2"])),
        ("full_supervisor_excluded", request("Academic Integrity and Plagiarism Detection Platform")),
        ("synthetic_variant", request("Machine learning chatbot to support education search purpose in Dublin", include_synthetic=True)),
        ("sample_archive_duplicate", request("Intelligent Platform for Diploma Project Lifecycle Management", source="sample")),
    ]
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        store = StateStore(temp / "state.db")
        logger = AgentLogger(temp / "calls.jsonl")
        orchestrator = Orchestrator(state_store=store, logger=logger)
        outcomes = []
        for name, payload in cases:
            report = orchestrator.run(payload)
            if name == "normal":
                (ARTIFACTS / "assignment4_demo_output.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                records = [json.loads(line) for line in logger.log_path.read_text(encoding="utf-8").splitlines()]
                (ARTIFACTS / "assignment4_demo_calls.jsonl").write_text(
                    "\n".join(json.dumps(record, ensure_ascii=False) for record in records if record["task_id"] == report["task_id"]) + "\n",
                    encoding="utf-8",
                )
            outcomes.append({
                "scenario": name,
                "task_id": report["task_id"],
                "status": report["status"],
                "decision": report["final_decision"],
                "duplication": report["agent_outputs"].get("duplication_control_agent", {}).get("duplication_report", {}).get("status"),
                "balanced_load": report["balanced_load"],
            })
        (ARTIFACTS / "assignment4_scenario_results.json").write_text(
            json.dumps(outcomes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Saved Assignment 4 artifacts to {ARTIFACTS}")


if __name__ == "__main__":
    main()
