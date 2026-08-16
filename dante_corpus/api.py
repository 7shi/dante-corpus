import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property

from . import case as _case
from . import dep as _dep
from . import hashes as _hashes
from . import morph as _morph
from . import np as _np
from . import skel as _skel
from ._paths import SRC_DIR, QUOTES_DIR
from .tokenizer import has_alpha, tokenize

MorphRow = _morph.MorphRow
CaseRow = _case.CaseRow
NPSpan = _np.NPSpan
DepRow = _dep.DepRow
SkelArg = _skel.SkelArg
SkelTuple = _skel.SkelTuple

VALID_CANTICLES = ("inferno", "purgatorio", "paradiso")
REF_RE = re.compile(
    r"^(?P<canticle>inferno|purgatorio|paradiso)\s+"
    r"(?P<canto>\d+)"
    r"(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$"
)


def _check_canticle(canticle: str) -> str:
    if canticle not in VALID_CANTICLES:
        raise ValueError(f"unknown canticle: {canticle}")
    return canticle


def _it_canticle_dir(canticle: str):
    return SRC_DIR / _check_canticle(canticle)


def _canto_base_path(canticle: str, number: int):
    return _it_canticle_dir(canticle) / f"{number:02d}"


@dataclass(frozen=True)
class Line:
    no: int
    text: str

    @cached_property
    def tokens(self) -> tuple[str, ...]:
        return tuple(token for token in tokenize(self.text) if has_alpha(token))

    def to_dict(self) -> dict[str, object]:
        return {"no": self.no, "text": self.text, "tokens": list(self.tokens)}


@dataclass(frozen=True)
class QuoteSpan:
    quote_id: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    marker: str
    head: str | None
    children: tuple["QuoteSpan", ...]

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.quote_id,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_col": self.start_col,
            "end_col": self.end_col,
            "marker": self.marker,
            "children": [child.to_dict() for child in self.children],
        }
        if self.head is not None:
            data["head"] = self.head
        return data


@dataclass(frozen=True)
class Canto:
    canticle: str
    number: int
    _lines: tuple[Line, ...]

    def line(self, number: int) -> Line:
        if not 1 <= number <= len(self._lines):
            raise ValueError(f"line out of range: {number}")
        return self._lines[number - 1]

    def lines(self, start: int = 1, end: int | None = None) -> tuple[Line, ...]:
        if end is None:
            end = len(self._lines)
        if not (1 <= start <= end <= len(self._lines)):
            raise ValueError(f"invalid line range: {start}-{end}")
        return self._lines[start - 1 : end]

    @cached_property
    def _quotes(self) -> tuple[QuoteSpan, ...]:
        return load_quotes(self.canticle, self.number)

    def quotes(self) -> tuple[QuoteSpan, ...]:
        return self._quotes

    def morph(self) -> dict[int, tuple[MorphRow, ...]]:
        """Frozen Layer-2 morphology: line-number -> per-token MorphRows (no model call)."""
        return _morph.load_morph(self.canticle, self.number)

    def case(self) -> dict[int, tuple[CaseRow, ...]]:
        """Frozen pronoun case (the Layer-2 annex): line-number -> CaseRows (no model call).

        Sparse — only pronoun-POS tokens carry a row, so a line without one has no key."""
        return _case.load_case(self.canticle, self.number)

    def np(self) -> tuple[NPSpan, ...]:
        """Frozen Layer-3 noun phrases as a nested forest, ordered by (line, start, -end).

        Each span carries its line, token range, head index, verbatim text, a derived id, and
        its nested children (no model call)."""
        return _np.nest_canto(self.canticle, self.number)

    def dep(self) -> dict[int, tuple[DepRow, ...]]:
        """Frozen Layer-4 dependencies: line-number -> per-token DepRows (no model call)."""
        return _dep.load_dep(self.canticle, self.number)

    def skel(self) -> tuple[SkelTuple, ...]:
        """Frozen Layer-5 predicate-argument skeleton: grouped, identified tuples, ordered by
        (line, token) (no model call)."""
        return _skel.tuples_canto(self.canticle, self.number)

    def hashes(self) -> dict[str, str]:
        """Content hash (sha256) of every layer artifact that exists for this canto, keyed by
        layer name (`text`/`morph`/`np`/`dep`/`skel`/`case`). See PLAN.md "Versioning"."""
        return _hashes.canto_hashes(self.canticle, self.number)

    def to_dict(self) -> dict[str, object]:
        return {
            "canticle": self.canticle,
            "canto": self.number,
            "lines": [line.to_dict() for line in self._lines],
        }


def canticles() -> tuple[str, ...]:
    return tuple(name for name in VALID_CANTICLES if (_it_canticle_dir(name)).exists())


def cantos(canticle: str) -> tuple[int, ...]:
    """Canto numbers present in `src/<canticle>/`.

    Raises `FileNotFoundError` when the canticle has no source cantos at all — an unbuilt `src/`
    tree is a missing prerequisite, not an empty corpus. Every caller is a build or `--check`
    driver that iterates the result, so returning `()` here would make them report success without
    having examined anything. Use `canticles()` to probe which canticles are present.
    """
    directory = _it_canticle_dir(canticle)
    paths = sorted(directory.glob("[0-9][0-9].txt"))
    if not paths:
        raise FileNotFoundError(
            f"no source cantos under {directory} — run `make -C src` to build the source tree"
        )
    return tuple(int(path.stem) for path in paths)


