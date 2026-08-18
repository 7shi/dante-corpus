#!/usr/bin/env python3
"""Census all Layer-5 skeleton derivation and verification rules.

Measures:
1. Population (baseline hits during normal zero-violation verification across all 100 cantos).
2. Count on removal (total violations generated across the corpus when the rule is disabled).
3. Status (active vs dead/auxiliary).

Runs completely in memory in < 15 seconds.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from dante_corpus import api, case, dep, morph, np, skel
from dante_corpus.skel import RULES

CANTICHE = ("inferno", "purgatorio", "paradiso")


class CachedCorpus:
    """Pre-loaded corpus tables for fast in-memory rule census."""

    def __init__(self) -> None:
        # List of parse units: (unit_nos, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows)
        self.units: list[tuple[list[int], list[str], dict[int, list], dict[int, list], dict[int, list], dict[int, list], dict[int, list]]] = []

    def load(self) -> None:
        for canticle in CANTICHE:
            for number in api.cantos(canticle):
                if not skel.has_skel(canticle, number):
                    continue
                data = skel.load_skel(canticle, number)
                morph_rows = {no: list(rows) for no, rows in morph.load_morph(canticle, number).items()} if morph.has_morph(canticle, number) else {}
                np_rows = {no: list(rows) for no, rows in np.load_np(canticle, number).items()} if np.has_np(canticle, number) else {}
                dep_rows = {no: list(rows) for no, rows in dep.load_dep(canticle, number).items()} if dep.has_dep(canticle, number) else {}
                case_rows = {no: list(rows) for no, rows in case.load_case(canticle, number).items()} if case.has_case(canticle, number) else {}

                lines = api.canto(canticle, number).lines()
                text_by_no = {line.no: line.text for line in lines}
                nos_all = [line.no for line in lines]
                texts_all = [line.text for line in lines]

                for unit in dep.sentence_groups(nos_all, texts_all, dep.MAX_UNIT_LINES):
                    unit_texts = [text_by_no[no] for no in unit]
                    rows_by_line = {no: list(data.get(no, [])) for no in unit}
                    self.units.append(
                        (unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows)
                    )


def run_census(corpus: CachedCorpus) -> list[dict[str, object]]:
    # 1. Baseline run (collect baseline hits / population)
    RULES.reset_disabled()
    RULES.reset_hits()

    baseline_violations = 0
    for unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows in corpus.units:
        v = skel.validate_unit(
            unit,
            unit_texts,
            rows_by_line,
            morph_rows=morph_rows,
            np_rows=np_rows,
            dep_rows=dep_rows,
            case_rows=case_rows,
        )
        # Only count soft violations (tag)
        soft = [x for x in v if x.kind == "tag"]
        baseline_violations += len(soft)

    if baseline_violations != 0:
        print(
            f"WARNING: Baseline corpus has {baseline_violations} violations! Expected 0.",
            file=sys.stderr,
        )

    all_rules = RULES.all_rules()
    population_counts = {r.id: RULES.hit_count(r.id) for r in all_rules}

    results: list[dict[str, object]] = []

    # 2. Measure removal count for each rule
    for rule in all_rules:
        RULES.reset_disabled()
        RULES.disable(rule.id)

        violations_on_removal = 0
        for unit, unit_texts, rows_by_line, morph_rows, np_rows, dep_rows, case_rows in corpus.units:
            v = skel.validate_unit(
                unit,
                unit_texts,
                rows_by_line,
                morph_rows=morph_rows,
                np_rows=np_rows,
                dep_rows=dep_rows,
                case_rows=case_rows,
            )
            soft = [x for x in v if x.kind == "tag"]
            violations_on_removal += len(soft)

        pop = population_counts.get(rule.id, 0)
        status = "active" if violations_on_removal > 0 else ("auxiliary" if pop > 0 else "dormant")

        results.append(
            {
                "id": rule.id,
                "name": rule.name,
                "kind": rule.kind,
                "population": pop,
                "removal_violations": violations_on_removal,
                "status": status,
                "description": rule.description,
            }
        )

    RULES.reset_disabled()
    return results


def print_markdown_table(results: list[dict[str, object]]) -> None:
    print("\n# Layer 5 Rule Census Report\n")
    print(f"Total Rules: {len(results)}\n")
    print("| Rule ID | Name | Kind | Population | Count on Removal | Status | Description |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        print(
            f"| `{r['id']}` | `{r['name']}` | `{r['kind']}` | {r['population']} | {r['removal_violations']} | **{r['status']}** | {r['description']} |"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Layer 5 Rule Census Tool")
    parser.add_argument(
        "--markdown", action="store_true", help="Print output as Markdown table"
    )
    args = parser.parse_args()

    t0 = time.perf_counter()
    print("Caching all 100 cantos into memory...", file=sys.stderr)
    corpus = CachedCorpus()
    corpus.load()
    t_load = time.perf_counter() - t0
    print(f"Loaded {len(corpus.units)} parse units across 100 cantos in {t_load:.2f}s.", file=sys.stderr)

    t1 = time.perf_counter()
    print("Executing rule census...", file=sys.stderr)
    results = run_census(corpus)
    t_census = time.perf_counter() - t1
    print(f"Census completed in {t_census:.2f}s.", file=sys.stderr)

    print_markdown_table(results)

    active_count = sum(1 for r in results if r["status"] == "active")
    auxiliary_count = sum(1 for r in results if r["status"] == "auxiliary")
    dormant_count = sum(1 for r in results if r["status"] == "dormant")
    print(f"\n**Summary**:")
    print(f"- Total Registered Rules: {len(results)}")
    print(f"- Directly Active Rules (removal violations > 0): {active_count}")
    print(f"- Auxiliary / Structural Rules (population > 0, removal violations = 0): {auxiliary_count}")
    print(f"- Dormant Rules: {dormant_count}")


if __name__ == "__main__":
    main()
