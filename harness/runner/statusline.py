"""Rich status bar for live runner CLIs (`harness/PLAN.md` §4 item 5).

`llm7shi.statusline.StatusLine` renders a spinner + completed/total bar that
coexists with streamed LLM output on one shared Rich console (the same wiring
the `skel/` build driver uses). Two adaptations keep it safe for the harness:

- The console is pinned to stderr, preserving the §4-item-5 convention that the
  human-facing display never mixes with machine-facing records (JSONL logs go
  to their own `--log` files either way).
- Rich parses `[...]` as inline markup, and this corpus' vocabulary makes that
  hazardous: a role citation like `[obl:a=(126,3)]` silently disappears and a
  closing-tag fragment like `[/b]` raises MarkupError mid-stream. The stream
  therefore forwards text with markup disabled while inheriting every other
  StatusLine behavior (bar coexistence, retry-countdown rows, error styling).

Import is guarded: without the `statusline` extra `HarnessStatusLine` is None
and callers fall back to plain stderr lines.
"""

from __future__ import annotations

import sys
import time

try:
    from llm7shi.statusline import (
        StatusLine,
        StatusLineConsoleStream,
        _MofNColumn,
        _ProcessElapsedColumn,
        _ProgressContext,
    )
    from rich.progress import (
        BarColumn,
        Progress,
        ProgressColumn,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )
    from rich.text import Text

    class _ExternalElapsedColumn(ProgressColumn):
        """Elapsed time since a caller-supplied unix timestamp — the run's
        true start, when that run spans more than this process (e.g.
        `harness/recon/Makefile` launches one `reconstruct.py` process per
        canto, so `_ProcessElapsedColumn`'s per-process clock cannot show
        the make invocation's cumulative time on its own; the Makefile
        exports `STARTED_AT` once and each canto passes it through as
        `--started-at`). Unlike `_ProcessElapsedColumn`, this has no
        llm7shi counterpart to subclass against — it is genuinely local."""

        def __init__(self, started_at: float):
            super().__init__()
            self._started_at = started_at

        def render(self, task) -> Text:
            elapsed = time.time() - self._started_at
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            text = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            return Text(text, style="progress.elapsed")

    class _PlainConsoleStream(StatusLineConsoleStream):
        """Forwarded text renders as-is: no Rich markup interpretation."""

        def __init__(self, console, status_line):
            super().__init__(console, status_line)
            # §4-item-5 measurement: llm7shi hides transient API failures (429
            # RESOURCE_EXHAUSTED et al.) behind automatic retries, so backoff
            # time would otherwise surface only inflated inside `turn_seconds`.
            # Every backoff passes through wait_retry on this stream — count
            # occurrences and accumulate the requested delays.
            self.api_retries = 0
            self.api_retry_seconds = 0.0

        def print(self, text: str, end: str = "\n") -> None:
            self._console.print(text, end=end, highlight=False, markup=False)

        def error(self, text: str) -> None:
            # Text objects are markup-immune, so alerts keep their styling
            # without re-parsing whatever the model just emitted.
            self._console.print(Text(str(text), style="red"))

        def wait_retry(self, delay, message="Retrying..."):
            self.api_retries += 1
            try:
                self.api_retry_seconds += float(delay)
            except (TypeError, ValueError):
                pass
            super().wait_retry(delay, message)

    class _HarnessProgressContext(_ProgressContext):
        """`llm7shi.statusline._ProgressContext`, with an elapsed-time column
        inserted right after the label so `inferno 2 xx:xx | ...` carries a
        second clock up front, alongside llm7shi's own per-bar elapsed column
        at the far right (`_ProcessElapsedColumn`, this process's own
        clock — correct as *this canto's* elapsed since `harness/recon/
        Makefile` launches one process per canto). The label-side clock is
        `_ExternalElapsedColumn(started_at)` when the caller supplied the
        enclosing run's start time (`HarnessStatusLine.run_started_at`, e.g.
        the Makefile's `STARTED_AT` threaded through `--started-at`), so it
        reads the run's true cumulative time instead of repeating the
        per-process one; without it, it falls back to `_ProcessElapsedColumn`
        (a bare single-canto invocation has no other clock to show).
        `__enter__`/`__exit__`/`update` are unchanged from the base class;
        only the column layout built in `__init__` differs, and
        `_ProgressContext` has no smaller hook to override for that."""

        def __init__(self, status_line, total, completed, label, started_at=None):
            columns = [SpinnerColumn()]
            if label:
                columns.append(TextColumn("[bold cyan]{task.description}"))
                columns.append(
                    _ExternalElapsedColumn(started_at) if started_at is not None
                    else _ProcessElapsedColumn()
                )
                columns.append(TextColumn("|"))
            columns += [_MofNColumn(), BarColumn(), TaskProgressColumn(), _ProcessElapsedColumn()]

            self._status_line = status_line
            self._progress = Progress(*columns, console=status_line.console)
            self._total = total
            self._completed = completed
            self._label = label
            self._task = None

    class HarnessStatusLine(StatusLine):
        """StatusLine whose console lives on stderr and whose stream never
        interprets markup."""

        def __init__(self):
            super().__init__()
            self.console.file = sys.stderr
            self.stream = _PlainConsoleStream(self.console, self)
            # Set by the caller (e.g. reconstruct.py's --started-at) when the
            # enclosing run spans more than this process, so progress() can
            # show the run's true cumulative time next to the label.
            self.run_started_at: float | None = None

        def progress(self, total: int, start: int = 0, label: str | None = None):
            return _HarnessProgressContext(self, total, start, label, self.run_started_at)

except ImportError:  # pragma: no cover - rich ships via llm7shi[statusline]
    HarnessStatusLine = None

__all__ = ["HarnessStatusLine"]
