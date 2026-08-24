# Architecture: Standing Design Patterns

Cross-cutting design patterns shared by this repo's LLM-in-the-loop tooling —
the layer build drivers (`skel/`, `dep/`) and the Grammar Agent Harness
(`harness/`). This document is the **single source for those patterns**: stage
plans (e.g. [`harness/PLAN.md`](harness/PLAN.md)) reference it instead of
restating them. Everything here is binding guidance for new entry points
unless a plan explicitly overrides it.

Patterns labelled **Standard** are the current common specification. Variants
labelled **Legacy** exist only as records of the trial-and-error process that
produced the standards — keep them where they already serve experiment CLIs,
but never copy them into new code.

---

## 1. Lineage

- **Build drivers (Phase 5–8)** — `skel/skel.py` (+ `driver_build.py`,
  `driver_fix.py`, `driver_ui.py`), `dep/dep.py`: single-shot Q&A with a fresh,
  disposable `llm7shi.Client` per attempt/question, system prompt swapped per
  question, free-text tables validated by deterministic code, an external retry
  loop, and failures appended to a log file. Introduced the StatusLine display
  wiring and validate-then-write-back resumability.
- **Grammar Agent Harness** — multi-turn closed-tool agent loop plus benchmark
  machinery; formalized the standards below.

## 2. Model access — Standard

- **llm7shi is the model-access layer.** Every live CLI reaches its model
  through llm7shi. Backends are always injected as callables — library cores
  (`harness/toolcall/transports.py`) never import llm7shi or ollama themselves,
  and llm7shi imports are lazy (inside functions), so importing a module never
  touches a model or network.
- **The stateful Client adapter is the common specification**:
  `runner.agent.llm7shi_generate` mirrors the loop transcript into a
  per-session `llm7shi.Client` (history + system prompt) and wraps a
  quality-retry loop that regenerates empty/repetitive replies instead of
  ending a session. Sessions have explicit boundaries: each session opens with
  `transport.reset()`, which re-creates the Client so no state leaks across
  units; transports forward `reset()` to any backend exposing it, and stateless
  backends simply don't define it.
- **Legacy variants — do not copy:**
  - `toolcall.probe.llm7shi_generate` (reused by `toolcall.parity`): stateless
    adapter over `llm7shi.compat.generate_with_schema`; predates the Client
    adapter.
  - The build drivers' disposable-Client Q&A pattern (§1): no session mirror,
    no quality retry.
- **Exception:** the native Ollama transport bypasses llm7shi deliberately
  (`llm7shi.Client.__call__` does not forward `tools`) and drives
  `ollama.chat(tools=...)` directly behind the same Transport interface.

## 3. Wire protocol & backends — Standard

- Prompt-instructed `<tool_call>` XML (`PromptXmlTransport`) is the official
  wire format; native Ollama tool calling (`OllamaNativeTransport`) stays
  implemented and gated for comparison experiments only. Backend choice is free
  (`google:gemma-4-31b-it` when wall clock matters, `ollama:gemma4:31b-it-qat`
  for offline/cost-constrained work); both ride the same protocol unchanged.
- Transports normalize everything to canonical OpenAI-format dicts plus
  parse-error envelopes; the agent loop above the transport layer is
  transport-agnostic.

## 4. Live-run observability — Standard

LLM-in-the-loop runs are inherently slow (minutes per turn on local models,
hours per benchmark). An unwatchable run is an unusable run: progress must be
**visible by default**, not silent-until-finished.

- Stream model output to stderr as it arrives; print one stderr progress line
  per turn with each call's compact return value and elapsed seconds
  (`progress_printer`); announce every session with its `[index/total]`
  position via major separators and divide named passes inside a session with
  minor ones (`progress_separator` / `progress_subseparator`, implemented in
  `toolcall.loop.py`).
