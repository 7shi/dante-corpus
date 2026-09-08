"""Generation 2, Layer 1: `tokenize()`'s full output, indexed — punctuation included.

`REDESIGN.md` §2.1: old Layer 1 (`dante_corpus.api.Line.tokens`) applies `has_alpha`
*before* indexing, so punctuation never receives a token position at all — the defect is
address, not loss, since `tokenize()` (`dante_corpus.tokenizer`) already splits punctuation
into its own token strings. L1 is that same `tokenize()` output taken whole, minus only the
pure-whitespace tokens `tokenize()` also produces (a space is not a terminal); every
remaining token — alphabetic or not — gets its own `(line, index)` address. This numbering
does not line up with old Layer 1's: a line with punctuation has more L1 tokens than it has
old-Layer-1 tokens, and the indices of the alpha tokens shift accordingly.

Nothing here reads old Layer 1, old Layer 2, or any annotated layer — only the frozen source
text (`dante_corpus.api`, which reads `src/*.txt` directly) and the tokenizer function
itself, both bootstrap-safe under premise 3 (`PLAN.md`). There is no model call and nothing
to persist: L1 is a pure, deterministic function of the source text, computed on demand the
same way old Layer 1's `Line.tokens` is.
"""

from __future__ import annotations

from dataclasses import dataclass

from dante_corpus.tokenizer import tokenize


@dataclass(frozen=True)
class L1Token:
    index: int
    text: str

    def to_dict(self) -> dict[str, object]:
        return {"index": self.index, "text": self.text}


@dataclass(frozen=True)
class L1Line:
    no: int
    text: str
    tokens: tuple[L1Token, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "no": self.no,
            "text": self.text,
            "tokens": [token.to_dict() for token in self.tokens],
        }


def tokenize_l1(text: str) -> tuple[str, ...]:
    """`tokenize()`'s full output with pure-whitespace tokens dropped, order preserved.

    Alpha tokens and punctuation tokens both survive; only a token that is entirely
    whitespace (`str.isspace()`) is filtered — that is the one thing `tokenize()` emits that
    is never a terminal."""
    return tuple(token for token in tokenize(text) if not token.isspace())


def l1_line(no: int, text: str) -> L1Line:
    tokens = tuple(L1Token(index, token) for index, token in enumerate(tokenize_l1(text)))
    return L1Line(no=no, text=text, tokens=tokens)


def l1_canto(canticle: str, number: int) -> tuple[L1Line, ...]:
    """L1 for every line of a canto, reading the raw source text via `dante_corpus.api`."""
    from dante_corpus.api import canto

    return tuple(l1_line(line.no, line.text) for line in canto(canticle, number).lines())


# --- Self-check: reproduce REDESIGN.md §2.1's corpus-wide punctuation measurement ---------


def _main() -> None:
    import argparse
    from collections import Counter

    from dante_corpus.api import canticles, cantos

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stats", action="store_true",
                        help="corpus-wide alpha/punctuation counts and quote-pair balance")
    args = parser.parse_args()
    if not args.stats:
        parser.print_help()
        return

    alpha = 0
    punct: Counter[str] = Counter()
    for canticle in canticles():
        for number in cantos(canticle):
            for line in l1_canto(canticle, number):
                for token in line.tokens:
                    if any(ch.isalpha() for ch in token.text):
                        alpha += 1
                    else:
                        punct[token.text] += 1

    print(f"alpha tokens        {alpha:>7}")
    print(f"punctuation tokens  {sum(punct.values()):>7}")
    for mark, count in punct.most_common():
        print(f"  {mark!r:>4} {count:>7}")

    pairs = (("«", "»"), ("‘", "’"), ("“", "”"))
    for open_mark, close_mark in pairs:
        print(f"balance {open_mark}/{close_mark}: {punct[open_mark]}/{punct[close_mark]}"
              f"{'  OK' if punct[open_mark] == punct[close_mark] else '  MISMATCH'}")


if __name__ == "__main__":
    _main()
