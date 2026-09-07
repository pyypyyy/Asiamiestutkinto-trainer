#!/usr/bin/env python3
"""Command-line interface using the shared trainer core."""
import argparse, sys
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from trainer.data import find_item, load_items, random_item
from trainer.grader import grade_answer
from trainer.ui_colab import assessment_markdown, question_markdown

console = Console()
def main() -> int:
    parser = argparse.ArgumentParser(description="Asiamiestutkinnon harjoittelusovellus")
    parser.add_argument("--list", action="store_true", help="listaa arvioitavat tehtävät")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--id", help="valitse tehtävä tunnisteella")
    group.add_argument("--random", action="store_true", help="valitse satunnainen tehtävä")
    parser.add_argument("--answer-file", help="lue vastaus tiedostosta (oletus: stdin)")
    args = parser.parse_args(); items = load_items()
    if args.list:
        table = Table("ID", "Vuosi", "Osa", "Tehtävä", "Pisteet")
        for item in items: table.add_row(item.id, str(item.year), item.exam_part, item.title, f"{item.max_points:g}")
        console.print(table)
        if not (args.id or args.random): return 0
    if not (args.id or args.random): parser.error("valitse --id ID tai --random (tai käytä --list)")
    try: item = find_item(items, args.id) if args.id else random_item(items)
    except (KeyError, ValueError) as exc: console.print(f"[red]{exc}[/red]"); return 2
    console.print(Markdown(question_markdown(item)))
    if not args.answer_file and sys.stdin.isatty(): console.print("Kirjoita vastaus ja lopeta Ctrl-D:")
    answer = open(args.answer_file, encoding="utf-8").read() if args.answer_file else sys.stdin.read()
    try: result = grade_answer(item, answer)
    except Exception as exc: console.print(f"[red]Arviointi epäonnistui: {exc}[/red]"); return 1
    console.print(Markdown(assessment_markdown(item, result))); return 0
if __name__ == "__main__": raise SystemExit(main())
