# Test Scenarios

These scenarios can be used for Assignment 4 and exam preparation. Assignment 2 already includes a runnable prototype and one automated unit test suite.

| ID | Scenario | Input Topic | Expected Result |
| --- | --- | --- | --- |
| TS-01 | Normal topic with partial similarity | Intelligent Platform for Managing Diploma and Master's Projects with Novelty Assessment and Supervisor Matching | Topic is accepted for teacher review or revision, supervisor recommendations are returned. |
| TS-02 | Clear duplicate | Intelligent Platform for Diploma Project Lifecycle Management | Duplication status is `BLOCKED` or `REVISION_REQUIRED`, with archived topic evidence. |
| TS-03 | Weak topic title | AI System | Topic Intake Agent returns warning about short title and Quality Gate asks for revision. |
| TS-04 | No department match | Quantum Biology Platform for Thesis Topics | Supervisor Matching Agent still ranks available supervisors but warns about weak expertise fit. |
| TS-05 | Supervisor capacity issue | Topic focused on plagiarism detection when matching supervisor is full | Recommendation excludes or penalizes full-capacity supervisor. |
| TS-06 | Full defense scenario | Dissertation topic with all required fields | All 6 agents run, logs show balanced distribution, final JSON is generated. |

## Manual Command Example

```bash
python3 -m src.main --demo
```

## Automated Test Command

```bash
python3 -m unittest discover -s tests
```
