from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def load_json_dataset(name: str) -> Any:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_topic_archive(
    source: str = "openalex",
    csv_path: str | None = None,
    include_synthetic: bool = False,
) -> dict[str, Any]:
    if csv_path:
        path = Path(csv_path).expanduser()
        source_name = "custom_csv"
    elif source == "openalex":
        path = DATA_DIR / "openalex_thesis_topics.csv"
        source_name = "openalex_csv"
    elif source == "sample":
        topics = load_json_dataset("archive_topics.json")
        return {
            "topics": [{**topic, "domain": topic.get("department", ""), "source": "Demo JSON", "is_synthetic": True, "url": ""} for topic in topics],
            "source": "sample_json",
            "file": "archive_topics.json",
            "records_total": len(topics),
            "records_used": len(topics),
            "synthetic_excluded": 0,
        }
    else:
        raise ValueError(f"Unknown archive source: {source}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"id", "title", "abstract", "keywords", "domain", "year", "is_synthetic"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            missing = ", ".join(sorted(required - set(reader.fieldnames or [])))
            raise ValueError(f"Archive CSV is missing columns: {missing}")
        topics = []
        total = 0
        excluded = 0
        seen_ids: set[str] = set()
        for row in reader:
            total += 1
            topic_id = (row["id"] or "").strip()
            title = (row["title"] or "").strip()
            if not topic_id or not title:
                raise ValueError(f"Archive CSV row {total} has no id or title")
            if topic_id in seen_ids:
                raise ValueError(f"Archive CSV contains duplicate id: {topic_id}")
            seen_ids.add(topic_id)
            synthetic_value = (row["is_synthetic"] or "").strip().lower()
            if synthetic_value not in {"true", "false"}:
                raise ValueError(f"Archive CSV row {total} has invalid is_synthetic")
            is_synthetic = synthetic_value == "true"
            if is_synthetic and not include_synthetic:
                excluded += 1
                continue
            year_value = (row["year"] or "").strip()
            topics.append({
                "id": topic_id,
                "title": title,
                "abstract": (row["abstract"] or "").strip(),
                "keywords": [item.strip() for item in (row["keywords"] or "").split(";") if item.strip()],
                "domain": (row["domain"] or "").strip(),
                "year": int(year_value) if year_value else None,
                "language": (row.get("language") or "").strip(),
                "source": (row.get("source") or source_name).strip(),
                "source_id": (row.get("source_id") or "").strip(),
                "url": (row.get("url") or "").strip(),
                "is_synthetic": is_synthetic,
            })
    if not topics:
        raise ValueError("Archive CSV contains no usable topics")
    return {
        "topics": topics,
        "source": source_name,
        "file": path.name,
        "records_total": total,
        "records_used": len(topics),
        "synthetic_excluded": excluded,
    }
