"""Build driver for Layer 5 (predicate-argument skeleton) — a per-step generation script.

Like `dep/dep.py` (Layer 4), the script that *generates* an artifact lives in its own step
directory (here `skel/`), while parsing, resolution, validation, and I/O stay in the shared
package (`dante_corpus/skel.py`, consumed by the runtime API). The runtime API never calls a
model.

Unlike Layers 2-4, this layer's checker is *not* the LLM's own output reformatted: `skel.
derive_unit` computes the same predicate-argument structure mechanically from the frozen
Layers 2-4, and the LLM proposes its own, independent reading of the same parse unit — it is
deliberately **not shown** the Layer-4 parse, only the numbered source lines, a POS-annotated
token list (Layer 2), and the Layer-3 noun-phrase list as citation anchors. A divergence
between the two is triage material (see `dante_corpus/skel.py`'s module docstring and
PLAN.md), not necessarily an LLM mistake.

Parse units are the same sentence groups as Layer 4 (`dep.sentence_groups`, reused verbatim) —
staying unit-aligned with Layer 4 is what makes the divergence check meaningful.

Generation resumes from its own output: each parse unit's rows are written back to the TSV as
soon as they validate (zero hard violations), so an interrupted run continues where it stopped.

    uv run skel.py inferno -m ollama:gpt-oss        # all of Inferno (resumes)
    uv run skel.py inferno -c 1 -m ollama:gpt-oss   # just canto 1
    uv run skel.py inferno --force -m ...           # rebuild from scratch
    uv run skel.py inferno --check                  # code-only, no model
    uv run skel.py inferno -n                        # dry run: show pending units, no LLM
    uv run skel.py inferno --clean                   # remove parse units with hard violations
    uv run skel.py inferno --fix -m ollama:gpt-oss   # regenerate units with soft violations

`--check` validates committed artifacts against the deterministic derivation (`skel.
derive_unit`) and reports soft violations (role outside the frozen vocabulary, a nominal-role
argument heading no NP/pronoun/predicate, and — the central check — every divergence from
the derivation: `missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`).
"""

import argparse
import sys
from pathlib import Path

from dante_corpus import api, dep, morph, np, skel
from dante_corpus.tokenizer import has_alpha, tokenize
from llm7shi.statusline import StatusLine

SYSTEM_PROMPT = """\
You are a predicate-argument skeleton extractor for archaic Italian (Dante's Divine Comedy).
For the given sentence you receive numbered source lines, a numbered token list, and a list of
noun phrases. Output ONLY a Markdown table with one row per (predicate, argument) pair:
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |

Rules:
* A predicate is any token that heads a clause: a finite or non-finite verb, or a copular
  adjective/noun predicate (the thing an "è"/"era"/etc. links to).
* Role is one of: subj, obj, iobj, attr, xcomp, ccomp, obl:<preposition lemma> (e.g. obl:in,
  obl:per, obl:di); use bare obl only if there truly is no preposition to name.
* Pred Line / Pred Token / Pred Word are copied from the token list.
* Arg Line / Arg Token cite another listed token — prefer a noun phrase's head token when the
  argument is a noun phrase (use the Noun phrases list to find it); Arg Word is that token's
  word, copied verbatim, so the citation can be checked.
* A pro-drop (missing) subject of a finite verb is still reported as its own row: Role subj,
  Arg Line 0, Arg Token 0, Arg Word ∅.
* A predicate with no arguments at all gets exactly one row: Role -, Arg Line 0, Arg Token 0,
  Arg Word -.
* A relative pronoun (che, cui, qual, ...) that is a clause's subject/object/oblique is cited
  as the argument itself — never resolve it to its antecedent.
* A verb token that already contains a fused enclitic pronoun (e.g. venendomi = venire + mi)
  encodes that pronoun's role internally; do not add a separate row citing the pronoun or the
  predicate's own token position as its argument — there is no separate token for it.
* Arguments may be on a different line than the predicate — enjambment is common in this text.
* Output only the table, with no commentary before or after it.

Example input:
Give the predicate-argument skeleton for this sentence:

1 Nel mezzo del cammin di nostra vita
2 mi ritrovai per una selva oscura,
3 ché la diritta via era smarrita.

Tokens (Line.Token Word (POS)):
1.1 Nel (preposition+article)
1.2 mezzo (noun)
1.3 del (preposition+article)
1.4 cammin (noun)
1.5 di (preposition)
1.6 nostra (adjective)
1.7 vita (noun)
2.1 mi (pronoun)
2.2 ritrovai (verb)
2.3 per (preposition)
2.4 una (article)
2.5 selva (noun)
2.6 oscura (adjective)
3.1 ché (conjunction)
3.2 la (article)
3.3 diritta (adjective)
3.4 via (noun)
3.5 era (verb)
3.6 smarrita (verb (past participle))

Noun phrases (Line.Head [text]):
1.2 [mezzo del cammin di nostra vita]
1.4 [cammin di nostra vita]
1.7 [nostra vita]
2.5 [una selva oscura]
3.4 [la diritta via]

Example output:
| Pred Line | Pred Token | Pred Word | Role | Arg Line | Arg Token | Arg Word |
|---|---|---|---|---|---|---|
| 2 | 2 | ritrovai | subj | 0 | 0 | ∅ |
| 2 | 2 | ritrovai | obl:in | 1 | 2 | mezzo |
| 2 | 2 | ritrovai | obl:per | 2 | 5 | selva |
| 3 | 6 | smarrita | subj | 3 | 4 | via |
"""

