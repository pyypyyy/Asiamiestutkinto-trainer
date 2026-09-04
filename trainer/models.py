"""Typed domain models and deterministic assessment validation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CriterionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion_id: str
    awarded_points: float
    explanation: str

    @field_validator("awarded_points")
    @classmethod
    def finite(cls, value: float) -> float:
        if not float(value) == value or value in (float("inf"), float("-inf")):
            raise ValueError("Pisteiden on oltava äärellinen luku")
        return value


class PenaltyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    penalty_id: str
    points_deducted: float = Field(ge=0)
    explanation: str


class ModelGrade(BaseModel):
    """Untrusted model output; application-derived fields are intentionally absent."""
    model_config = ConfigDict(extra="forbid")
    final_points: float
    max_points: float
    summary: str
    strengths: list[str]
    missing_or_incomplete: list[str]
    improvement_advice: list[str]
    criteria_results: list[CriterionResult] | None
    penalties_applied: list[PenaltyResult]
    holistic_reasoning: str | None


@dataclass(frozen=True)
class Item:
    raw: dict[str, Any]

    def __getattr__(self, name: str) -> Any:
        try:
            return self.raw[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def public_view(self) -> dict[str, Any]:
        """Only information safe to reveal before answering."""
        keys = ("id", "year", "exam_part", "category", "question_number", "title",
                "question_type", "max_points", "practice_pass_points", "question_text")
        return {key: self.raw.get(key) for key in keys}


@dataclass(frozen=True)
class Assessment:
    item_id: str
    final_points: float
    max_points: float
    pass_points: float
    passed: bool
    summary: str
    strengths: list[str]
    missing_or_incomplete: list[str]
    improvement_advice: list[str]
    criteria_results: list[CriterionResult]
    penalties_applied: list[PenaltyResult]
    holistic_reasoning: str | None
    legal_state_notice: str
    official_group_status: str | None


@dataclass(frozen=True)
class Attempt:
    timestamp: str
    item_id: str
    year: int
    exam_part: str
    title: str
    answer: str
    awarded_points: float
    maximum_points: float
    passed: bool
    assessment_summary: str

    @classmethod
    def create(cls, item: Item, answer: str, result: Assessment) -> "Attempt":
        return cls(datetime.now(timezone.utc).isoformat(), item.id, item.year, item.exam_part,
                   item.title, answer, result.final_points, result.max_points,
                   result.passed, result.summary)
