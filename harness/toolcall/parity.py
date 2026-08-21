"""Migration parity check: XML interim vs native Ollama tool calling (`TOOLCALL.md` §5.3).

Runs every probe scenario twice against a real model — once through
`PromptXmlTransport`, once through `OllamaNativeTransport` — and verifies that both
paths speak one protocol. Per §5.3, sequences need not match turn-for-turn (the model
may behave differently under each wire format); the *protocol* is verified by the
canonical representation:

- **interop (hard criterion)**: every well-formed call recorded under either transport
  renders back through `format_tool_call` and re-parses to the identical canonical dict,
  i.e. native-mode calls are accepted unchanged by XML mode's parser and vice versa.
- **observational**: flattened call-name sequences and final `validate_candidate`
  candidate rows are compared between transports and reported, not gated.

Each transport gets its idiomatic opening: the XML side carries the `<tool_call>`
contract and few-shot demo, the native side relies on `chat(tools=...)` alone — an
XML-shaped demo would teach the wrong wire format there.

Live usage (operator-run):

    uv run python -m harness.toolcall.parity --model ollama:gemma4:31b-it-qat \
        --repeat 3 --log harness/parity.log

Streaming JSONL log semantics mirror `probe.py`: one scenario record per completed
scenario, summary record last (a log without the summary line = interrupted run);
`*.log` is gitignored. Deterministic tests drive both sides with stubbed transports.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .loop import run_tool_loop
from .parser import format_tool_call, is_parse_error, parse_tool_calls
from .prompts import few_shot_messages, tool_specs_section, xml_contract_section
from .transports import (
    ChatFn,
    OllamaNativeTransport,
    PromptXmlTransport,
    Transport,
    TransportResponse,
)

__all__ = ["ParityReport", "RecordingTransport", "ollama_chat", "run_parity"]

FINAL_TEXT_LIMIT = 500


def ollama_chat(
    model: str, temperature: float | None = None, options: dict | None = None
) -> ChatFn:
    """Build a native chat backend over the `ollama` package's `chat(tools=...)`.

    Returns `(messages, tools) -> response message`; non-streaming. Import is lazy so
    the module stays importable without ollama installed (deterministic tests inject
    fakes instead).
    """
    from ollama import chat as _chat

    def chat(messages: list[dict], tools) -> object:
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "tools": [dict(spec) for spec in tools],
        }
        opts = dict(options or {})
        if temperature is not None:
            opts.setdefault("temperature", temperature)
        if opts:
            kwargs["options"] = opts
        return _chat(**kwargs).message

    return chat


class RecordingTransport:
    """Wrap any transport and record every normalized turn it produces.

    The loop keeps only assistant *text* in the transcript, but parity needs each
    turn's canonical tool calls — including the native transport's, whose transcript
    text does not carry them. Recording at the transport boundary treats both wire
    formats uniformly.
    """

    def __init__(self, inner: Transport) -> None:
        self.inner = inner
        self.turns: list[TransportResponse] = []

    def complete(self, messages: list[dict], tools) -> TransportResponse:
        response = self.inner.complete(messages, tools)
        self.turns.append(response)
        return response


def call_sequences(transport: RecordingTransport) -> tuple[list[list[dict]], int]:
    """Per-turn well-formed calls as `[{"name": ..., "arguments": <parsed>}]`.

    Error envelopes are skipped and counted; returns `(sequences, error_count)`.
    """
    sequences: list[list[dict]] = []
    errors = 0
    for response in transport.turns:
        turn: list[dict] = []
        for item in response.tool_calls:
            if is_parse_error(item):
                errors += 1
                continue
            function = item.get("function", {})
            try:
                arguments = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                errors += 1
                continue
            turn.append({"name": function.get("name"), "arguments": arguments})
        sequences.append(turn)
    return sequences, errors


def canonical_groups(transport: RecordingTransport) -> list[list[dict]]:
    """Canonical tool-call dicts per turn, error envelopes dropped."""
    return [
        [item for item in response.tool_calls if not is_parse_error(item)]
        for response in transport.turns
    ]


def interop_ok(groups: list[list[dict]]) -> bool:
    """§5.3 hard criterion: canonical calls survive the XML formatter/parser round trip.

    Every well-formed call either transport produced must render back through
    `format_tool_call` and re-parse to the identical canonical dict — native-mode
    calls accepted unchanged by XML mode's parser, and vice versa.
    """
    for group in groups:
        for call in group:
            try:
                rendered = format_tool_call(call)
            except ValueError:
                return False
            if parse_tool_calls(rendered) != [call]:
                return False
    return True


def candidate_rows(sequences: list[list[dict]]) -> list[dict]:
    """Candidate rows from the last `validate_candidate` call in the sequences."""
    rows: list[dict] = []
    for turn in sequences:
        for call in turn:
            if call["name"] == "validate_candidate":
                submitted = call["arguments"].get("candidate_rows")
                if isinstance(submitted, list):
                    rows = submitted
    return rows


def _opening_messages(variant: str, task: str, tools) -> list[dict]:
    """Idiomatic opening per variant: XML contract+demo vs bare native specs."""
    sections = ["You are a grammar analysis agent working on Dante's Divine Comedy."]
    if variant == "xml":
        sections.append(xml_contract_section())
    sections.append(tool_specs_section(tools))
    messages = [{"role": "system", "content": "\n\n".join(sections)}]
    if variant == "xml":
        messages.extend(few_shot_messages())
    messages.append({"role": "user", "content": task})
    return messages


def _run_side(variant, make_transport, task, toolkit_factory, tools, max_turns) -> dict:
    """One session for one variant; returns its measurement block."""
    recorder = RecordingTransport(make_transport())
    result = run_tool_loop(
        transport=recorder,
        toolkit=toolkit_factory(),
        messages=_opening_messages(variant, task, tools),
        tools=tools,
        max_turns=max_turns,
    )
    sequences, parse_errors = call_sequences(recorder)
    stats = {
        "turns": result.turns,
        "exhausted": result.exhausted,
        "final_text": result.text[:FINAL_TEXT_LIMIT],
        "calls": sum(len(turn) for turn in sequences),
        "parse_errors": parse_errors,
        "sequences": sequences,
        "candidate_rows": candidate_rows(sequences),
    }
    return stats, canonical_groups(recorder)


def run_parity(
    scenarios: list[dict],
    *,
    xml_transport_fn,
    native_transport_fn,
    toolkit_fn,
    tools,
    max_turns: int = 6,
    sink=None,
) -> "ParityReport":
    """Run every scenario through both transports and compare.

    `xml_transport_fn` / `native_transport_fn` / `toolkit_fn` are zero-argument
    factories — each session gets a fresh conversation, transport instance, and
    toolkit (the grammar toolkit tracks one active unit, so sharing one across
    sessions would couple the two runs). `sink`, when given, receives one JSONL
    record per completed scenario, flushed immediately (interrupted runs keep
    everything already finished); the caller writes the summary record.
    """
    report = ParityReport()
    for scenario in scenarios:
        xml_stats, xml_groups = _run_side(
            "xml", xml_transport_fn, scenario["task"], toolkit_fn, tools, max_turns
        )
        native_stats, native_groups = _run_side(
            "native",
            native_transport_fn,
            scenario["task"],
            toolkit_fn,
            tools,
            max_turns,
        )

        xml_names = [c["name"] for turn in xml_stats["sequences"] for c in turn]
        native_names = [c["name"] for turn in native_stats["sequences"] for c in turn]
        comparison = {
            # Hard criterion (§5.3): one protocol across both wire formats.
            "interop_xml": interop_ok(xml_groups),
            "interop_native": interop_ok(native_groups),
            # Observational: behavior may legitimately differ turn-for-turn.
            "names_equal": xml_names == native_names,
            "rows_equal": xml_stats["candidate_rows"] == native_stats["candidate_rows"],
        }
        record = {
            "record": "scenario",
            "name": scenario["name"],
            "xml": xml_stats,
            "native": native_stats,
            "comparison": comparison,
        }
        report.records.append(record)
        if sink is not None:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.flush()
    return report


@dataclass
class ParityReport:
    """Aggregate verdicts over all scenario records."""

    records: list[dict] = field(default_factory=list)

    @property
    def parity_pass(self) -> bool:
        return all(
            r["comparison"]["interop_xml"] and r["comparison"]["interop_native"]
            for r in self.records
        )

    def metrics(self) -> dict:
        comparisons = [r["comparison"] for r in self.records]

        def count(key: str) -> int:
            return sum(bool(c[key]) for c in comparisons)

        def side(key: str) -> dict:
            return {
                "turns": sum(r[key]["turns"] for r in self.records),
                "calls": sum(r[key]["calls"] for r in self.records),
                "parse_errors": sum(r[key]["parse_errors"] for r in self.records),
                "exhausted": sum(r[key]["exhausted"] for r in self.records),
            }

        return {
            "scenarios": len(self.records),
            "parity_pass": self.parity_pass,
            "interop_scenarios": count("interop_xml") + count("interop_native"),
            "interop_checks": 2 * len(self.records),
            "names_equal_scenarios": count("names_equal"),
            "rows_equal_scenarios": count("rows_equal"),
            "xml": side("xml"),
            "native": side("native"),
        }

    def summary(self) -> str:
        m = self.metrics()
        verdict = "PASS" if m["parity_pass"] else "FAIL"
        lines = [
            f"scenarios: {m['scenarios']} "
            f"(interop {m['interop_scenarios']}/{m['interop_checks']} checks: {verdict})",
            f"names equal: {m['names_equal_scenarios']}/{m['scenarios']} "
            f"(observational)",
            f"candidate rows equal: {m['rows_equal_scenarios']}/{m['scenarios']} "
            f"(observational)",
            f"xml: turns={m['xml']['turns']} calls={m['xml']['calls']} "
            f"parse_errors={m['xml']['parse_errors']} exhausted={m['xml']['exhausted']}",
            f"native: turns={m['native']['turns']} calls={m['native']['calls']} "
            f"parse_errors={m['native']['parse_errors']} "
            f"exhausted={m['native']['exhausted']}",
        ]
        return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="XML vs native migration parity check (TOOLCALL.md §5.3)."
    )
    parser.add_argument("--model", default="ollama:gemma4:31b-it-qat")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-turns", type=int, default=6)
    parser.add_argument(
        "--scenario", action="append", help="restrict to these scenario names"
    )
    parser.add_argument(
        "--repeat", type=int, default=1, help="run every scenario N times (pooled)"
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

    from .probe import expand_scenarios, llm7shi_generate
    from harness.runner.tools import GrammarToolkit, tool_specs

    specs = tool_specs()
    scenarios = expand_scenarios(args.scenario, args.repeat)

    def xml_transport_fn():
        return PromptXmlTransport(
            generate=llm7shi_generate(args.model, args.temperature, quiet=not args.verbose)
        )

    def native_transport_fn():
        return OllamaNativeTransport(chat=ollama_chat(args.model, args.temperature))

    print(f"parity: model={args.model} scenarios={[s['name'] for s in scenarios]}")
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # "w" mode: the log is truncated at startup so runs never append across attempts.
    sink = open(args.log, "w", encoding="utf-8") if args.log else None
    try:
        report = run_parity(
            scenarios,
            xml_transport_fn=xml_transport_fn,
            native_transport_fn=native_transport_fn,
            toolkit_fn=GrammarToolkit,
            tools=specs,
            max_turns=args.max_turns,
            sink=sink,
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
        print(f"records written to {args.log}")
    print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
