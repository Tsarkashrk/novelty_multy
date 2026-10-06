from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.orchestrator import Orchestrator
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore


class PrototypeTest(unittest.TestCase):
    def test_full_pipeline_runs_and_balances_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            orchestrator = Orchestrator(
                state_store=StateStore(temp_path / "state.db"),
                logger=AgentLogger(temp_path / "calls.jsonl"),
            )

            report = orchestrator.run(
                {
                    "raw_topic": "Intelligent Platform for Managing Diploma and Master's Projects",
                    "student": "Test Student",
                    "department": "Computer Science",
                    "keywords": ["multi-agent", "novelty", "supervisor matching"],
                }
            )

            self.assertIn("quality_gate_agent", report["agent_outputs"])
            self.assertEqual(len(report["call_distribution"]), 6)
            self.assertTrue(report["balanced_load"])
            for item in report["call_distribution"].values():
                self.assertLessEqual(item["share_percent"], 40.0)


if __name__ == "__main__":
    unittest.main()
