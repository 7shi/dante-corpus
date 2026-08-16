"""Per-position read tool for the Layer-5 audit series — all five layers side by side.

The audit discipline (see PLAN.md's *The Read Series*) is to read every soft violation in a
5-canto batch position by position, with Layers 1-4 and both Layer-5 readings visible at once.
`--check` names a position; this prints everything needed to decide what is wrong with it.

    uv run read.py <canticle> <canto> <start> [end]

Prints, for the whole parse unit(s) containing the given line range:

  * the source line, and per token: Layer-2 lemma/POS/features/note, the `case` annex value,
    and the Layer-4 deprel with its head (`nsubj<-10.4`);
  * the Layer-3 NP spans, with their heads;
  * the **artifact** rows (what the LLM read) and the **derived** rows (what `derive_unit`
    computes) for the same unit, which is exactly the pair `--check` diffs.

Lines inside the requested range are marked `===*`; surrounding lines of the same parse unit are
printed as context because the derivation is computed per unit, not per line.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dante_corpus import api, dep as _dep, skel as _skel


def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(2)
    canticle, canto = sys.argv[1], int(sys.argv[2])
    start = int(sys.argv[3])
    end = int(sys.argv[4]) if len(sys.argv) > 4 else start

    c = api.canto(canticle, canto)
    morph, dep, nps, case = c.morph(), c.dep(), c.np(), c.case()
    lines = {ln.no: ln for ln in c.lines()}

    nos_all = sorted(lines)
    texts_all = [lines[n].text for n in nos_all]
    units = _dep.sentence_groups(nos_all, texts_all, _dep.MAX_UNIT_LINES)
    target = [u for u in units if any(start <= n <= end for n in u)]
    if not target:
        raise SystemExit(f"no parse unit covers {canticle} {canto}:{start}-{end}")
    lo, hi = min(min(u) for u in target), max(max(u) for u in target)

    case_by_line = {no: {r.token: r for r in rows} for no, rows in (case or {}).items()}

    for no in range(lo, hi + 1):
        ln = lines.get(no)
        if ln is None:
            continue
        mark = "*" if start <= no <= end else " "
        print(f"\n==={mark} {canto}:{no}  {ln.text}")
        drows = {r.token: r for r in dep.get(no, ())}
        crows = case_by_line.get(no, {})
        for i, m in enumerate(morph.get(no, ()), 1):
            d = drows.get(i)
            cs = crows.get(i)
            attach = f"{d.deprel}<-{d.head_line}.{d.head_token}" if d else "-"
            cstr = f" case={cs.case}" if cs is not None and cs.case else ""
            feats = " ".join(x for x in (m.gender, m.number, m.person, m.tense, m.mood) if x)
            print(f"  {no}.{i:<3}{m.word:<13}{m.lemma:<13}{m.pos:<20}{feats:<28}"
                  f"{attach}{cstr} {m.note}")
        for sp in nps:
            if sp.line == no:
                print(f"   NP [{sp.start}-{sp.end}] head={sp.head} '{sp.text}'")

    print("\n--- skel artifact (the LLM's independent reading) ---")
    for t in c.skel():
        if lo <= t.line <= hi:
            args = ", ".join(f"{a.role}=({a.line},{a.token})" for a in t.args)
            print(f"  {t.line}.{t.token} {t.word}: {args}")

    print("\n--- derived (derive_unit, the checker) ---")
    for unit in target:
        derived = _skel.derive_unit(unit, dep, morph, case)
        print(f"  unit lines {min(unit)}-{max(unit)}")
        for no in sorted(derived):
            for r in derived[no]:
                print(f"    {r.line}.{r.token} {r.word}: {r.role}=({r.arg_line},{r.arg_token})")


if __name__ == "__main__":
    main()
