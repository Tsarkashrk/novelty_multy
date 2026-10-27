from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from src.orchestrator import Orchestrator
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore
from src.tools.data_loader import load_topic_archive
from src.tools.text_similarity import tokenize


class OpenAlexArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.orchestrator = Orchestrator(
            state_store=StateStore(root / "state.db"),
            logger=AgentLogger(root / "calls.jsonl"),
        )

    @staticmethod
    def request(title: str, **options) -> dict:
        return {
            "raw_topic": title,
            "student": "Archive Test",
            "department": "Computer Science",
            "keywords": [],
            "current_week": 5,
            "completed_milestones": ["M1"],
            **options,
        }

    def test_real_openalex_title_is_blocked_with_source_evidence(self) -> None:
        title = "Artificial intelligence, education and music : the use of artificial intelligence to encourage and facilitate music composition by novices"
        report = self.orchestrator.run(self.request(title))
        self.assertEqual(report["status"], "COMPLETED")
        self.assertEqual(report["final_decision"], "BLOCK_TOPIC")
        novelty = report["agent_outputs"]["novelty_assessment_agent"]["novelty_report"]
        self.assertEqual(novelty["archive"]["records_used"], 160)
        match = novelty["top_matches"][0]
        self.assertEqual(match["id"], "OA0001")
        self.assertEqual(match["similarity"], 1.0)
        self.assertFalse(match["is_synthetic"])
        self.assertEqual(match["source"], "OpenAlex")
        self.assertTrue(match["url"].startswith("https://openalex.org/"))

    def test_synthetic_variants_are_opt_in(self) -> None:
        real = load_topic_archive()
        all_rows = load_topic_archive(include_synthetic=True)
        self.assertEqual((real["records_used"], all_rows["records_used"]), (160, 230))
        title = "Machine learning chatbot to support education search purpose in Dublin"
        report = self.orchestrator.run(self.request(title, include_synthetic=True))
        match = report["agent_outputs"]["novelty_assessment_agent"]["novelty_report"]["top_matches"][0]
        self.assertEqual(match["id"], "NEAR0001")
        self.assertTrue(match["is_synthetic"])

    def test_custom_csv_archive(self) -> None:
        path = Path(self.temp.name) / "custom.csv"
        fieldnames = ["id", "title", "abstract", "keywords", "domain", "year", "is_synthetic", "source", "url"]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                "id": "CUSTOM-1", "title": "Adaptive Research Topic Matching",
                "abstract": "", "keywords": "research topics;similarity",
                "domain": "Information Systems", "year": "2025", "is_synthetic": "false",
                "source": "Local University", "url": "",
            })
        report = self.orchestrator.run(self.request("Adaptive Research Topic Matching", archive_csv=str(path)))
        self.assertEqual(report["status"], "COMPLETED")
        self.assertEqual(report["final_decision"], "BLOCK_TOPIC")
        novelty = report["agent_outputs"]["novelty_assessment_agent"]["novelty_report"]
        self.assertEqual(novelty["archive"]["source"], "custom_csv")
        self.assertEqual(novelty["top_matches"][0]["id"], "CUSTOM-1")

    def test_malformed_csv_returns_clear_failure(self) -> None:
        path = Path(self.temp.name) / "invalid.csv"
        path.write_text("id,title\n1,Invalid Archive\n", encoding="utf-8")
        report = self.orchestrator.run(self.request("Invalid Archive", archive_csv=str(path)))
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("missing columns", report["errors"][0]["message"])

    def test_tokenizer_preserves_non_ascii_letters(self) -> None:
        self.assertIn("жобалар", tokenize("Дипломдық жобалар"))


if __name__ == "__main__":
    unittest.main()
