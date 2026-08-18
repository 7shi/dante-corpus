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
    uv run skel.py inferno -c 12- -m ollama:gpt-oss # canto 12 on (resume after a failure)
    uv run skel.py inferno -c 11-15 --stats         # a canto range, inclusive
    uv run skel.py inferno --force -m ...           # rebuild from scratch
    uv run skel.py inferno --check                  # code-only, no model
    uv run skel.py inferno --stats                  # code-only; soft violations by class
    uv run skel.py inferno -n                        # dry run: show pending units, no LLM
    uv run skel.py inferno --clean                   # remove parse units with hard violations
    uv run skel.py inferno --repair                  # deterministic rewrites only, no model
    uv run skel.py inferno --fix -m ollama:gpt-oss   # reduce soft violations (three stages)
    uv run skel.py inferno --fix --no-whole -m ...   # ... without the regeneration fallback

`--fix` works in three stages, cheapest first: the deterministic rewrites that need no reading
(`--repair`'s own rules, run inline), then one narrow question per remaining violation *class* —
each with its own system prompt and its own small answer, spliced back in at row level — and
only then, for units neither stage moved, the whole-unit regeneration this mode originally
consisted of. Splitting by class is what lets an instruction reach the model at the flagged
position, and lets a unit keep the classes that were settled instead of discarding a partial
improvement.

`--check` validates committed artifacts against the deterministic derivation (`skel.
derive_unit`) and reports soft violations (role outside the frozen vocabulary, a nominal-role
argument heading no NP/pronoun/predicate, and — the central check — every divergence from
the derivation: `missing_tuple`/`extra_tuple`/`missing_arg`/`extra_arg`/`role_mismatch`).

`--log FILE` collects two things: the responses that failed to validate, and the model's own
`NOTE` lines — one per question it could not answer in the shape asked for (see the *field
notes* section below). The second is a discovery instrument, not telemetry: it names positions
worth reading without anyone having to read the canticle to find them.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from dante_corpus import api, dep, morph, skel

try:
    from .driver_build import (
        RETRIES,
        SYSTEM_PROMPT,
        _build_canto,
        _continue_if_missing,
        _hard_violations,
        _merge_tables,
        _prompt,
        _try_parse,
        build,
    )
    from .driver_fix import (
        _ANSWER_RE,
        _ASK_HEADER,
        _CLASS_ORDER,
        _CLASS_PROMPTS,
        _CONV_ADJECTIVE,
        _CONV_ADJUNCT,
        _CONV_ADVERB,
        _CONV_ADVERB_ARG,
        _CONV_DATIVE,
        _CONV_PRODROP,
        _CONV_RELPRON,
        _CONV_REPEATED,
        _CONV_ROLES,
        _CONV_SUBJECT,
        _CONV_VERBLESS,
        _EXTRA_ARG_CLASSES,
        _HINT_PHRASING,
        _MISSING_ARG_CLASSES,
        _ROLE_MENU,
        _STAND_PAT,
        _TABLE_HEADER,
        _TOKEN_REF_RE,
        _ClassPrompt,
        _UnitContext,
        _apply_arg_slot,
        _apply_dual_role,
        _apply_extra_arg,
        _apply_extra_tuple,
        _apply_missing_arg,
        _apply_missing_tuple,
        _apply_role_mismatch,
        _ask_arg_slot,
        _ask_class,
        _ask_dual_role,
        _ask_extra_arg,
        _ask_extra_tuple,
        _ask_missing_arg,
        _ask_missing_tuple,
        _ask_missing_tuple_nominal,
        _ask_role_mismatch,
        _find_arg_row,
        _fix_canto,
        _fix_hint,
        _is_refusal,
        _numbered,
        _parse_answers,
        _rows_of_predicate,
        _split_slot_conflicts,
        _token_ref,
        _violation_subclass,
        fix,
    )
    from .driver_ui import (
        _DIVERGENCE_KINDS,
        _NOTE_RE,
        _FieldNote,
        _alpha_tokens,
        _apply_unit_repairs,
        _case_rows,
        _classify_violations,
        _dep_rows,
        _describe_repair,
        _fix_summary_lines,
        _is_improvement,
        _load_committed,
        _log_field_notes,
        _log_rejection,
        _morph_rows,
        _np_rows,
        _print_fix_summary,
        _print_stats,
        _split_field_notes,
        _units,
        _violation_class,
    )
except ImportError:
    _THIS_DIR = Path(__file__).resolve().parent
    if str(_THIS_DIR) not in sys.path:
        sys.path.insert(0, str(_THIS_DIR))
    from driver_build import (
        RETRIES,
        SYSTEM_PROMPT,
        _build_canto,
        _continue_if_missing,
        _hard_violations,
        _merge_tables,
        _prompt,
        _try_parse,
        build,
    )
    from driver_fix import (
        _ANSWER_RE,
        _ASK_HEADER,
        _CLASS_ORDER,
        _CLASS_PROMPTS,
        _CONV_ADJECTIVE,
        _CONV_ADJUNCT,
        _CONV_ADVERB,
        _CONV_ADVERB_ARG,
        _CONV_DATIVE,
        _CONV_PRODROP,
        _CONV_RELPRON,
        _CONV_REPEATED,
        _CONV_ROLES,
        _CONV_SUBJECT,
        _CONV_VERBLESS,
        _EXTRA_ARG_CLASSES,
        _HINT_PHRASING,
        _MISSING_ARG_CLASSES,
        _ROLE_MENU,
        _STAND_PAT,
        _TABLE_HEADER,
        _TOKEN_REF_RE,
        _ClassPrompt,
        _UnitContext,
        _apply_arg_slot,
        _apply_dual_role,
        _apply_extra_arg,
        _apply_extra_tuple,
        _apply_missing_arg,
        _apply_missing_tuple,
        _apply_role_mismatch,
        _ask_arg_slot,
        _ask_class,
        _ask_dual_role,
        _ask_extra_arg,
        _ask_extra_tuple,
        _ask_missing_arg,
        _ask_missing_tuple,
        _ask_missing_tuple_nominal,
        _ask_role_mismatch,
        _find_arg_row,
        _fix_canto,
        _fix_hint,
        _is_refusal,
        _numbered,
        _parse_answers,
        _rows_of_predicate,
        _split_slot_conflicts,
        _token_ref,
        _violation_subclass,
        fix,
    )
    from driver_ui import (
        _DIVERGENCE_KINDS,
        _NOTE_RE,
        _FieldNote,
        _alpha_tokens,
        _apply_unit_repairs,
        _case_rows,
        _classify_violations,
        _dep_rows,
        _describe_repair,
        _fix_summary_lines,
        _is_improvement,
        _load_committed,
        _log_field_notes,
        _log_rejection,
        _morph_rows,
        _np_rows,
        _print_fix_summary,
        _print_stats,
        _split_field_notes,
        _units,
        _violation_class,
    )


def check(canticles: list[str], spec: str | None) -> int:
    hard = 0
    soft = 0
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                print(f"Missing: skel/{canticle}/{number:02d}.tsv", file=sys.stderr)
                hard += 1
                continue
            data = skel.load_skel(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            np_rows = _np_rows(canticle, number)
            dep_rows = _dep_rows(canticle, number)
            case_rows = _case_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {line.no: line.text for line in lines}
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            missing = [no for no in nos_all if no not in data]
            hard += len(missing)
            for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                if any(no in missing for no in unit):
                    continue
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data[no]) for no in unit}
                hard_vs, soft_vs = _classify_violations(
                    unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows,
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


def stats(canticles: list[str], spec: str | None) -> int:
    hard = 0
    all_soft: list[morph.Violation] = []
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                hard += 1
                continue
            data = skel.load_skel(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            np_rows = _np_rows(canticle, number)
            dep_rows = _dep_rows(canticle, number)
            case_rows = _case_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {line.no: line.text for line in lines}
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            missing = [no for no in nos_all if no not in data]
            hard += len(missing)
            for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                if any(no in missing for no in unit):
                    continue
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: list(data[no]) for no in unit}
                hard_vs, soft_vs = _classify_violations(
                    unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows,
                )
                hard += len(hard_vs)
                all_soft.extend(soft_vs)
    _print_stats(all_soft)
    print(f"stats complete: {len(all_soft)} soft violation(s) ({hard} hard)")
    return 1 if hard else 0


def clean(canticles: list[str], size: int, spec: str | None) -> int:
    removed = 0
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                continue
            data = skel.load_skel(canticle, number)
            lines = api.canto(canticle, number).lines()
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            text_by_no = dict(zip(nos_all, texts_all))

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


def repair(canticles: list[str], spec: str | None) -> int:
    totals: Counter[str] = Counter()
    cantos_touched = 0
    for canticle in canticles:
        for number in api.select_cantos(canticle, spec):
            if not skel.has_skel(canticle, number):
                continue
            data = skel.load_skel(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            np_rows = _np_rows(canticle, number)
            dep_rows = _dep_rows(canticle, number)
            case_rows = _case_rows(canticle, number)
            lines = api.canto(canticle, number).lines()
            text_by_no = {line.no: line.text for line in lines}
            nos_all = [line.no for line in lines]
            texts_all = [line.text for line in lines]
            missing = [no for no in nos_all if no not in data]
            out = {no: list(rows) for no, rows in data.items()}
            n_canto = 0
            for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                if any(no in missing for no in unit):
                    continue
                unit_texts = [text_by_no[no] for no in unit]
                rows_by_line = {no: out[no] for no in unit}
                for r in _apply_unit_repairs(unit, unit_texts, rows_by_line, morph_rows,
                                             np_rows, dep_rows, case_rows):
                    totals[r.kind] += 1
                    n_canto += 1
                    print(f"{canticle} {number}:{_describe_repair(r)}")
            if n_canto:
                skel.write_skel(canticle, number, [(no, rows) for no, rows in sorted(out.items())])
                print(f"Repaired skel/{canticle}/{number:02d}.tsv — {n_canto} rewrite(s)")
                cantos_touched += 1
    summary = ", ".join(f"{n} {kind}" for kind, n in sorted(totals.items())) or "no"
    print(f"repair complete: {summary} rewrite(s) across {cantos_touched} canto(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="skel.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. ollama:gpt-oss (required unless --check)")
    parser.add_argument("--chunk", type=int, default=dep.MAX_UNIT_LINES,
                        help=f"max lines per parse unit (default {dep.MAX_UNIT_LINES})")
    parser.add_argument("-c", "--canto", metavar="SPEC", help=api.CANTO_SPEC_HELP)
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    parser.add_argument("--stats", action="store_true",
                        help="validate artifacts, no model call; print soft-violation counts by class")
    parser.add_argument("--clean", action="store_true",
                        help="remove parse units with hard violations, then exit")
    parser.add_argument("--repair", action="store_true",
                        help="run --fix's deterministic stage on its own: rewrite committed TSVs "
                             "for divergences that need no reading, no model call")
    parser.add_argument("--fix", action="store_true",
                        help="reduce soft violations in built units: deterministic repairs, then "
                             "one targeted question per violation class, keeping only improvements")
    parser.add_argument("--whole", action=argparse.BooleanOptionalAction, default=True,
                        help="with --fix, fall back to whole-unit regeneration for units the "
                             "targeted questions did not move (default: enabled)")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="show pending parse units without calling the LLM")
    parser.add_argument("--log", nargs="?", const="skel.log", metavar="FILE",
                        help="append failed LLM responses, and the model's own NOTE lines for "
                             "questions it could not answer cleanly, to FILE (default: skel.log)")
    args = parser.parse_args()

    if err := api.check_canto_spec(args.canticles, args.canto):
        parser.error(err)

    if args.check:
        return check(args.canticles, args.canto)
    if args.stats:
        return stats(args.canticles, args.canto)
    if args.clean:
        return clean(args.canticles, args.chunk, args.canto)
    if args.repair:
        return repair(args.canticles, args.canto)
    log_path = Path(args.log) if args.log else None
    if args.fix:
        if not args.model:
            parser.error("--model is required for --fix")
        return fix(args.canticles, args.model, args.canto, log_path, args.whole)
    if args.dry_run:
        return build(args.canticles, args.model or "", args.chunk, args.force, True, args.canto)
    if not args.model:
        parser.error("--model is required for building (or pass --check / --dry-run)")
    return build(args.canticles, args.model, args.chunk, args.force, False, args.canto, log_path)


if __name__ == "__main__":
    sys.exit(main())
