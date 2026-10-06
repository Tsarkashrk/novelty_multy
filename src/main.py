from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.orchestrator import Orchestrator


DEFAULT_TOPIC = (
    "Intelligent Platform for Managing Diploma and Master's Projects with Functions "
    "for Assessing Topic Novelty, Eliminating Duplication, Assigning Supervisors, "
    "and Monitoring the Basic Completion Cycle"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assignment 2 multi-agent prototype for diploma project management."
    )
    parser.add_argument("--demo", action="store_true", help="Run with the default topic.")
    parser.add_argument("--topic", help="Submitted diploma or master's project topic.")
    parser.add_argument("--student", default="Sample Student", help="Student full name.")
    parser.add_argument("--department", default="Computer Science", help="Department name.")
    parser.add_argument(
        "--keywords",
        default="multi-agent, novelty assessment, duplication detection, supervisor matching, monitoring",
        help="Comma-separated topic keywords.",
    )
    parser.add_argument("--output", help="Optional path for saving the JSON report.")
    return parser


def request_from_args(args: argparse.Namespace) -> dict[str, Any]:
    topic = DEFAULT_TOPIC if args.demo or not args.topic else args.topic
    keywords = [item.strip() for item in args.keywords.split(",") if item.strip()]
    return {
        "raw_topic": topic,
        "student": args.student,
        "department": args.department,
        "keywords": keywords,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    orchestrator = Orchestrator()
    report = orchestrator.run(request_from_args(args))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
