import os, sys, json, uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

from openai import OpenAI
from rich.console import Console
from rich.table import Table

console = Console()
MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")  # Vaihda halutessasi

# ---------- HELPERS ----------

def load_items(path: str = "items.jsonl") -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        console.print(f"[red]Ei löytynyt tiedostoa: {path}[/red]")
        sys.exit(1)
    items = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items

def load_prompt_template(path: str = "prompt_template.txt") -> str:
    p = Path(path)
    if not p.exists():
        console.print(f"[red]Ei löytynyt tiedostoa: {path}[/red]")
        sys.exit(1)
    return p.read_text(encoding="utf-8")

def build_messages(template: str, *, question_text: str, rubric: Dict[str, Any], user_answer: str, max_points: int):
    # Korvaa paikkamerkit → ei f-stringejä, joten sulkeet eivät aiheuta ongelmia
    user_prompt = (
        template
        .replace("{{question_text}}", question_text)
        .replace("{{rubric_json}}", json.dumps(rubric, ensure_ascii=False))
        .replace("{{user_answer}}", user_answer)
        .replace("{{max_points}}", str(max_points))
    )
    return [
        {"role": "system", "content": "Olet täsmällinen, tiukka arvioija. Pisteytä vain RUBRICin mukaan ja palauta JSON."},
        {"role": "user", "content": user_prompt},
    ]

def ensure_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
        raise

def pretty_print_result(result: Dict[str, Any], max_points: int):
    fp = result.get("final_points", result.get("total_points", 0))
    mp = result.get("max_points", max_points)
    console.rule("[bold green]Tulos[/bold green]")
    console.print(f"[bold]Pisteet:[/bold] {fp}/{mp}")
    console.print(f"[bold]Palaute:[/bold] {result.get('short_feedback','(ei palautetta)')}\n")

    if "criteria" in result:
        t = Table(title="Kriteerit")
        t.add_column("ID", style="cyan")
        t.add_column("Täyttyi", style="green")
        t.add_column("Pisteet", justify="right")
        t.add_column("Perustelu", overflow="fold")
        for c in result["criteria"]:
            met = "✅" if c.get("met") else "❌"
            t.add_row(c.get("id","-"), met, str(c.get("points",0)), c.get("explanation",""))
        console.print(t)

    if result.get("penalties_applied"):
        t2 = Table(title="Vähennykset")
        t2.add_column("ID", style="red")
        t2.add_column("Vähennys", justify="right")
        t2.add_column("Perustelu", overflow="fold")
        for p in result["penalties_applied"]:
            t2.add_row(p.get("id","-"), str(p.get("points",0)), p.get("explanation",""))
        console.print(t2)

def save_result(result_dir: str, item_id: str, user_answer: str, result_json: Dict[str, Any]):
    Path(result_dir).mkdir(parents=True, exist_ok=True)
    out = {
        "item_id": item_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "answer": user_answer,
        "result": result_json,
    }
    outpath = Path(result_dir) / f"{item_id}-{uuid.uuid4().hex}.json"
    outpath.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[dim]Tallennettu: {outpath}[/dim]")

# ---------- MAIN ----------

def main():
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Aseta OPENAI_API_KEY ympäristömuuttuja.[/red]")
        sys.exit(1)

    items = load_items("items.jsonl")
    template = load_prompt_template("prompt_template.txt")

    item = items[0]  # ota eka kysymys
    console.rule("[bold]Harjoituskysymys[/bold]")
    console.print(f"[bold]{item['title']}[/bold] ({item['year']} {item['exam']} {item['section']})")
    console.print(item["question_text"])

    console.print("\nKirjoita vastauksesi (lopeta: CTRL+D / CTRL+Z):")
    user_answer = sys.stdin.read().strip()
    if not user_answer:
        console.print("[red]Tyhjä vastaus[/red]")
        sys.exit(0)

    messages = build_messages(
        template,
        question_text=item["question_text"],
        rubric=item["rubric"],
        user_answer=user_answer,
        max_points=item.get("max_points", 50),
    )

    client = OpenAI()
    resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
    raw = resp.choices[0].message.content.strip()
    result = ensure_json(raw)

    pretty_print_result(result, item.get("max_points", 50))
    save_result("results", item["id"], user_answer, result)

if __name__ == "__main__":
    main()