RETRIES = 2


def _alpha_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if has_alpha(t)]


def _units(lines: tuple[api.Line, ...], size: int) -> list[tuple[api.Line, ...]]:
    """Group a canto's lines into skeleton parse units (same sentence groups as Layer 4)."""
    nos = [line.no for line in lines]
    texts = [line.text for line in lines]
    by_no = {line.no: line for line in lines}
    return [tuple(by_no[no] for no in group) for group in dep.sentence_groups(nos, texts, size)]


def _load_committed(canticle: str, number: int) -> list[tuple[int, list[skel.SkelRow]]]:
    """Already-frozen rows for a canto, ordered by line number — the checkpoint to resume from."""
    if not skel.has_skel(canticle, number):
        return []
    data = skel.load_skel(canticle, number)
    return [(no, list(rows)) for no, rows in sorted(data.items())]


def _morph_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-2 rows per line, or {} when absent."""
    if not morph.has_morph(canticle, number):
        return {}
    return {no: list(rows) for no, rows in morph.load_morph(canticle, number).items()}


def _np_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-3 rows per line, or {} when absent."""
    if not np.has_np(canticle, number):
        return {}
    return {no: list(rows) for no, rows in np.load_np(canticle, number).items()}


def _dep_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-4 rows per line, or {} when absent."""
    if not dep.has_dep(canticle, number):
        return {}
    return {no: list(rows) for no, rows in dep.load_dep(canticle, number).items()}


def _merge_tables(text: str) -> str:
    """Merge multiple Markdown pipe-tables into one (shared recovery pattern; see PLAN.md).

    Handles two failure modes:
    - Blank line between tables: gap + repeated header + separator are removed.
    - No blank line: repeated header appears inline within the body and is removed in place.
    In both cases trailing blank lines before the repeated header are also stripped.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    first_header: list[str] | None = None

    i = 0
    while i < len(lines):
        stripped = lines[i].rstrip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if (first_header is not None
                    and cells == first_header
                    and i + 1 < len(lines)
                    and lines[i + 1].rstrip().startswith("|")
                    and "---" in lines[i + 1]):
                while out and out[-1].rstrip() == "":
                    out.pop()
                i += 2
                continue
            if (first_header is None
                    and i + 1 < len(lines)
                    and lines[i + 1].rstrip().startswith("|")
                    and "---" in lines[i + 1]):
                first_header = cells
            out.append(lines[i])
        else:
            out.append(lines[i])
        i += 1

    return "".join(out)


