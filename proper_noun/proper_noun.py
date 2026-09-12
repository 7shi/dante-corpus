"""
Extract proper nouns from the Italian text of Dante's *Divine Comedy*,
one row per Italian line.

The source is the Italian original (read through the `dante_corpus` API),
not a translation, and a noun is recorded in the spelling the line itself
uses. That choice is what makes the model's answer checkable: a reported
noun is located in its line and the matching substring is sliced out of
the line, so every noun written to the TSV is verbatim text of that line
and a hallucinated one cannot get through.

The canto's lines are handed to the LLM in `--block-size`-line groups
(default 3, normally a tercet - enough context to tell a name from a
capitalized common noun without diluting the task), numbered by their
canto-wide line number. The model answers in the output format itself:
one tab-separated row per line, its number followed by the proper nouns
occurring in it. The reply's rows are the output file's rows, so there is
no intermediate representation to convert - this is why the script asks
for plain TSV rather than structured output.

This is deliberately *not* entity extraction - only literal proper nouns
are collected (names of people, places, peoples, rivers, deities,
stars/planets, books), never a periphrasis or metaphor standing for a
named person ("il maestro", "quel savio gentil", "colui che ..."), and
never a common noun that merely happens to be capitalized.

Output (one file per canto, written to proper_noun/<canticle>/):
- `<NN>.tsv`: variable-length TSV, one row per processed Italian line, in
  line order: `line_number<TAB>noun<TAB>noun...`. A line with no proper
  noun keeps its row, holding just the line number - that row is what
  records the line as processed. A line that has not been processed (yet)
  simply has no row: nothing is ever written as a placeholder.
- `<NN>.log`: full processing trace, also printed to the console as the
  script runs; unconditionally overwritten every run.

Every mechanical check runs inside the client's own retry loop (see
BlockClient, which overrides `llm7shi.Client.should_retry`), so a reply
with a malformed row, a wrong line number or a noun that is not in its
line is regenerated exactly as an empty reply is. There is deliberately no
second retry loop here: one client, built once with `keep_history=False`,
serves the whole run, and a group where no attempt validates is simply
left for a later run.

A missing row is therefore the pending marker. Rows are appended group by
group as they are extracted, so a failed or interrupted run just stops
writing, and the next run asks only about the lines that have no row:
each block's missing lines, split into contiguous runs, so a single
missing line in the middle of a block costs a one-line call rather than a
whole block. A canto whose file holds a row for every line is skipped with
a single console line (after a line-number cross-check). Rows stay sorted
by line number: a group that extends the file is appended, while one
filling a gap left by an earlier failure rewrites the whole file in line
order. Delete a row by hand to force just that line to be redone; delete
the file to redo the canto.

Progress display follows dante-corpus's ARCHITECTURE.md §4: one
`llm7shi.statusline.StatusLine` for the whole run, its bar labeled
`{canticle} {canto}/{n_cantos}` and walking the canto's Italian lines, with
every human-facing line sharing its console (`ui.log` /
`ui.stream.error`) so streamed model output, the bar, and this script's
own messages never clobber each other. See STATUSLINE.md for the full
design rationale (client reuse, the bar's two elapsed clocks, notify()).

The script stands on its own: it reads its text through `dante_corpus`,
talks to the LLM through `llm7shi`, and assumes nothing about the
repository it happens to sit in beyond writing beside itself.
"""

import re
import time
import argparse
from pathlib import Path
from typing import List, NamedTuple, Tuple

import dante_corpus
from llm7shi import Client
from llm7shi.statusline import StatusLine

# Output root: one subdirectory per canticle, beside this script
PROPER_NOUN_DIR = Path(__file__).resolve().parent

# Default number of Italian lines per LLM call (normally a tercet): the unit
# the canto is blocked into, and so also the largest group a rerun re-asks
DEFAULT_BLOCK_SIZE = 3


# ============================================================================
# Logging
# ============================================================================

_log_file = None


def log_print(*args, **kwargs):
    """Print to log file only"""
    if _log_file:
        print(*args, **kwargs, file=_log_file)
        _log_file.flush()


