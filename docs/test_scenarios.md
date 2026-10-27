# Assignment 4 Test Scenarios

Run all scenarios with `python3 -m unittest discover -s tests -v`. The 12 integrated cases below are implemented in `tests/test_assignment4.py`. Five archive integration checks are in `tests/test_openalex_archive.py`. `test_threshold_boundaries` is an additional unit check. The older Assignment 2 smoke test also remains.

| ID | Input or fault | Expected result |
| --- | --- | --- |
| TS-01 | New topic, week 5, M1 complete, OpenAlex default archive | Six agents complete; 10 tool events and six agent events; no share above 40%; 160 of 230 rows used. |
| TS-02 | Exact title `Intelligent Platform for Diploma Project Lifecycle Management` with `archive_source=sample` | Duplication `BLOCKED`, final `BLOCK_TOPIC`, sample archive ID T-2026-002 cited. |
| TS-03 | Short title `AI System` | Intake warning and `REVISE_BEFORE_TEACHER_REVIEW`. |
| TS-04 | Week 11 with M2 incomplete | M2 `OVERDUE`, high risk and revision requested. |
| TS-05 | Week 10 with M1 and M2 complete | M1/M2 `DONE`; M3 `IN_PROGRESS`. |
| TS-06 | Topic matching supervisor S-005, whose capacity is full | S-005 excluded from available recommendations. |
| TS-07 | Blank title | Structured `FAILED` report, clear title error, no repeated validation. |
| TS-08 | Intake agent fails transiently once | Second attempt succeeds; both attempts appear in logs. |
| TS-09 | Archive source raises `OSError` twice | Two failed tool and agent attempts logged; structured `FAILED` report. |
| TS-10 | Agent sleeps past the time budget | Prompt `ExecutionTimeout` report and `TIMEOUT` event. |
| TS-11 | Maximum of three agent steps | Three outputs saved, then structured step-limit failure. |
| TS-12 | Normal request | Twelve SQLite messages, final task state, six agent events, ten tool events persisted. |

## OpenAlex and CSV Checks

| Scenario | Expected result |
| --- | --- |
| Exact real OpenAlex title OA0001 | `BLOCK_TOPIC`, similarity 1.0, OpenAlex URL and `is_synthetic=false` in evidence. |
| Synthetic variant NEAR0001 | 160 records by default; 230 and NEAR0001 in evidence with `--include-synthetic`. |
| Custom compatible CSV | Exact custom title is blocked and source recorded as `custom_csv`. |
| CSV missing required columns | Structured `FAILED` report with missing-column error. |
| Non-ASCII title tokenization | Kazakh letters are retained as tokens. |

## Enriched CSV Checks

`tests/test_enriched_csv.py` verifies that all 230 source rows and original fields are preserved, calculated supervisor and milestone previews are present, `--record-id` avoids self-matches and reproduces the preview for OA0001/OA0004, edited project inputs survive regeneration and feed the agents, the enriched file can also be used as an archive, and unknown IDs return a clear error.

Representative inputs and outcomes are also available in `artifacts/assignment4_scenario_results.json`. The demo output and its 16 JSONL events are in `artifacts/assignment4_demo_output.json` and `artifacts/assignment4_demo_calls.jsonl`. Regenerate these with `python3 -m scripts.generate_assignment4_artifacts`.
