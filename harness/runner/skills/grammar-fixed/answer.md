### The answer: the whole unit's rows, every time

Finish with one `<rows>` block holding the analysis you stand behind, as tab-separated columns in this order:

    line	token	word	role	arg_line	arg_token

For example:

    <rows>
    1	3	trovai	subj	0	0
    1	3	trovai	obl:in	2	2
    </rows>

Rules for that block, all of them mechanical:

- Submit **every row of the unit**, not just the ones you changed. The block replaces the analysis on record in full: a row you leave out is a row you have deleted.
- One row per (predicate, argument) pair. A predicate with no argument at all takes a single row with an empty role and `0 0` as its argument.
- Coordinates are integers; `word` may be left empty, but keep the column (two tabs in a row) so every line has six fields.
- Nothing but rows inside the block, and exactly one block. Put your reasoning before it, in prose.

Your rows are checked automatically the moment you send them, and you may be asked again with what the check found. A request that comes back with the same evidence and a list of points is not a new unit: it is this one, still open. Change what the points concern and what your own reading no longer supports, keep the rest, and send the whole unit again.
