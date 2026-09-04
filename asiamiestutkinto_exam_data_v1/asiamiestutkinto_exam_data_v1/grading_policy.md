# Grading policy

1. **Exam-year basis only.** Score against the official model answer/examiner criteria stored with that item. Do not update the answer to current law during scoring.
2. **No invented criteria.** Credit only content supported by `official_grading_text` or structured `grading.criteria`.
3. **Respect the maximum.** Final score must be between 0 and `max_points`.
4. **Respect explicit point splits.** If the official source assigns a specific number of points to a matter, use that number.
5. **Holistic material stays holistic.** If the official material only lists features of a good answer, do not assign equal or otherwise fabricated points to each bullet. Judge the answer as a whole within the official maximum.
6. **No invented negative marking.** Apply a deduction only where the official criteria support it, or where a contradiction directly defeats credit that would otherwise be awarded.
7. **Practice pass.** `practice_pass = final_points >= practice_pass_points`. Show e.g. `7/10 – HYVÄKSYTTY` and `Hyväksymisraja 5/10`.
8. **Official group pass.** If `exam_pass_group` exists and contains several subitems, do not call the official group passed until all its member items have been graded. Until then use `official_group_status = incomplete`.
9. **Feedback.** Explain awarded points, missing points, and the most important improvements, grounded in the official source.
10. **Do not reveal the model answer before submission.** The app may show it after grading if desired.
11. **Historical-law notice.** Append: `Arviointi perustuu kyseisen koevuoden viralliseen mallivastaukseen ja arvosteluperusteisiin. Lainsäädäntö, määräykset, ohjeet ja oikeuskäytäntö ovat voineet muuttua. Tarkista ajantasainen oikeustila erikseen.`
