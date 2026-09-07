# Asiamiestutkinto exam data v1

Machine-readable source package for `pyypyyy/Asiamiestutkinto-trainer`.

## What is included

- 35 gradable open-response items.
- Common-part essay/open-response material from 2020–2024 where an official answer/grading basis and a defensible maximum score are available.
- Patent-part open-response sections 1–3 from 2020–2023, each with the full supplied task text and examiner report/model-answer material.
- 7 additional common-part questions kept in `ungraded_items.json` because the local source does not support reliable automated scoring.
- Metadata for official 2024 patent and 2025 sources in `pending_sources.json`; exact text is intentionally not fabricated.

## Integration

`data/items.jsonl` is intended to replace the current shortened-question dataset for essay/open-response practice. The application should display `question_text` only before submission. `official_grading_text`, `grading`, and any model-answer material are evaluator-only data.

## Pass thresholds

Every item contains `practice_pass_points = 50% * max_points`, as requested. When the source explicitly states an official pass threshold for a larger question group, this is stored separately in `exam_pass_group`. A single subquestion result must not be presented as proof that the whole official group has been passed.

## Historical law

No automatic current-law comparison is performed. Every item carries this notice:

> Arviointi perustuu kyseisen koevuoden viralliseen mallivastaukseen ja arvosteluperusteisiin. Lainsäädäntö, määräykset, ohjeet ja oikeuskäytäntö ovat voineet muuttua. Tarkista ajantasainen oikeustila erikseen.

## Important data rule

Do not invent points. `explicit_structured` means a point split is directly supported by the official material. `official_text_holistic` means the official source gives qualitative features rather than a defensible per-feature point table. `official_text_with_explicit_points` means the examiner report contains explicit point values throughout the source text and the grader must follow those values without inventing a new redistribution.
