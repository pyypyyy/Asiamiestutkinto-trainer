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
        self._updating_filters = False
        self.part.observe(self._part_changed, names="value"); self.year.observe(self._year_changed, names="value")
        self.category.observe(self._refresh_questions, names="value"); self.question.observe(self._select, names="value")
        self.random.on_click(self._choose_random); self.next.on_click(self._choose_random)
        self.submit.on_click(self._grade); self.retry.on_click(self._retry); self.reveal.on_click(self._reveal)
        self.export_json.on_click(lambda _: self._download("harjoitteluhistoria.json", self.history.to_json()))
        self.export_csv.on_click(lambda _: self._download("harjoitteluhistoria.csv", self.history.to_csv()))
        self._part_changed()

    def _matching(self):
        return filter_items(self.items, exam_part=self.part.value, year=self.year.value, category=self.category.value)
    def _part_changed(self, change=None):
        """Rebuild every dependent filter without exposing an invalid interim state."""
        if self._updating_filters:
            return
        self._updating_filters = True
        try:
            previous_year = self.year.value
            matching = filter_items(self.items, exam_part=self.part.value)
            years = sorted({i.year for i in matching}, reverse=True)
            self.year.options = [(str(year), year) for year in years]
            self.year.value = previous_year if previous_year in years else (years[0] if years else None)
            self._rebuild_categories()
        finally:
            self._updating_filters = False

    def _year_changed(self, change=None):
        if self._updating_filters:
            return
        self._updating_filters = True
        try:
            self._rebuild_categories()
        finally:
            self._updating_filters = False

    def _rebuild_categories(self):
        matching = filter_items(self.items, exam_part=self.part.value, year=self.year.value)
        categories = sorted({i.category for i in matching})
        previous_category = self.category.value
        self.category.options = [(category, category) for category in categories]
        self.category.value = (previous_category if previous_category in categories
                               else (categories[0] if categories else None))
        self._refresh_questions()

    def _refresh_questions(self, change=None):
        if self._updating_filters and change is not None:
            return
        matches = self._matching()
        previous_question = self.question.value
        self.question.options = [(f"{i.question_number}: {i.title}", i.id) for i in matches]
        if not matches:
            self._show_no_questions()
            return
        selected_id = previous_question if any(i.id == previous_question for i in matches) else matches[0].id
        self.question.value = selected_id
        selected = next(item for item in matches if item.id == selected_id)
        if self.current is None or self.current.id != selected_id:
            self._set_item(selected)

    def _select(self, change):
        if not self._updating_filters and change.get("new"):
            self._set_item(next(i for i in self.items if i.id == change["new"]))
    def _set_item(self, item: Item):
        self.current = item; self.answer.value = ""; self.retry.disabled = True; self.reveal.disabled = True
        self.submit.disabled = False; self.random.disabled = False; self.next.disabled = False
        with self.question_out: clear_output(); display(Markdown(question_markdown(item)))
        with self.result_out: clear_output()
        with self.official_out: clear_output()
    def _show_no_questions(self):
        self.current = None; self.answer.value = ""
        self.submit.disabled = True; self.random.disabled = True; self.next.disabled = True
        self.retry.disabled = True; self.reveal.disabled = True
        with self.question_out:
            clear_output(); display(Markdown("**Valituilla suodattimilla ei löytynyt tehtäviä.**"))
        with self.result_out: clear_output()
        with self.official_out: clear_output()

    def _choose_random(self, _):
        matches = self._matching()
        if not matches:
            self._show_no_questions()
            return
        item = random_item(matches)
        self.question.value = item.id
        if self.current is None or self.current.id != item.id:
            self._set_item(item)
    def _grade(self, _):
        if self.current is None:
            self._show_no_questions()
            return
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