- Optional Rich status bar (`HarnessStatusLine`, wrapping
  `llm7shi.statusline.StatusLine`): its bar counts the same units as the
  separators, its console stays pinned to stderr by convention, forwarded text
  renders with Rich markup disabled (corpus text routinely contains bracket
  fragments that markup parsing would silently swallow or crash on), and the
  same console stream is handed to llm7shi as the streaming sink so model
  output shares the display instead of clobbering the bar.
- **Per-turn timing is a measurement instrument, not decoration**: per-turn
  wall-clock seconds ride in results (`LoopResult.turn_seconds`) and JSONL
  records; summaries must aggregate them (total / mean / max, plus
  `slow_turns` at `SLOW_TURN_SECONDS = 300`).
- **Turn-granularity discipline**: one healthy model turn is one reasoning
  step plus its dispatches. A turn that sits thinking for many minutes means
  too much work was bundled into one response — reconsider the prompt or
  workflow; do not accept the latency.
- **Make the invisible measurable**: llm7shi auto-retries API 429s silently;
  count them via the status stream's `wait_retry` hook (`api_retries` /
  `api_retry_seconds`, per unit of work and rolled into summaries) so silent
  backoffs stay measurable instead of only inflating `turn_seconds`.
- Human-facing streams go to stderr by convention, but **log durability never
  relies on shell redirection**: every CLI opens and writes its own artifact
  files (`--log`, `--trace`); nothing downstream may depend on where the
  console display lands.

## 5. Streaming JSONL log contract — Standard

Binding for every live CLI that takes `--log FILE`:

- Append one JSON object per completed unit of work (`scenario` / comparison /
  `case` / `session`) and flush immediately — an interrupted run keeps
  everything already finished on disk.
- Write a final `summary` record carrying the aggregate metrics including
  total elapsed time. **Completion marker: a log whose last line is the
  summary record is complete.**
- Timing in summaries is summed per-session/per-turn seconds — never a
  start-to-end wall span (interruptions make spans meaningless; no
  `started_at` field).
- Resuming CLIs load an existing log at startup: completed records rejoin the
  aggregates, their work is skipped, fresh records append, progress displays
  span the whole run (`[offset+i/offset+N]`, status bar starts at the offset),
  and superseded summary records are stripped atomically (tempfile +
  `os.replace`) so the completion marker stays exact. Unparsable torn tails
  from killed runs are skipped, not fatal. One-shot experiment CLIs may
  instead truncate on startup (`"w"` mode: one file per attempt) — pick per
  CLI, keep the contract exact either way.
- Run logs are ephemeral artifacts (`*.log` is gitignored); durable numbers
  belong in the relevant PLAN file — record numbers, never log filenames.

## 6. Reporting shape — Standard

Every report class ships both faces:

- `metrics()` — machine-readable dict, embedded in the log's summary record;
- `summary()` — human-readable one-screen text printed by the CLI.

Gate values appear with their thresholds in output (e.g. parse success rate
`(gate >= 0.95: PASS)`).

## 7. Error discipline — Standard

Errors never raise across boundaries: parser failures become parse-error
envelopes, tool-dispatch failures become structured `{"ok": false, ...}`
payloads, and both are fed back verbatim to the model for self-correction.
Driver-side validation follows the same shape — structured violation lists
with logged responses, not exceptions into the generation loop.

## 8. Deterministic testing — Standard

No test touches a model or network. Sessions are scripted via `StubTransport`
(raw strings routed through the real parser, so tests exercise the actual wire
format) against real frozen data; live adapters are lazy-imported inside
functions so they execute only when modules run as scripts. Masking guarantees
are tested adversarially (e.g. poisoning masked modules to prove no code path
can reach them).

## 9. CLI skeleton — Standard

Shared shape for operator-run entry points: argparse with
`--model` / `--temperature` / `--max-turns` / `--log` / `--verbose`; a header
line announcing the run; `try/finally` sink close; final
`records written to ...` line followed by `report.summary()` output.
