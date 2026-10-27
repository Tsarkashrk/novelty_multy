# Topic archive provenance

`openalex_thesis_topics.csv` was copied from the user-provided OpenAlex silver dataset in the local `novelty-similarity-detection-model` project. The file has 230 topic records: 160 metadata records from OpenAlex and 70 controlled synthetic variants derived from those records. It also contains source IDs, URLs, language, year, and domain metadata. The original project's `data/openalex_silver/README.md` describes its collection and silver-label construction.

The multi-agent application reads all rows, validates IDs and required columns, and by default excludes the 70 records marked `is_synthetic=true` from novelty and duplication decisions. `--include-synthetic` includes them for benchmark demonstrations. Results link to the OpenAlex record where the URL is present.

The archive is a limited research sample; a low lexical overlap with these records does not prove academic novelty. Synthetic variants are generated examples, not independent university theses. The separate `archive_topics.json` file is a small demonstration archive and is used only with `--archive-source sample`.

## Enriched Project CSV

`openalex_projects_enriched.csv` preserves every column of the original file and adds:

| Columns | Meaning |
| --- | --- |
| `student`, `department`, `current_week`, `completed_milestones` | Editable input for a selected project row. Leave blank to use the documented demo defaults. Milestones use codes such as `M1;M2`. |
| `demo_nearest_topic_id`, `demo_nearest_similarity`, `demo_novelty_score`, `demo_duplication_status` | Preview from the novelty and duplicate agents, excluding the row itself from the 160 nonsynthetic archive records. |
| `demo_recommended_supervisor_id`, `demo_recommended_supervisor_name`, `demo_recommended_supervisor_score`, `demo_supervisor_alternatives` | Predicted recommendations using `supervisors.json`, which is a synthetic roster. These are not actual historical assignments. |
| `demo_completion_risk`, `demo_milestone_plan` | Preview from the completion-cycle agent for the demo semester week and completed milestones. |
| `demo_quality_decision`, `demo_quality_issues`, `demo_assumptions` | Preview of the quality gate and the exact scenario assumptions used to generate it. |

`supervisor_id` remains unchanged and blank where the source did not supply a real supervisor. Run `python3 -m src.main --record-id OA0001` to recalculate one row through all six agents. Run `python3 -m scripts.build_enriched_openalex_csv` to refresh the derived `demo_*` columns; the four editable input columns are preserved by ID. The source CSV is never overwritten.