def notify(ui: StatusLine, text: str, error: bool = False) -> None:
    """
    Print to both the console (via the status bar's shared Rich console, so
    it never races with the bar or streamed model output) and this canto's
    log file.
    """
    (ui.stream.error if error else ui.log)(text)
    log_print(text)


# ============================================================================
# Shared parsing/loading helpers
# ============================================================================

class ItalianLine:
    """Represents a single line of Italian source text, read via dante_corpus."""

    def __init__(self, full_text: str, line_num: int):
        self.full_text = full_text
        self.line_num = line_num

    def __repr__(self):
        return f"ItalianLine({self.full_text!r}, line_num={self.line_num})"


def load_italian_lines(canticle: str, canto: int) -> List[ItalianLine]:
    """Load a canto's Italian lines via the dante_corpus API."""
    return [ItalianLine(line.text, line.no)
            for line in dante_corpus.canto(canticle, canto).lines()]


def pending_groups(italian_lines: List[ItalianLine], rows: dict,
                   block_size: int) -> List[List[ItalianLine]]:
    """
    The line groups still to ask the LLM about: each `block_size`-line
    block's lines that have no row yet, split into contiguous runs.

    Two properties the rest of the script relies on: a group is always
    consecutive lines (the prompt numbers them by their real line numbers,
    which only reads correctly for a run), and a line that already has a
    row is never asked about again - a rerun costs exactly the lines that
    are missing. A block missing lines 4 and 6 therefore yields two
    one-line groups rather than one block-sized call. On a first run
    nothing has a row, so the groups are just the blocks.
    """
    groups: List[List[ItalianLine]] = []
    for block in chunk_lines(italian_lines, block_size):
        run: List[ItalianLine] = []
        for line in block:
            if line.line_num in rows:
                if run:
                    groups.append(run)
                    run = []
            else:
                run.append(line)
        if run:
            groups.append(run)
    return groups


def line_range(lines: List[ItalianLine]) -> str:
    """`first-last` for a block of lines, the number alone for a single one."""
    first, last = lines[0].line_num, lines[-1].line_num
    return str(first) if first == last else f"{first}-{last}"


def chunk_lines(lines: List[ItalianLine], block_size: int) -> List[List[ItalianLine]]:
    """
    Split a flat list of Italian lines into consecutive groups of
    `block_size` lines - the fixed blocking of the canto that pending_groups
    then subsets. The final group may be shorter when the line count is not
    a multiple of `block_size` (136 lines at block size 3 end in a group of
    one), which every stage handles as an ordinary group.
    """
    return [lines[i:i + block_size] for i in range(0, len(lines), block_size)]


def normalize(text: str) -> str:
    """
    Casefolded text with the apostrophe and quote variants unified, for
    locating a model-reported noun inside its line: the model may echo
    `dell'` as `dell’` (or vice versa) and may change the case of a name,
    neither of which should make a genuine match fail.
    """
    return text.translate(str.maketrans("’‘`´", "''''")).lower()


def find_verbatim(noun: str, line: str) -> str | None:
    """
    The substring of `line` that `noun` names, spelled as the line spells
    it - the surface form actually written to the TSV - or None when the
    model's noun does not occur in the line at all.

    Slicing the line rather than trusting the reply is what keeps the
    output verbatim: a model that normalizes `Iulio` to `Giulio`, or
    invents a name outright, produces no match and the whole reply is
    regenerated.
    """
    pos = normalize(line).find(normalize(noun))
    if pos < 0:
        return None
    return line[pos:pos + len(noun)]


# ============================================================================
# Extraction (one LLM call per group of consecutive Italian lines)
# ============================================================================

class LineRow(NamedTuple):
    """One row of output: an Italian line and its proper nouns."""
    line: ItalianLine
    nouns: List[str]


