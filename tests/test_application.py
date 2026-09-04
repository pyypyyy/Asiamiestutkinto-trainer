import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from trainer.data import AUTHORITATIVE_ITEMS_PATH, load_items
from trainer.grader import grade_answer, validate_grade
from trainer.models import Item, ModelGrade
from trainer.ui_colab import assessment_markdown, question_markdown

@pytest.fixture(scope="module")
def items(): return load_items()

def raw_grade(points=1.5, criteria=None, holistic=None, max_points=10):
    return {"final_points": points, "max_points": max_points, "summary": "Yhteenveto", "strengths": ["Hyvä havainto"],
            "missing_or_incomplete": ["Täydennä perustelua"], "improvement_advice": ["Jäsennä vastaus"],
            "criteria_results": criteria, "penalties_applied": [], "holistic_reasoning": holistic}

def test_authoritative_dataset_loads(items): assert len(items) == 35
def test_only_gradable_items_are_exposed(items):
    ungraded = json.loads((AUTHORITATIVE_ITEMS_PATH.parent / "ungraded_items.json").read_text())
    ungraded_ids = {x["id"] for x in ungraded}
    assert ungraded_ids.isdisjoint(i.id for i in items)
def test_ids_unique(items): assert len({i.id for i in items}) == len(items)
def test_old_root_dataset_cannot_be_used(items):
    assert not (AUTHORITATIVE_ITEMS_PATH.parents[2] / "items.jsonl").exists()
    with pytest.raises(ValueError): load_items(Path("some-other-items.jsonl"))
def test_full_question_text(items): assert all(len(i.question_text) >= 90 for i in items)
def test_pass_threshold_exactly_half(items): assert all(i.practice_pass_points == i.max_points / 2 for i in items)
def test_half_points_and_python_pass(items):
    item = next(i for i in items if i.id == "common-2021-q2a")
    criteria = [{"criterion_id": c["id"], "awarded_points": c["max_points"] / 2,
                 "explanation": "Perustelu"} for c in item.grading["criteria"]]
    result = validate_grade(item, raw_grade(1.5, criteria, max_points=item.max_points))
    assert result.final_points == 1.5 and result.passed is True
def test_score_below_zero_rejected(items):
    item = next(i for i in items if i.grading["mode"] == "official_text_holistic")
    with pytest.raises(ValueError, match="välillä"): validate_grade(item, raw_grade(-0.5, holistic="Perustelu"))
def test_score_above_maximum_rejected(items):
    item = next(i for i in items if i.grading["mode"] == "official_text_holistic")
    with pytest.raises(ValueError, match="välillä"): validate_grade(item, raw_grade(item.max_points + .5, holistic="Perustelu"))
def test_pass_is_computed_not_accepted_from_model(items):
    item = next(i for i in items if i.grading["mode"] == "official_text_holistic")
    raw = raw_grade(item.practice_pass_points - .5, holistic="Perustelu")
    raw["passed"] = True
    with pytest.raises(ValueError): validate_grade(item, raw)
    assert not validate_grade(item, raw_grade(item.practice_pass_points - .5, holistic="Perustelu")).passed
def test_structured_unknown_criterion_rejected(items):
    item = next(i for i in items if i.grading["mode"] == "explicit_structured")
    with pytest.raises(ValueError, match="Tuntemattomia"):
        validate_grade(item, raw_grade(0, [{"criterion_id":"invented", "awarded_points":0, "explanation":"-"}], max_points=item.max_points))
def test_holistic_needs_no_fabricated_criteria(items):
    item = next(i for i in items if i.grading["mode"] == "official_text_holistic")
    assert validate_grade(item, raw_grade(5, holistic="Kokonaisarvio")).criteria_results == []
    with pytest.raises(ValueError, match="Holistisessa"):
        validate_grade(item, raw_grade(5, [{"criterion_id":"fake", "awarded_points":5, "explanation":"-"}], "x"))
def test_evaluator_fields_hidden_before_answer(items):
    view = items[0].public_view(); rendered = question_markdown(items[0])
    assert "official_grading_text" not in view and "grading" not in view
    assert items[0].official_grading_text not in rendered
def test_legal_notice_always_rendered(items):
    item = next(i for i in items if i.grading["mode"] == "official_text_holistic")
    result = validate_grade(item, raw_grade(5, holistic="Kokonaisarvio"))
    assert item.legal_state_notice in assessment_markdown(item, result)
def test_provider_is_mockable_without_openai(items):
    item = next(i for i in items if i.grading["mode"] == "official_text_holistic")
    class Fake:
        def grade(self, selected, answer): return raw_grade(5, holistic="Kokonaisarvio")
    assert grade_answer(item, "Oma vastaus", Fake()).final_points == 5
def test_model_grade_requires_structured_shape():
    with pytest.raises(ValidationError): ModelGrade.model_validate({"final_points": 1})
