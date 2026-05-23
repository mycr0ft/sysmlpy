# sysmlpy — Project Status

Current version: **v0.20.0** (2026-05-23)

---

## Completed

### Public API Classes

These classes are fully implemented, have programmatic construction, `dump()` serialization, and test coverage.

| Class | SysML Keyword(s) | Notes |
|---|---|---|
| `Package` | `package` | Name, shortname, children, `load_from_grammar` |
| `Model` | *(root)* | Wraps packages; load from string |
| `Part` | `part` / `part def` | Typed by, children, `load_from_grammar` |
| `Item` | `item` / `item def` | Typed by, children |
| `Attribute` | `attribute` / `attribute def` | `set_value`/`get_value` with `pint` units |
| `Port` | `port` / `port def` | In/out/inout directed features, add attribute |
| `Action` | `action` / `action def` | Add in/out parameters, typed by, specializes |
| `Reference` | `ref` | Simple, typed, and redefinition (`ref :>> name : Type;`) |
| `Requirement` | `requirement def` / `requirement` | Subject, actor, doc, constraint, assume constraint |
| `UseCase` | `use case def` / `use case` | Subject, actor, include |
| `Interface` | `interface def` / `interface` | Add end, add connection |
| `Message` | `message` | From, to, of-type |
| `State` | `state def` / `state` | Transitions, entry/do/exit actions, `.parent` property |
| `Transition` | `transition` | Source, target, guard, trigger, effect |
| `Constraint` | `constraint def` / `constraint` | Assert constraint, derivation forms |
| `AnalysisCase` | `analysis def` / `analysis` | Subject, objective, result expression |
| `VerificationCase` | `verification def` / `verification` | Parse and load from grammar |
| `Concern` | `concern def` / `concern` | Parse and load from grammar |
| `View` | `view def` / `view` | Parse and load from grammar |
| `Viewpoint` | `viewpoint def` / `viewpoint` | Parse and load from grammar |
| `Individual` | `individual def` / `individual` | Parse and load from grammar |
| `Metadata` | `metadata def` / `metadata` | Parse and load from grammar |
| `Rendering` | `rendering def` / `rendering` | Parse and load from grammar |
| `Allocation` | `allocation def` / `allocation` | Parse and load from grammar |
| `Flow` | `flow def` / `flow` | Parse and load from grammar |
| `Connection` | `connection def` / `connection` | Parse and load from grammar |
| `Calculation` | `calc def` / `calc` | Parse and load from grammar |
| `Enumeration` | `enum def` / `enum` | Parse and load from grammar |

### Relationship Methods (on all Usage/Definition classes)

| Method | Syntax |
|---|---|
| `_set_typed_by()` | `: TypeName` |
| `_set_specializes()` | `:> SuperDef` (definitions) |
| `_set_subsets()` | `:> superset` (usages) |
| `_set_redefines()` | `:>> original` |

### Parser

- **ANTLR4 parser** — default parser, using OMG grammar v2026.03.0
  - `load()`, `loads()`, `load_grammar()` (public API)
  - `load_antlr()`, `load_grammar_antlr()` (explicit ANTLR4 path)
  - Full ANTLR4 visitor (`antlr_visitor.py`, ~11K lines) converting parse tree to internal dict representation
  - Supports comments, documentation blocks, and annotating elements
  - Supports Case, AnalysisCase, VerificationCase, and TradeStudy definitions
  - State machine support: entry/do/exit actions, accept/send/perform/assign nodes, transitions with guards

### Grammar Round-Trip Coverage (parse → dump)

**56 / 56 tests passing (100%)** as of 2026-05-23.

| Category | Pass | Total | Notes |
|---|---|---|---|
| Packages | 3 | 3 | Comments, docs, package structure |
| Part definitions | 1 | 1 | |
| Generalization / Subsetting / Redefinition | 3 | 3 | |
| Enumerations | 2 | 2 | |
| Parts | 2 | 2 | |
| Items | 1 | 1 | |
| Connections | 1 | 1 | |
| Ports | 2 | 2 | |
| Interfaces | 2 | 2 | |
| Binding connectors | 2 | 2 | |
| Flow connections | 3 | 3 | |
| Actions | 5 | 5 | |
| States | 5 | 5 | |
| Expressions | 4 | 4 | |
| Calculations | 3 | 3 | |
| Constraints | 7 | 7 | |
| Requirements | 4 | 4 | |
| Analysis | 3 | 3 | |
| **Total** | **56** | **56** | **100%** |

### Semantic Analysis Engine (v0.17.0 → v0.20.0)

| Feature | Status | Details |
|---|---|---|
| Symbol table | ✅ Complete | Hierarchical scopes with parent chain lookup |
| Import resolution | ✅ Complete | Namespace (`::*`), membership, recursive (`::*::**`) |
| Import visibility | ✅ Complete | `private`/`public`/`protected` enforcement |
| Library symbol index | ✅ Complete | 88 `.kerml`/`.sysml` files, ~1,417 symbols |
| Inheritance resolution | ✅ Complete | Supertype chain traversal for subsetting/redefinition |
| OCL constraints | ✅ 8 checks | See table below |

