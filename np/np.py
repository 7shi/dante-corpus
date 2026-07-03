"""Build driver for Layer 3 (noun-phrase enumeration) — a per-step generation script.

Like `morph/morph.py` (Layer 2), the script that *generates* an artifact lives in its own step
directory (here `np/`), while the parsing, alignment, nesting, and I/O it depends on stay in the
shared package (`dante_corpus/np.py`, consumed by the runtime API). An LLM proposes a Markdown
table listing every noun phrase per chunk of lines, which is parsed and aligned to the
deterministic tokens (`np.align_chunk`) and frozen as `np/<canticle>/NN.tsv`. The runtime API
never calls a model.

Generation resumes from its own output: each chunk's spans are written back to the TSV as soon
as they validate, so an interrupted run continues where it stopped — already-committed lines are
skipped and only the remaining chunks are requested.

    uv run np.py inferno -m ollama:gpt-oss        # all of Inferno (resumes)
    uv run np.py inferno -c 1 -m ollama:gpt-oss   # just canto 1
    uv run np.py inferno --force -m ...           # rebuild from scratch
    uv run np.py inferno --check                  # code-only, no model
    uv run np.py inferno -n                       # dry run: show pending chunks, no LLM
    uv run np.py inferno --clean                  # remove chunks with hard violations
    uv run np.py inferno --fix-clitics            # backfill clitic mentions, no model
    uv run np.py inferno --fix-repeats            # reassign duplicate repeat spans, no model
    uv run np.py inferno --fix -m ollama:gpt-oss  # regenerate lines with soft violations

`--check` validates committed artifacts against the deterministic tokens (every NP is a
contiguous token run with its head inside and verbatim text), and — when Layer-2 morphology is
present — reports soft coverage (every nominal token heads at least one NP).
"""

import argparse
import sys
from pathlib import Path

from dante_corpus import api, morph, np
from llm7shi.statusline import StatusLine

SYSTEM_PROMPT = """\
You are a syntactic analyzer for archaic Italian (Dante's Divine Comedy).
For the given numbered source lines, enumerate EVERY noun phrase, exhaustively and
over-inclusively. Output ONLY a Markdown table with columns:
| Line | Noun Phrase | Head |

Rules:
* List every noun phrase, including nested ones: emit the whole phrase AND each smaller noun
  phrase inside it as separate rows (e.g. both "mezzo del cammin di nostra vita" and "nostra vita").
* Copy the Noun Phrase verbatim from the source line (a contiguous run of words, no line number).
* Head is the single head word of the phrase, copied verbatim from it.
* Line is the source line number the phrase belongs to.
* It is correct to over-include; do not decide whether a phrase is important.
* Output only the table, with no commentary before or after it.

Example input:
1 Nel mezzo del cammin di nostra vita
2 mi ritrovai per una selva oscura,
3 ché la diritta via era smarrita.

Example output:
| Line | Noun Phrase | Head |
|---|---|---|
| 1 | mezzo del cammin di nostra vita | mezzo |
| 1 | cammin di nostra vita | cammin |
| 1 | nostra vita | vita |
| 2 | una selva oscura | selva |
| 3 | la diritta via | via |
"""

RETRIES = 2


def _chunks(lines: tuple[api.Line, ...], size: int):
    for start in range(0, len(lines), size):
        yield lines[start : start + size]


def _load_committed(canticle: str, number: int) -> list[tuple[int, list[np.NPSpan]]]:
    """Already-frozen spans for a canto, ordered by line number — the checkpoint to resume from.

    Includes zero-NP sentinel lines (present with an empty list), so a processed-but-empty line
    still counts as done."""
    if not np.has_np(canticle, number):
        return []
    data = np.load_np(canticle, number)
    return [(no, list(spans)) for no, spans in sorted(data.items())]


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