# The prompt carries the three decisions the mechanical checks then enforce:
# names only (not the entity behind a periphrasis), the line's own spelling
# (so every noun can be found in its line), and the output file's own row
# format (so a valid reply needs no conversion).
PROMPT_TEMPLATE = """Below are {n} consecutive line(s) of the Italian text of Dante's Divine Comedy,
each prefixed by its line number in the canto.

For each line, list the proper nouns it contains, in the order they occur.

What counts as a proper noun (collect these):
- names of people, mythological or biblical figures, and deities (e.g. "Virgilio", "Beatrice", "Giove")
- names of peoples, families and factions (e.g. "Troiani", "Ghibellin")
- place names: cities, regions, countries, rivers, mountains, realms of the afterlife
  (e.g. "Fiorenza", "Arno", "Inferno" when used as the name of the place)
- names of stars, planets and constellations, and titles of books or works

What is NOT a proper noun (never collect these):
- a periphrasis, epithet or metaphor standing for a named person, even when it
  clearly refers to one (e.g. "il maestro", "quel savio gentil", "colui che ...",
  "'l mio duca"). This task collects names only, not entities.
- common nouns that merely happen to be capitalized (line-initial capitals, or
  words capitalized for emphasis), and pronouns of any kind

Spell every noun exactly as the line spells it (same letters, same accents and
apostrophes, same capitalization), so it can be found in the line verbatim. Give
a multi-word name as one entry ("Santo Spirito"); list nothing for a line that
has no proper noun.

Italian lines:
{numbered}

Output exactly {n} row(s), one per Italian line above, in the order shown. Each row is
that line's number followed by the nouns found in it, all separated by TAB characters
(e.g. "7<TAB>Virgilio<TAB>Roma" for a line with two, "8" alone for a line with none).
Output nothing else: no header, no commentary, no code fence, no empty rows."""


