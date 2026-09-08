"""Generation 2's layers.

`l2` is deliberately **not** re-exported here. It carries a CLI, run as
`uv run python -m layers.gen2.l2`, and a package that eagerly imports its own
runnable submodule makes `-m` warn on every invocation ("found in sys.modules …
prior to execution"). Import it as a module instead: `from layers.gen2 import l2`.
"""

from .l1 import L1Line, L1Token, l1_canto, l1_line, tokenize_l1

__all__ = [
    "L1Line",
    "L1Token",
    "l1_canto",
    "l1_line",
    "tokenize_l1",
]
