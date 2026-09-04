#!/usr/bin/env python3
import json, math, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
items=[]
for line in (root/"data/items.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip(): items.append(json.loads(line))
errors=[]
ids=set()
for x in items:
    if x["id"] in ids: errors.append(f"duplicate id: {x['id']}")
    ids.add(x["id"])
    if not x.get("question_text","").strip(): errors.append(f"empty question: {x['id']}")
    if not x.get("official_grading_text","").strip(): errors.append(f"empty grading: {x['id']}")
    if x.get("max_points",0)<=0: errors.append(f"bad max: {x['id']}")
    if not math.isclose(x.get("practice_pass_points",-1),x["max_points"]/2): errors.append(f"bad practice pass: {x['id']}")
    g=x.get("exam_pass_group")
    if g and not math.isclose(g["pass_points"],g["max_points"]/2): errors.append(f"bad group pass: {x['id']}")
    if x.get("grading",{}).get("mode")=="explicit_structured":
        s=sum(c.get("max_points",0) for c in x["grading"].get("criteria",[]))
        if not math.isclose(s,x["max_points"]): errors.append(f"structured criteria sum {s} != max {x['max_points']}: {x['id']}")
if errors:
    print("VALIDATION FAILED")
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(items)} gradable items; all IDs unique; pass thresholds and structured criterion sums valid.")
