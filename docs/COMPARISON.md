# sysmlpy vs OpenSysML vs gosysml — Comparison and Contrast

*Written 2026-09-18 after running OpenSysML's runtime-showcase models
through sysmlpy (see `tests/runtime_showcase_test.py` and
`tests/fixtures/runtime_showcase/`). Version references: sysmlpy 0.95.0,
OpenSysML v0.8.1, gosysml v0.2.0.*

---

## 1. The three projects

| | sysmlpy | gosysml | OpenSysML |
|---|---|---|---|
| Author | mycr0ft | mycr0ft (Go evolution of sysmlpy) | Open-MBEE (JPL/Boeing-backed org behind MMS/Flexo) |
| Language | Python 3.9+ | Go (ANTLR 4.13) | Go 1.23 (hand-written parser) |
| Size | ~152K lines | ~122K lines | ~681K lines |
| License | MIT | MIT | Apache-2.0 |
| Current release | 0.95.0 | v0.2.0 | v0.8.1 (2026-09-16; nightly prereleases from `develop` via git-flow) |
| Scope | parse → grammar objects → round-trip, semantic analysis, validator, views, evaluator, sim, interchange, stores | parse → typed grammar structs → round-trip (sysmlpy's architecture in Go) | parse → resolve → validate → **execute** (instances, actions, state machines), solve (z3), query, document generation, LSP, REPL, gRPC service + 5 language clients |
| Conformance story | OMG XPect 123/123; 165 grammar round-trips | 79 round-trips + 123 spec files bundled; 122/123 conformance gate (1 known issue, pre-existing) | Pilot differential vs OMG pilot over the pilot's own corpora, golden ASTs/traces, fUML + PSSM referees; refuses to claim certification |
| Units | pint (dimensions checked, units carried) | none | own ISO-80000 quantity system enforced at runtime feature writes |
| Delivery | pip / poetry, pure Python | go install, single binary | brew/winget/msi/scoop/tarballs, PyPI `opensysml` (drives the Go engine), nightly prereleases |

The relationship: OpenSysML and sysmlpy/gosysml overlap in scope (SysML v2
textual implementation) but differ in ambition and center of gravity.
sysmlpy is a **model library** — you hold a live object tree in your
process. OpenSysML is a **toolchain** — you hold a REPL/LSP/service that
answers questions about models, in your process or over the wire. gosysml
is the first third of sysmlpy in Go — parser + round-trip as an importable
library, a niche OpenSysML deliberately leaves empty (`internal/` is not
importable by Go convention; embedders must use its fat public API or gRPC).

## 2. The runtime-showcase comparison (what the fixtures showed)

OpenSysML's showcase (five models, `examples/runtime-showcase/`) makes
specific claims: validation passes where the runtime finds execution-only
defects; a delta-v analysis computes with units and rebinds arguments; a
recursive mass rollup stops at an unvalued leaf; a clocked mission state
machine advances; a spacecraft-comms model sends 100 kB while a battery
drains and recharges. We copied those five models into sysmlpy unchanged
and measured the same interactions. Result, per fixture:

| Fixture | Parse | Round-trip dump | Elements surface | Eval/sim outcome |
|---|---|---|---|---|
| delta-v-budget | ✓ | ✓ | ✓ (4 calc defs, analysis case, requirement) | **RocketEquation evaluates with pint units to OpenSysML's exact published digits** (3037.6966629706967 / 6432.955324716369 m/s, margin 70.65198768706614) via positional arg binding + `ln` built-in added this round |
| mass-rollup | ✓ | ✓ | ✓ (recursive defaults, `sum`) | evaluator collects declared values; the recursive rollup (feature chains through collections) is not evaluable — documented gap |
| mission-sequence | ✓ | ✓ (after fixes) | ✓ (`perform action` + `exhibit state` now surface) | MissionPhases machine drives through all six phases via completion/time transitions |
| reliability | ✓ | ✓ | ✓ (2 calcs, requirements with UUID-named satisfies) | calc bodies parse; typed-parameter invocation needs positional args (documented) |
| spacecraft-comms | ✓ | ✓ (after fixes; was lossy 1177→5334 chars) | ✓ (`exhibit state` in part defs now surfaces) | GroundStation `modes` machine builds and drives (idle ↔ operation); parallel `dataTransit | charging` machine builds |

**Fixes made in sysmlpy to get here** (all previously silent drops):
1. Visitor: `exhibitStateUsage` had zero handling — `exhibit state` usages
   (both `exhibit state m { ... }` and `exhibit state m : M;`) vanished
   from the visitor dict, the public tree, `Model.dump()`, boxes, and sim.
   Now normalized to a StateUsage dict with `exhibit: True`.
2. Grammar classes: `StateUsage` gained the `exhibit` flag and dumps it.
3. Public-API: `state def` inside a part/item def body was dropped (no
   dispatch arm); `perform action m : M { ... }` was dropped (no
   `_load_behavior_child` branch — and its PerformActionUsageDeclaration
   keeps name/typing in `.children`, extracted explicitly).
4. Evaluator: `ln`, `exp`, `log`, `log2`, `log10` built-ins added
   (pint-aware, dimensionless results), motivated directly by the
   showcase's rocket equation.

## 3. Capability boundary (honest accounting)

Where the same showcase question can be asked of both tools:

| Question | OpenSysML | sysmlpy |
|---|---|---|
| Does the model parse and validate? | yes, plus 4 warnings it justifies | yes, plus import/expression findings that reflect the stdlib-import story, not model defects |
| What is stage1DeltaV? | runtime computes through the part tree | evaluator computes the same number given positional bindings (per-calc invocation) |
| Can the model's own two-stage part compute its totalDeltaV without help? | yes — instances materialize, features chain | no — attribute defaults holding feature references (chains into part structures) are collected but not computed |
| Does InjectionDeltaV's wrong-dimension mu fail? | yes, at write time, with a dimension message | n/a — the body uses a parenthesized `^` exponent, which the expression capture falls back to text on (documented limitation of the structured-emit path); pint *would* catch the dimension if the body were evaluable |
| Does the mission state machine advance on `after 9000 [s]`? | yes, on a runtime clock | yes — time triggers drive transition-by-transition (no wall clock; you step the machine) |
| Can I ask "solve these constraints for x"? | yes (`%solve`, z3) | no — on the inspiration list |
| Can I run the same model 1000× with a parameter swept? | yes (`-sweep`) | partially (what-if bindings; no sweep CLI) |

The structural difference in one line: sysmlpy evaluates **expressions**;
OpenSysML executes **objects**. The missing layer is instance
materialization (parts with live feature values) — that, not parser
coverage, is the real gap the showcase exposes.

## 4. What sysmlpy does that OpenSysML does not

- pint unit-aware evaluation with user-declared derived units; unit errors
  raised as evaluator exceptions (theirs is a bespoke ISO-80000 engine).
- ReqIF 1.0 requirement interchange; spreadsheet (CSV/XLSX) export/import.
- Graph storage backends (NetworkX/Kuzu/Cayley) with query parity.
- Official-notation PlantUML rendering (verified against the OMG pilot's
  generator edge encodings) + terminal/SVG boxes rendering.
- Pure-Python embeddability: no child process, no gRPC hop, no 681K-line
  binary to ship — `loads()` returns a mutable tree you can extend.
- Python-native extensibility for LLM/agent workflows (the whole tree is
  dicts + duck-typed objects; easy to walk, patch, and regenerate).

## 5. Ranked inspiration (status after this exercise)

0. ~~REPL~~ — **done this round** (`sysmlpy repl`): accumulating session
   with member-granularity merge (ipython_magic semantics), %eval/%set/
   %calc/%check/%values, %sim/%send/%step, %view, %load/%save/%reset.
   OpenSysML's ~60-command surface is the same face over its runtime;
   sysmlpy's command set grows as its machinery does.

1. ~~Math built-ins~~ — **done this round** (`ln`/`exp`/`log`).
2. Sweep/samples engine (`sysmlpy sweep FILE calc param a,b,c` → table) —
   what-if bindings exist; the CLI is the missing piece. High value/effort.
3. z3 SMT solving over constraints (`sysmlpy solve`) — biggest capability
   jump; evaluator already has the constraint collection side.
4. Golden execution traces + scheduling policies + choice points for
   `sysmlpy sim` (determinism you can test, not assume).
5. doc-counts-style census: regenerate STATUS.md's test table from
   `pytest --collect-only` in CI; refuse hand-typed numbers. STATUS.md's
   header is already stale (v0.90.1 vs 0.93.0) — this exact drift is the
   failure mode the tool prevents.
6. Self-model: sysmlpy's pipeline as a `.sysml` model, AGENTS.md
   invariants as requirements checked by sysmlpy itself in CI.
7. Neutral Rendering IR (typed view model with mermaid/dot/plantuml/text
   writers) — refactor that makes the boxes renderer and future forms
   share one layer.
8. Element identity from qualified names (deterministic, stable across
   round-trips) for diff/interchange/traceability alignment.
9. Execution budgets (step/recursion caps) in the evaluator — cheap;
   the evaluator already has a calc recursion limit, budgets generalize it.
10. Pilot-differential discipline for validator rules: for each of the 31
    rule codes, record what the OMG pilot says on the same input.

## 6. Notes for gosysml

- OpenSysML validates the Go market; gosysml's niche (small importable
  parser library) is deliberately unoccupied by them. Stay lean.
- The daltskin-derived grammar deltas in sysmlpy (precedence-climbing
  expression ladder, import visibility tightening) were ported to
  gosysml's ANTLR grammar — see the v0.2.x change notes in gosysml's repo.
- Their `cmd/grammar-coverage` tool (which grammar productions does the
  test corpus actually exercise?) is a one-day port that would rank
  gosysml's remaining TODO items by risk.
- Their four-layer test contract (parser features → behavioral features →
  general, each gating the next) is the right shape for gosysml's
  PORTING_CHECKLIST ordering.