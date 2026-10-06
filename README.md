# Intelligent Platform for Managing Diploma and Master's Projects

Assignment 2 prototype for a multi-agent AI system that supports diploma and master's project management:

- assessing topic novelty;
- eliminating duplication;
- assigning supervisors;
- monitoring the basic completion cycle.

The project is based on the dissertation topic: **Intelligent Platform for Managing Diploma and Master's Projects with Functions for Assessing Topic Novelty, Eliminating Duplication, Assigning Supervisors, and Monitoring the Basic Completion Cycle**.

## Why This Needs Multiple Agents

A single agent would have to validate the submitted topic, compare it with archived works, decide whether it is duplicated, assign a supervisor, plan milestones, and check final policy compliance. These tasks use different data sources, criteria, and decision logic. The system therefore separates responsibilities between specialized agents:

1. **Topic Intake Agent** structures the student's request.
2. **Novelty Assessment Agent** estimates how new the topic is.
3. **Duplication Control Agent** decides whether the topic duplicates previous work.
4. **Supervisor Matching Agent** recommends supervisors.
5. **Completion Cycle Monitor Agent** builds the basic project cycle.
6. **Quality Gate Agent** checks the final decision and risks.

An orchestrator only routes structured JSON messages and does not perform domain work.

## Assignment 2 Checklist

| Requirement | Status |
| --- | --- |
| Architecture for 5+ agents | Done: 6 domain agents + orchestrator |
| Agent roles do not duplicate each other | Done |
| Role, inputs, outputs, tools, completion criterion for each agent | Done in `docs/agents_specification.md` |
| Interaction scheme | Done in `docs/architecture.md` |
| Structured messages | Done with `AgentMessage` JSON objects |
| Prototype where at least 2 agents exchange data | Done: full pipeline runs 6 agents |
| External tools / data sources | Done: JSON datasets + SQLite state/log storage |
| Explicit task state | Done: `runtime/state.db` |
| Logging | Done: SQLite + JSONL logs |
| API keys not stored in code | Done: prototype uses local data only |

## Quick Start

Use Python 3.10+.

```bash
cd outputs/diploma_ai_platform_assignment2
python3 -m src.main \
  --topic "Intelligent Platform for Managing Diploma and Master's Projects with Functions for Assessing Topic Novelty, Eliminating Duplication, Assigning Supervisors, and Monitoring the Basic Completion Cycle" \
  --student "Sample Student" \
  --department "Computer Science" \
  --keywords "multi-agent, novelty assessment, supervisor matching, diploma projects"
```

Run the default demo:

```bash
python3 -m src.main --demo
```

Run tests:

```bash
python3 -m unittest discover -s tests
```

## Prototype Output

The CLI returns a JSON report with:

- normalized topic profile;
- novelty score and nearest archived topics;
- duplication decision;
- ranked supervisor recommendations;
- completion cycle milestones;
- final quality gate decision;
- load distribution by agents.

Runtime artifacts are written to:

- `runtime/state.db` - explicit task state, messages, and call records;
- `runtime/agent_calls.jsonl` - human-readable agent/tool call log.

## Repository Structure

```text
.
├── data/
│   ├── archive_topics.json
│   ├── completion_template.json
│   └── supervisors.json
├── docs/
│   ├── agents_specification.md
│   ├── architecture.md
│   ├── message_formats.md
│   └── test_scenarios.md
├── src/
│   ├── agents/
│   ├── storage/
│   ├── tools/
│   ├── main.py
│   └── orchestrator.py
└── tests/
    └── test_prototype.py
```

## Notes for Assignment 4

The current Assignment 2 prototype uses deterministic local agent logic so that it can be launched without API keys. For Assignment 4, each agent can be connected to an LLM adapter while keeping the same JSON message contracts, state store, and logging format.
