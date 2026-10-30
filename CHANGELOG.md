# CHANGELOG

## 0.99.4 (2026-10-29)

- **`part def`-body feature-value members no longer drop from the
  model** (issue #19, Shamal Faily). A `:>> feature = value;` member
  sharing its body with a sibling (the ARCH reproducer's
  `:>> description = "ArchObjt";` next to
  `part aTemplate subsets templates : RefinedTemplate;`) parsed but
  vanished from `model.dump()` — the shared body flatten had no
  `DefaultReferenceUsage` dispatch, so the member was not rebuilt
  (bare members survived only by luck of an untouched rebuild). The
  shared body walker now builds a `Reference` child, and
  `Reference.load_from_grammar` handles the `DefaultReferenceUsage`
  shape (name/type from the `:>>` chain, value kept in the grammar
  for byte-faithful re-serialization).
- `Reference._typed_by_name` for a bare redefinition member resolves
  to the redefined feature (`find()` navigation works).
- Regression: `tests/issue19_test.py` (3, incl. the full ARCH
  reproducer and body-order permutations). Full suite 0 failed.

## 0.99.3 (2026-10-29)

- **Annex A dump round-trip (Vehicle Example, issues reported by
  Luciano Kruk — SYSMLPY_099_ANNEX_A_UPSTREAM_ISSUES.md)**: the dump
  of a model whose source parses emitted unparseable text in four
  shapes. Fixed in the grammar-class serializers:
  1. `Usage.dump` / `UsageCompletion.dump` joined the declaration,
     `default` valuepart, and body with no separator —
     `attribute :>> cargoMassdefault 0[kg];` (also the
     expression-valued and the `subject ... default` forms) — joins
     are space-separated now.
  2. `FeatureDeclaration.dump` glued the identification onto the
     specialization (`shankPort:>>`, `I: WheelHubInterface`) — space
     separated.
  3. `InterfaceUsage.dump` dropped the statement terminator for
     body-less usages (`interface I : X` unparseable on reparse).
  4. `InterfaceEnd.dump` emitted connector-end cross multiplicities
     AFTER the feature chain; the grammar
     (`connectorEnd : (ownedCrossMultiplicityMember)? (name (::>)?
     ownedReferenceSubsetting)`) requires them FIRST — now
     `[1] lugNutCompositePort ::> wheel1.lugNutCompositePort`.
  Result: the complete Annex A model parses (no recovery warnings),
  its dump reparses cleanly, and 7 regression tests pin every form
  (`tests/annex_a_roundtrip_test.py`, incl. the withdrawn
  trailing-multiplicity form being rejected deterministically).
  Note: the report's issue 4 misquotes the source — the Annex A
  connect lines (640/642) already use the normative LEADING
  multiplicity form; the trailing form is upstream-withdrawn.
  Residual (cosmetic, not in scope): doc-comment text re-wraps
  whitespace on round trip.

## 0.99.2 (2026-10-29)

- **pyproject: the ``boxes`` extra's constraint broke Poetry/pip
  metadata** — ``boxes = ["diagramboxes (>=0.15.1)"]`` violates
  Poetry's extras pattern (must be a bare name); it also referenced
  a dependency never declared. Fixed:
  ``diagramboxes = { version = ">=0.15.1", optional = true }`` plus
  ``boxes = ["diagramboxes"]`` — the first ``sysmlpy[boxes]``
  install that actually pulls diagramboxes.
- **boxes_view: an actionable error for stale diagramboxes
  environments** (issue #17). The v2 action-flow glyphs
  (``chamfer=`` octagons, ``action_start()`` solid diamonds) need
  diagramboxes >= 0.15.1; the ``boxes`` extra used to be
  unconstrained, so stale environments surfaced 23 raw
  ``TypeError: Diagram.add_node() got an unexpected keyword
  argument 'chamfer'`` failures. ``as_action_flow_view_boxes`` now
  capability-checks ``Diagram.add_node`` and raises an ImportError
  with the upgrade line; the extra is pinned
  ``diagramboxes (>=0.15.1)``. Tests:
  ``boxes_view_test.py::TestDiagramboxesVersionGuard`` (2; the file
  is 71 green with diagramboxes 0.18.5).

## 0.99.0 (2026-10-28)

- **Variation / variant / abstract round-tripping** (the
  SysML-v2-Release Vehicle Example, "SysML v2 Spec Annex A
  SimpleVehicleModel.sysml"): the usage-level ``abstract``/
  ``variation`` ref-prefixes were parsed but dropped (a bare
  ``abstract part family`` produced NO prefix dict at all) and every
  ``variant part/attribute x`` member inside a variation body was
  silently dropped — the same silent-loss shape as the earlier
  message-in-body bug. Fixed end to end: the ref-prefix extractors
  now carry ``isAbstract``/``isVariation`` for both the occurrence
  and usage dict paths; the definition/usage body walkers dispatch
  the ``VARIANT variantUsageElement`` alternative through a new
  ``VariantUsageMember`` wrapper (grammar class + dump emits
  ``variant ``); the semantic model carries ``is_variant`` /
  ``is_variation`` / ``is_abstract`` on Usage elements, and the
  dumps re-emit the keywords so parse -> dump -> reparse is stable.
- **Helper functions**: ``Usage.variants()`` — the variant members
  of a variation; ``Usage.variant_types()`` — the types referenced
  by ``variant part x : T`` members, resolved against the model tree
  (mirrors the corpus' ``variant part
  transmissionAutomatic:TransmissionAutomatic``).
- Known pre-existing (unchanged): the Annex A full-dump reparse
  still fails at 0.98.0 — value parts concatenate
  (``massActualdefault 0[kg]``) and bind connectors serialize as
  ``[1] to ... [1]`` — tracked separately from this change.
- tests/variation_variant_test.py: 9 tests incl. the corpus file.

## 0.98.1 (2026-10-28)

- **Interchange export keeps `:>>` redefinitions/typing on unnamed
  end features** (PR #18): an `allocation def` re-exported through
  `to_interchange`/`dump()` dropped the end redefinition/typing and
  the dump reparse failed; the ANTLR dict builder
  (`_make_end_feature_usage_dict`) now extracts specialization from
  the direct featureDeclaration too (via
  `_build_full_specialization_from_fsp`, the typings/redefinitions/
  subsettings/references builder) and merges in textual order.
  Regression: `tests/interchange_test.py` `TestAllocationEndExport`
  (round-trip, dump content, dump reparse, CLI exit code).
- Includes 0.98.0 (the interaction def/usage grammar fix + the
  message ends/payload carrying).

## 0.98.0 (2026-10-28)

- **Interaction definitions/usages parse (the `interaction def` rule).**
  The generated grammar's `interaction` rule
  (`typePrefix INTERACTION classifierDeclaration typeBody`) rejected
  every `interaction def X { ... }` form (and even a bare
  `interaction T;`) - the rule now follows the part/occurrence shape:
  `interactionDefinition : occurrenceDefinitionPrefix INTERACTION DEF
  definition` + `interactionUsage : occurrenceUsagePrefix INTERACTION
  usage`, dispatched in `definitionElement`/`structureUsageElement`;
  the parser regenerated with the bundled 4.13.2 jar.

## 0.97.1 (2026-10-16)
## 0.97.1 (2026-10-16)

- **Boxes action-flow view: v2-native glyphs** (with diagramboxes
  0.15.x-0.17.x): action usages/definitions render as chamfered
  octagons and succession starts as the solid v2 start diamond;
  named succession statements (`succession s1 first start then b;`)
  bind their keyword ends (start/done/terminate) to the control
  primitives, parented to the anchor action's owner box. Duplicate
  flow/succession edges from wrapper re-collection are deduped
  (`_edge_once`). Example: `examples/v2_action_flow_poc.py`
  (validated 10/10 against the Intro deck's providePower figure).
- Fixes the stale `__version__` string (shipped 0.96.4 inside the
  0.97.0 wheel).

## 0.97.0 (2026-09-30)


- **CI integrations: GitHub Actions, GitLab CI, pre-commit (new
  `sysmlpy ci` subcommand).** One engine (`src/sysmlpy/ci_check.py`)
  behind every integration, one exit-code contract: 0 clean, 1
  findings at/above the failure level (parse failures always block),
  2 operational error.
  - **Parse gate (blocking, always on):** every `.sysml`/`.kerml` file
    must parse (`.kerml` via the KerML grammar). Syntax errors carry
    `file:line:col`.
  - **Semantic gate (advisory by default, `--semantic strict`
    opt-in):** findings are reported and labeled, but never fail the
    check by default — the bundled standard library is symbol-indexed,
    not model-loaded, so re-export facades (`ISQ`) and unit usages
    (`SI::*`, `kg`, `['m/s²']`) are known false-positive classes
    (28/71 valid-corpus files). Promote per-codebase once clean; the
    `known_limitation` flag in JSON output identifies the classes.
  - **GitHub reusable workflow** `.github/workflows/sysml-check.yml`
    (`uses: mycr0ft/sysmlpy/.github/workflows/sysml-check.yml@vX.Y.Z`)
    with DFA-cache restore for fast re-runs; also dogfoods on this
    repo's pushes/PRs (gating the bundled library + showcase fixtures).
  - **GitLab template** `.gitlab/sysml-check.gitlab-ci.yml`
    (`include: project: mycr0ft/sysmlpy, file:
    .gitlab/sysml-check.gitlab-ci.yml`, extend `.sysml-check`).
  - **pre-commit hooks** `.pre-commit-hooks.yaml` (`sysmlpy-ci`,
    `sysmlpy-parse`) — commit-time checks on changed files.
  - Docs: `docs/ci-integration.md` (full options + promote-to-strict
    path); README CI section. Tests: `tests/ci_check_test.py` (25).
- **Visitor fix: named multiplicity bounds** (`[nCauses]`, `[wallNumber]`)
  — two of the three `_make_bound` copies in `antlr_visitor.py` called
  `int()` on the bound text and crashed (`invalid literal for int()`)
  on non-numeric bounds; both now emit a `FeatureReferenceExpression`
  like the third copy. Found by dogfooding the new CI gate on the
  bundled library: `CausationConnections.sysml` and
  `ShapeItems.sysml` now parse (previously crashed at load).


- **`qn_registry()` (P3 Vee-join side table).** Every
  `to_interchange(stable_ids=True)` document now carries
  `"#qn_registry"`: deduped declared-QN path → stable `@id`
  (Identification nodes; doc-carried explicit ids included), readable
  with the new public helper of the same name — downstream consumers
  (pyoslc STEP domain) join SysML elements by qualified name without
  re-deriving hash chains. Empty for position-id exports. The
  registry is stable across export→import→export, survives JSON
  round-trips, and reconcile_ids adoption remaps it alongside the
  graph refs. Pinned by `tests/qn_registry_test.py` (11).

## v0.96.4 (2026-09-30)

- **`doc_ids=True` on `to_interchange` (Phase 2b, L3 explicit
  identity)** — `doc /* @id: … */` comments inside an element's own
  braces fix its interchange `@id` (implies `stable_ids`): never
  re-minted over, surviving any edit (ancestor renames, re-nesting,
  cross-file moves) because the carrier rides the source text.
  Duplicate claims of one id raise at export.  Placement contract
  (inside braces vs sibling-level bubbling) pinned by tests; end-to-end
  verified export → dump → re-parse → export.  Scope record:
  `docs/stable-identities.md` §4 Phase 2b; demo:
  `examples/element_identity.py` section 6.
- **`reconcile_ids` / `to_interchange(reconcile_with=...)`** carry
  forward from v0.96.3 (L3 registry reconciliation).

## v0.96.3 (2026-09-28)

- **Stable element identities across edits (L2 + L3 idempotency).**
  - `to_interchange(stable_ids=True)` / CLI `sysmlpy export
    --stable-ids`: content-addressed `@id`s — named elements hash
    their declared qualified-name path + metaclass type, unnamed
    elements hash the nearest named anchor + structural path.
    Inserting/reordering unrelated elements elsewhere leaves
    untouched ids unchanged.  Default (`stable_ids=False`) stays
    byte-identical to the v0.63.0 position scheme.
  - **`reconcile_ids(document, registry)`** / CLI
    `sysmlpy export --reconcile-with model.json -o model.json`: the
    previous export doubles as an id registry — name-matched
    elements adopt registry ids, so ids survive ancestor renames and
    re-nesting (injective (declaredName, @type) matching keeps
    documents collision-free; nested `{"@id"}` refs are remapped so
    reconciled documents import cleanly; the CLI one-liner is an
    idempotent fixed point after the first export).
- New public exports: `reconcile_ids`,
  `STABLE_NAMESPACE`, `doc_ids=True` (v0.96.4: explicit
  `doc /* @id: … */` ids honored at export).
- New demo: `examples/element_identity.py` — all identity layers
  (parse uuid4, position uuid5, content uuid5, registry reconciliation)
  runnable end to end.
- New docs: `docs/stable-identities.md` (idempotency levels L0-L3,
  options analysis, design decision: declared-path not resolved-QN,
  Phase 1 + Phase 2 implementation records); README section
  "Element Identity: Stable Interchange IDs".
- All gates green: interchange 59/59 (11 stable-id + 10 reconcile
  tests), fast suite 654 passed/1 skipped.  (Grammar 168/168, XPect
  conformance 123/3 optional-dep skips, KerML 5/5 — unchanged from
  v0.96.2, untouched by this release.)

## v0.96.2 (2026-09-28)

- **Grammar upgraded to OMG release 2026-08** — the vendored ANTLR4
  grammar is now daltskin/sysml-v2-grammar **v2026.08.1** (upstream
  `14b0d7a`), replacing the 2026.05.0 base + local patches. Includes
  upstream #11's flat precedence-correct `ownedExpression` cascade and
  upstream #16's required import visibility (bare `import X;` is now a
  `SysMLSyntaxError`; use `private`/`public`/`protected`).
- **Non-normative forms removed** (resolved against the OMG KEBNF and
  the pilot KerMLExpressions.xtext with daltskin): bare qualified
  identification (`subject SystemGateway::System_Driver;` — use the
  typed form `subject : SystemGateway::System_Driver;`) and
  connector-end trailing multiplicity (`connect a[1] to b;` — use the
  normative leading form `connect [1] a to b;`).
- Visitor: structured expression chains re-emitted from the flat
  left-recursive parse tree (revived v0.52.0 splice machinery);
  symbol-form `&`/`|` operators structured; multi-segment
  `FeatureChainMember` (one context, many name segments) fully
  captured so feature-chain type resolution reports the whole chain.
- `ConnectorEnd` preserves the normative leading cross-multiplicity
  and dumps it before the declared name.
- All gates green: grammar 168/168, fast suite 595 passed/1 skipped,
  OMG XPect conformance 123 passed/3 skipped (optional-dep skips),
  KerML batteries 5/5.


- (empty — Phase 2b released in v0.96.4, registry reconciliation in
  v0.96.3)

## v0.96.1 (2026-09-25)

- **doc comments survive everywhere** — `doc /* ... */` on a package,
  on any part/item/port/action/... usage or definition, and inside
  interface bodies is captured as `.doc` on the API object (previously
  silently dropped whenever the comment shared its body with
  siblings; only Requirement carried doc). `dump()`/`classtree()` re-emits
  the doc alongside the other body items, and re-parsing the dumped
  text keeps `.doc` intact. New example `examples/doc_ends_flows.py`
  + 11 tests (doc_ends_flows 5/5).
- **interface ends captured** — `end <name>;` and
  `end <name> ::> part.port;` members of an interface body now parse
  into `Interface.ends` (name/type/multiplicity) and
  `Interface.iface_connections` (the `::>` targets as feature-path
  strings); previously the ends stayed in the grammar layer only and
  `.ends` was always empty. `end ::>` targets are re-emitted through
  the References/OwnedReferenceSubsetting/OwnedFeatureChain
  specialization chain, so they survive a dump round-trip (and
  re-parsing rebuilds `iface_connections`).
- **fix: round-trip of interface usages emitted a spurious `connect`
  keyword** — `InterfaceUsageDeclaration` marked ANY `part1` as the
  CONNECT form, but the visitor also emits an empty `part1` for plain
  ``interface x : T { ... }``; the resulting
  ``interface x: T connect {...}`` dump re-parsed with a syntax error.
  The `connect` keyword is now only set when the binary part actually
  carries the CONNECT-form ends (grammar tests 165/165).
- **flows** — verified end-to-end (already working): `flow a to b;`
  parses into a `Flow` child of the owning part, `dump()` re-emits it,
  and the Interconnection View renders the flow edge.

- **perf: DFA cache supersede** - `save_dfa_cache()` refused to update
  an existing cache file, so DFA states learned after the file was
  written (short-name `<K>` forms, `[1..*] nonunique` multiplicity
  chains, STRING short-names) were re-built by every fresh process:
  the OMG library files SI / ISQSpaceTime / MeasurementReferences /
  ShapeItems and Annex A SimpleVehicleModel took 60-200 s per parse.
  A strictly-warmer in-process cache now atomically replaces the file;
  after one absorbing run per construct family, all six slowest OMG
  files parse in 0.2-8 s per fresh CLI process. 2 new supersede tests
  (dfa_cache 16/16).
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