#### Implemented OCL Well-Formness Checks

| Code | Rule | Description |
|------|------|-------------|
| `UNDEFINED_SYMBOL` | — | Reference to non-existent type or feature |
| `DUPLICATE_NAME` | Namespace.duplicate_names | Two members with same name in a scope |
| `CYCLIC_SPECIALIZATION` | Type.no_cyclic_specialization | Type specializing itself (directly or indirectly) |
| `INCOMPATIBLE_SUBSETTING` | Feature.subsetting_compatible | Subsetting ref to undefined feature |
| `INCOMPATIBLE_REDEFINITION` | Feature.redefinition_compatible | Redefinition ref to undefined feature |
| `INCOMPATIBLE_PART_DEFINITION` | Part.definition_compatible | Part typed by non-PartDefinition |
| `INCOMPATIBLE_PORT_DEFINITION` | Port.definition_compatible | Port typed by non-PortDefinition |
| `INCOMPATIBLE_FEATURE_CHAIN` | Feature.chaining_compatible | Chained features with incompatible types |
| `INVALID_MULTIPLICITY_BOUNDS` | Multiplicity.bounds_valid | Lower bound > upper bound |
| `UNRESOLVED_IMPORT` | — | Import target does not exist |

### Storage Backends

| Backend | Dependencies | Persistence | Use Case |
|---------|-------------|-------------|----------|
| `InMemoryStore` | None | Volatile | Testing, small models |
| `NetworkXStore` | networkx | Volatile | Graph analysis, centrality, cycles |
| `KuzuStore` | kuzu | Disk (optional) | Embedded graph DB, Cypher queries |
| `CayleyStore` | requests | Server-managed | Remote graph DB, multi-tenant |

### PlantUML Generation

- Definitions render with sharp corners, usages with rounded corners
- Relationships differentiated by arrow style, thickness, and color
- Filtering and focus support (`focus=`, `elements=`, `max_depth=`)

### Test Coverage

| Test file | Count | Scope |
|---|---|---|
| `tests/class_test.py` | 53 tests | Programmatic API unit tests |
| `tests/grammar_test.py` | 56 tests | Grammar round-trip (parse → dump) |
| `tests/semantic_test.py` | 90 tests | Semantic analysis and OCL constraints |
| `tests/store_test.py` | 82 tests | Storage backends (memory + networkx) |
| `tests/main_test.py` | 7 tests | `load`/`loads`/`load_grammar` integration |
| `tests/conformance_test.py` | 123 tests | OMG XPect parse conformance suite |
| **Total** | **411** | |

### Documentation

- `README.md` — installation, usage examples, semantic analysis docs
- `docs/index.md` — project overview with semantic analysis reference
- `docs/quickstart.md` — step-by-step usage guide
- `docs/TUTORIAL.md` — comprehensive guide with class mapping tables
- `docs/PROJECT_SUMMARY.md` — work summary for future agents/team members
- `docs/plantuml-reference-analysis.md` — PlantUML generator assessment
- `docs/plantuml-examples/` — 9 rendered diagram examples

---

## In Progress

### Public API Stubs (parse works, `dump()` partial or broken)

These classes are instantiated during `Package.load_from_grammar()` and hold the grammar tree, but the `dump()` / `get_definition()` path is incomplete for some body elements.

| Class | SysML Keyword(s) | Status |
|---|---|---|
| `State` | `state def` / `state` | `.parent` property, transitions, entry/do/exit actions implemented; some body edge cases remain |
| `Constraint` | `constraint def` / `constraint` | Assert constraint and derivation forms now supported |
| `Connection` | `connection def` / `connection` | Multiplicity on connect-ends not parsed |
| `Flow` | `flow connection def` / `flow` | Definition and interface-body variants failing |
| `Calculation` | `calc def` / `calc` | Nested `:>>` redefines in return not yet handled |
| `Enumeration` | `enum def` | Largely working; edge cases remain |

### Internal Grammar Classes

Of the ~319 internal grammar classes in `grammar/classes.py`, approximately 175+ now have `get_definition()` implemented (up from ~145).

### ANTLR4 Grammar Limitations

All known ANTLR grammar limitations have been resolved. The conformance suite passes at 100%.

### Other Incomplete Items

- **Typed-by in `load_from_grammar`** — Type relationships are not preserved when loading elements from grammar (`usage.py`, marked `#!TODO Typed By`)
- **CHANGELOG** — Not updated since v0.5.3; v0.6.0+ work needs a new entry

### Known Bugs

| Location | Description |
|---|---|
| `grammar/classes.py` | `PackageBodyElement` name is hardcoded; `!TODO This isn't always the case` |
| `grammar/classes.py` | Identified broken code path; `#!TODO This won't work` |
| `definition.py` (`RootNamespace`) | `load_package_body()` raises `NotImplementedError` for `AliasMember` and `Import` nodes |
| `antlr_visitor.py` ~line 9558 | Top-level attribute multiplicity not captured (nested attributes work) |

---

## Not Started

### High Priority

| Feature | Description |
|---|---|
| Typed-by preservation | Type relationships not preserved when loading elements from grammar (`usage.py`, marked `#!TODO Typed By`) |
| Fix top-level attribute multiplicity | Visitor hardcodes `specialization=None` for top-level attributes |