class BlockClient(Client):
    """
    The run's LLM client, with this script's mechanical checks folded into
    the retry loop `llm7shi.Client` already runs: `should_retry` first lets
    the base class apply its plain-text quality checks, then parses the
    reply as TSV rows and validates them against the group's Italian lines
    (see validate_group), so a malformed row, a wrong line number or a
    hallucinated noun is regenerated the same way an empty reply is - there
    is no second retry loop of this script's own.

    The group being asked about is state rather than an argument, since
    `should_retry`'s signature is fixed: `extract_group` sets `lines`
    before the call and reads `rows` after it (None when no reply
    validated, with `problem` describing the last failure).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lines: List[ItalianLine] = []  # the group of the call in flight
        self.rows: List[List[str]] | None = None  # its per-line surface forms
        self.problem = ""  # why the last rejected reply was rejected

    def should_retry(self, resp, schema=None) -> str | None:
        # None-out first: the attributes describe the reply being judged
        # right now, and a caller reading them after a failed call must not
        # see an earlier attempt's rows
        self.rows, self.problem = None, ""
        reason = super().should_retry(resp, schema)  # empty/truncated/repetitive reply first
        if reason is not None:
            self.problem = reason
            return reason
        self.rows, self.problem = validate_group(resp.text, self.lines)
        return self.problem or None


def validate_group(text: str,
                   lines: List[ItalianLine]) -> Tuple[List[List[str]], str] | Tuple[None, str]:
    """
    Parse the model's TSV reply and check it mechanically against the
    group's lines, turning it into per-line surface forms. Returns (rows,
    "") when valid, else (None, description of the first problem found).

    Checks: one row per line, each starting with that line's own number, in
    the group's order; every noun non-empty and occurring verbatim in its
    line. A Markdown code fence around the rows is tolerated (it carries no
    data); duplicates within a line are dropped, keeping the first
    occurrence.
    """
    expected = [line.line_num for line in lines]
    got: List[int] = []
    fields: List[List[str]] = []
    for row in text.strip().splitlines():
        row = row.strip()
        if not row or row.startswith('```'):
            continue
        number, *nouns = (field.strip() for field in row.split('\t'))
        if not number.isdigit():
            return None, f"row {row!r} does not start with a line number"
        got.append(int(number))
        fields.append(nouns)
    if got != expected:
        return None, f"line numbers {got} do not match the group's lines {expected}"

    rows: List[List[str]] = []
    for line, found in zip(lines, fields):
        nouns: List[str] = []
        for noun in found:
            if not noun:
                return None, f"line {line.line_num}: empty proper noun"
            verbatim = find_verbatim(noun, line.full_text)
            if verbatim is None:
                return None, (f"line {line.line_num}: proper noun {noun!r} does not occur in "
                              f"the line {line.full_text!r}")
            if verbatim not in nouns:
                nouns.append(verbatim)
        rows.append(nouns)
    return rows, ""


def extract_group(ui: StatusLine, client: BlockClient, lines: List[ItalianLine],
                  index: int, total: int) -> List[List[str]] | None:
    """
    Ask the LLM for the proper nouns of one group of consecutive Italian
    lines. `index`/`total` are this group's position among the canto's
    pending groups. Returns one list of surface forms per line (possibly
    empty), or None
    when the call fails or no reply validated - the caller then writes
    nothing for the group, leaving its lines for a later run. The reply is
    plain TSV rows, parsed and checked inside the client (see BlockClient),
    which retries against these very lines.

    `client` is the run's single BlockClient, built with
    `keep_history=False`: every group is an independent single-shot Q&A, so
    nothing carries over between calls and one client serves the whole run.
    """
    n = len(lines)
    numbered = '\n'.join(f"{line.line_num} {line.full_text}" for line in lines)
    prompt = PROMPT_TEMPLATE.format(n=n, numbered=numbered, y="y" if n == 1 else "ies")

    ui.log("")
    notify(ui, f"Group {index}/{total}: line(s) {line_range(lines)}")
    for line in lines:
        log_print(f"  {line.line_num} {line.full_text}")

    # `ui.log("")` is the session-boundary blank line ahead of the call;
    # `ui.stream.end()` flushes the streamed reply's trailing partial line
    # once it lands.
    client.lines = lines
    call_started = time.monotonic()
    ui.log("")
    try:
        client(prompt)
    except Exception as e:
        ui.stream.end()
        notify(ui, f"  ✗ LLM call failed after {time.monotonic() - call_started:.1f}s: {e}",
              error=True)
        return None
    ui.stream.end()
    elapsed = time.monotonic() - call_started

    rows = client.rows
    if rows is None:
        notify(ui, f"  ✗ no valid reply ({elapsed:.1f}s): {client.problem}", error=True)
        return None

    log_print(f"  ✓ accepted ({elapsed:.1f}s)")
    for line, nouns in zip(lines, rows):
        log_print(f"    {line.line_num}: {nouns}")
    return rows


# ============================================================================
# TSV I/O (variable-length rows, a missing row = not processed yet)
# ============================================================================

def format_row(line: ItalianLine, nouns: List[str]) -> str:
    """`line_number<TAB>noun<TAB>noun...`, the number alone when there is none."""
    return '\t'.join([str(line.line_num), *nouns])


def append_rows(texts: List[str], path: Path):
    """
    Append one group's rows to the file, keeping what is already there -
    the normal write, since groups are processed in line order and a run
    usually extends the file at its end.
    """
    with open(path, 'a', encoding='utf-8') as f:
        for text in texts:
            f.write(text + '\n')


def rewrite_tsv(rows: dict, path: Path):
    """
    Rewrite the whole file in line order - what a group filling a gap left
    by an earlier failure (or a hand-deleted row) needs, since appending
    its rows would leave the file out of line order. Sortedness is worth
    this much because the file is meant to be read and diffed as a table,
    not just consumed by this script.
    """
    with open(path, 'w', encoding='utf-8') as f:
        for line_num in sorted(rows):
            f.write(rows[line_num] + '\n')


def load_tsv(ui: StatusLine, path: Path,
             italian_lines: List[ItalianLine]) -> Tuple[dict, bool] | None:
    """
    Load an existing `<NN>.tsv` as a {line number: row} mapping plus a flag
    saying whether the file is already sorted by line number (an unsorted
    file - hand-edited, say - is put back in order by the first group that
    writes). Rows may be missing: those lines are simply not processed yet,
    which is the whole resume mechanism. Every row present must carry a
    line number of this canto, and no number twice; anything else means the
    file does not belong to this canto, so the run stops rather than
    appending to it. Returns None (after reporting) on a mismatch.
    """
    rows: dict = {}
    order: List[int] = []
    for row_num, text in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not text.strip():
            continue  # a stray blank line carries no data; drop it on rewrite
        field = text.split('\t')[0]
        if not field.isdigit() or not 1 <= int(field) <= len(italian_lines):
            notify(ui, f"✗ {path} row {row_num}: {field!r} is not a line number of this "
                  f"canto (1-{len(italian_lines)}) - delete the file to regenerate", error=True)
            return None
        line_num = int(field)
        if line_num in rows:
            notify(ui, f"✗ {path} row {row_num}: line {line_num} appears twice - "
                  f"delete the file to regenerate", error=True)
            return None
        rows[line_num] = text
        order.append(line_num)
    return rows, order == sorted(order)


# ============================================================================
# Pipeline driver
# ============================================================================

def run_canto(args: argparse.Namespace, ui: StatusLine, client: BlockClient, italian_lines: List[ItalianLine],
              tsv_path: Path, rows: dict, in_order: bool, prog=None) -> List[LineRow]:
    """
    Extract every line that has no row yet - every line when `rows` is
    empty (the file does not exist yet) - keeping every row already on
    disk. The lines are asked about in groups: each `--block-size` block's
    missing lines, split into contiguous runs (see pending_groups), so a
    rerun re-asks only what is missing rather than whole blocks. Each group
    is written out as it completes: appended when its lines follow
    everything in the file, and otherwise (a group filling a gap, or a file
    that was not sorted to begin with) written as a full rewrite in line
    order. A group whose answer never validates writes nothing and the run
    moves on: its lines stay missing, and a later run retries just them.
    """
    log_print("=" * 80)
    log_print("EXTRACT: Italian line -> proper nouns")
    log_print("=" * 80)
    log_print(f"Block size: {args.block_size}, Test: {args.test}")
    log_print()

    groups = pending_groups(italian_lines, rows, args.block_size)
    if args.test:
        groups = groups[:1]
    log_print(f"{len(groups)} group(s) to extract, "
              f"{len(rows)}/{len(italian_lines)} line(s) already on disk")
    log_print()

    done = 0
    skipped = 0
    total_groups = len(groups)
    # Highest line number in the file as written, so a group can tell
    # "extends the file" (append) from "fills a gap" (rewrite)
    disk_max = max(rows, default=0)
    for index, group in enumerate(groups, 1):
        if prog is not None:
            # Bar numerator walks the canto's Dante lines (ARCHITECTURE.md
            # §4): advanced to this group's first Italian line.
            prog.update(group[0].line_num)
        nums = [line.line_num for line in group]

        group_rows = extract_group(ui, client, group, index, total_groups)
        if group_rows is None:
            notify(ui, f"✗ Group {index}/{total_groups} left unwritten; rerun to retry", error=True)
            skipped += 1
            log_print()
            continue

        texts = [format_row(line, nouns) for line, nouns in zip(group, group_rows)]
        rows.update(zip(nums, texts))
        # Written per group rather than once at the end: an interrupted run
        # then leaves a file that is correct as far as it goes, and the next
        # run picks up exactly where it stopped.
        if in_order and nums[0] > disk_max:
            append_rows(texts, tsv_path)
        else:
            rewrite_tsv(rows, tsv_path)
            in_order = True
        disk_max = max(rows)
        done += 1
        log_print()

    # Report from `rows`, not from what this run extracted: the coverage
    # figure is about the file as it now stands, kept rows included.
    out = [LineRow(line, rows[line.line_num].split('\t')[1:])
           for line in italian_lines if line.line_num in rows]
    n_nouns = sum(len(row.nouns) for row in out)

    log_print("-" * 80)
    log_print("Results")
    log_print("-" * 80)
    for row in out:
        if row.nouns:
            log_print(f"{row.line.line_num}: {row.nouns}")
    log_print()
    log_print(f"Coverage: {len(out)}/{len(italian_lines)} lines, {n_nouns} proper noun(s)")
    log_print()

    suffix = f" ({done} group(s) extracted)" if done else ""
    tail = f"; {skipped} group(s) left unwritten - rerun to retry" if skipped else ""
    notify(ui, f"✓ Complete: {len(out)}/{len(italian_lines)} lines, {n_nouns} proper noun(s)"
          f"{suffix}{tail}")
    return out


def extract_canto(canticle: str, canto: int, args: argparse.Namespace, n_cantos: int,
                  ui: StatusLine, client: BlockClient) -> None:
    """
    Extract one canto of one canticle. `n_cantos` is the canticle's total
    canto count, folded into the status bar's label (`{canticle}
    {canto}/{n_cantos}`) - the bar itself carries the run position, so
    there is no separate major-separator line.

    A canto that is already complete costs one line of output and no LLM
    call; an incomplete one is resumed from its file rather than redone,
    and a file that does not check out stops this canto (the run moves on
    to the next) instead of being overwritten.
    """
    out_dir = PROPER_NOUN_DIR / canticle
    out_dir.mkdir(parents=True, exist_ok=True)
    tsv_path = out_dir / f"{canto:02d}.tsv"
    log_path = out_dir / f"{canto:02d}.log"

    global _log_file
    with open(log_path, 'w', encoding='utf-8') as log_f:
        _log_file = log_f

        log_print(f"=== {canticle.capitalize()} Canto {canto} Proper Nouns (proper_noun.py) ===")
        log_print(f"Model: {args.model}, Temperature: {args.temperature}, Think: {args.think}, "
                  f"Block size: {args.block_size}, Test: {args.test}")
        log_print()

        italian_lines = load_italian_lines(canticle, canto)

        rows: dict = {}
        in_order = True
        if tsv_path.exists():
            loaded = load_tsv(ui, tsv_path, italian_lines)
            if loaded is None:
                return
            rows, in_order = loaded
            if len(rows) == len(italian_lines):
                notify(ui, f"✓ {canticle.capitalize()} {canto}/{n_cantos}: skipped "
                      f"(output file already exists, every line present)")
                return
            notify(ui, f"{len(rows)}/{len(italian_lines)} line(s) on disk - "
                  f"extracting only what is missing")

        label = f"{canticle.capitalize()} {canto}/{n_cantos}"
        with ui.progress(len(italian_lines), label=label, dual=True) as prog:
            run_canto(args, ui, client, italian_lines, tsv_path, rows, in_order, prog)

    ui.log(f"✓ Proper nouns: {tsv_path}")
    ui.log(f"✓ Log: {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract proper nouns from the Italian text, one row per processed line "
                    "(variable-length TSV, one LLM call per group of consecutive lines)")
    parser.add_argument("canticles", nargs="+", choices=["inferno", "purgatorio", "paradiso"],
                        help="Cantica name(s)")
    parser.add_argument("-c", "--canto", help=dante_corpus.api.CANTO_SPEC_HELP)
    parser.add_argument("-m", "--model", default="ollama:ministral-3:14b", help="LLM model to use")
    parser.add_argument("--temperature", type=float, default=1.0, help="LLM temperature (default: 1.0)")
    parser.add_argument("--think", action="store_true", help="Enable LLM thinking (disabled by default)")
    parser.add_argument("-b", "--block-size", type=int, default=DEFAULT_BLOCK_SIZE,
                        help=f"Number of Italian lines per LLM call (default: {DEFAULT_BLOCK_SIZE}); "
                             f"a rerun asks about at most this many, and only missing lines")
    parser.add_argument("--test", action="store_true",
                        help="Process only the first pending group, for a quick local smoke test")

    args = parser.parse_args()

    if err := dante_corpus.api.check_canto_spec(args.canticles, args.canto):
        parser.error(err)
    if args.block_size < 1:
        parser.error("--block-size must be at least 1")

    ui = StatusLine()
    # One client for the whole run: with `keep_history=False` each call is an
    # independent single-shot Q&A, so there is no state to reset between
    # groups, cantos, or retries - and its retry loop, extended in
    # BlockClient, is the only retry mechanism in the script.
    client = BlockClient(model=args.model, include_thoughts=args.think, temperature=args.temperature,
                         file=ui.stream, show_params=False, keep_history=False)
    for canticle in args.canticles:
        n_cantos = len(dante_corpus.api.cantos(canticle))
        for canto in dante_corpus.api.select_cantos(canticle, args.canto):
            extract_canto(canticle, canto, args, n_cantos, ui, client)


if __name__ == '__main__':
    main()
