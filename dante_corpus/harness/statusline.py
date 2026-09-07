"""Rich status bar for live runner CLIs (`harness/PLAN.md` §4 item 5).

`llm7shi.statusline.StatusLine` renders a spinner + completed/total bar that
coexists with streamed LLM output on one shared Rich console (the same wiring
the `skel/` build driver uses). One adaptation keeps it useful for the harness:
every backoff passes through the stream's `wait_retry`, so counting there is the
only place the §4-item-5 measurement can see how much wall time went to retries.

The bar itself needs no subclassing. `run_started_at`, when the caller sets it
(e.g. `reconstruct.py`'s `--started-at`, exported once by `harness/recon/
Makefile` because it launches one process per canto), is handed to llm7shi as
`progress(started_at=...)`, which puts a clock for the whole run beside the label
alongside the per-process one at the far right.

Import is guarded: without the `statusline` extra `HarnessStatusLine` is None
and callers fall back to plain stderr lines.
"""

from __future__ import annotations

try:
    from llm7shi.statusline import StatusLine, StatusLineConsoleStream
except ImportError:  # pragma: no cover - rich ships via llm7shi[statusline]
    HarnessStatusLine = None
else:

    class _CountingConsoleStream(StatusLineConsoleStream):
        """Stream that keeps a tally of the time spent waiting on retries."""

        def __init__(self, console, status_line):
            super().__init__(console, status_line)
            # §4-item-5 measurement: llm7shi hides transient API failures (429
            # RESOURCE_EXHAUSTED et al.) behind automatic retries, so backoff
            # time would otherwise surface only inflated inside `turn_seconds`.
            # Every backoff passes through wait_retry on this stream — count
            # occurrences and accumulate the requested delays.
            self.api_retries = 0
            self.api_retry_seconds = 0.0

        def wait_retry(self, delay, message="Retrying..."):
            self.api_retries += 1
            try:
                self.api_retry_seconds += float(delay)
            except (TypeError, ValueError):
                pass
            super().wait_retry(delay, message)

    class HarnessStatusLine(StatusLine):
        """StatusLine whose stream counts retries, and whose bar shows the
        enclosing run's elapsed time when the caller supplies its start."""

        def __init__(self):
            super().__init__()
            self.stream = _CountingConsoleStream(self.console, self)
            # Set by the caller (e.g. reconstruct.py's --started-at) when the
            # enclosing run spans more than this process, so progress() can
            # show the run's true cumulative time next to the label.
            self.run_started_at: float | None = None

        def progress(self, total, start=0, label=None, started_at=None):
            return super().progress(total, start, label, started_at or self.run_started_at)

__all__ = ["HarnessStatusLine"]