def _continue_if_truncated(
    client, nos: list[int], texts: list[str], table_text: str, ui: StatusLine
) -> str:
    """If the chunk's last line produced no NP rows (likely truncation), ask the client to continue."""
    try:
        partial, _ = np.align_chunk(nos, texts, table_text)
    except ValueError:
        return table_text
    if partial.get(nos[-1]):  # last line has NPs → not truncated
        return table_text
    short = [no for no in nos if not partial.get(no)]
    short_texts = [texts[nos.index(no)] for no in short]
    cont_prompt = (
        "The table was truncated. Please continue with the remaining noun phrases for these lines:\n\n"
        + "\n".join(f"{no} {text}" for no, text in zip(short, short_texts))
    )
    cont_text = client(cont_prompt).text
    ui.stream.end()
    return _merge_tables(table_text + "\n" + cont_text)


def _hard_violations(nos: list[int], texts: list[str],
                     aligned: dict[int, list[np.NPSpan]], unaligned: int) -> list[str]:
    hard: list[str] = []
    if unaligned:
        hard.append(f"{unaligned} unalignable NP row(s)")
    for no, text in zip(nos, texts):
        for v in np.validate_line(no, text, list(aligned.get(no, []))):
            if v.kind != "tag":
                hard.append(f"{no}:{v.detail}")
    return hard


def _try_align(nos: list[int], texts: list[str], model: str,
               ui: StatusLine, label: str,
               log_path: Path | None = None,
               morph_rows: dict[int, list] | None = None) -> dict | None:
    """Call LLM and align; return aligned dict on success, None after all retries fail."""
    from llm7shi import Client

    prompt = "List the noun phrases for these lines:\n\n" + "\n".join(
        f"{no} {text}" for no, text in zip(nos, texts)
    )
    for attempt in range(RETRIES + 1):
        client = Client(model=model, file=ui.stream, show_params=False)
        client.set_system_prompt(SYSTEM_PROMPT)
        table_text = client(prompt).text
        ui.stream.end()
        table_text = _merge_tables(table_text)
        table_text = _continue_if_truncated(client, nos, texts, table_text, ui)
        try:
            aligned, unaligned = np.align_chunk(nos, texts, table_text, morph_rows)
            hard = _hard_violations(nos, texts, aligned, unaligned)
            if hard:
                raise ValueError("; ".join(hard))
            return aligned
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
    line_no: int, text: str, spans: list[np.NPSpan], morph_rows: list | None
) -> tuple[list[morph.Violation], list[morph.Violation]]:
    """Split validate_line results into (hard, soft). tag -> soft; range/head/word -> hard."""
    hard, soft = [], []
    for v in np.validate_line(line_no, text, spans, morph_rows):
        (soft if v.kind == "tag" else hard).append(v)
    return hard, soft


def _morph_rows(canticle: str, number: int) -> dict[int, list]:
    """Layer-2 rows per line for soft checks, or {} when morphology is absent."""
    if not morph.has_morph(canticle, number):
        return {}
    return {no: list(rows) for no, rows in morph.load_morph(canticle, number).items()}


