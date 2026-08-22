"""Live probe: parse-success-rate measurement for the XML tool-call protocol (T4).

Runs small scripted scenarios against a real model through `PromptXmlTransport` and
measures how reliably the model speaks the `<tool_call>` wire format. This is the
go/no-go gate of `harness/TOOLCALL.md` §5.2 before wiring the protocol into the Stage 1
runner — run it from the repo root, e.g.:

    uv run python -m harness.toolcall.probe --model ollama:gemma4:31b-it-qat

Metrics:
- **parse success rate** (primary gate, target >= 0.95): fraction of turns where at
  least one well-formed tool call is extractable. A no-call turn counts as success only
  if it is a legitimate final answer (the scenario already made a successful call);
  answering without ever calling a tool is a protocol failure.
- **malformed-but-recoverable rate**: parse-failure turns followed by a well-formed turn
  within the same scenario (one feedback turn fixed it).
- **hallucinated-tool rate**: well-formed calls naming a tool outside the closed set.
- **dispatch error rate**: dispatched calls rejected by `GrammarToolkit.dispatch`.

This module is an experiment harness, not part of the deterministic library: it imports
llm7shi lazily and touches the network/model only when run as a script.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .loop import progress_printer, progress_separator, run_tool_loop
from .parser import is_parse_error, parse_tool_calls
from .prompts import few_shot_messages, tool_specs_section, xml_contract_section
from .transports import PromptXmlTransport

__all__ = ["ProbeReport", "SCENARIOS", "expand_scenarios", "main", "run_probe"]

DEFAULT_MODEL = "ollama:gemma4:31b-it-qat"  # model.mk default: Gemma 4 31B QAT via Ollama


def _system_prompt(specs) -> str:
    return "\n\n".join(
        [
            "You are a grammar analysis agent working on Dante's Divine Comedy.",
            xml_contract_section(),
            tool_specs_section(specs),
        ]
    )


def _rows_example() -> str:
    return json.dumps(
        [
            {
                "line": 2,
                "token": 2,
                "word": "ritrovai",
                "role": "subj",
                "arg_line": 0,
                "arg_token": 0,
                "arg_word": "",
            },
            {
                "line": 2,
                "token": 2,
                "word": "ritrovai",
                "role": "obl:per",
                "arg_line": 2,
                "arg_token": 5,
                "arg_word": "selva",
            },
        ],
        ensure_ascii=False,
    )


SCENARIOS = [
    {
        "name": "read_unit",
        "task": (
            "Read the complete grammatical context of the parse unit containing "
            "Inferno I line 1. Call read_unit now."
        ),
    },
    {
        "name": "search_corpus",
        "task": (
            "Find occurrences of the lemma 'ritrovare' in cantos other than Inferno I. "
            "Call search_corpus now."
        ),
    },
    {
        "name": "validate_candidate",
        "task": (
            "Validate this candidate skeleton for the unit Inferno I lines 1-3:\n"
            f"{_rows_example()}\n"
            "Call validate_candidate with exactly these rows now."
        ),
    },
    {
        "name": "read_then_validate",
        "task": (
            "Read the parse unit containing Inferno I line 1, then propose and "
            "validate a candidate skeleton for it. Work step by step with the tools."
        ),
        "max_turns": 6,
    },
]


@dataclass
class ProbeReport:
    """Aggregate measurements over all scenarios."""

    turns: int = 0
    parse_success_turns: int = 0
    parse_failure_turns: int = 0
    recoverable_failures: int = 0
    calls: int = 0
    hallucinated_calls: int = 0
    dispatch_errors: int = 0
    scenarios: list[dict] = field(default_factory=list)

    @property
    def parse_success_rate(self) -> float:
        return self.parse_success_turns / self.turns if self.turns else 0.0

    def metrics(self) -> dict:
        """Machine-readable measurements, as embedded in the `--log` summary record."""
        return {
            "turns": self.turns,
            "parse_success_turns": self.parse_success_turns,
            "parse_failure_turns": self.parse_failure_turns,
            "parse_success_rate": round(self.parse_success_rate, 4),
            "gate_pass": self.parse_success_rate >= 0.95,
            "malformed_but_recoverable": self.recoverable_failures,
            "calls": self.calls,
            "hallucinated_calls": self.hallucinated_calls,
            "dispatch_errors": self.dispatch_errors,
        }

    def summary(self) -> str:
        metrics = self.metrics()
        verdict = "PASS" if metrics["gate_pass"] else "FAIL"
        lines = [
            f"turns: {self.turns}",
            f"parse success rate: {self.parse_success_rate:.3f} (gate >= 0.95: {verdict})",
            f"malformed-but-recoverable: {self.recoverable_failures}",
            f"calls: {self.calls} "
            f"(hallucinated: {self.hallucinated_calls}, "
            f"dispatch errors: {self.dispatch_errors})",
        ]
        return "\n".join(lines)


def run_probe(
    transport, toolkit, specs, scenarios=None, max_turns=4, sink=None, progress=False
) -> ProbeReport:
    """Run every scenario through the real loop code and measure protocol compliance.

    `sink` is an optional writable text file: each scenario record is appended and
    flushed the moment it completes, so an interrupted run still leaves every finished
    scenario on disk for post-mortem (a log without a summary record = incomplete run).
    `progress` prints one stderr line per model turn, labeled with the scenario name
    (see `toolcall.progress_printer`) so long live runs stay watchable.
    """
    report = ProbeReport()
    scenario_list = list(scenarios) if scenarios is not None else SCENARIOS
    for pos, scenario in enumerate(scenario_list, 1):
        if progress:
            progress_separator(scenario["name"], pos, len(scenario_list))
        messages = [{"role": "system", "content": _system_prompt(specs)}]
        messages.extend(few_shot_messages())
        messages.append({"role": "user", "content": scenario["task"]})

        budget = scenario.get("max_turns", max_turns)
        result = run_tool_loop(
            transport=transport,
            toolkit=toolkit,
            messages=messages,
            tools=specs,
            max_turns=budget,
            on_turn=(
                progress_printer(f"{scenario['name']}", budget) if progress else None
            ),
        )

        scenario_calls = 0
        scenario_hallucinations = 0
        scenario_dispatch_errors = 0
        known_tools = {spec["function"]["name"] for spec in specs}
        pending_failure = False

        # Per-turn call lists, reconstructed from the transcript's assistant messages.
        opening_len = len(messages)
        turn_texts = [
            m["content"]
            for m in result.messages[opening_len:]
            if m["role"] == "assistant"
        ]
        outcome_cursor = 0  # outcomes align 1:1 with parsed items, in order
        for text in turn_texts:
            items = parse_tool_calls(text)
            well_formed = [it for it in items if not is_parse_error(it)]
            report.turns += 1

            if not items:
                # No blocks at all: legitimate final answer only after real work.
                if scenario_calls > 0:
                    report.parse_success_turns += 1
                else:
                    report.parse_failure_turns += 1
                continue

            if well_formed:
                report.parse_success_turns += 1
                if pending_failure:
                    report.recoverable_failures += 1
                    pending_failure = False
            else:
                report.parse_failure_turns += 1
                pending_failure = True

            for item in items:
                outcome = result.outcomes[outcome_cursor]
                outcome_cursor += 1
                if is_parse_error(item):
                    continue
                name = item.get("function", {}).get("name", "")
                scenario_calls += 1
                if name not in known_tools:
                    scenario_hallucinations += 1
                if outcome.get("ok") is False:
                    scenario_dispatch_errors += 1

        report.calls += scenario_calls
        report.hallucinated_calls += scenario_hallucinations
        report.dispatch_errors += scenario_dispatch_errors
        record = {
            "record": "scenario",
            "name": scenario["name"],
            "turns": len(turn_texts),
            "turn_seconds": result.turn_seconds,
            "exhausted": result.exhausted,
            "final_text": result.text[:500],
            "outcomes": result.outcomes,
        }
        report.scenarios.append(record)
        if sink is not None:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.flush()
    return report


def expand_scenarios(
    selected: list[str] | None = None, repeat: int = 1
) -> list[dict]:
    """Resolve `--scenario` / `--repeat` into the concrete scenario list.

    No selection means every scenario; `repeat > 1` duplicates each one (fresh
    conversation per copy) with `#N` suffixes so pooled measurements stay attributable.
    """
    base = (
        [s for s in SCENARIOS if s["name"] in set(selected)] if selected else list(SCENARIOS)
    )
    if repeat > 1:
        base = [
            {**s, "name": f"{s['name']}#{run + 1}"}
            for run in range(repeat)
            for s in base
        ]
    return base


def llm7shi_generate(model: str, temperature: float | None = None, quiet: bool = True):
    """Build a stateless generate function over `llm7shi.compat.generate_with_schema`."""
    from llm7shi.compat import generate_with_schema

    def generate(messages: list[dict]) -> str:
        response = generate_with_schema(
            messages,
            schema=None,
            model=model,
            temperature=temperature,
            show_params=not quiet,
        )
        return response.text

    return generate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="XML tool-call protocol live probe (TOOLCALL.md §5.2)."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-turns", type=int, default=4)
    parser.add_argument(
        "--scenario", action="append", choices=[s["name"] for s in SCENARIOS]
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="run every scenario N times (fresh conversation each) for a pooled sample",
    )
    parser.add_argument(
        "--log",
        help=(
            "streaming JSONL log: one scenario record per line as it completes, "
            "summary record last; a file without the summary record = interrupted run"
        ),
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    from harness.runner.tools import GrammarToolkit, tool_specs

    specs = tool_specs()
    transport = PromptXmlTransport(
        generate=llm7shi_generate(args.model, args.temperature, quiet=not args.verbose)
    )
    scenarios = expand_scenarios(args.scenario, args.repeat)

    print(f"probe: model={args.model} scenarios={[s['name'] for s in scenarios or SCENARIOS]}")
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # "w" mode: the log is truncated at startup so runs never append across attempts.
    sink = open(args.log, "w", encoding="utf-8") if args.log else None
    try:
        report = run_probe(
            transport, GrammarToolkit(), specs, scenarios, args.max_turns, sink=sink,
            progress=True,
        )
        if sink is not None:
            summary = {
                "record": "summary",
                "model": args.model,
                "temperature": args.temperature,
                "repeat": args.repeat,
                "max_turns": args.max_turns,
                "started_at": started_at,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                **report.metrics(),
            }
            sink.write(json.dumps(summary, ensure_ascii=False) + "\n")
            sink.flush()
    finally:
        if sink is not None:
            sink.close()

    if args.log:
        print(f"transcripts written to {args.log}")
    print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
