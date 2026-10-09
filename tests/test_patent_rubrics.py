"""Official patent-claim rubric regression tests; no live API calls."""
from __future__ import annotations

import math

import pytest

from trainer.data import load_items, find_item
from trainer.grader import build_user_payload, grade_answer, validate_grade
from trainer.models import Item


TARGET_IDS = (
    "patent-2021-section-1",
    "patent-2022-section-1",
    "patent-2023-section-1",
)

PIANO_CLAIMS = """1. Menetelmä pianon äänenvärin säätämiseksi, joka menetelmä käsittää seuraavat vaiheet: Pianon vasaran (1) lyömäpinnan (2) huovan kuumentamisen vähintään 80 celsiusasteeseen ja korkeintaan 220 celsiusasteeseen.
2. Patenttivaatimuksen 1 mukainen menetelmä, pianon äänen kirkastamiseksi, jossa kuumentaminen toteutetaan kontaktoimalla työkalu (10) vasten lyömäpintaa (2).
3. Patenttivaatimuksen 1 tai 2 mukainen menetelmä, pianon äänen pehmentämiseksi, jossa menetelmä käsittää lisäksi seuraavan vaiheen: Pianon vasaran (1) lyömäpinnan (2) kärkialueen (3) käsittelyn vedellä, ennen mainittua kuumentamista.
4. Patenttivaatimuksen 3 mukainen menetelmä, jossa työkalun (10) ja lyömäpinnan (2) väliin asetetaan kostutettu huokoinen materiaalikerros ennen mainittua kuumentamista, jossa edullisesti materiaalikerros on tekstiiliä, edullisimmin puuvillaa.
5. Patenttivaatimuksen 3 tai 4 mukainen menetelmä, jossa vesikäsittely toteutetaan ruiskuttamalla neulalla vettä kärkialueen sisään.
6. Työkalu (10) pianon vasaran (1) lyömäpinnan (2) kuumentamiseksi, jossa työkalun kuumennettava osa on muotoiltu siten, että kuumennettava osa myötäilee lyömäpinnan (2) muotoa muodostaen kosketuksen kauttaaltaan lyömäpinnan kanssa."""


def _raw_grade(item, credits=None, deductions=None):
    credits = credits or {}
    deductions = deductions or {}
    results = [
        {
            "criterion_id": entry["id"],
            "awarded_points": credits.get(entry["id"], 0),
            "explanation": "Perusteltu kriteerikohtainen arvio",
        }
        for entry in item.grading["criteria"]
    ]
    penalties = [
        {
            "penalty_id": key,
            "points_deducted": amount,
            "explanation": "Virallisesta tekstistä tunnistettu erillinen virhe",
        }
        for key, amount in deductions.items()
    ]
    points = max(0, sum(r["awarded_points"] for r in results) - sum(deductions.values()))
    return {
        "final_points": points, "max_points": item.max_points,
        "summary": "Harjoitusarvio", "strengths": ["Yksittäisiä oikeita piirteitä"],
        "missing_or_incomplete": ["Muita olennaisia piirteitä puuttuu"],
        "improvement_advice": ["Tarkenna vaatimusten rakennetta"],
        "criteria_results": results, "penalties_applied": penalties,
        "holistic_reasoning": None,
    }


@pytest.fixture(scope="module")
def items():
    return load_items()


@pytest.mark.parametrize("item_id", TARGET_IDS)
def test_official_claims_rubrics_cover_exactly_fifty_points(items, item_id):
    item = find_item(items, item_id)
    assert item.grading["mode"] == "explicit_structured"
    ids = [c["id"] for c in item.grading["criteria"]]
    assert len(ids) == len(set(ids))
    assert math.isclose(sum(c["max_points"] for c in item.grading["criteria"]), 50)
    assert item.max_points == 50


def test_piano_response_earns_nonzero_credit_for_individually_correct_features(items):
    item = find_item(items, "patent-2022-section-1")
    # These are partial-credit anchors, not an assertion about the exact
    # official score of the full real-world answer.
    credits = {
        "main-heat-impact-face": 6,
        "main-colour-adjustment": 2,
        "dependent-brightening-contact": 5,
        "dependent-water-injection": 3,
        "dependent-moistened-porous-layer": 3,
    }

    class FakeProvider:
        def grade(self, chosen, answer):
            assert chosen.id == item.id
            assert "Patenttivaatimuksen 3 tai 4" in answer
            return _raw_grade(item, credits)

    result = grade_answer(item, PIANO_CLAIMS, FakeProvider())
    assert result.final_points == 19
    assert result.passed is False
    assert len(result.criteria_results) == 13
    assert item.official_grading_text in build_user_payload(item, PIANO_CLAIMS)


def test_structured_final_zero_rejected_if_components_earn_points(items):
    item = find_item(items, "patent-2022-section-1")
    raw = _raw_grade(item, {"main-heat-impact-face": 6})
    raw["final_points"] = 0
    with pytest.raises(ValueError, match="Loppupisteet"):
        validate_grade(item, raw)


def test_structured_zero_still_allowed_for_actually_empty_evidence(items):
    item = find_item(items, "patent-2022-section-1")
    assert validate_grade(item, _raw_grade(item)).final_points == 0


def test_official_penalty_amount_cannot_be_invented(items):
    item = find_item(items, "patent-2022-section-1")
    raw = _raw_grade(item, {"main-heat-impact-face": 6}, {"softening-temperature": 3})
    with pytest.raises(ValueError, match="pistemäärä"):
        validate_grade(item, raw)


def test_repeatable_official_penalties_are_multiples_of_unit(items):
    item = find_item(items, "patent-2022-section-1")
    result = validate_grade(
        item, _raw_grade(item, {"main-heat-impact-face": 6},
                         {"wrong-dependent-reference": 4})
    )
    assert result.final_points == 2
    raw = _raw_grade(item, {"main-heat-impact-face": 6},
                     {"wrong-dependent-reference": 3})
    with pytest.raises(ValueError, match="pistemäärä"):
        validate_grade(item, raw)


def test_duplicate_penalty_ids_rejected(items):
    item = find_item(items, "patent-2022-section-1")
    raw = _raw_grade(item, {"main-heat-impact-face": 6})
    raw["penalties_applied"] = [
        {"penalty_id": "softening-temperature", "points_deducted": 2,
         "explanation": "a"},
        {"penalty_id": "softening-temperature", "points_deducted": 2,
         "explanation": "b"},
    ]
    raw["final_points"] = 2
    with pytest.raises(ValueError, match="useammin"):
        validate_grade(item, raw)


def test_unknown_penalty_rejected(items):
    item = find_item(items, "patent-2022-section-1")
    raw = _raw_grade(item, {"main-heat-impact-face": 6},
                     {"invented-penalty": 2})
    with pytest.raises(ValueError, match="virallisen vähennyksen"):
        validate_grade(item, raw)


@pytest.mark.parametrize("item_id", TARGET_IDS)
def test_preanswer_public_view_hides_scoring_material(items, item_id):
    item = find_item(items, item_id)
    assert "grading" not in item.public_view()
    assert "official_grading_text" not in item.public_view()
    assert item.official_grading_text not in str(item.public_view())
