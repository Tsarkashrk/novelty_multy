# Intelligent Platform for Managing Diploma and Master's Projects

Assignment 2 architecture and Assignment 4 working multi-agent system for diploma and master's project management:

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

## Assignment 2 Review

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

The Assignment 2 design and two-agent exchange requirements are met. The earlier 16.7% figure measured agent invocations only; Assignment 4 now measures actual tool calls. See [Assignment 4 submission](ASSIGNMENT_4_SUBMISSION_RU.md) for evidence and limitations.

## Quick Start

Use Python 3.10+ on macOS or Linux. From the repository root:

```bash
python3 -m src.main \
  --topic "Intelligent Platform for Managing Diploma and Master's Projects with Functions for Assessing Topic Novelty, Eliminating Duplication, Assigning Supervisors, and Monitoring the Basic Completion Cycle" \
  --student "Sample Student" \
  --department "Computer Science" \
  --keywords "multi-agent, novelty assessment, supervisor matching, diploma projects"
```

Run the default demo:

```bash
python3 -m src.main --demo --completed M1

# Exact archived title: duplication is BLOCKED
python3 -m src.main --topic "Intelligent Platform for Diploma Project Lifecycle Management" --completed M1

# Monitor progress at week 10
python3 -m src.main --demo --current-week 10 --completed M1,M2
```

Run tests:

```bash
python3 -m unittest discover -s tests -v

# Regenerate shareable result and JSONL log files
python3 -m scripts.generate_assignment4_artifacts
```

## Prototype Output

The CLI returns a JSON report with:

- normalized topic profile;
- novelty score and nearest archived topics;
- duplication decision;
- ranked supervisor recommendations;
- completion cycle milestones;
- final quality gate decision;
- load distribution by real tool calls (and LLM calls if later integrated).
- structured `status` and `errors` for failures.

Runtime artifacts are written to:

- `runtime/state.db` - task state, request/result messages, and per-call events;
- `runtime/agent_calls.jsonl` - per-agent and per-tool JSONL events.

Each successful run makes 6 agent calls and 10 actual tool calls. The largest tool-call share is 20%. The orchestrator stops after the configured number of steps or time budget, retries temporary failures once by default, and returns a clear error report when a run fails. CLI exits with code 2 for a failed run.

## Repository Structure

```text
.
├── data/
│   ├── archive_topics.json
│   ├── completion_template.json
│   └── supervisors.json
├── artifacts/
├── docs/
│   ├── agents_specification.md
│   ├── architecture.md
│   ├── message_formats.md
│   └── test_scenarios.md
├── scripts/
├── src/
│   ├── agents/
│   ├── storage/
│   ├── tools/
│   ├── main.py
│   └── orchestrator.py
└── tests/
    ├── test_assignment4.py
    └── test_prototype.py
```

## Scope and Limitations

The system runs entirely offline using transparent lexical similarity and rule-based decisions. There are no LLM calls or API keys. The novelty score is an estimate relative to the synthetic seven-topic archive, not a plagiarism verdict or academic approval. Supervisor records are also synthetic; recommendations do not reserve a slot. The hard time limit uses `SIGALRM` on macOS/Linux in the main thread; other environments use deadline checks between calls. The CLI handles one request at a time.
