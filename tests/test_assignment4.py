from __future__ import annotations

import json
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from src.agents.base import TransientAgentError
from src.agents.intake_agent import TopicIntakeAgent
from src.orchestrator import Orchestrator
from src.storage.logger import AgentLogger
from src.storage.state_store import StateStore
from src.tools.domain_tools import classify_duplication


class FlakyIntake(TopicIntakeAgent):
    def __init__(self) -> None:
        self.calls = 0

    def run(self, message, context):
        self.calls += 1
        if self.calls == 1:
            raise TransientAgentError("temporary source outage")
        return super().run(message, context)


class SlowIntake(TopicIntakeAgent):
    def run(self, message, context):
        time.sleep(0.2)
        return super().run(message, context)


class Assignment4Scenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = StateStore(self.root / "state.db")
        self.log_path = self.root / "calls.jsonl"

    def orchestrator(self, **kwargs) -> Orchestrator:
        return Orchestrator(state_store=self.store, logger=AgentLogger(self.log_path), **kwargs)

    @staticmethod
    def request(topic: str = "Adaptive Assessment of Student Project Progress Using Research Analytics", **kwargs) -> dict:
        request = {"raw_topic": topic, "student": "Test Student", "department": "Computer Science", "keywords": [], "current_week": 5, "completed_milestones": ["M1"]}
        request.update(kwargs)
        return request

    def events(self) -> list[dict]:
        return [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines()]

    def test_ts01_normal_topic_and_real_tool_balance(self) -> None:
        report = self.orchestrator().run(self.request())
        self.assertEqual(report["status"], "COMPLETED")
        self.assertEqual(report["steps_executed"], 6)
        self.assertTrue(report["balanced_load"])
        self.assertEqual(sum(item["calls"] for item in report["call_distribution"].values()), 10)
        self.assertLessEqual(max(item["share_percent"] for item in report["call_distribution"].values()), 40)
        events = self.events()
        self.assertEqual(sum(item["event_type"] == "AGENT" for item in events), 6)
        self.assertEqual(sum(item["event_type"] == "TOOL" for item in events), 10)

    def test_ts02_exact_archive_duplicate_is_blocked(self) -> None:
        report = self.orchestrator().run(self.request("Intelligent Platform for Diploma Project Lifecycle Management"))
        self.assertEqual(report["status"], "COMPLETED")
        self.assertEqual(report["final_decision"], "BLOCK_TOPIC")
        duplicate = report["agent_outputs"]["duplication_control_agent"]["duplication_report"]
        self.assertEqual(duplicate["status"], "BLOCKED")
        self.assertEqual(duplicate["evidence"][0]["id"], "T-2026-002")

    def test_ts03_short_topic_requires_revision(self) -> None:
        report = self.orchestrator().run(self.request("AI System"))
        self.assertEqual(report["final_decision"], "REVISE_BEFORE_TEACHER_REVIEW")
        self.assertTrue(report["agent_outputs"]["topic_intake_agent"]["topic_profile"]["warnings"])

    def test_ts04_overdue_milestone_is_reported(self) -> None:
        report = self.orchestrator().run(self.request(current_week=11))
        plan = report["agent_outputs"]["completion_cycle_monitor_agent"]["completion_plan"]
        self.assertEqual(plan["milestones"][1]["status"], "OVERDUE")
        self.assertEqual(plan["overall_risk"], "HIGH")
        self.assertEqual(report["final_decision"], "REVISE_BEFORE_TEACHER_REVIEW")

    def test_ts05_completed_milestones_are_tracked(self) -> None:
        report = self.orchestrator().run(self.request(completed_milestones=["M1", "M2"], current_week=10))
        statuses = [item["status"] for item in report["agent_outputs"]["completion_cycle_monitor_agent"]["completion_plan"]["milestones"]]
        self.assertEqual(statuses[:3], ["DONE", "DONE", "IN_PROGRESS"])

    def test_ts06_full_supervisor_is_excluded(self) -> None:
        report = self.orchestrator().run(self.request("Academic Integrity and Plagiarism Detection Platform"))
        supervisors = report["agent_outputs"]["supervisor_matching_agent"]["supervisor_recommendations"]
        self.assertNotIn("S-005", [item["id"] for item in supervisors["ranked_supervisors"]])

    def test_ts07_missing_title_fails_with_clear_error(self) -> None:
        report = self.orchestrator().run(self.request(""))
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("Topic title is required", report["errors"][0]["message"])
        self.assertEqual(report["steps_executed"], 0)
        self.assertEqual([item["status"] for item in self.events()], ["ERROR", "ERROR"])

    def test_ts08_transient_failure_retries_and_recovers(self) -> None:
        flaky = FlakyIntake()
        orchestrator = self.orchestrator()
        orchestrator.agents[0] = flaky
        report = orchestrator.run(self.request())
        self.assertEqual(report["status"], "COMPLETED")
        self.assertEqual(flaky.calls, 2)
        calls = [item for item in self.events() if item["agent"] == "topic_intake_agent" and item["event_type"] == "AGENT"]
        self.assertEqual([item["status"] for item in calls], ["ERROR", "OK"])

    def test_ts09_persistent_source_failure_is_logged(self) -> None:
        with patch("src.agents.novelty_agent.load_json_dataset", side_effect=OSError("archive unavailable")):
            report = self.orchestrator().run(self.request())
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["errors"][0]["agent"], "novelty_assessment_agent")
        calls = [item for item in self.events() if item["name"] == "archive_topics_dataset"]
        self.assertEqual([item["status"] for item in calls], ["ERROR", "ERROR"])

    def test_ts10_timeout_stops_slow_agent(self) -> None:
        orchestrator = self.orchestrator(max_runtime_seconds=0.03)
        orchestrator.agents[0] = SlowIntake()
        started = time.monotonic()
        report = orchestrator.run(self.request())
        self.assertLess(time.monotonic() - started, 0.18)
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["errors"][0]["type"], "ExecutionTimeout")
        self.assertIn("TIMEOUT", [item["status"] for item in self.events()])

    def test_ts11_step_limit_stops_pipeline(self) -> None:
        report = self.orchestrator(max_steps=3).run(self.request())
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["steps_executed"], 3)
        self.assertIn("Step limit", report["errors"][0]["message"])

    def test_ts12_messages_and_state_are_persisted(self) -> None:
        report = self.orchestrator().run(self.request())
        with closing(sqlite3.connect(self.root / "state.db")) as conn:
            messages = conn.execute("SELECT sender, recipient, payload_json FROM messages WHERE task_id = ?", (report["task_id"],)).fetchall()
            state = conn.execute("SELECT state_json FROM tasks WHERE task_id = ?", (report["task_id"],)).fetchone()
            events = conn.execute("SELECT event_type, COUNT(*) FROM call_events WHERE task_id = ? GROUP BY event_type", (report["task_id"],)).fetchall()
        self.assertEqual(len(messages), 12)
        self.assertEqual(messages[0][0:2], ("orchestrator", "topic_intake_agent"))
        self.assertEqual(messages[1][0:2], ("topic_intake_agent", "orchestrator"))
        self.assertIn("topic_profile", json.loads(messages[2][2])["previous_outputs"]["topic_intake_agent"])
        self.assertEqual(json.loads(state[0])["status"], "COMPLETED")
        self.assertEqual(dict(events), {"AGENT": 6, "TOOL": 10})

    def test_threshold_boundaries(self) -> None:
        self.assertEqual(classify_duplication(0.78)["status"], "BLOCKED")
        self.assertEqual(classify_duplication(0.55)["status"], "REVISION_REQUIRED")
        self.assertEqual(classify_duplication(0.5499)["status"], "CLEAR")


if __name__ == "__main__":
    unittest.main()
