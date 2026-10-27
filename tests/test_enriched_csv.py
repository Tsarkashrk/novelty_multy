from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.build_enriched_openalex_csv import OUTPUT, SOURCE, build_enriched_csv
from src.main import build_parser, request_from_args
from src.orchestrator import Orchestrator
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore
from src.tools.data_loader import load_project_record, load_topic_archive


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


class EnrichedCsvTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.orchestrator = Orchestrator(
            state_store=StateStore(root / "state.db"),
            logger=AgentLogger(root / "calls.jsonl"),
        )

    def test_original_columns_and_actual_supervisor_ids_are_preserved(self) -> None:
        original = csv_rows(SOURCE)
        enriched = csv_rows(OUTPUT)
        self.assertEqual(len(original), len(enriched))
        for old, new in zip(original, enriched):
            self.assertEqual({key: new[key] for key in old}, old)
            self.assertEqual(new["supervisor_id"], old["supervisor_id"])
            self.assertTrue(new["demo_recommended_supervisor_id"])
            self.assertTrue(new["demo_milestone_plan"])

    def test_selected_row_matches_demo_preview_without_self_match(self) -> None:
        for record_id in ("OA0001", "OA0004"):
            with self.subTest(record_id=record_id):
                row = load_project_record(record_id)
                args = build_parser().parse_args(["--record-id", record_id])
                request = request_from_args(args)
                self.assertEqual(request["exclude_archive_id"], record_id)
                self.assertEqual(request["completed_milestones"], ["M1"])
                report = self.orchestrator.run(request)
                novelty = report["agent_outputs"]["novelty_assessment_agent"]["novelty_report"]
                supervisor = report["agent_outputs"]["supervisor_matching_agent"]["supervisor_recommendations"]["ranked_supervisors"][0]
                self.assertEqual(report["status"], "COMPLETED")
                self.assertNotEqual(novelty["top_matches"][0]["id"], record_id)
                self.assertEqual(novelty["novelty_score"], float(row["demo_novelty_score"]))
                self.assertEqual(supervisor["id"], row["demo_recommended_supervisor_id"])
                self.assertEqual(report["final_decision"], row["demo_quality_decision"])

    def test_edited_row_values_survive_regeneration_and_feed_agents(self) -> None:
        path = Path(self.temp.name) / "edited.csv"
        shutil.copyfile(OUTPUT, path)
        rows = csv_rows(path)
        rows[0].update({
            "student": "A. Student", "department": "Data Science",
            "current_week": "10", "completed_milestones": "M1;M2",
        })
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        self.assertEqual(build_enriched_csv(SOURCE, path), 230)
        row = load_project_record("OA0001", str(path))
        self.assertEqual(row["department"], "Data Science")
        self.assertIn("week=10", row["demo_assumptions"])
        args = build_parser().parse_args(["--record-id", "OA0001", "--record-csv", str(path)])
        request = request_from_args(args)
        self.assertEqual((request["student"], request["department"], request["current_week"]), ("A. Student", "Data Science", 10))
        self.assertEqual(request["completed_milestones"], ["M1", "M2"])
        report = self.orchestrator.run(request)
        self.assertEqual(report["final_decision"], row["demo_quality_decision"])
        override = build_parser().parse_args(["--record-id", "OA0001", "--record-csv", str(path), "--current-week", "12"])
        self.assertEqual(request_from_args(override)["current_week"], 12)

    def test_enriched_file_is_compatible_with_archive_loader(self) -> None:
        archive = load_topic_archive(csv_path=str(OUTPUT))
        self.assertEqual((archive["records_total"], archive["records_used"]), (230, 160))

    def test_unknown_record_is_reported(self) -> None:
        with self.assertRaisesRegex(ValueError, "was not found"):
            load_project_record("MISSING")


if __name__ == "__main__":
    unittest.main()
