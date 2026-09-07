"""The reconstruction apparatus: the loop, the gates' shape, the artifact, the
fix machinery — all indifferent to what a row means.

`harness/` was built to reconstruct Layer 5 and, measured after Stage 10 closed,
turned out to be coupled to that layer by a *type* rather than by behaviour. This
package is the half that is indifferent. A subject supplies four things and the
apparatus supplies everything else:

| the apparatus asks for | defined in | Layer 5's |
|---|---|---|
| `RowCodec` — its row type, order and columns | `rows.py` | `layers.SKEL_CODEC` |
| `Subject` — its layers and gates 1-2 | `pipeline.py` | `layers.SKEL_SUBJECT` |
| `Criteria` — its finding levels | `fixrun.py` | the `fixlevel` module |
| `Observer` — its per-iteration verdict | `fixedcontext.py` | `observe.SkelObserver` |

All four of Layer 5's live in the repository's top-level `harness/`, which is
the driver: the CLI, gate 3's write, the toolset, the skill files and the
`recon/` artifact tree.

The rule that keeps the two apart: **nothing under `dante_corpus/harness/` may
import anything else from `dante_corpus`.** `tests/test_harness_boundary.py`
enforces it, because the coupling grows back silently otherwise.
"""

from __future__ import annotations

from .artifact import TsvArtifact, render_tsv
from .fixedcontext import (
    MAX_ITERATIONS,
    FixedUnitResult,
    IterationRecord,
    Observer,
    fixed_fallback,
    parse_rows,
    render_sigma,
    rows_from_skel,
    run_unit_fixed,
    unit_message,
    verdict_block,
)
from .fixrun import (
    Criteria,
    FixPlan,
    Span,
    Validator,
    fix_diagnosis,
    fix_summary_line,
    fix_verdict,
    plan_fix,
    refusal_note,
    revert_outcome,
    row_delta,
    salvage_by_row,
    salvage_outcome,
    salvage_rows,
)
from .llm import DEFAULT_MODEL, llm7shi_generate, token_usage
from .outcome import (
    SAMPLE_VIOLATIONS,
    CantoReconstruction,
    UnitOutcome,
    final_validation_errors,
    replay_unit_outcome,
    violation_record,
)
from .pipeline import AgentFallback, Subject, progress_separator, reconstruct_canto
from .report import ReconstructReport, load_log
from .rows import (
    ROW_FIELDS,
    PositionKey,
    Row,
    RowCodec,
    RowKey,
    Violation,
    position_key,
    row_key,
)
from .skills import Skill, SkillError
from .statusline import HarnessStatusLine

__all__ = [
    "DEFAULT_MODEL",
    "MAX_ITERATIONS",
    "ROW_FIELDS",
    "SAMPLE_VIOLATIONS",
    "AgentFallback",
    "CantoReconstruction",
    "Criteria",
    "FixPlan",
    "FixedUnitResult",
    "HarnessStatusLine",
    "IterationRecord",
    "Observer",
    "PositionKey",
    "ReconstructReport",
    "Row",
    "RowCodec",
    "RowKey",
    "Skill",
    "SkillError",
    "Span",
    "Subject",
    "TsvArtifact",
    "UnitOutcome",
    "Validator",
    "Violation",
    "final_validation_errors",
    "fix_diagnosis",
    "fix_summary_line",
    "fix_verdict",
    "fixed_fallback",
    "llm7shi_generate",
    "load_log",
    "parse_rows",
    "plan_fix",
    "position_key",
    "progress_separator",
    "reconstruct_canto",
    "refusal_note",
    "render_sigma",
    "render_tsv",
    "replay_unit_outcome",
    "revert_outcome",
    "row_delta",
    "row_key",
    "rows_from_skel",
    "run_unit_fixed",
    "salvage_by_row",
    "salvage_outcome",
    "salvage_rows",
    "token_usage",
    "unit_message",
    "verdict_block",
    "violation_record",
]
