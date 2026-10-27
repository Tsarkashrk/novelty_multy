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
        description="Multi-agent diploma project topic assessment and completion monitoring."
    )
    parser.add_argument("--demo", action="store_true", help="Run with the default topic.")
    parser.add_argument("--topic", help="Submitted diploma or master's project topic.")
    parser.add_argument("--student", default="Sample Student", help="Student full name.")
    parser.add_argument("--department", default="Computer Science", help="Department name.")
    parser.add_argument(
        "--keywords",
        default=None,
        help="Comma-separated topic keywords.",
    )
    parser.add_argument("--output", help="Optional path for saving the JSON report.")
    parser.add_argument("--archive-source", choices=("openalex", "sample"), default="openalex", help="Archive used for novelty and duplication checks.")
    parser.add_argument("--archive-csv", help="Optional path to a compatible CSV archive; overrides --archive-source.")
    parser.add_argument("--include-synthetic", action="store_true", help="Include controlled synthetic OpenAlex variants.")
    parser.add_argument("--current-week", type=int, default=5, help="Current semester week (1-30).")
    parser.add_argument("--completed", default="", help="Comma-separated completed milestone codes, e.g. M1,M2.")
    parser.add_argument("--max-steps", type=int, default=10, help="Maximum number of agent steps.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Maximum run time in seconds.")
    parser.add_argument("--retries", type=int, default=1, help="Retries for transient agent failures.")
    return parser


def request_from_args(args: argparse.Namespace) -> dict[str, Any]:
    topic = DEFAULT_TOPIC if args.demo or args.topic is None else args.topic
    default_keywords = "multi-agent, novelty assessment, duplication detection, supervisor matching, monitoring" if args.demo or not args.topic else ""
    keywords = [item.strip() for item in (args.keywords if args.keywords is not None else default_keywords).split(",") if item.strip()]
    return {
        "raw_topic": topic,
        "student": args.student,
        "department": args.department,
        "keywords": keywords,
        "current_week": args.current_week,
        "completed_milestones": [item.strip() for item in args.completed.split(",") if item.strip()],
        "archive_source": args.archive_source,
        "archive_csv": args.archive_csv,
        "include_synthetic": args.include_synthetic,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        orchestrator = Orchestrator(
            max_steps=args.max_steps,
            max_runtime_seconds=args.timeout,
            max_agent_retries=args.retries,
        )
    except ValueError as exc:
        parser.error(str(exc))
    report = orchestrator.run(request_from_args(args))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    print(rendered)
    return 0 if report["status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
