import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dante_corpus.tokenizer import convert_apostrophe

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "pg1000.txt"
CANTICLES = {"Inferno": "inferno", "Purgatorio": "purgatorio", "Paradiso": "paradiso"}


def roman_number(value: str) -> int:
    if match := re.match(r"(|X|XX|XXX)(|I(?=X$|V$))(X?)(V?)(|I|II|III)$", value.upper()):
        x1 = len(match.group(1))
        i1 = len(match.group(2))
        x2 = len(match.group(3))
        v1 = len(match.group(4))
        i2 = len(match.group(5))
        return x1 * 10 - i1 + x2 * 10 + v1 * 5 + i2
    raise ValueError(f"invalid roman number: {value}")


def write_canto(canticle: str | None, number: int, lines: list[str]) -> None:
    if canticle is None:
        return
    out_dir = SCRIPT_DIR / canticle
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{number:02d}.txt"
    out_path.write_text("".join(lines), encoding="utf-8")


def materialize(source: Path) -> None:
    canticle: str | None = None
    number = 0
    lines: list[str] = []

    with source.open(encoding="utf-8") as handle:
        iterator = iter(handle)
        for raw_line in iterator:
            line = raw_line.rstrip()
            if re.fullmatch(r"[A-Z]+", line):
                continue
            if line in CANTICLES:
                write_canto(canticle, number, lines)
                canticle = CANTICLES[line]
                lines = []
                canto_line = next(iterator).rstrip()
                if not (match := re.match(r"Canto (\w+)", canto_line)):
                    raise ValueError(f"invalid line: {canto_line}")
                number = roman_number(match.group(1))
                continue
            if line.lstrip().startswith("*** END"):
                write_canto(canticle, number, lines)
                break
            if line and canticle is not None:
                lines.append(convert_apostrophe(line.lstrip()) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        nargs="?",
        default=str(TARGET),
        help="Path to pg1000.txt (default: %(default)s)",
    )
    args = parser.parse_args()
    materialize(Path(args.source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