# The one `-c` help string every build driver shows, so the selection syntax is documented
# identically in `morph.py --help` and `skel.py --help`.
CANTO_SPEC_HELP = ("limit to these cantos: N, N-M, N- (from N on), -M (up to M), "
                   "or a comma-separated mix, e.g. 12- / -20 / 11-20 / 1,5,7 / 1,3-5,11-")


def parse_canto_spec(spec: str) -> tuple[tuple[int | None, int | None], ...]:
    """Parse a build driver's `-c` selection into inclusive `(start, end)` bounds.

    The grammar is one comma-separated list of `N`, `N-M`, `N-` (open end) and `-M` (open start):
    `12-`, `-20`, `11-20`, `1,5,7`, `1,3-5,11-`. `None` on either side means unbounded, so the
    bound is resolved against whichever cantos the canticle actually has — a spec is a filter,
    never an assertion that a numbered canto exists.

    Raises `ValueError` with a message naming the offending item; callers that are argparse-driven
    pass it to `parser.error` (see `check_canto_spec`).
    """
    ranges: list[tuple[int | None, int | None]] = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            raise ValueError(f"empty canto range in {spec!r}")
        head, dash, tail = item.partition("-")
        head, tail = head.strip(), tail.strip()
        if not dash:
            if not head.isdigit():
                raise ValueError(f"not a canto number: {item!r}")
            ranges.append((int(head), int(head)))
            continue
        if not head and not tail:
            raise ValueError(f"canto range with no bound: {item!r}")
        if (head and not head.isdigit()) or (tail and not tail.isdigit()):
            raise ValueError(f"not a canto range: {item!r}")
        start = int(head) if head else None
        end = int(tail) if tail else None
        if start is not None and end is not None and start > end:
            raise ValueError(f"canto range runs backwards: {item!r}")
        ranges.append((start, end))
    return tuple(ranges)


def select_cantos(canticle: str, spec: str | None) -> tuple[int, ...]:
    """The cantos of `canticle` a `-c` spec selects, in canto order; all of them when `spec` is
    `None`. Raises `ValueError` for an unparsable spec, or for one that matches no canto at all —
    a selection that would silently do nothing is a typo, not a no-op run."""
    available = cantos(canticle)
    if spec is None:
        return available
    ranges = parse_canto_spec(spec)
    selected = tuple(
        n for n in available
        if any((start is None or n >= start) and (end is None or n <= end)
               for start, end in ranges)
    )
    if not selected:
        raise ValueError(f"no canto of {canticle} matches {spec!r} "
                         f"(it has {available[0]}-{available[-1]})")
    return selected


def check_canto_spec(canticles: Iterable[str], spec: str | None) -> str | None:
    """Validate a `-c` spec against every canticle a run names, up front: the message to hand to
    `parser.error`, or `None` when the spec is good. Build drivers call this before doing any
    work, so a typo fails at the command line instead of part-way through a canticle."""
    if spec is None:
        return None
    for canticle in canticles:
        try:
            select_cantos(canticle, spec)
        except ValueError as exc:
            return str(exc)
    return None


def _load_lines(canticle: str, number: int) -> tuple[Line, ...]:
    path = _canto_base_path(canticle, number).with_suffix(".txt")
    if not path.exists():
        raise FileNotFoundError(path)
    lines = [
        Line(no=index, text=raw)
        for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if raw.strip()
    ]
    return tuple(lines)


def canto(canticle: str, number: int) -> Canto:
    _check_canticle(canticle)
    return Canto(
        canticle=canticle,
        number=number,
        _lines=_load_lines(canticle, number),
    )


def _parse_line_attr(value: str) -> tuple[int, int]:
    if "-" in value:
        start, end = value.split("-", 1)
        return int(start), int(end)
    point = int(value)
    return point, point


def _parse_col_attr(value: str) -> tuple[int, int]:
    start, end = value.split("-", 1)
    return int(start), int(end)


def _parse_quote_node(node: ET.Element) -> QuoteSpan:
    start_line, end_line = _parse_line_attr(node.attrib["line"])
    start_col, end_col = _parse_col_attr(node.attrib["col"])
    return QuoteSpan(
        quote_id=node.attrib["id"],
        start_line=start_line,
        end_line=end_line,
        start_col=start_col,
        end_col=end_col,
        marker=node.attrib["marker"],
        head=node.attrib.get("head"),
        children=tuple(_parse_quote_node(child) for child in node.findall("q")),
    )


def load_quotes(canticle: str, number: int) -> tuple[QuoteSpan, ...]:
    path = QUOTES_DIR / f"{_check_canticle(canticle)}.xml"
    if not path.exists():
        raise FileNotFoundError(path)
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    canto_node = root.find(f"./canto[@n='{number}']")
    if canto_node is None:
        raise ValueError(f"canto {number} not found in {path}")
    return tuple(_parse_quote_node(node) for node in canto_node.findall("q"))


def quote_xml(canticle: str, number: int) -> str:
    path = QUOTES_DIR / f"{_check_canticle(canticle)}.xml"
    if not path.exists():
        raise FileNotFoundError(path)
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    canto_node = root.find(f"./canto[@n='{number}']")
    if canto_node is None:
        raise ValueError(f"canto {number} not found in {path}")
    return ET.tostring(canto_node, encoding="unicode")


def ref(spec: str) -> tuple[Line, ...]:
    match = REF_RE.fullmatch(spec.strip())
    if not match:
        raise ValueError(f"invalid reference: {spec}")

    selected_canto = canto(match.group("canticle"), int(match.group("canto")))
    start_text = match.group("start")
    if start_text is None:
        return selected_canto.lines()
    end_text = match.group("end")
    start = int(start_text)
    end = int(end_text) if end_text is not None else start
    return selected_canto.lines(start, end)
