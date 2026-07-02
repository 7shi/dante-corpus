"""Rich-based progress display for the build-time generation scripts (e.g. morph/morph.py).

Adapted from multilingual-reader's `trtools/statusline.py`. `ConsoleStream` is imported from
`llm7shi` so the progress line logic coexists with streamed model output.

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

from llm7shi import ConsoleStream

_PROCESS_START = time.monotonic()


class _MofNColumn(ProgressColumn):
    """`completed/total` — here line-number / lines-in-canto.

    A task may override the numerator via the `remaining` field (e.g. the retry
    countdown, where the bar fills forward but the number counts down).
    """

    def render(self, task) -> Text:
        n = int(task.total) if task.total is not None else "?"
        numerator = task.fields.get("remaining", task.completed)
        return Text(f"{int(numerator)}/{n}", style="progress.download")


class _ProcessElapsedColumn(ProgressColumn):
    """Elapsed time since process start (not since this task was added).

    Suppressed for tasks with `show_elapsed=False` (e.g. the retry countdown row),
    since it would duplicate the elapsed time already shown on the main progress line.
    """

    def render(self, task) -> Text:
        if not task.fields.get("show_elapsed", True):
            return Text("")
        elapsed = time.monotonic() - _PROCESS_START
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        text = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        return Text(text, style="progress.elapsed")


class StatusLineConsoleStream(ConsoleStream):
    def __init__(self, console, status_line: "StatusLine"):
        super().__init__(console)
        self.status_line = status_line

    def print(self, text: str, end: str = "\n") -> None:
        self._console.print(text, end=end, highlight=False)

    def wait_retry(self, delay: int, message: str = "Retrying...") -> None:
        import time
        width = len(str(delay))
        if self.status_line.active_progress is not None:
            progress = self.status_line.active_progress
            task = progress.add_task(
                f"[red]{message}", total=delay, completed=0, remaining=delay, show_elapsed=False
            )
            with progress._lock:
                progress._tasks = {task: progress._tasks.pop(task), **progress._tasks}
            try:
                for i in range(delay, -1, -1):
                    progress.update(task, completed=delay - i, remaining=i)
                    if i == 0:
                        break
                    time.sleep(1)
            finally:
                progress.remove_task(task)
        else:
            for i in range(delay, -1, -1):
                self.print(f"\r{message} {i:>{width}}s", end="")
                if i == 0:
                    break
                time.sleep(1)
            self.print("", end="\n")

    def error(self, text: str) -> None:
        self._console.print(f"[red]{text}")


class StatusLine:
    def __init__(self):
        self.console = Console()
        self.stream = StatusLineConsoleStream(self.console, self)
        self.active_progress = None

    def write(self, text: str) -> None:
        self.stream.write(text)

    def log(self, text: str) -> None:
        """Print a full status line that coexists with an active progress bar."""
        self.console.print(text, highlight=False)

    def progress(self, total: int, start: int = 0, label: str | None = None) -> "_ProgressContext":
        return _ProgressContext(self, total, start, label)


class _ProgressContext:
    def __init__(self, status_line: StatusLine, total: int, completed: int, label: str | None):
        columns = [SpinnerColumn()]
        if label:
            columns.append(TextColumn("[bold cyan]{task.description}"))
            columns.append(TextColumn("|"))
        columns += [_MofNColumn(), BarColumn(), TaskProgressColumn(), _ProcessElapsedColumn()]

        self._status_line = status_line
        self._progress = Progress(*columns, console=status_line.console)
        self._total = total
        self._completed = completed
        self._label = label
        self._task = None

    def __enter__(self):
        self._status_line.active_progress = self._progress
        self._progress.__enter__()
        self._task = self._progress.add_task(
            self._label or "", total=self._total, completed=self._completed
        )
        return self

    def __exit__(self, *args):
        self._status_line.active_progress = None
        return self._progress.__exit__(*args)

    def update(self, completed: int) -> None:
        self._progress.update(self._task, completed=completed)

