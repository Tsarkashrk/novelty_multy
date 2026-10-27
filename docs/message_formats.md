# Message Formats

## Input Request

```json
{
  "raw_topic": "Intelligent Platform for Managing Diploma and Master's Projects...",
  "student": "Sample Student",
  "department": "Computer Science",
  "keywords": ["multi-agent", "novelty assessment", "supervisor matching"],
  "current_week": 5,
  "completed_milestones": ["M1"],
  "archive_source": "openalex",
  "archive_csv": null,
  "include_synthetic": false,
  "exclude_archive_id": null
}
```

For `--record-id OA0001`, the CLI reads the corresponding row of `openalex_projects_enriched.csv`, fills the request fields, and sets `exclude_archive_id` to `OA0001`. The novelty agent uses that ID only to avoid comparing the selected record with itself.

## Agent Message

`RUN_AGENT` carries the user request and completed agent outputs. `AGENT_RESULT` carries the current agent's output. Both have `message_id`, `task_id`, `sender`, `recipient`, `message_type`, `payload`, and `created_at`. The orchestrator stores both directions in SQLite.

## Call Event

Every actual agent or tool call writes one JSONL record and one SQLite `call_events` row with `task_id`, `agent`, `event_type` (`AGENT` or `TOOL`), `name`, `status`, `duration_ms`, `attempt`, and optional `error`. The load calculation counts `TOOL` and `LLM` event types only. The current offline version makes no `LLM` calls.

## `topic_profile`

```json
{
  "title": "Intelligent Platform for Managing Diploma and Master's Projects...",
  "normalized_title": "intelligent platform managing diploma master projects...",
  "student": "Sample Student",
  "department": "Computer Science",
  "keywords": ["multi-agent", "novelty", "supervisor", "monitoring"],
  "warnings": []
}
```

## `novelty_report`

```json
{
  "novelty_score": 72.4,
  "interpretation": "MEDIUM_NOVELTY",
  "top_matches": [
    {
      "id": "OA0105",
      "title": "An integrated software platform for the efficient management of projects",
      "domain": "Software Engineering Techniques and Practices",
      "source": "OpenAlex",
      "url": "https://openalex.org/W2912835758",
      "is_synthetic": false,
      "similarity": 0.16
    }
  ],
  "archive": {
    "source": "openalex_csv",
    "file": "openalex_thesis_topics.csv",
    "records_total": 230,
    "records_used": 160,
    "synthetic_excluded": 70
  }
}
```

## `duplication_report`

```json
{
  "status": "REVISION_REQUIRED",
  "risk_level": "MEDIUM",
  "max_similarity": 0.61,
  "evidence": []
}
```

## `supervisor_recommendations`

```json
{
  "ranked_supervisors": [
    {
      "id": "S-001",
      "name": "Dr. Aigerim Sadykova",
      "score": 0.82,
      "reason": "Strong keyword match and available capacity"
    }
  ]
}
```

## `completion_plan`

```json
{
  "milestones": [
    {
      "code": "M2",
      "name": "Architecture and agent specification",
      "week": 5,
      "status": "IN_PROGRESS"
    }
  ],
  "overall_risk": "LOW"
}
```

## `quality_gate_report`

```json
{
  "decision": "APPROVE_FOR_TEACHER_REVIEW",
  "issues": [],
  "next_actions": [
    "Submit architecture diagram and agent table"
  ]
}
```
