"""Driver UI, common dataset accessors, violation classification, and formatted output for Layer 5."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dante_corpus import api, case, dep, morph, np, skel
from dante_corpus.tokenizer import has_alpha, tokenize


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


def _case_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-2 `case`-annex rows per line, or {} when absent."""
    if not case.has_case(canticle, number):
        return {}
    return {no: list(rows) for no, rows in case.load_case(canticle, number).items()}


_DIVERGENCE_KINDS = ("missing_tuple", "extra_tuple", "missing_arg", "extra_arg", "role_mismatch")


def _violation_class(v: morph.Violation) -> str:
    prefix = v.detail.split(":", 1)[0]
    if prefix in _DIVERGENCE_KINDS:
        return prefix
    if prefix == "dual_role":
        return "dual_role"
    if "heads no NP" in v.detail:
        return "membership"
    if "not in frozen vocabulary" in v.detail:
        return "unknown_role"
    return "other"


def _classify_violations(
    nos: list[int], texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    morph_rows: dict[int, list] | None, np_rows: dict[int, list] | None,
    dep_rows: dict[int, list] | None, case_rows: dict[int, list] | None = None,
) -> tuple[list[morph.Violation], list[morph.Violation]]:
    """Split validate_unit results into (hard, soft). tag -> soft; rest -> hard."""
    hard, soft = [], []
    for v in skel.validate_unit(nos, texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows):
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def _is_improvement(
    soft_before: list[morph.Violation], soft_after: list[morph.Violation]
) -> bool:
    """A regeneration is accepted only if it removes violations *without* introducing a class
    that was not already there (PLAN.md Phase 5c)."""
    if len(soft_after) >= len(soft_before):
        return False
    before_classes = {_violation_class(v) for v in soft_before}
    return all(_violation_class(v) in before_classes for v in soft_after)


# --- Field notes -----------------------------------------------------------------------------

_NOTE_RE = re.compile(r"^[ \t]*N(\d+)(?:[ \t]*\.[ \t]*(\d+))?[ \t]*[:.)][ \t]*(.+?)[ \t]*$",
                      re.MULTILINE)


@dataclass(frozen=True)
class _FieldNote:
    """One report."""
    index: int | None
    pos: tuple[int, int] | None
    text: str


def _split_field_notes(text: str) -> tuple[str, list[_FieldNote]]:
    """Take the `N…` lines out of a response and return them beside the response without them."""
    notes: list[_FieldNote] = []
    for m in _NOTE_RE.finditer(text):
        body = " ".join(m.group(3).split())
        if not body:
            continue
        pos = (int(m.group(1)), int(m.group(2))) if m.group(2) else None
        notes.append(_FieldNote(None if pos else int(m.group(1)), pos, body[:300]))
    return _NOTE_RE.sub("", text), notes


def _log_field_notes(
    log_path: Path | None, label: str, nos: list[int], cls: str, notes: list[_FieldNote],
    anchors: dict[int, str] | None = None,
    word_at: Callable[[tuple[int, int]], str] | None = None,
) -> None:
    if not log_path or not notes:
        return
    with log_path.open("a", encoding="utf-8") as f:
        for note in notes:
            if note.pos is not None:
                word = word_at(note.pos) if word_at else "?"
                anchor = f"{note.pos[0]}.{note.pos[1]} '{word}'"
            else:
                anchor = (anchors or {}).get(note.index, "-")
            f.write(f"NOTE\t{label}\t{nos[0]}-{nos[-1]}\t{cls}\t{anchor}\t{note.text}\n")


def _log_rejection(log_path, label, unit, cls, soft_before, soft_after, hard_after) -> None:
    """Record a candidate the acceptance gate turned down."""
    if not log_path:
        return
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"=== {label} lines {unit[0]}-{unit[-1]} [{cls}]: not accepted "
                f"({len(soft_before)} -> {len(soft_after)}"
                f"{f', {len(hard_after)} hard' if hard_after else ''}) ===\n")
        for v in hard_after:
            f.write(f"hard:   {v.detail}\n")
        for v in soft_before:
            f.write(f"before: {v.detail}\n")
        for v in soft_after:
            f.write(f"after:  {v.detail}\n")
        f.write("\n")


def _describe_repair(r: skel.Repair) -> str:
    """One line naming what a rewrite changed, for the `--repair` log and `--fix`'s stage 1."""
    where = f"{r.before.line}.{r.before.token}"
    if r.kind == "null_subject":
        return (f"{where} [null_subject] subj (0,0) -> "
                f"({r.after.arg_line},{r.after.arg_token})")
    return (f"{where} [{r.kind}] {r.before.role} -> {r.after.role} "
            f"arg ({r.before.arg_line},{r.before.arg_token})")


