"""Session-local attempt history and portable exports."""
from __future__ import annotations
import csv, io, json
from dataclasses import asdict
from .models import Attempt

class SessionHistory:
    def __init__(self) -> None: self.attempts: list[Attempt] = []
    def add(self, attempt: Attempt) -> None: self.attempts.append(attempt)
    def to_json(self) -> str:
        return json.dumps([asdict(a) for a in self.attempts], ensure_ascii=False, indent=2)
    def to_csv(self) -> str:
        output = io.StringIO()
        fields = list(Attempt.__dataclass_fields__)
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader()
        writer.writerows(asdict(a) for a in self.attempts)
        return output.getvalue()
