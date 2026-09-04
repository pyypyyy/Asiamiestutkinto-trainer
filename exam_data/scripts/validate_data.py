#!/usr/bin/env python3
"""Validate the authoritative gradable examination dataset."""
import json
import math
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path(__file__).resolve().parents[1]
items_path = root / "data" / "items.jsonl"
schema = json.loads((root / "schema" / "item.schema.json").read_text(encoding="utf-8"))
items = [json.loads(line) for line in items_path.read_text(encoding="utf-8").splitlines() if line.strip()]
errors: list[str] = []
ids: set[str] = set()
validator = Draft202012Validator(schema)
valid_modes = {"explicit_structured", "official_text_with_explicit_points", "official_text_holistic"}
notice = "Arviointi perustuu kyseisen koevuoden viralliseen mallivastaukseen ja arvosteluperusteisiin."
for item in items:
    item_id = item.get("id", "<missing-id>")
    for error in validator.iter_errors(item):
        errors.append(f"schema {item_id} ({'.'.join(map(str, error.path))}): {error.message}")
    if item_id in ids: errors.append(f"duplicate id: {item_id}")
    ids.add(item_id)
    if not item.get("question_text", "").strip(): errors.append(f"empty question: {item_id}")
    if not item.get("official_grading_text", "").strip(): errors.append(f"empty grading: {item_id}")
    if item.get("max_points", 0) <= 0: errors.append(f"bad max: {item_id}")
    if not math.isclose(item.get("practice_pass_points", -1), item.get("max_points", 0) / 2):
        errors.append(f"bad practice pass: {item_id}")
    grading = item.get("grading", {})
    if grading.get("mode") not in valid_modes: errors.append(f"bad grading mode: {item_id}")
    if not grading.get("instruction", "").strip(): errors.append(f"empty grading instruction: {item_id}")
    if not item.get("source", {}).get("provenance", "").strip(): errors.append(f"missing provenance: {item_id}")
    if not item.get("legal_state_notice", "").startswith(notice): errors.append(f"bad legal notice: {item_id}")
    group = item.get("exam_pass_group")
    if group:
        if not math.isclose(group["pass_points"], group["max_points"] / 2): errors.append(f"bad group pass: {item_id}")
        if item_id not in group.get("members", []): errors.append(f"group omits member: {item_id}")
    if grading.get("mode") == "explicit_structured":
        criteria = grading.get("criteria", [])
        criterion_ids = [c.get("id") for c in criteria]
        if len(criterion_ids) != len(set(criterion_ids)): errors.append(f"duplicate criterion ID: {item_id}")
        total = sum(c.get("max_points", 0) for c in criteria)
        if not math.isclose(total, item["max_points"]): errors.append(f"structured criteria sum {total} != max {item['max_points']}: {item_id}")
if errors:
    print("VALIDATION FAILED")
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(items)} gradable items; schema, IDs, provenance, pass thresholds and grading rules valid.")
