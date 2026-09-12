"""
Aggregate the per-canto proper_noun/<canticle>/<NN>.tsv files into a single
proper_noun/proper_noun.tsv: one row per distinct name (the verbatim string
recorded by proper_noun.py), listing every place it occurs.

    uv run proper_noun/aggregate.py

Output format, one row per name, occurrences tab-separated and sorted by
canticle (inferno, purgatorio, paradiso), then canto, then line. Each
canticle is abbreviated (i/pu/pa) to keep the file small:

    Name<TAB>i:canto:line<TAB>pu:canto:line<TAB>pa:canto:line...

Names are grouped by exact string match (case and accents as written in the
source TSVs), so a name spelled differently across occurrences (e.g. because
one occurrence capitalizes it and another does not) gets its own row - the
per-canto files already carry each name in its own line's verbatim spelling,
and this script does not normalize across them.
"""

from pathlib import Path
from collections import defaultdict

PROPER_NOUN_DIR = Path(__file__).resolve().parent
CANTICLE_ABBREV = {"inferno": "i", "purgatorio": "pu", "paradiso": "pa"}


def main() -> None:
    occurrences: dict[str, list[tuple[int, str]]] = defaultdict(list)

    for canticle_index, (canticle, abbrev) in enumerate(CANTICLE_ABBREV.items()):
        canticle_dir = PROPER_NOUN_DIR / canticle
        for tsv_path in sorted(canticle_dir.glob("*.tsv")):
            canto = int(tsv_path.stem)
            for row in tsv_path.read_text(encoding="utf-8").splitlines():
                if not row.strip():
                    continue
                line_num, *nouns = row.split("\t")
                location = f"{abbrev}:{canto}:{line_num}"
                sort_key = (canticle_index, canto, int(line_num))
                for noun in nouns:
                    occurrences[noun].append((sort_key, location))

    out_path = PROPER_NOUN_DIR / "proper_noun.tsv"
    with open(out_path, "w", encoding="utf-8") as f:
        for name in sorted(occurrences):
            locations = [loc for _, loc in sorted(occurrences[name])]
            f.write("\t".join([name, *locations]) + "\n")

    n_locations = sum(len(v) for v in occurrences.values())
    print(f"{out_path}: {len(occurrences)} name(s), {n_locations} occurrence(s)")


if __name__ == "__main__":
    main()