def _prompt(
    nos: list[int], texts: list[str], morph_rows: dict[int, list], np_rows: dict[int, list],
) -> str:
    lines_block = "\n".join(f"{no} {text}" for no, text in zip(nos, texts))
    token_lines: list[str] = []
    for no, text in zip(nos, texts):
        tokens = _alpha_tokens(text)
        rows = morph_rows.get(no)
        for i, tok in enumerate(tokens, start=1):
            pos = f" ({rows[i - 1].pos})" if rows and i - 1 < len(rows) else ""
            token_lines.append(f"{no}.{i} {tok}{pos}")
    np_lines: list[str] = []
    for no in nos:
        for span in sorted(np_rows.get(no, ()), key=lambda s: (s.start, -s.end)):
            np_lines.append(f"{no}.{span.head} [{span.text}]")
    parts = [
        "Give the predicate-argument skeleton for this sentence:\n\n" + lines_block,
        "Tokens (Line.Token Word (POS)):\n" + "\n".join(token_lines),
    ]
    if np_lines:
        parts.append("Noun phrases (Line.Head [text]):\n" + "\n".join(np_lines))
    return "\n\n".join(parts)


def _continue_if_missing(
    client, nos: list[int], texts: list[str], table_text: str, ui: StatusLine,
    derived: dict[int, list[skel.SkelRow]],
) -> str:
    """If any derived predicate got no row (likely truncation), ask the client to continue."""
    try:
        partial, _ = skel.resolve_chunk(nos, texts, table_text)
    except ValueError:
        return table_text
    have = {(row.line, row.token) for rows in partial.values() for row in rows if row.token > 0}
    missing: list[str] = []
    for no in nos:
        tokens = _alpha_tokens(texts[nos.index(no)])
        for row in derived.get(no, []):
            if (row.line, row.token) not in have:
                word = tokens[row.token - 1] if 1 <= row.token <= len(tokens) else row.word
                missing.append(f"{no}.{row.token} {word}")
    missing = sorted(set(missing))
    if not missing:
        return table_text
    cont_prompt = (
        "The table was truncated. Please continue with rows for these predicates:\n\n"
        + "\n".join(missing)
    )
    cont_text = client(cont_prompt).text
    ui.stream.end()
    return _merge_tables(table_text + "\n" + cont_text)


def _hard_violations(
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    mismatches: list[str], morph_rows: dict[int, list] | None,
    np_rows: dict[int, list] | None, dep_rows: dict[int, list] | None,
) -> list[str]:
    hard = list(mismatches)
    for v in skel.validate_unit(nos, texts, rows_by_line, morph_rows, np_rows, dep_rows):
        if v.kind != "tag":
            hard.append(f"{v.line}:[{v.kind}] {v.detail}")
    return hard