def _apply_unit_repairs(
    unit: list[int], unit_texts: list[str], rows_by_line: dict[int, list[skel.SkelRow]],
    morph_rows: dict[int, list], np_rows: dict[int, list], dep_rows: dict[int, list],
    case_rows: dict[int, list] | None = None,
) -> list[skel.Repair]:
    """Stage 1 of `--fix`, and the whole of `--repair`: apply deterministic rewrites."""
    applied: list[skel.Repair] = []
    rejected: set[tuple[str, skel.SkelRow]] = set()
    while True:
        _, soft = _classify_violations(
            unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows)
        derived = skel.derive_unit(unit, dep_rows, morph_rows, case_rows)
        candidates = [
            r for r in skel._find_repairs(rows_by_line, derived, soft, morph_rows, dep_rows)
            if (r.kind, r.before) not in rejected
        ]
        if not candidates:
            return applied
        r = candidates[0]
        rows = rows_by_line.get(r.before.line, [])
        if r.before not in rows:
            rejected.add((r.kind, r.before))
            continue
        i = rows.index(r.before)
        rows[i] = r.after
        hard_after, soft_after = _classify_violations(
            unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows)
        if not hard_after and _is_improvement(soft, soft_after):
            applied.append(r)
        else:
            rows[i] = r.before
            rejected.add((r.kind, r.before))


def _print_stats(violations: list[morph.Violation]) -> None:
    by_kind: Counter[str] = Counter()
    by_role: Counter[tuple[str, str]] = Counter()
    by_role_null: Counter[tuple[str, str]] = Counter()
    role_mismatch_pairs: Counter[tuple[str | None, str | None]] = Counter()

    for v in violations:
        kind = _violation_class(v)
        by_kind[kind] += 1
        if kind in ("extra_arg", "missing_arg") and v.role is not None:
            by_role[(kind, v.role)] += 1
            if v.arg == (0, 0):
                by_role_null[(kind, v.role)] += 1
        if kind == "role_mismatch":
            role_mismatch_pairs[(v.given_role, v.role)] += 1

    print("By kind:", file=sys.stderr)
    for kind, count in by_kind.most_common():
        print(f"  {kind:15s} {count:6d}", file=sys.stderr)

    print("\nBy role (extra_arg / missing_arg):", file=sys.stderr)
    for (kind, role), count in by_role.most_common():
        null_count = by_role_null[(kind, role)]
        null_tag = f" (of which ∅ (0,0): {null_count})" if null_count else ""
        print(f"  {kind:12s} {role:12s} {count:6d}{null_tag}", file=sys.stderr)

    if role_mismatch_pairs:
        print("\nTop role_mismatch pairs (given vs derived):", file=sys.stderr)
        for (grole, drole), count in role_mismatch_pairs.most_common():
            print(f"  {grole!r:14s} vs {drole!r:14s} {count:6d}", file=sys.stderr)


def _fix_summary_lines(totals: Counter[str]) -> list[str]:
    """The per-class `calls / removed / per call / refused` table, as lines."""
    flagged = totals["units:flagged"]
    calls = sum(n for k, n in totals.items() if k.startswith("calls:"))
    removed = sum(n for k, n in totals.items() if k.startswith("removed:"))
    refused = sum(n for k, n in totals.items() if k.startswith("refused:"))
    repairs = {k.split(":", 1)[1]: n for k, n in totals.items() if k.startswith("repair:")}

    lines = [f"units flagged: {flagged}; "
             f"cleared with no model call: {totals['units:cleared_deterministically']}; "
             f"cleared outright: {totals['units:cleared']}"]
    if repairs:
        lines.append("stage 1 (deterministic, 0 calls): "
                     + ", ".join(f"{n} {kind}" for kind, n in sorted(repairs.items()))
                     + f" -> {totals['removed:_deterministic']} violation(s)")
    lines.append(f"{'class':24s} {'calls':>7s} {'removed':>8s} {'per call':>9s} {'refused':>8s}")
    for key in sorted(k for k in totals if k.startswith("calls:")):
        cls = key.split(":", 1)[1]
        n_calls = totals[key]
        n_removed = totals[f"removed:{cls}"]
        rate = n_removed / n_calls if n_calls else 0.0
        lines.append(f"{cls:24s} {n_calls:7d} {n_removed:8d} {rate:9.3f} "
                     f"{totals[f'refused:{cls}']:8d}")
    rate = removed / calls if calls else 0.0
    lines.append(f"{'TOTAL':24s} {calls:7d} {removed:8d} {rate:9.3f} {refused:8d}")
    lines.append(f"fix complete: {removed} soft violation(s) removed over {calls} LLM call(s); "
                 f"{refused} refused (the reading stands)")
    return lines


def _print_fix_summary(totals: Counter[str], log_path: Path | None = None) -> None:
    lines = _fix_summary_lines(totals)
    print("\n" + "\n".join(lines))
    if log_path:
        with log_path.open("a", encoding="utf-8") as f:
            f.write("=== fix summary ===\n" + "\n".join(lines) + "\n")
