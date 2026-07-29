"""case/ pilot, step 2: read results.{A,B,C}.jsonl and answer the kill gate.

    uv run case/report.py

Reports, per bucket (parked / mirror / control):
  * self-agreement: how often the three presentation variants give the same case
  * the answer vocabulary actually produced (this is what step 2 would freeze, per
    case/PLAN.md — the vocabulary comes from the pilot's output, not from a grammar)
  * direction: where the model's majority answer sides, `dep` (Layer 4) or `skel` (the
    Layer-5 LLM read), on the disputed positions

Stop rule (case/PLAN.md, step 1): if disputed self-agreement is not clearly higher than
control self-agreement, the column is measuring noise and the plan ends.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

# Answer -> the dep deprel that reading implies. Built from the pilot's own vocabulary; any
# answer not listed is reported as unmapped rather than silently bucketed.
CASE_TO_DEPREL = {
    "accusative": "obj",
    "dative": "iobj",
    "nominative": "subj",
    "genitive": "other",
    "ablative": "other",
    "oblique": "other",
    "locative": "other",
    "partitive": "other",
    "reflexive": "other",
    # The prompt asks for English, but the model answers in Italian often enough to map here.
    "accusativo": "obj",
    "dativo": "iobj",
    "nominativo": "subj",
    "genitivo": "other",
    "ablativo": "other",
    "obliquo": "other",
    "locativo": "other",
    "partitivo": "other",
    "riflessivo": "other",
}


def main() -> int:
    ap = argparse.ArgumentParser(prog="report.py")
    ap.add_argument("--population", default=str(Path(__file__).with_name("population.json")),
                    help="default: population.json next to this script")
    ap.add_argument("--dir", default=None, help="directory holding results.*.jsonl")
    args = ap.parse_args()

    pop_path = Path(args.population)
    base = Path(args.dir) if args.dir else pop_path.parent
    pop = {}
    for item in json.loads(pop_path.read_text(encoding="utf-8")):
        item["id"] = (f"{item['canticle']}-{item['canto']}-{item['line']}.{item['token']}"
                      f"-p{item['pred_line']}.{item['pred_token']}")
        pop[item["id"]] = item

    answers: dict[str, dict[str, str]] = defaultdict(dict)
    runs = []
    for run in "ABC":
        path = base / f"results.{run}.jsonl"
        if not path.exists():
            print(f"missing {path} — run pilot.py --run {run} first")
            continue
        runs.append(run)
        for row in path.read_text(encoding="utf-8").splitlines():
            if row.strip():
                rec = json.loads(row)
                answers[rec["id"]][run] = rec["answer"]

    print(f"runs present: {', '.join(runs) or 'none'}\n")

    vocab = Counter(a for per in answers.values() for a in per.values())
    print("answer vocabulary (all runs):")
    for value, n in vocab.most_common():
        mark = "" if value in CASE_TO_DEPREL else "   <- unmapped"
        print(f"  {value:<16} {n}{mark}")
    print()

    stats: dict[str, Counter] = defaultdict(Counter)
    for pid, per in answers.items():
        item = pop.get(pid)
        if item is None or len(per) < len(runs) or not runs:
            continue
        bucket = item["bucket"]
        values = list(per.values())
        top, n_top = Counter(values).most_common(1)[0]
        stats[bucket]["n"] += 1
        stats[bucket]["unanimous" if n_top == len(values)
                      else "majority" if n_top >= 2 else "split"] += 1
        if bucket == "control":
            continue
        implied = CASE_TO_DEPREL.get(top, "other")
        dep_side = "obj" if item["derived_role"] in ("obj", "subj") else "iobj"
        # `given_role` is the Layer-5 LLM read, `derived_role` the one dep produces.
        skel_side = "obj" if item["given_role"] in ("obj", "subj") else "iobj"
        if implied == dep_side:
            stats[bucket]["sides_with_dep"] += 1
        elif implied == skel_side:
            stats[bucket]["sides_with_skel"] += 1
        else:
            stats[bucket]["sides_with_neither"] += 1

    print(f"{'bucket':<10} {'n':>4} {'unanim':>8} {'major':>8} {'split':>7}"
          f" {'->dep':>7} {'->skel':>7} {'->none':>7}")
    for bucket in ("parked", "mirror", "control"):
        s = stats.get(bucket)
        if not s:
            continue
        n = s["n"] or 1
        print(f"{bucket:<10} {s['n']:>4} {s['unanimous']:>7} ({s['unanimous']/n:.0%})"
              f" {s['majority']:>7} {s['split']:>7}"
              f" {s['sides_with_dep']:>7} {s['sides_with_skel']:>7}"
              f" {s['sides_with_neither']:>7}")

    disputed_n = stats["parked"]["n"] + stats["mirror"]["n"]
    disputed_u = stats["parked"]["unanimous"] + stats["mirror"]["unanimous"]
    ctrl_n, ctrl_u = stats["control"]["n"], stats["control"]["unanimous"]
    if disputed_n and ctrl_n:
        print(f"\nkill gate: disputed unanimity {disputed_u}/{disputed_n} "
              f"({disputed_u/disputed_n:.0%}) vs control {ctrl_u}/{ctrl_n} "
              f"({ctrl_u/ctrl_n:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
