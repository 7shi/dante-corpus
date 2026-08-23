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

try:
    from llm7shi.statusline import StatusLine, StatusLineConsoleStream
    from rich.text import Text

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

    class HarnessStatusLine(StatusLine):
        """StatusLine whose console lives on stderr and whose stream never
        interprets markup."""

        def __init__(self):
            super().__init__()
            self.console.file = sys.stderr
            self.stream = _PlainConsoleStream(self.console, self)

except ImportError:  # pragma: no cover - rich ships via llm7shi[statusline]
    HarnessStatusLine = None

__all__ = ["HarnessStatusLine"]
