# CHANGELOG

## v0.96.1 (unreleased)

- **New loaders for package-less snippets**: `loads_wrapped()` /
  `load_wrapped()` wrap bare top-level SysML (OMG `Simple Tests` /
  training-snippet style, e.g. `part def Camera { ... }` with no
  enclosing package) in a synthetic package and load normally.
  Content already carrying a top-level `package` /
  `standard library package` passes through untouched. `Model.load`'s
  documented strictness ("Base Model must be encapsulated by a
  package") is unchanged. The corpus sweep helper (`parse_one.py`)
  now uses the wrapped loader, eliminating the 3 package-less
  rejections from the OMG release-repo sweep (DecisionTest,
  ControlNodeTest, Camera).

## v0.96.0 (2026-09-23)

**KerML parsing, OMG-corpus hardening, and community contributions
(external PRs #10/#11/#12/#13).**

- **New: KerML parser** (`src/sysmlpy/kerml/`) - ANTLR4 grammar
  generated from the OMG KerML textual-notation KEBNF
  (Systems-Modeling/SysML-v2-Release, 2026-08 checkout) via the
  daltskin generator in KerML-only mode, plus `parse`/`parse_file`/
  `parse_to_dict` and a SysML-shaped visitor-dict layer. 7 documented
  corpus corrections (generator dead-rule reverts, KEBNF-vs-example
  fixes) in `src/sysmlpy/kerml/README.md`. Corpus: **130/130 .kerml
  files parse and extract non-empty structure** (OMG examples 58, OMG
  kernel libraries 36, bundled kernel 36). KerML imports carry no
  visibility keyword (unlike SysML). Tests: `tests/kerml_test.py` (3
  pytest tests over standalone batteries).
- **LibrarySymbolIndex parses .kerml files** (was regex-scraping):
  `.kerml` files now go through `parse_to_dict`; `.sysml` files keep
  the line-regex walk (shared as the parse-failure fallback). Library
  symbols 1,604 to 2,986; all 94 OMG `.kerml` files yield symbols.
  3 regex-only names were false positives (keyword-collision in
  `feature all ...` and a doc-expression line).
- **fix: `connect [N]` with leading multiplicity through interface
  ends** - `_visit_multiplicity` reads through
  `ownedCrossMultiplicity().ownedMultiplicity()`. Found by
  categorizing the OMG corpus-sweep failures; the Annex A
  SimpleVehicleModel now parses fully (241 elements).
- **fix: Port definitions lost `is_definition`** (external PR #10) -
  `Usage.load_from_grammar`'s `__init__()` reset cleared the flag;
  port defs rendered as `<<port>>` instead of `<<port def>>`.
- **IV: boundary ports** (external PR #13) - ports render as PlantUML
  native `port` syntax on the hosting part's boundary, declared and
  inherited.
- **IV: interface-usage connections** (external PR #12) - interface
  usages render as connection edges; top-level `connect`-form and
  body-declared `end ... ::> part.port` ends, nested interfaces scoped
  to their containing part.
- **IV: binding connectors** (external PR #11) - `bind p = A.p;` is
  preserved in the public tree (was silently dropped) and renders as
  a thick binding edge between the referenced features.
- **fix: UseCase missing re-declaration chain fields** - loading any
  model with a use case crashed with `AttributeError`
  (`_specializes_names` uninitialized).

Corpus status: the OMG release-repo sweep (404 files) now has zero
correctness failures; what remains is 5 slow-but-finite large library
files (42-94 s, perf tuning candidate) and 3 package-less snippet
examples rejected by the loader's intentional package-wrapper guard.


**Markdown tables column-align in monospace (`sysmlpy.mdtables`).**

Every markdown table sysmlpy emits now lines up pipe-for-pipe when
viewed in a monospace font:

- new `src/sysmlpy/mdtables.py`: `pretty_markdown_tables(text)`
  post-processes arbitrary markdown (re-pads every pipe table that
  has a GFM separator; everything else passes through untouched) and
  `format_table(header, rows, align)` builds aligned tables
  directly. Widths follow the East Asian Width convention (Wide/
  Fullwidth = 2, combining marks = 0, Ambiguous - including the
  satisfy check mark - = 1) and count escaped characters (`\|`) as
  the single character they render as; GFM alignment colons are
  preserved through re-padding (`:--` left, `--:` right, `:-:`
  center).
- wired into every markdown emitter: all PlantUML grid views
  (tabular, data-value, relationship matrix) via
  `_format_table_rows_markdown`, the traceability report
  (`to_markdown`) and `as_traceability_matrix_view`.
- **fixed a latent matrix-structure bug the alignment work
  surfaced**: `as_relationship_matrix_view` data rows carried the
  row-label element name as the first cell but the header lacked
  the label column, so every row had one cell more than the header
  and GFM renderers silently dropped the last column. The header
  now carries the label column; the matrix CSV gains it too (header
  and rows now have equal field counts).

Honest limits (docstring): alignment cannot hold for cells whose
*rendered* width differs from the measured one - emoji and other
beyond-BMP glyphs (ambiguous across terminal fonts) or cells with
embedded newlines (which GFM tables cannot carry anyway).

Test updates: new `tests/mdtables_test.py` (10 tests); alignment-
sensitive exact-shape asserts in plantuml/traceability/cli/
spreadsheet tests updated to width-tolerant regexes; matrix CSV
test now asserts the label column and equal field counts.


## v0.95.0 (2026-09-18)

**Interactive REPL (`sysmlpy repl`), runtime-showcase fixtures, and four
silent-drop fixes found by them.**

Inspired by Open-MBEE's OpenSysML REPL, built on machinery sysmlpy
already had. See `docs/COMPARISON.md` for the three-way contrast
(sysmlpy vs OpenSysML vs gosysml) that motivated the round.

- **New tool: `sysmlpy repl`** (`src/sysmlpy/repl.py`, 28 tests in
  `tests/repl_test.py`). Declarations accumulate into a session model
  with member-granularity merge (re-declared member replaces the prior
  one, other members kept, `note:` line reports the replacement —
  the semantics `ipython_magic.py` has carried since v0.64.0, now
  shared). Multi-line submissions continue on `...>` while brackets
  stay open; a non-declaration line falls back to expression
  evaluation. 19 `%commands`: `%list/%show/%dump`, `%eval/%set/
  %bindings/%calc/%check/%values` (evaluator, pint-aware),
  `%sim/%send/%step/%state` (simulator session), `%view` (all 8
  views), `%load/%save/%reset/%quit`, `%help`; readline completion
  over commands and element names; UUID names filtered from
  qualified-name display. Session core is I/O-injectable and
  headless-testable (same pattern as `sim.run_tui`).
- **Visitor: `exhibit state` no longer silently dropped.** The grammar
  rule `exhibitStateUsage` had zero visitor handling — both spellings
  (`exhibit state m { ... }` and `exhibit state m : M;`) vanished from
  the visitor dict, the public tree, `Model.dump()`, the boxes view,
  and the simulator. Now emitted as a StateUsage dict with
  `exhibit: True`; `StateUsage` grammar class carries/dumps the
  `exhibit` keyword. Spacecraft-comms' dump went from lossy 1,177
  chars to faithful 5,334.
- **Public-API: `state def` in part/item def bodies no longer dropped**
  (no dispatch arm in the Usage body walk) and **`perform action m : M`
  no longer dropped** (no `_load_behavior_child` branch;
  PerformActionUsageDeclaration keeps name/typing in `.children`,
  now extracted — `perform action mission : LunarMission { in budget =
  Flight::budget; }` round-trips and surfaces as an Action child).
- **Evaluator: KerML math built-ins** `ln`, `exp`, `log`, `log2`,
  `log10` added (pint-aware, dimensionless results) — motivated by the
  showcase's rocket equation; positional calc-arg binding unchanged.
- **New fixtures**: the five OpenSysML runtime-showcase models copied
  to `tests/fixtures/runtime_showcase/` (Apache-2.0, attribution
  README; unchanged model text) with `tests/runtime_showcase_test.py`
  (18 tests). The evaluator reproduces OpenSysML's published showcase
  digits exactly (stage delta-v 3037.6966629706967 / 6432.955324716369
  m/s, margin 70.65198768706614) and both showcase state machines
  build and drive.
- Docs: `README.md` command table + REPL example; `STATUS.md` CLI
  section + test map; `docs/COMPARISON.md`.

Test totals at this release: 1,368 fast + 123 conformance passing
(8 skipped for optional deps not installed).


## v0.94.0 (2026-09-16)

**Relationship Matrix View: verify cells — the Vee's V side.**

`verify <req>;` relationships now land as V cells, closing the
requirements loop in the cross-checking grid: satisfy (check) shows
that a part claims to meet a requirement, verify (V) shows that a
verification case demonstrates it.

- new `_extract_verifies` recovers verify references from both
  placements: surfaced VerifyRequirementUsage wrappers (read
  directly, like satisfy) and members nested anywhere in a
  VerificationCase/Requirement grammar's definition dict (objectives
  included), recovered via an iterative `get_definition()` walk;
  qualified references (`verify P::req;`) resolve to the last
  segment, so usage-level and definition-level verifications both
  reach the requirement's axis name
- vocabulary gains `"verify": "V"`; verify wrappers join satisfy/
  allocation/connection usages in the cells-not-axes exclusion
- 2 new tests (verify-in-definition-objective and
  qualified-ref-in-usage), 13/13 matrix tests, 158/158
  plantuml_test.py


## v0.93.0 (2026-09-16)