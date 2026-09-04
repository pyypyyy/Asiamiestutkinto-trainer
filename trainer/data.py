"""Authoritative examination-data access."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Iterable

from .models import Item

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE_ITEMS_PATH = REPOSITORY_ROOT / "exam_data" / "data" / "items.jsonl"


def load_items(path: Path | None = None) -> list[Item]:
    """Load gradable items. Ungraded and pending files are deliberately excluded."""
    source = path or AUTHORITATIVE_ITEMS_PATH
    if path is not None and source.resolve() != AUTHORITATIVE_ITEMS_PATH.resolve():
        raise ValueError("Only the authoritative gradable dataset may be loaded")
    with source.open(encoding="utf-8") as handle:
        items = [Item(json.loads(line)) for line in handle if line.strip()]
    ids = [item.id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Dataset contains duplicate item IDs")
    return items


def filter_items(items: Iterable[Item], *, exam_part: str | None = None,
                 year: int | None = None, category: str | None = None) -> list[Item]:
    return [item for item in items
            if (exam_part is None or item.exam_part == exam_part)
            and (year is None or item.year == year)
            and (category is None or item.category == category)]


def find_item(items: Iterable[Item], item_id: str) -> Item:
    try:
        return next(item for item in items if item.id == item_id)
    except StopIteration as exc:
        raise KeyError(f"Tuntematon tehtävä: {item_id}") from exc


def random_item(items: Iterable[Item], rng: random.Random | None = None) -> Item:
    choices = list(items)
    if not choices:
        raise ValueError("Suodattimilla ei löytynyt tehtäviä")
    return (rng or random).choice(choices)
