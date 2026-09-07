"""Layer 5's binding of the apparatus's fixed-context loop.

The loop is `dante_corpus.harness.fixedcontext`, which sends $P + O + \\Sigma$,
reads rows back and stops on a fixed point without knowing what a row means.
Layer 5 supplies the four things it does not know:

| the loop asks for | Layer 5 gives |
|---|---|
| $P$ | `runner/prompts.py` `fixed_system_prompt` (the `grammar-fixed` skill) |
| the evidence and the schema gate | `runner/tools.py` `GrammarToolkit` |
| the verdict | `observe.py` `SkelObserver` |
| the row facts | `layers.py` `SKEL_CODEC` |

Binding them here keeps `run_unit_fixed` and `fixed_fallback` callable with the
arguments the pipeline and the tests have always passed.
"""

from __future__ import annotations

from typing import Callable, Sequence

from dante_corpus.harness import fixedcontext as _fixedcontext
from dante_corpus.harness.fixedcontext import (
    MAX_ITERATIONS,
    FixedUnitResult,
    IterationRecord,
    Observer,
    parse_rows,
    render_sigma,
    unit_message,
    _ROWS_BLOCK,
    _TSV_HEADER,
)
from dante_corpus.harness.rows import Row

from harness.extractor.layers import SKEL_CODEC
from harness.extractor.observe import SkelObserver
from harness.runner.prompts import fixed_system_prompt

__all__ = [
    "MAX_ITERATIONS",
    "FixedUnitResult",
    "IterationRecord",
    "Observer",
    "fixed_fallback",
    "parse_rows",
    "render_sigma",
    "rows_from_skel",
    "run_unit_fixed",
    "unit_message",
    "verdict_block",
]


def rows_from_skel(rows_by_line: dict[int, list[Row]] | None) -> list[dict]:
    """Candidate-row dicts for the artifact's own `SkelRow`s (the `--fix` $\\Sigma_0$)."""
    return _fixedcontext.rows_from_skel(rows_by_line, codec=SKEL_CODEC)


def verdict_block(
    *,
    schema_errors: Sequence[str],
    observations: Sequence[object],
    empty: bool,
    unparsed: bool = False,
    render: Callable[[Sequence[object]], str] | None = None,
) -> str:
    """The verdict half of $O$, rendered in Layer 5's own notices."""
    from harness.extractor.observe import render_observations

    return _fixedcontext.verdict_block(
        schema_errors=schema_errors,
        observations=observations,
        empty=empty,
        unparsed=unparsed,
        render=render_observations if render is None else render,
    )


def run_unit_fixed(**kwargs) -> FixedUnitResult:
    """`fixedcontext.run_unit_fixed` with Layer 5's prompt and observer."""
    kwargs.setdefault("system_prompt", fixed_system_prompt)
    if kwargs.get("observer") is None:
        kwargs["observer"] = SkelObserver()
    return _fixedcontext.run_unit_fixed(**kwargs)


def fixed_fallback(*, payload_tier: str = "R1", **kwargs):
    """`fixedcontext.fixed_fallback` over Layer 5's toolkit, prompt and observer.

    `clausal_registration` stays on: every answer carries the whole unit here by
    construction, which is the condition that check needs. No fix-level flag is
    passed — the level's bar is the frozen-layer observation the runtime
    recomputes each iteration (`observe.py`), not a gate the model must satisfy
    to be heard at all.
    """
    from harness.runner.tools import GrammarToolkit

    kwargs.setdefault(
        "toolkit",
        GrammarToolkit(payload_tier=payload_tier, clausal_registration=True),
    )
    kwargs.setdefault("system_prompt", fixed_system_prompt)
    if kwargs.get("observer") is None:
        kwargs["observer"] = SkelObserver()
    return _fixedcontext.fixed_fallback(**kwargs)
