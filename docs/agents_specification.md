# Agent Specification

| Agent | Role | Inputs | Outputs | Tools | Completion Criterion |
| --- | --- | --- | --- | --- | --- |
| Orchestrator | Plans route, sends messages, stores state. It does not perform domain analysis. | User request, agent outputs, runtime limits. | Final report, stored task state, call distribution. | SQLite state store, JSONL logger, retry controller. | All planned agents completed or controlled failure returned. |
| Topic Intake Agent | Converts the raw topic request into a structured topic profile. | `raw_topic`, `student`, `department`, optional `keywords`. | `topic_profile` with normalized title, extracted keywords, warnings. | Schema validator, keyword extractor. | Required fields are valid; short titles and sparse keywords produce warnings. |
| Novelty Assessment Agent | Estimates how different the proposed topic is from archived works. | `topic_profile`, archive topic dataset. | `novelty_report` with novelty score, nearest matches, interpretation. | Archive dataset reader, text similarity tool. | Top matches and a novelty score are produced. |
| Duplication Control Agent | Applies duplication thresholds to novelty evidence. | `novelty_report`. | `duplication_report` with status, risk level, evidence. | Duplication threshold policy. | Duplication status is one of `CLEAR`, `REVISION_REQUIRED`, `BLOCKED`. |
| Supervisor Matching Agent | Ranks available supervisors by expertise, department fit, and free capacity. | `topic_profile`, supervisor dataset. | `supervisor_recommendations` with ranked candidates and reasons. | Supervisor dataset reader, supervisor ranker. | At least one supervisor is recommended or a capacity warning is returned. |
| Completion Cycle Monitor Agent | Builds the basic completion cycle and milestone risks. | `topic_profile`, `duplication_report`, supervisor recommendations. | `completion_plan` with milestones, status, risks. | Completion template reader, milestone planner. | All required assignment/exam milestones are represented. |
| Quality Gate Agent | Checks final readiness and explains decision. | Outputs of all previous agents. | `quality_gate_report` with decision, issues, next actions. | Policy checklist. | Final decision and next actions are produced. |

## Structured Message Contract

The orchestrator sends each agent a `RUN_AGENT` message containing the request and previous outputs. Each agent returns an `AGENT_RESULT` message to the orchestrator. Both are persisted as `AgentMessage` objects:

```json
{
  "message_id": "uuid",
  "task_id": "uuid",
  "sender": "orchestrator",
  "recipient": "novelty_assessment_agent",
  "message_type": "RUN_AGENT",
  "payload": {
    "request": {},
    "previous_outputs": {}
  },
  "created_at": "2026-10-06T17:49:00Z"
}
```

## Tools Per Agent

No agent has more than 5 tools. Tool boundaries are intentionally narrow so that agent roles remain separate and balanced.

| Agent | Tool Count |
| --- | ---: |
| Topic Intake Agent | 2 |
| Novelty Assessment Agent | 2 |
| Duplication Control Agent | 1 |
| Supervisor Matching Agent | 2 |
| Completion Cycle Monitor Agent | 2 |
| Quality Gate Agent | 1 |