def _build_canto(canticle: str, number: int, n_cantos: int, model: str, size: int,
                 force: bool, dry_run: bool, ui: StatusLine,
                 log_path: Path | None = None) -> bool:
    canto = api.canto(canticle, number)
    lines = canto.lines()
    out = [] if force else _load_committed(canticle, number)
    done = {no for no, _ in out}
    morph_rows = _morph_rows(canticle, number)

    pending = [chunk for chunk in _chunks(lines, size)
               if any(line.no not in done for line in chunk)]
    label = f"{canticle} {number}/{n_cantos}"
    if not pending:
        ui.log(f"[dim]Skip (complete): np/{canticle}/{number:02d}.tsv[/dim]")
        return True
    if done:
        ui.log(f"Resume: np/{canticle}/{number:02d}.tsv "
               f"({len(done)} line(s) done, {len(pending)} chunk(s) left)")

    if dry_run:
        for chunk in pending:
            nos = [line.no for line in chunk]
            ui.log(f"  [dry-run] np/{canticle}/{number:02d}.tsv "
                   f"lines {nos[0]}-{nos[-1]} ({len(nos)} line(s))")
        return True

    with ui.progress(len(lines), start=pending[0][0].no, label=label) as prog:
        for chunk in pending:
            nos = [line.no for line in chunk]
            prog.update(nos[0])
            texts = [line.text for line in chunk]
            label = f"{canticle} {number}"
            aligned = _try_align(nos, texts, model, ui, label, log_path, morph_rows)
            if aligned is None and len(chunk) > 1:
                ui.stream.error(f"  {label}: chunk failed, retrying line by line")
                aligned = {}
                for line in chunk:
                    result = _try_align(
                        [line.no], [line.text], model, ui, label, log_path, morph_rows
                    )
                    if result is None:
                        ui.stream.error(f"  {label}: giving up at line {line.no}; "
                                        f"earlier lines saved for resume")
                        return False
                    aligned.update(result)
            elif aligned is None:
                ui.stream.error(f"  {label}: giving up at line {nos[0]}; "
                                f"earlier lines saved for resume")
                return False
            for line in chunk:
                rows = morph_rows.get(line.no)
                if rows:
                    tokens = [tok for tok, _, _ in np.token_spans(line.text)]
                    aligned.setdefault(line.no, []).extend(
                        np.clitic_mentions(line.no, tokens, rows)
                    )
            chunk_nos = {line.no for line in chunk}
            out = [(no, spans) for no, spans in out if no not in chunk_nos]
            out.extend((line.no, aligned.get(line.no, [])) for line in chunk)
            out.sort(key=lambda item: item[0])
            np.write_np(canticle, number, out)
    ui.log(f"Wrote: np/{canticle}/{number:02d}.tsv")
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
            if not np.has_np(canticle, number):
                print(f"Missing: np/{canticle}/{number:02d}.tsv", file=sys.stderr)
                hard += 1
                continue
            data = np.load_np(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            missing: list[int] = []
            for line in api.canto(canticle, number).lines():
                if line.no not in data:
                    missing.append(line.no)
                    hard += 1
                    continue
                spans = list(data.get(line.no, ()))
                hard_vs, soft_vs = _classify_violations(
                    line.no, line.text, spans, morph_rows.get(line.no)
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


def fix_clitics(canticles: list[str], only: int | None) -> int:
    """Backfill missing clitic mentions into frozen artifacts — deterministic, no model call.

    Artifacts built before `clitic_mentions()` existed lack the synthetic `+lemma` spans that
    Layer 2's compound POS implies. Those spans are a pure function of the frozen Layer-2
    artifact, so they can be added in place without rebuilding."""
    added = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not np.has_np(canticle, number):
                continue
            data = np.load_np(canticle, number)
            morph_rows = _morph_rows(canticle, number)
            out: list[tuple[int, list[np.NPSpan]]] = []
            n_added = 0
            for line in api.canto(canticle, number).lines():
                if line.no not in data:
                    continue
                spans = list(data[line.no])
                rows = morph_rows.get(line.no)
                if rows:
                    tokens = [tok for tok, _, _ in np.token_spans(line.text)]
                    have = {(s.head, s.text) for s in spans if s.text.startswith("+")}
                    missing = [m for m in np.clitic_mentions(line.no, tokens, rows)
                               if (m.head, m.text) not in have]
                    spans.extend(missing)
                    n_added += len(missing)
                out.append((line.no, spans))
            if n_added:
                np.write_np(canticle, number, out)
                print(f"Fixed np/{canticle}/{number:02d}.tsv — added {n_added} clitic mention(s)")
                added += n_added
    print(f"fix-clitics complete: {added} mention(s) added")
    return 0


def fix_repeats(canticles: list[str], only: int | None) -> int:
    """Backfill repeated-word/phrase spans onto distinct occurrences — deterministic, no model call.

    Artifacts built before `align_chunk` tracked claimed occurrences collapsed every proposal for
    a repeated word or phrase in one line (e.g. "a poco a poco") onto the first occurrence,
    leaving identical duplicate rows. Reassigns each duplicate to a further, unclaimed occurrence
    of the same run when one exists."""
    changed = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not np.has_np(canticle, number):
                continue
            data = np.load_np(canticle, number)
            out: list[tuple[int, list[np.NPSpan]]] = []
            n_changed = 0
            for line in api.canto(canticle, number).lines():
                if line.no not in data:
                    continue
                spans, n = np.dedupe_repeats(line.no, line.text, list(data[line.no]))
                out.append((line.no, spans))
                n_changed += n
            if n_changed:
                np.write_np(canticle, number, out)
                print(f"Fixed np/{canticle}/{number:02d}.tsv — reassigned {n_changed} repeat(s)")
                changed += n_changed
    print(f"fix-repeats complete: {changed} span(s) reassigned")
    return 0


def _fix_canto(canticle: str, number: int, n_cantos: int, model: str, ui: StatusLine,
               log_path: Path | None = None) -> tuple[int, int]:
    """Fix one canto's flagged lines under a progress bar; returns (fixed, attempted)."""
    data = np.load_np(canticle, number)
    morph_rows = _morph_rows(canticle, number)
    if not morph_rows:
        return 0, 0
    lines = api.canto(canticle, number).lines()
    lines_by_no = {line.no: line for line in lines}
    out: list[tuple[int, list[np.NPSpan]]] = []
    changed = False
    fixed = 0
    attempted = 0
    label = f"{canticle} {number}/{n_cantos}"
    with ui.progress(len(lines), label=label) as prog:
        for no, spans in sorted(data.items()):
            prog.update(no)
            spans = list(spans)
            line = lines_by_no[no]
            _, soft_before = _classify_violations(no, line.text, spans, morph_rows.get(no))
            tag_before = [v for v in soft_before if "clitic mention" not in v.detail]
            if not tag_before:
                out.append((no, spans))
                continue
            attempted += 1
            result = _try_align([no], [line.text], model, ui, label, log_path, morph_rows)
            if result is None:
                out.append((no, spans))
                continue
            new_spans = list(result.get(no, []))
            rows = morph_rows.get(no)
            if rows:
                tokens = [tok for tok, _, _ in np.token_spans(line.text)]
                new_spans.extend(np.clitic_mentions(no, tokens, rows))
            _, soft_after = _classify_violations(no, line.text, new_spans, morph_rows.get(no))
            tag_after = [v for v in soft_after if "clitic mention" not in v.detail]
            if len(tag_after) < len(tag_before):
                out.append((no, new_spans))
                fixed += 1
                changed = True
                ui.log(f"Fixed {canticle} {number}:{no} — "
                       f"{len(tag_before)} -> {len(tag_after)} soft violation(s)")
            else:
                out.append((no, spans))
                if log_path:
                    with log_path.open("a", encoding="utf-8") as f:
                        f.write(f"=== {label} line {no}: not improved "
                                f"({len(tag_before)} -> {len(tag_after)}) ===\n")
                        for v in tag_before:
                            f.write(f"before: {v.detail}\n")
                        for v in tag_after:
                            f.write(f"after:  {v.detail}\n")
                        f.write("\n")
    if changed:
        np.write_np(canticle, number, out)
        ui.log(f"Wrote: np/{canticle}/{number:02d}.tsv")
    return fixed, attempted


def fix(canticles: list[str], model: str, only: int | None, log_path: Path | None = None) -> int:
    """Re-run the model on lines carrying soft ("tag") violations, keeping only real improvements.

    A soft violation can reflect either a genuine Layer 3 omission/over-inclusion or a legitimate
    reading (Dante substantivizing a function word) — the `che` mistag review (PLAN.md) found
    both occur in the same population, and telling them apart needed hand review per case. This
    regenerates each flagged line in isolation (same prompt as `build`) and swaps in the new spans
    only if they carry strictly fewer tag violations than before, with no new hard violations —
    a no-worse-off guarantee, not a promise every case clears. Clitic-coverage violations are
    excluded since `--fix-clitics` already handles those deterministically.
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
            if not np.has_np(canticle, number):
                continue
            f, a = _fix_canto(canticle, number, n_cantos, model, ui, log_path)
            fixed += f
            attempted += a
    print(f"fix complete: {fixed}/{attempted} line(s) improved")
    return 0


def clean(canticles: list[str], size: int, only: int | None) -> int:
    removed = 0
    for canticle in canticles:
        numbers = [only] if only else list(api.cantos(canticle))
        for number in numbers:
            if not np.has_np(canticle, number):
                continue
            data = np.load_np(canticle, number)
            lines = api.canto(canticle, number).lines()

            # Remove chunks with any hard violation (soft coverage is reported, not cleaned).
            bad: set[int] = set()
            for chunk in _chunks(lines, size):
                for line in chunk:
                    spans = list(data.get(line.no, ()))
                    hard_vs, _ = _classify_violations(line.no, line.text, spans, None)
                    if hard_vs:
                        for l in chunk:
                            bad.add(l.no)
                        break
            has_data = bad & data.keys()
            if has_data:
                for no in bad:
                    data.pop(no, None)
                out = sorted(data.items())
                np.write_np(canticle, number, [(no, list(spans)) for no, spans in out])
                print(f"Cleaned np/{canticle}/{number:02d}.tsv — removed lines {sorted(bad)}")
            removed += len(has_data)
    print(f"clean complete: {removed} line(s) removed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="np.py")
    parser.add_argument("canticles", nargs="+", help="canticle names, e.g. inferno")
    parser.add_argument("-m", "--model", help="LLM, e.g. ollama:gpt-oss (required unless --check)")
    parser.add_argument("--chunk", type=int, default=3, help="lines per LLM call (default 3)")
    parser.add_argument("-c", "--canto", type=int, help="limit to a single canto number")
    parser.add_argument("--force", action="store_true", help="rebuild even if artifact exists")
    parser.add_argument("--check", action="store_true", help="validate artifacts, no model call")
    parser.add_argument("--clean", action="store_true",
                        help="remove chunks with hard violations, then exit")
    parser.add_argument("--fix-clitics", action="store_true",
                        help="backfill missing clitic mentions from Layer 2, no model call")
    parser.add_argument("--fix-repeats", action="store_true",
                        help="reassign duplicate repeated-word spans to distinct occurrences, no model call")
    parser.add_argument("--fix", action="store_true",
                        help="regenerate lines with soft violations, keep only improvements")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="show pending chunks without calling the LLM")
    parser.add_argument("--log", nargs="?", const="np.log", metavar="FILE",
                        help="append failed LLM responses to FILE (default: np.log)")
    args = parser.parse_args()

    if args.check:
        return check(args.canticles, args.canto)
    if args.fix_clitics:
        return fix_clitics(args.canticles, args.canto)
    if args.fix_repeats:
        return fix_repeats(args.canticles, args.canto)
    if args.clean:
        return clean(args.canticles, args.chunk, args.canto)
    if args.dry_run:
        return build(args.canticles, args.model or "", args.chunk, args.force, True, args.canto)
    log_path = Path(args.log) if args.log else None
    if args.fix:
        if not args.model:
            parser.error("--model is required for --fix")
        return fix(args.canticles, args.model, args.canto, log_path)
    if not args.model:
        parser.error("--model is required for building (or pass --check / --dry-run)")
    return build(args.canticles, args.model, args.chunk, args.force, False, args.canto,
                 log_path)


if __name__ == "__main__":
    sys.exit(main())
