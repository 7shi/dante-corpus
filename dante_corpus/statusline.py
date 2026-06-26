"""Rich-based progress display for the build-time generation scripts (e.g. morph/morph.py).

Adapted from multilingual-reader's `trtools/statusline.py`. `ConsoleStream` is folded in here
(dante_corpus has no `llm` module) so the whole thing is self-contained: it is a build-time UI
helper and is never imported by the runtime API.

The progress line reads, per canto:

    ⠋ inferno 1/34 | 1/136 ━━━━━━━━━ 0% 0:00:00
      └ canticle + canto/total   └ line/total (within-canto)  └ bar  └ %  └ elapsed

`StatusLine` owns one Rich `Console`; pass `ui.stream` as `generate_with_schema(file=...)` so the
model's streamed output is routed through the same console and coexists with the live bar.
"""

import time

from rich.console import Console
from rich.progress import (
    Progress, ProgressColumn, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn,
)
from rich.text import Text

_PROCESS_START = time.monotonic()


class ConsoleStream:
    """File-like wrapper for `generate_with_schema(file=...)`: buffers by line and forwards each
    completed line to a Rich console, so streamed model output coexists with a live progress bar."""

    def __init__(self, console: Console):
        self._console = console
        self._buf = ""

    def write(self, text: str) -> None:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._console.print(line, highlight=False)

    def flush(self) -> None:
        pass

    def end(self) -> None:
        """Flush any trailing partial line (no newline) after a generation finishes."""
        if self._buf.strip():
            self._console.print(self._buf, highlight=False)
        self._buf = ""


class _MofNColumn(ProgressColumn):
    """`completed/total` — here line-number / lines-in-canto."""

    def render(self, task) -> Text:
        n = int(task.total) if task.total is not None else "?"
        return Text(f"{int(task.completed)}/{n}", style="progress.download")


class _ProcessElapsedColumn(ProgressColumn):
    """Elapsed time since process start (not since this task was added)."""

    def render(self, task) -> Text:
        elapsed = time.monotonic() - _PROCESS_START
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        text = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        return Text(text, style="progress.elapsed")


class StatusLine:
    def __init__(self):
        self.console = Console()
        self.stream = ConsoleStream(self.console)

    def write(self, text: str) -> None:
        self.stream.write(text)

    def log(self, text: str) -> None:
        """Print a full status line that coexists with an active progress bar."""
        self.console.print(text, highlight=False)

    def progress(self, total: int, start: int = 0, label: str | None = None) -> "_ProgressContext":
        return _ProgressContext(self.console, total, start, label)


class _ProgressContext:
    def __init__(self, console: Console, total: int, completed: int, label: str | None):
        columns = [SpinnerColumn()]
        if label:
            columns.append(TextColumn("[bold cyan]{task.description}"))
            columns.append(TextColumn("|"))
        columns += [_MofNColumn(), BarColumn(), TaskProgressColumn(), _ProcessElapsedColumn()]

        self._progress = Progress(*columns, console=console)
        self._total = total
        self._completed = completed
        self._label = label
        self._task = None

    def __enter__(self):
        self._progress.__enter__()
        self._task = self._progress.add_task(
            self._label or "", total=self._total, completed=self._completed
        )
        return self

    def __exit__(self, *args):
        return self._progress.__exit__(*args)

    def update(self, completed: int) -> None:
        self._progress.update(self._task, completed=completed)