def _try_parse(
    nos: list[int], texts: list[str], model: str, ui: StatusLine, label: str,
    log_path: Path | None = None, morph_rows: dict[int, list] | None = None,
    np_rows: dict[int, list] | None = None, dep_rows: dict[int, list] | None = None,
) -> dict[int, list[skel.SkelRow]] | None:
    """Call LLM and resolve; return rows-by-line on success, None after all retries fail."""
    from llm7shi import Client

    derived = (
        skel.derive_unit(nos, dep_rows, morph_rows) if dep_rows is not None and morph_rows is not None
        else {}
    )
    prompt = _prompt(nos, texts, morph_rows or {}, np_rows or {})
    for attempt in range(RETRIES + 1):
        client = Client(model=model, file=ui.stream, show_params=False)
        client.set_system_prompt(SYSTEM_PROMPT)
        table_text = client(prompt).text
        ui.stream.end()
        table_text = _merge_tables(table_text)
        table_text = _continue_if_missing(client, nos, texts, table_text, ui, derived)
        try:
            rows_by_line, mismatches = skel.resolve_chunk(nos, texts, table_text)
            hard = _hard_violations(nos, texts, rows_by_line, mismatches, morph_rows, np_rows, dep_rows)
            if hard:
                raise ValueError("; ".join(hard))
            return rows_by_line
        except ValueError as exc:
            msg = (f"  {label} lines {nos[0]}-{nos[-1]}: {exc} "
                   f"(attempt {attempt + 1}/{RETRIES + 1})")
            ui.stream.error(msg)
            if log_path:
                with log_path.open("a", encoding="utf-8") as f:
                    f.write(f"=== {label} lines {nos[0]}-{nos[-1]} "
                            f"attempt {attempt + 1}/{RETRIES + 1} ===\n")
                    f.write(f"Error: {exc}\n")
                    f.write("--- response ---\n")
                    f.write(table_text.strip())
                    f.write("\n\n")
    return None


def _classify_violations(
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    morph_rows: dict[int, list] | None, np_rows: dict[int, list] | None,
    dep_rows: dict[int, list] | None,
) -> tuple[list[morph.Violation], list[morph.Violation]]:
    """Split validate_unit results into (hard, soft). tag -> soft; rest -> hard."""
    hard, soft = [], []
    for v in skel.validate_unit(nos, texts, rows_by_line, morph_rows, np_rows, dep_rows):
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def _build_canto(
    canticle: str, number: int, n_cantos: int, model: str, size: int,
    force: bool, dry_run: bool, ui: StatusLine, log_path: Path | None = None,
) -> bool:
    canto = api.canto(canticle, number)
    lines = canto.lines()
    out = [] if force else _load_committed(canticle, number)
    done = {no for no, _ in out}
    morph_rows = _morph_rows(canticle, number)
    np_rows = _np_rows(canticle, number)
    dep_rows = _dep_rows(canticle, number)

    units = _units(lines, size)
    pending = [unit for unit in units if any(line.no not in done for line in unit)]
    label = f"{canticle} {number}/{n_cantos}"
    if not pending:
        ui.log(f"[dim]Skip (complete): skel/{canticle}/{number:02d}.tsv[/dim]")
        return True
    if done:
        ui.log(f"Resume: skel/{canticle}/{number:02d}.tsv "
               f"({len(done)} line(s) done, {len(pending)} unit(s) left)")

    if dry_run:
        for unit in pending:
            nos = [line.no for line in unit]
            ui.log(f"  [dry-run] skel/{canticle}/{number:02d}.tsv "
                   f"lines {nos[0]}-{nos[-1]} ({len(nos)} line(s))")
        return True

    with ui.progress(len(lines), start=pending[0][0].no, label=label) as prog:
        for unit in pending:
            nos = [line.no for line in unit]
            prog.update(nos[0])
            texts = [line.text for line in unit]
            label = f"{canticle} {number}"
            rows_by_line = _try_parse(
                nos, texts, model, ui, label, log_path, morph_rows, np_rows, dep_rows,
            )
            if rows_by_line is None:
                # No per-line fallback: a lone line cannot host cross-line arguments, so a
                # parse unit is the smallest unit worth retrying.
                ui.stream.error(f"  {label}: giving up at lines {nos[0]}-{nos[-1]}; "
                                f"earlier units saved for resume")
                return False
            unit_nos = set(nos)
            out = [(no, rows) for no, rows in out if no not in unit_nos]
            out.extend((no, rows_by_line.get(no, [])) for no in nos)
            out.sort(key=lambda item: item[0])
            skel.write_skel(canticle, number, out)
    ui.log(f"Wrote: skel/{canticle}/{number:02d}.tsv")
    return True


