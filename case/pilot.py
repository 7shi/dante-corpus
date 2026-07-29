"""case/ pilot, step 1: the kill gate — does the model agree with itself on the disputed
clitics at a clearly higher rate than on undisputed ones?

One *run* = one presentation variant (A / B / C). Each run asks the model for the case of
every position in population.json once, in a fresh session, in shuffled order. Running the
three variants is what makes the three answers independent; they can be run in three shells
in parallel, exactly like `make -C skel fix`.

    uv run case/pilot.py --run A -m google:gemma-4-31b-it
    uv run case/pilot.py --run B -m google:gemma-4-31b-it
    uv run case/pilot.py --run C -m google:gemma-4-31b-it

Blind by construction: the prompt carries the terzina and the marked pronoun and nothing
else — no `dep/` row, no `skel/` row, no hint that a position is disputed, and disputed and
control positions are interleaved in one shuffled stream (see case/PLAN.md, *Independence*).

Resumable: answers are appended to results.<RUN>.jsonl as they arrive; a restart skips the
ids already present. The verdict the runs produce goes to case/CORRECTIONS.md.
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")
from dante_corpus.tokenizer import has_alpha, tokenize  # noqa: E402

SYSTEM_PROMPT = """\
You are a morphological analyzer for archaic Italian (Dante's Divine Comedy).
You are given one sentence from the poem with a single pronoun marked between ** and **.
Name the grammatical case that pronoun bears in that sentence.

Answer with ONE English word and nothing else — no explanation, no punctuation, no
restatement (e.g. accusative).
"""


def marked(text: str, token: int, left: str = "**", right: str = "**") -> str:
    """`text` with its `token`-th alpha token (1-based, Layer-1 numbering) wrapped."""
    out, seen = [], 0
    for tok in tokenize(text):
        if has_alpha(tok):
            seen += 1
            if seen == token:
                out.append(f"{left}{tok}{right}")
                continue
        out.append(tok)
    return "".join(out)


def prompt_for(item: dict, run: str) -> str:
    """The three presentation variants. They differ in how much context is shown and how the
    question is worded, so that agreement across runs is not a trivially correlated repeat."""
    unit, texts, line, token = item["unit"], item["texts"], item["line"], item["token"]
    idx = unit.index(line)
    shown = [t if no != line else marked(t, token) for no, t in zip(unit, texts)]

    if run == "A":
        body = "\n".join(f"{no} {t}" for no, t in zip(unit, shown))
        return (f"{body}\n\nWhich grammatical case does the marked pronoun bear?")
    if run == "B":
        window = shown[max(0, idx - 1): idx + 1]
        body = "\n".join(window)
        return (f"{body}\n\nCase of the marked pronoun?")
    if run == "C":
        body = " ".join(t.strip() for t in shown)
        return (f"{body}\n\nIn this passage the pronoun **{item['word']}** is marked. "
                f"What case is it?")
    raise ValueError(run)


def main() -> int:
    ap = argparse.ArgumentParser(prog="pilot.py")
    ap.add_argument("--run", required=True, choices=["A", "B", "C"])
    ap.add_argument("-m", "--model", required=True, help="e.g. google:gemma-4-31b-it")
    ap.add_argument("--population", default=str(Path(__file__).with_name("population.json")),
                    help="default: population.json next to this script")
    ap.add_argument("--out", help="default results.<RUN>.jsonl next to --population")
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="print the first few prompts and exit, no model call")
    ap.add_argument("--limit", type=int, help="stop after N positions (smoke test)")
    args = ap.parse_args()

    pop_path = Path(args.population)
    items = json.loads(pop_path.read_text(encoding="utf-8"))
    for i, item in enumerate(items):
        item["id"] = f"{item['canticle']}-{item['canto']}-{item['line']}.{item['token']}-p{item['pred_line']}.{item['pred_token']}"
    # One shuffle per run: the disputed and control positions must not arrive in blocks.
    random.Random({"A": 1, "B": 2, "C": 3}[args.run]).shuffle(items)
    if args.limit:
        items = items[: args.limit]

    if args.dry_run:
        for item in items[:3]:
            print(f"--- {item['id']} [{item['bucket']}] ---")
            print(prompt_for(item, args.run))
            print()
        return 0

    out_path = Path(args.out) if args.out else pop_path.with_name(f"results.{args.run}.jsonl")
    log_path = out_path.with_suffix(".log")
    done = set()
    if out_path.exists():
        for row in out_path.read_text(encoding="utf-8").splitlines():
            if row.strip():
                done.add(json.loads(row)["id"])
        print(f"resume: {len(done)} answered, {len(items) - len(done)} left")

    from llm7shi import Client

    with log_path.open("a", encoding="utf-8") as log, \
            out_path.open("a", encoding="utf-8") as out:
        for i, item in enumerate(items, 1):
            if item["id"] in done:
                continue
            prompt = prompt_for(item, args.run)
            client = Client(model=args.model, file=log, show_params=False)
            client.set_system_prompt(SYSTEM_PROMPT)
            raw = client(prompt).text.strip()
            answer = raw.split()[0].strip(".,;:'\"").lower() if raw.split() else ""
            out.write(json.dumps({"id": item["id"], "bucket": item["bucket"],
                                  "run": args.run, "word": item["word"],
                                  "answer": answer, "raw": raw}, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{args.run}] {i}/{len(items)} {item['id']:<32} {answer}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
