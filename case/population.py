"""case/ pilot, step 0: rebuild the disputed clitic population + a control group.

Run from skel/ (`cd skel && uv run ../case/population.py ../case/population.json`) so
`import skel as driver` resolves to the Layer-5 build driver. No LLM calls; writes the JSON
pilot.py consumes.

Buckets (case/PLAN.md, *How to rebuild the disputed population*):
  parked   role_mismatch, given `obl:*` / derived `obj`|`subj`, argument has no `case`
           child, argument POS is pronoun, predicate has no second `obj` child      (~67)
  mirror   given `obj`|`subj` / derived `obl:*`, argument's dep deprel is `iobj`     (~28)
  control  clitic arguments where given and derived agree on the role — same word
           forms, same terzina-shaped context, sampled corpus-wide to ~the same size
"""

import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")
import skel as driver  # noqa: E402
from dante_corpus import api, dep, skel  # noqa: E402
from dante_corpus.tokenizer import has_alpha, tokenize  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "population.json")

CLITICS = {"mi", "ti", "si", "ci", "vi", "ne", "lo", "la", "li", "le", "gli",
           "m'", "t'", "s'", "c'", "v'", "n'", "l'"}
OBL_RE = re.compile(r"obl(:.+)?$")

orig = skel._classify_divergence
captured: list[tuple] = []


def wrapper(given, derived, dep_index_by_pos=None, morph_pos_by_position=None):
    vs = orig(given, derived, dep_index_by_pos, morph_pos_by_position)
    captured.append((given, derived, dep_index_by_pos, morph_pos_by_position, vs))
    return vs


skel._classify_divergence = wrapper
driver.skel._classify_divergence = wrapper


def alpha_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if has_alpha(t)]


def main() -> int:
    parked, mirror, control = [], [], []
    rng = random.Random(20260729)

    for canticle in api.canticles():
        for number in api.cantos(canticle):
            data = skel.load_skel(canticle, number)
            morph_rows = driver._morph_rows(canticle, number)
            np_rows = driver._np_rows(canticle, number)
            dep_rows = driver._dep_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {ln.no: ln.text for ln in lines}
            words = {ln.no: alpha_tokens(ln.text) for ln in lines}
            nos = [ln.no for ln in lines]
            texts = [ln.text for ln in lines]

            for unit in dep.sentence_groups(nos, texts, dep.MAX_UNIT_LINES):
                if any(no not in data for no in unit):
                    continue
                captured.clear()
                driver._classify_violations(
                    unit, [text_by_no[no] for no in unit],
                    {no: list(data[no]) for no in unit}, morph_rows, np_rows, dep_rows)
                if not captured:
                    continue
                given, derived, dep_index, morph_pos, vs = captured[-1]

                def word_at(pos):
                    ws = words.get(pos[0], [])
                    return ws[pos[1] - 1] if 1 <= pos[1] <= len(ws) else ""

                def record(bucket, pred, arg, given_role, derived_role):
                    dep_row = (dep_index or {}).get(arg)
                    return {
                        "bucket": bucket,
                        "canticle": canticle, "canto": number,
                        "unit": list(unit),
                        "texts": [text_by_no[no] for no in unit],
                        "line": arg[0], "token": arg[1], "word": word_at(arg),
                        "pred_line": pred[0], "pred_token": pred[1],
                        "pred_word": word_at(pred),
                        "given_role": given_role, "derived_role": derived_role,
                        "dep_deprel": dep_row.deprel if dep_row else "",
                        "morph_pos": (morph_pos or {}).get(arg, ""),
                    }

                # --- the two disputed buckets, from the violations themselves ---
                for v in vs:
                    if not v.detail.startswith("role_mismatch"):
                        continue
                    g, d, arg, pred = v.given_role, v.role, v.arg, v.predicate
                    if arg is None or pred is None:
                        continue
                    pos_tag = (morph_pos or {}).get(arg, "").lower()
                    if OBL_RE.fullmatch(g or "") and d in ("obj", "subj"):
                        has_case_child = any(
                            r.deprel == "case" and (r.head_line, r.head_token) == arg
                            for r in (dep_index or {}).values())
                        second_obj = sum(
                            1 for r in (dep_index or {}).values()
                            if r.deprel == "obj" and (r.head_line, r.head_token) == pred
                            and (r.line, r.token) != arg)
                        if (not has_case_child and "pronoun" in pos_tag and not second_obj):
                            parked.append(record("parked", pred, arg, g, d))
                    elif g in ("obj", "subj") and OBL_RE.fullmatch(d or ""):
                        dep_row = (dep_index or {}).get(arg)
                        if dep_row is not None and dep_row.deprel == "iobj":
                            mirror.append(record("mirror", pred, arg, g, d))

                # --- control: clitic args where the two reads already agree ---
                disputed_args = {v.arg for v in vs if v.arg is not None}
                given_by_pred, derived_by_pred = {}, {}
                for rows in given.values():
                    for r in rows:
                        if r.token > 0 and r.role and (r.arg_line, r.arg_token) != (r.line, r.token):
                            given_by_pred.setdefault((r.line, r.token), {})[
                                (r.arg_line, r.arg_token)] = skel._canonicalize_role(r.role)
                for rows in derived.values():
                    for r in rows:
                        if r.role and (r.arg_line, r.arg_token) != (r.line, r.token):
                            derived_by_pred.setdefault((r.line, r.token), {})[
                                (r.arg_line, r.arg_token)] = skel._canonicalize_role(r.role)
                for pred, gargs in given_by_pred.items():
                    dargs = derived_by_pred.get(pred, {})
                    for arg, grole in gargs.items():
                        if arg in disputed_args or dargs.get(arg) != grole:
                            continue
                        if word_at(arg).lower() not in CLITICS:
                            continue
                        if "pronoun" not in (morph_pos or {}).get(arg, "").lower():
                            continue
                        control.append(record("control", pred, arg, grole, grole))

    # Dedupe (a position can be flagged under more than one predicate) and sample the control.
    def dedupe(items):
        seen, out = set(), []
        for it in items:
            key = (it["canticle"], it["canto"], it["line"], it["token"],
                   it["pred_line"], it["pred_token"])
            if key not in seen:
                seen.add(key)
                out.append(it)
        return out

    parked, mirror, control = dedupe(parked), dedupe(mirror), dedupe(control)
    n_disputed = len(parked) + len(mirror)
    rng.shuffle(control)
    control = control[:n_disputed]

    print(f"parked  {len(parked)}")
    print(f"mirror  {len(mirror)}")
    print(f"control {len(control)} (sampled to the disputed size {n_disputed})")
    from collections import Counter
    for name, items in (("parked", parked), ("mirror", mirror), ("control", control)):
        print(f"  {name} word forms: "
              f"{Counter(i['word'].lower() for i in items).most_common(8)}")

    OUT.write_text(json.dumps(parked + mirror + control, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"wrote {OUT} ({n_disputed + len(control)} positions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
