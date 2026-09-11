# Codex task: ingest missing 2024–2025 patent open-response examination sections

You are working in:

`pyypyyy/Asiamiestutkinto-trainer`

A source/ingestion package named approximately `patent_question_expansion_2024_2025/` has been added to the repository. Read its `README.md`, `source_manifest.json`, `expected_items_metadata.json`, and `integration_checklist.md` before changing code or data.

This is primarily a **data-ingestion expansion**, not an architectural rewrite.

## Goal

Add the six missing open-response patent examination sections from the official PRH 2024 and 2025 patent examination/model-answer PDFs:

- patent-2024-section-1
- patent-2024-section-2
- patent-2024-section-3
- patent-2025-section-1
- patent-2025-section-2
- patent-2025-section-3

Do not add the multiple-choice sections in this task.

The repository currently has 35 gradable items. After this task it should have 41.

## 1. Official sources are authoritative

Use the exact PRH PDF URLs and page ranges in `source_manifest.json`.

Download the PDFs into a temporary local cache for extraction/review. The helper script in the package may be used, or fetch them another reliable way.

Do not rely on memory, summaries, or general patent knowledge to reconstruct any examination content.

For each section, extract and preserve:

- full original question/task text,
- all application/prior-art/attachment text that forms part of the task,
- official examiner/model-answer text,
- explicit official scoring information and deductions,
- source/provenance metadata.

Do not modernize the legal content or compare it with current law.

## 2. Create six normal dataset items

Follow the schema and conventions already used by the existing 2020–2023 patent items.

Create/update:

- `exam_data/data/patent_2024.json`
- `exam_data/data/patent_2025.json`
- `exam_data/data/items.jsonl`

Use the exact IDs and core metadata in `expected_items_metadata.json`.

For all six items:

- `max_points = 50`
- `practice_pass_points = 25.0`
- `exam_part = "patent"`
- `question_type = "open_response"`
- preserve the standard historical-law notice.

Use the existing single-item pass-group convention used by earlier patent sections unless the current schema has since changed in a compatible way.

## 3. Grading mode and official points

Default all six items to:

`official_text_with_explicit_points`

because the official examiner documents contain explicit point values throughout but are not necessarily represented as a clean one-row-per-point structured rubric.

Do NOT transform prose point allocations into an invented equal-weight rubric.

Do NOT create model-generated criterion IDs.

Only use `explicit_structured` if the official PDF itself provides a complete, unambiguous point table that maps exactly to the repository structured rubric and can be represented without reinterpretation. If there is any doubt, keep `official_text_with_explicit_points` and preserve the official point text verbatim in evaluator-only grading material.

Important verified structural anchors:

- 2024 section 1: device and method protection each account for 25 points in the official scoring logic.
- 2024 section 3: invention 1 totals 25 points and invention 2 totals 25 points.
- 2025 section 1: independent device claim 20 points, independent method claim 20 points, dependent claims 10 points; official deductions for major drafting errors are also stated.
- 2025 section 3: PHST totals 25 points and PHST+B totals 25 points.

These anchors are checks, not substitutes for reading the full official scoring text.

## 4. PDF extraction must be visually verified

These are patent drafting/response tasks. Text extraction alone is not always reliable because the PDFs contain figures, tables, claims and prior-art layouts.

For every source section:

1. extract text with a layout-preserving method such as `pdftotext -layout` or PyMuPDF,
2. render the relevant PDF pages to images,
3. visually compare the extracted task text against the rendered pages,
4. correct extraction artifacts only where the PDF clearly establishes the intended text,
5. do not silently omit figures/tables that are necessary to answer the question.

Do not use OCR unless the normal PDF text layer is inadequate.

## 5. Minimal support for essential visual assets if needed

Inspect the existing application before modifying the schema/UI.

If a new question contains essential figure/table information that cannot be represented faithfully in `question_text`, implement a **minimal optional asset mechanism** rather than dropping the visual information.

A reasonable design is an optional item field such as:

`assets: [{"path": "...", "caption": "..."}]`

Requirements if assets are added:

- assets shown before submission are candidate-visible task material only,
- evaluator/model-answer pages must never be exposed before grading,
- `Item.public_view()` may expose only safe candidate-visible asset metadata,
- Colab UI displays the assets near the task,
- existing items without assets continue to work unchanged,
- add tests that evaluator-only material is not leaked.

Keep this change minimal. Do not redesign the application.

If all necessary content is faithfully preserved in text, do not add asset infrastructure merely for aesthetics.

## 6. Update pending and coverage metadata

After and only after successful ingestion:

- remove the 2024 patent entry from `exam_data/data/pending_sources.json`,
- remove the 2025 patent entry from `exam_data/data/pending_sources.json`,
- leave the 2025 common-part pending entry untouched,
- update `exam_data/INDEX.md`, coverage data, README references if necessary.

Do not delete provenance/source information.

## 7. Tests

Update/add tests so that at minimum:

- gradable item count is 41,
- all six expected new IDs exist,
- patent year filters include 2024 and 2025,
- every new item has max 50 and practice pass 25,
- every new item has non-empty full question text and official grading text,
- new items use an allowed grading mode,
- pending sources no longer list 2024 patent or 2025 patent,
- 2025 common remains pending,
- historical-law notice is present,
- no evaluator-only grading data is exposed before submission,
- tests make no live OpenAI calls.

If asset support is implemented, test it separately.

Do not weaken existing tests to make the new data pass.

## 8. Validation

Before finishing run:

```bash
python exam_data/scripts/validate_data.py
pytest
python -m compileall trainer app.py
```

Also manually inspect all six new records for:

- correct page/source provenance,
- no accidental question/model-answer mixing,
- no truncated task text,
- no invented legal content,
- no invented point allocation.

## 9. Do not modify unrelated behavior

Do not:

- migrate frameworks,
- change the OpenAI architecture unless required by the new data,
- add current-law web research,
- add the 2024/2025 multiple-choice patent section,
- modify old official exam texts for stylistic consistency,
- turn this into a broad refactor.

## 10. Completion report / PR

Open a focused PR.

Report:

1. six items added,
2. exact data files changed,
3. whether any visual assets were required,
4. pending-source changes,
5. validator result,
6. pytest result,
7. any extraction ambiguity that remains.