def build(canticles: list[str], model: str, size: int, force: bool, dry_run: bool,
          only: int | None, log_path: Path | None = None) -> int:
    if log_path:
        log_path.write_text("", encoding="utf-8")
    ui = StatusLine()
    for canticle in canticles:
        all_numbers = list(api.cantos(canticle))
        n_cantos = len(all_numbers)
        numbers = [only] if only else all_numbers
        for number in numbers:
            _build_canto(canticle, number, n_cantos, model, size, force, dry_run, ui, log_path)
    return 0


def check(canticles: list[str], only: int | None) -> int:
    hard = 0
    soft = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not skel.has_skel(canticle, number):
                print(f"Missing: skel/{canticle}/{number:02d}.tsv", file=sys.stderr)
                hard += 1
                continue
            data = skel.load_skel(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            np_rows = _np_rows(canticle, number)
            dep_rows = _dep_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {line.no: line.text for line in lines}
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            missing = [no for no in nos_all if no not in data]
            hard += len(missing)
            for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                if any(no in missing for no in unit):
                    continue  # already counted above; don't double-report as a count violation
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data[no]) for no in unit}
                hard_vs, soft_vs = _classify_violations(
                    unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows,
                )
                for v in hard_vs:
                    print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}", file=sys.stderr)
                    hard += 1
                for v in soft_vs:
                    soft += 1
                    print(f"{canticle} {number}:{v.line} [{v.kind}] {v.detail}", file=sys.stderr)
            if missing:
                print(f"{canticle} {number}: missing lines {missing}", file=sys.stderr)
    print(f"check complete: {hard} hard, {soft} soft violation(s)")
    return 1 if hard else 0


def clean(canticles: list[str], size: int, only: int | None) -> int:
    removed = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not skel.has_skel(canticle, number):
                continue
            data = skel.load_skel(canticle, number)
            lines = api.canto(canticle, number).lines()
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            text_by_no = dict(zip(nos_all, texts_all))

            # Remove parse units with any hard violation (soft is reported, not cleaned).
            bad: set[int] = set()
            for unit in dep.sentence_groups(nos_all, texts_all, size):
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data.get(no, ())) for no in unit}
                hard_vs, _ = _classify_violations(unit, unit_texts, rows_by_line, None, None, None)
                if hard_vs:
                    bad.update(unit)
            has_data = bad & data.keys()
            if has_data:
                for no in bad:
                    data.pop(no, None)
                out = sorted(data.items())
                skel.write_skel(canticle, number, [(no, list(rows)) for no, rows in out])
                print(f"Cleaned skel/{canticle}/{number:02d}.tsv — removed lines {sorted(bad)}")
            removed += len(has_data)
    print(f"clean complete: {removed} line(s) removed")
    return 0


def _fix_canto(
    canticle: str, number: int, n_cantos: int, model: str, ui: StatusLine,
    log_path: Path | None = None,
) -> tuple[int, int]:
    """Fix one canto's flagged parse units under a progress bar; returns (fixed, attempted)."""
    data = skel.load_skel(canticle, number)
    morph_rows = _morph_rows(canticle, number)
    np_rows = _np_rows(canticle, number)
    dep_rows = _dep_rows(canticle, number)
    lines = api.canto(canticle, number).lines()
    text_by_no = {line.no: line.text for line in lines}
    nos_all = [line.no for line in lines]
    texts_all = [line.text for line in lines]
    out = dict(data)
    changed = False
    fixed = 0
    attempted = 0
    label = f"{canticle} {number}/{n_cantos}"
    units = dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES)
    with ui.progress(len(lines), label=label) as prog:
        for unit in units:
            prog.update(unit[0])
            if any(no not in out for no in unit):
                continue  # unit incomplete; leave it to `build`/resume
            unit_texts = [text_by_no[no] for no in unit]
            rows_by_line = {no: list(out[no]) for no in unit}
            _, soft_before = _classify_violations(
                unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows,
            )
            if not soft_before:
                continue
            attempted += 1
            new_rows = _try_parse(
                unit, unit_texts, model, ui, label, log_path, morph_rows, np_rows, dep_rows,
            )
            if new_rows is None:
                continue
            _, soft_after = _classify_violations(
                unit, unit_texts, new_rows, morph_rows, np_rows, dep_rows,
            )
            if len(soft_after) < len(soft_before):
                for no in unit:
                    out[no] = tuple(new_rows.get(no, []))
                fixed += 1
                changed = True
                ui.log(f"Fixed {canticle} {number}:{unit[0]}-{unit[-1]} — "
                       f"{len(soft_before)} -> {len(soft_after)} soft violation(s)")
            elif log_path:
                with log_path.open("a", encoding="utf-8") as f:
                    f.write(f"=== {label} lines {unit[0]}-{unit[-1]}: not improved "
                            f"({len(soft_before)} -> {len(soft_after)}) ===\n")
                    for v in soft_before:
                        f.write(f"before: {v.detail}\n")
                    for v in soft_after:
                        f.write(f"after:  {v.detail}\n")
                    f.write("\n")
    if changed:
        skel.write_skel(canticle, number, [(no, list(rows)) for no, rows in sorted(out.items())])
        ui.log(f"Wrote: skel/{canticle}/{number:02d}.tsv")
    return fixed, attempted


