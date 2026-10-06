from __future__ import annotations

import math
import re
from collections import Counter


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
    "и",
    "в",
    "для",
    "на",
    "по",
    "с",
    "со",
    "the",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zа-я0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def normalize_text(text: str) -> str:
    return " ".join(tokenize(text))


def cosine_similarity(left: str, right: str) -> float:
    left_counts = Counter(tokenize(left))
    right_counts = Counter(tokenize(right))
    if not left_counts or not right_counts:
        return 0.0

    common = set(left_counts) & set(right_counts)
    numerator = sum(left_counts[token] * right_counts[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def blended_similarity(left: str, right: str) -> float:
    cosine = cosine_similarity(left, right)
    jaccard = jaccard_similarity(left, right)
    return round((0.7 * cosine) + (0.3 * jaccard), 4)


def topic_to_text(topic: dict) -> str:
    parts = [
        topic.get("title", ""),
        " ".join(topic.get("keywords", [])),
        topic.get("abstract", ""),
    ]
    return " ".join(parts)