### Medium Priority

| Feature | Description |
|---|---|
| Flow connection definition/interface | `flow def` and `flow` in interface bodies |
| Connection multiplicity ends | `connect X[0..1] to Y[1]` multiplicity in connector ends |
| Interface decomposition | End-connector structure in decomposed interfaces |
| Nested `:>>` redefines in return | `return attribute X : Type { :>> feature = expr; }` |
| Typed literal values | `LiteralInteger`, `LiteralReal`, `LiteralString` |
| Multiplicity ranges (connect ends) | `[1..5]` or `[*]` on connector end members |

### Low Priority

| Feature | Description |
|---|---|
| Grammar auto-update pipeline | Automated refresh from the OMG KEBNF spec when new releases drop |
| Activity nodes | `ActionNode`, `AssignmentNode`, `ControlNode`, `DecisionNode` |
| Full OCL constraint library | Machine-readable OCL constraints extendable without code changes |
| Parse library files (not regex) | Replace `LibrarySymbolIndex._extract_from_file()` with actual parsing |

---

## Conformance Test Suite

Source: **SysML-v2-Pilot-Implementation-2026-03** (`org.omg.sysml.xpect.tests`)
Library: **88 files** bundled at `src/sysmlpy/library/` (kernel/ systems/ domain/)
Test files: **123 `.sysml` files** under `tests/sysmlv2/`, each with a `.error` sidecar

Run with: `pytest -m conformance`

### Current results (2026-05-23)

**123 / 123 passing (100%)**

| Category | Files | Pass | Fail | Pass % |
|---|---|---|---|---|
| `simpletests/` | 37 | 37 | 0 | 100% |
| `validation/valid/` | 34 | 34 | 0 | 100% |
| `validation/invalid/` | 47 | 47 | 0 | 100% |
| `expression/` | 4 | 4 | 0 | 100% |
| `linking/` | 1 | 1 | 0 | 100% |
| **Total** | **123** | **123** | **0** | **100%** |

### Remaining Failures

None. All 123 conformance tests pass.

### Key Fixes (v0.11.0 → v0.20.0)

| Version | Fix | Tests unblocked |
|---|---|---|
| v0.11.0 | Add `LPAREN AS typeReference RPAREN` to `baseExpression` | `ElementFilter.sysml` — `(as Type)` cast syntax |
| v0.11.0 | Add `ownedExpression DOT bodyExpression` to `ownedExpression` | `PathExpressions.sysml` — lambda/filter expressions |
| v0.11.0 | Handle `filterPackage` imports in `_visit_import_rule_dict` | `ElementFilter.sysml` — `vehicle1_c1::*[@Security]` |
| v0.11.0 | Fix `interface_part` UnboundLocalError | `InterfaceUsage_Invalid.sysml` |
| v0.11.0 | Add `get_definition()` to `SuccessionFlowConnectionUsage` | `ActionUsage.sysml` |
| v0.11.0 | Add `CaseDefinition` to `DefinitionElement` dispatch table | `CaseUsage.sysml` |
| v0.11.0 | Fix `UsageExtensionKeyword` to handle `keyword` field directly | `CaseSubjectObjective_Invalid.sysml`, `Verification_invalid.sysml` |
| v0.17.0 | Fix `ImportPrefix` to accept `None` visibility | Import visibility defaults to private per spec |
| v0.17.0 | Initialize `Usage.completion` to `UsageCompletion()` | Programmatic API consistency |
| v0.17.0 | Fix `NetworkXStore.put()` missing `add_node()` | All graph algorithms were silently failing |
| v0.19.0 | Add missing `get_definition()` to interface grammar classes | Interface round-trip tests |
| v0.20.0 | Fix multiplicity capture in `_build_full_specialization_from_ctx` | Multiplicity bounds validation |

### How to Add New Conformance Tests

1. Place `.sysml` file under `tests/sysmlv2/<category>/`
2. Add companion `.error` file (empty = expects parse success, non-empty = expected error regex)
3. Tests are auto-discovered by `conformance_test.py:_collect()`

---

## Summary Counts

| Category | Count |
|---|---|
| Public API classes (complete) | 28 |
| Public API stubs (parse-only or partial) | 0 |
| Grammar classes with `get_definition()` | ~175+ of 319 |
| Grammar classes missing `get_definition()` | ~144 of 319 |
| Unit + grammar + integration tests | 216 (53 unit + 56 grammar + 7 integration + 90 semantic + 10 store) |
| Grammar round-trip tests passing | **56 / 56 (100%)** |
| Conformance tests (2026-03 XPect suite) | 123 total — **123 passing (100%)** |
| Semantic analysis tests | **90 passing** |
| Storage backend tests | **82 passing** (memory + networkx) |
| **Total tests** | **411 total — 411 passing (100%)** |
| Bundled standard library files | 88 (kernel `.kerml` + systems `.sysml` + domain `.sysml`) |
| Library symbols indexed | ~1,417 |
| LOC (as of v0.20.0) | 73,896 across 539+ commits |