def fix(canticles: list[str], model: str, only: int | None, log_path: Path | None = None) -> int:
    """Re-run the model on parse units carrying soft violations, keeping only real improvements.

    Like Layer 4's `--fix`, a skeleton parse unit's rows can cite each other across its lines,
    so the smallest thing worth regenerating is the whole unit, not a single line (mirrors
    `build`'s no-per-line-fallback rule). Swaps in the regenerated rows only if the unit carries
    strictly fewer soft violations than before and no new hard ones — `_try_parse` already
    guarantees zero hard violations in whatever it returns, so the only check needed here is the
    soft-count improvement. A no-worse-off guarantee, not a promise every case clears.
    """
    if log_path:
        log_path.write_text("", encoding="utf-8")
    ui = StatusLine()
    fixed = 0
    attempted = 0
    for canticle in canticles:
        all_numbers = list(api.cantos(canticle))
        n_cantos = len(all_numbers)
        numbers = [only] if only else all_numbers
        for number in numbers:
            if not skel.has_skel(canticle, number):
                continue
            f, a = _fix_canto(canticle, number, n_cantos, model, ui, log_path)
            fixed += f
            attempted += a
    print(f"fix complete: {fixed}/{attempted} unit(s) improved")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="skel.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. ollama:gpt-oss (required unless --check)")
    parser.add_argument("--chunk", type=int, default=dep.MAX_UNIT_LINES,
                        help=f"max lines per parse unit (default {dep.MAX_UNIT_LINES})")
    parser.add_argument("-c", "--canto", type=int, help="limit to a single canto number")
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    parser.add_argument("--clean", action="store_true",
                        help="remove parse units with hard violations, then exit")
    parser.add_argument("--fix", action="store_true",
                        help="regenerate parse units carrying soft violations, keep only improvements")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="show pending parse units without calling the LLM")
    parser.add_argument("--log", nargs="?", const="skel.log", metavar="FILE",
                        help="append failed LLM responses to FILE (default: skel.log)")
    args = parser.parse_args()

    if args.check:
        return check(args.canticles, args.canto)
    if args.clean:
        return clean(args.canticles, args.chunk, args.canto)
    log_path = Path(args.log) if args.log else None
    if args.fix:
        if not args.model:
            parser.error("--model is required for --fix")
        return fix(args.canticles, args.model, args.canto, log_path)
    if args.dry_run:
        return build(args.canticles, args.model or "", args.chunk, args.force, True, args.canto)
    if not args.model:
        parser.error("--model is required for building (or pass --check / --dry-run)")
    return build(args.canticles, args.model, args.chunk, args.force, False, args.canto, log_path)


if __name__ == "__main__":
    sys.exit(main())
