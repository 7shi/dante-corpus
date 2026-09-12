# StatusLine: Progress Display in proper_noun.py

`proper_noun.py`'s progress display follows dante-corpus's `ARCHITECTURE.md`
§4 ("Live-run observability"), mirroring the pattern used by dante-corpus's
`skel/skel.py` (specifically `skel/driver_build.py`). This note records the
design so a future change (or a similar script elsewhere in this repo) can
follow the same shape without re-deriving it.

## Model calls and progress display

`proper_noun.py` calls the model through `BlockClient`, a thin
`llm7shi.Client` subclass, and drives an `llm7shi.statusline.StatusLine`
(`ui`) for the whole run, giving a live Rich progress bar per canto plus a
single console every human-facing line and every streamed model reply
shares.

`llm7shi.Client` provides:

- A `file=` sink for streaming model output, which is exactly the hook
  `StatusLine` needs to keep streamed text from clobbering the live bar
  (`BlockClient(..., file=ui.stream)`).
- Its own quality-retry loop (empty replies, repetition).

`BlockClient.should_retry` extends that loop rather than wrapping it: it
first lets the base class's checks run, then parses the reply as TSV and
validates it against the group's Italian lines (`validate_group`), so a
malformed row, a wrong line number or a hallucinated noun is regenerated the
same way an empty reply is. There is deliberately no second, script-level
retry loop - unlike a pipeline whose own checks (e.g. range validity, word-
multiset equality) can't be expressed inside `should_retry`, every check
this script needs fits inside that one override.

## `StatusLine` wiring, mirroring `skel/driver_build.py`

- **One `StatusLine` for the whole run** (`ui = StatusLine()` in `main()`),
  not one per canto. It is threaded through every function that needs to
  print or call the model, as a `ui: StatusLine` parameter.
- **One `BlockClient` for the whole run, not a fresh one per attempt.** With
  `keep_history=False` every call is already an independent single-shot
  Q&A, so a reused client costs nothing extra and building one avoids
  reconstructing it per group; `main()` builds it once and passes it down
  to every canto and group. `ui.log("")` right before each call
  (`extract_group`) is the session-boundary blank line the docstring
  ascribes to constructing a fresh `Client` in the driver pattern - here it
  plays the same spacing role ahead of a call on the shared client instead.
  `ui.stream.end()` right after the call flushes the streamed reply's
  trailing partial line.
- **One progress bar per canto**, opened with
  `ui.progress(len(italian_lines), label=f"{canticle.capitalize()}
  {canto}/{n_cantos}", dual=True)` and closed automatically at the end of
  `extract_canto`'s `with` block. `n_cantos` is the canticle's *total* canto
  count (`len(dante_corpus.api.cantos(canticle))`), not the number of
  cantos selected for this run - so the label reads e.g. `Inferno 5/34`
  even when invoked as `-c 5-10`. This folds the "which canto, out of how
  many" fact straight into the bar's label instead of a separate
  `[index/total]` separator line.
- **The bar's numerator walks the canto's Italian lines** (ARCHITECTURE.md
  §4's "Canticle Canto Line" convention): `run_canto` calls
  `prog.update(group[0].line_num)` with the first Italian line number of
  the group about to be extracted.
- **`dual=True` gives two different clocks**: the left column
  (`ProcessElapsedColumn`, beside the label) reads from this process's own
  start time (`_PROCESS_START`, a module-level constant), so it is the
  whole run's elapsed time end to end - unlike the driver pattern in
  ARCHITECTURE.md §4, this script needs no `--started-at` threaded in from
  a wrapping Makefile, since one process already handles every canticle and
  canto of the run. The right column (`ElapsedColumn(self._started_at,
  monotonic=True)`, after the bar) reads from `self._started_at`, which
  `ProgressContext.__init__` fills in fresh with `time.monotonic()` each
  time `extract_canto` opens a new `ui.progress(...)` block - so it is this
  canto's own elapsed time, restarting every canto.
- **No separate stderr stream.** `StatusLine`'s `Console()` defaults to
  stdout; forcing progress text to stderr would just split one run's output
  across two streams for no benefit here (there is no JSONL log or other
  machine-readable stdout this needs to stay clean of). All human-facing
  output - the bar, streamed model replies, and this script's own messages
  - shares the one console.

## The `notify()` helper

```python
def notify(ui: StatusLine, text: str, error: bool = False) -> None:
    (ui.stream.error if error else ui.log)(text)
    log_print(text)
```

`ui.log()` prints a normal line that coexists with the active bar;
`ui.stream.error()` does the same in red, for retries/failures.
`log_print()` is `proper_noun.py`'s own pre-existing per-canto trace file
(`<NN>.log`, unrelated to `StatusLine`) - `notify()` keeps writing to both.
