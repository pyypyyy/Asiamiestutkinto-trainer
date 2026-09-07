"""ipywidgets user interface for Google Colab and Jupyter."""
from __future__ import annotations
import html
from pathlib import Path

import ipywidgets as widgets
from IPython.display import Markdown, clear_output, display

from .data import filter_items, load_items, random_item
from .grader import grade_answer
from .history import SessionHistory
from .models import Attempt, Assessment, Item

PART_NAMES = {"common": "Yhteinen osa", "patent": "Patenttioikeus"}

def _n(value: float) -> str: return f"{value:g}"
def question_markdown(item: Item) -> str:
    public = item.public_view()
    return (f"## {html.escape(public['title'])}\n**Vuosi:** {public['year']} · **Osa:** "
            f"{PART_NAMES.get(public['exam_part'], public['exam_part'])} · **Tehtävä:** "
            f"{html.escape(public['question_number'])} · **Enimmäispisteet:** {_n(public['max_points'])}\n\n"
            f"{public['question_text']}")

def assessment_markdown(item: Item, result: Assessment) -> str:
    status = "HYVÄKSYTTY" if result.passed else "HYLÄTTY"
    lines = [f"## Tulos: {_n(result.final_points)}/{_n(result.max_points)} – {status}",
             f"**Hyväksymisraja: {_n(result.pass_points)}/{_n(result.max_points)}**", result.summary,
             "### Mikä onnistui", *[f"- {x}" for x in result.strengths],
             "### Puuttuvat tai riittämättömät asiat", *[f"- {x}" for x in result.missing_or_incomplete],
             "### Näin parannat vastausta", *[f"- {x}" for x in result.improvement_advice]]
    if result.criteria_results:
        official = {c["id"]: c for c in item.grading["criteria"]}
        lines += ["### Kriteerikohtainen arvio", "| Kriteeri | Pisteet | Perustelu |", "|---|---:|---|"]
        for row in result.criteria_results:
            criterion = official[row.criterion_id]
            lines.append(f"| {criterion['description']} | {_n(row.awarded_points)}/{_n(criterion['max_points'])} | {row.explanation} |")
    if result.holistic_reasoning: lines += ["### Kokonaisarvion perustelu", result.holistic_reasoning]
    if result.official_group_status == "incomplete":
        lines += ["> Tämä on yksittäisen tehtävän harjoitustulos. Virallisen tehtäväryhmän hyväksymistä ei voida ratkaista ennen kaikkien osatehtävien arviointia."]
    lines += ["---", f"⚠️ **Historiallista oikeustilaa koskeva huomautus:** {result.legal_state_notice}"]
    return "\n\n".join(lines)


class TrainerUI:
    def __init__(self) -> None:
        self.items = load_items(); self.history = SessionHistory(); self.current: Item | None = None
        parts = sorted({i.exam_part for i in self.items})
        self.part = widgets.Dropdown(description="Osa", options=[(PART_NAMES[p], p) for p in parts])
        self.year = widgets.Dropdown(description="Vuosi")
        self.category = widgets.Dropdown(description="Kategoria")
        self.question = widgets.Dropdown(description="Tehtävä", layout=widgets.Layout(width="80%"))
        self.random = widgets.Button(description="Satunnainen tehtävä", button_style="info")
        self.next = widgets.Button(description="Uusi tehtävä", button_style="info")
        self.answer = widgets.Textarea(description="Vastaus", placeholder="Kirjoita vastauksesi tähän…",
            layout=widgets.Layout(width="100%", height="260px"))
        self.submit = widgets.Button(description="Arvioi vastaus", button_style="success")
        self.retry = widgets.Button(description="Yritä uudelleen", disabled=True)
        self.reveal = widgets.Button(description="Näytä virallinen arvosteluperuste", disabled=True)
        self.export_json = widgets.Button(description="Lataa historia JSON")
        self.export_csv = widgets.Button(description="Lataa historia CSV")
        self.question_out = widgets.Output(); self.result_out = widgets.Output(); self.official_out = widgets.Output()
        self.part.observe(self._filters_changed, names="value"); self.year.observe(self._filters_changed, names="value")
        self.category.observe(self._refresh_questions, names="value"); self.question.observe(self._select, names="value")
        self.random.on_click(self._choose_random); self.next.on_click(self._choose_random)
        self.submit.on_click(self._grade); self.retry.on_click(self._retry); self.reveal.on_click(self._reveal)
        self.export_json.on_click(lambda _: self._download("harjoitteluhistoria.json", self.history.to_json()))
        self.export_csv.on_click(lambda _: self._download("harjoitteluhistoria.csv", self.history.to_csv()))
        self._refresh_filters()

    def _matching(self):
        return filter_items(self.items, exam_part=self.part.value, year=self.year.value, category=self.category.value)
    def _refresh_filters(self):
        matching = filter_items(self.items, exam_part=self.part.value)
        years = sorted({i.year for i in matching}, reverse=True); self.year.options = [(str(y), y) for y in years]
        self._filters_changed()
    def _filters_changed(self, change=None):
        matching = filter_items(self.items, exam_part=self.part.value, year=self.year.value)
        categories = sorted({i.category for i in matching}); self.category.options = [(c, c) for c in categories]
        self._refresh_questions()
    def _refresh_questions(self, change=None):
        matches = self._matching(); self.question.options = [(f"{i.question_number}: {i.title}", i.id) for i in matches]
        if matches: self._set_item(matches[0])
    def _select(self, change):
        if change.get("new"):
            self._set_item(next(i for i in self.items if i.id == change["new"]))
    def _set_item(self, item: Item):
        self.current = item; self.answer.value = ""; self.retry.disabled = True; self.reveal.disabled = True
        with self.question_out: clear_output(); display(Markdown(question_markdown(item)))
        with self.result_out: clear_output()
        with self.official_out: clear_output()
    def _choose_random(self, _):
        item = random_item(self._matching()); self.question.value = item.id; self._set_item(item)
    def _grade(self, _):
        assert self.current
        with self.result_out:
            clear_output(); print("Arvioidaan…")
            try: result = grade_answer(self.current, self.answer.value)
            except Exception as exc: clear_output(); print(f"Arviointi epäonnistui: {exc}"); return
            clear_output(); display(Markdown(assessment_markdown(self.current, result)))
        self.history.add(Attempt.create(self.current, self.answer.value, result))
        self.retry.disabled = False; self.reveal.disabled = False
    def _retry(self, _):
        self.answer.value = ""; self.retry.disabled = True; self.reveal.disabled = True
        with self.result_out: clear_output()
        with self.official_out: clear_output()
    def _reveal(self, _):
        assert self.current
        with self.official_out: clear_output(); display(Markdown("### Virallinen arvosteluperuste\n\n" + self.current.official_grading_text))
    def _download(self, filename: str, content: str):
        Path(filename).write_text(content, encoding="utf-8")
        try:
            from google.colab import files
            files.download(filename)
        except ImportError:
            print(f"Historia tallennettu tiedostoon {filename}")
    def display(self):
        display(widgets.VBox([widgets.HTML("<h1>Asiamiestutkinto-trainer</h1>"),
            widgets.HBox([self.part, self.year, self.category]), self.question,
            widgets.HBox([self.random, self.next]), self.question_out, self.answer,
            widgets.HBox([self.submit, self.retry, self.reveal]), self.result_out,
            self.official_out, widgets.HTML("<h3>Istuntohistoria</h3>"),
            widgets.HBox([self.export_json, self.export_csv])]))

def launch() -> TrainerUI:
    app = TrainerUI(); app.display(); return app
