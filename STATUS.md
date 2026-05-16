# sysml2py — Project Status

Current version: **v0.10.0**

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
  - Full ANTLR4 visitor (`antlr_visitor.py`, ~10,800 lines) converting parse tree to internal dict representation
  - Supports comments, documentation blocks, and annotating elements
  - Supports Case, AnalysisCase, VerificationCase, and TradeStudy definitions
  - State machine support: entry/do/exit actions, accept/send/perform/assign nodes, transitions with guards

### Grammar Classes with `get_definition()`

The following grammar classes now have `get_definition()` for serialization (added in v0.10.0):

- `FeatureChainMember`, `FeatureBinding`, `ResultExpressionMember`, `UsagePrefix`
- `PerformActionUsage`, `AcceptNodeDeclaration`, `SendNodeDeclaration`
- `SenderReceiverPart`, `EmptyParameterMember`, `StateAcceptActionUsage`, `StateSendActionUsage`
- `EffectBehaviorMember`, `GuardExpressionMember`, `NodeParameterMember`, `ReferenceUsage`
- `AssertConstraintUsage`, `RequirementConstraintMember`, `RequirementConstraintKind`
- `RequirementConstraintUsage`, `RequirementUsage`, `SatisfyRequirementUsage`
- `SatisfactionSubjectMember`, `SatisfactionParameter`, `SatisfactionFeatureValue`, `SatisfactionReferenceExpression`
- `FlowConnectionDefinition`, `ActionDefinition`, `RequirementDefinition`, `RequirementBody`
- `MultiplicityRelatedElement` (handles `FeatureReferenceExpression` for variable bounds)
- `QualifiedName` (handles both `names` and `parts` keys)

### Grammar Round-Trip Coverage (parse → dump)

**34 / 56 tests passing (61%)** as of 2026-05-16.

| Category | Pass | Total | Notes |
|---|---|---|---|
| Packages | 3 | 3 | Comments, docs, package structure |
| Part definitions | 1 | 1 | |
| Generalization / Subsetting / Redefinition | 3 | 3 | |
| Enumerations | 2 | 2 | |
| Parts | 2 | 2 | |
| Items | 1 | 1 | |
| Connections | 0 | 1 | Multiplicity in `connect` syntax |
| Ports | 2 | 2 | |
| Interfaces | 1 | 2 | Interface decomposition still failing |
| Binding connectors | 2 | 2 | |
| Flow connections | 1 | 3 | Definition and interface variants failing |
| Actions | 5 | 5 | All action tests now pass |
| States | 0 | 5 | State machine bodies not yet implemented |
| Expressions | 4 | 4 | |
| Calculations | 2 | 3 | Nested `:>>` redefines in return not yet handled |
| Constraints | 2 | 7 | `assert constraint`, derivation, time constraints remaining |
| Requirements | 0 | 4 | Requirement body items not yet implemented |
| Analysis | 0 | 3 | Analysis case bodies not yet implemented |
| **Total** | **34** | **56** | **61%** |

### Test Coverage

| Test file | Count | Scope |
|---|---|---|
| `tests/class_test.py` | 53 tests | Programmatic API unit tests |
| `tests/grammar_test.py` | 56 tests | Grammar round-trip (parse → dump) |
| `tests/main_test.py` | 7 tests | `load`/`loads`/`load_grammar` integration |
| `tests/conformance_test.py` | 123 tests | OMG XPect parse conformance suite |

### Documentation

- `README.md` — installation, basic usage examples
- `docs/source/quickstart.md` — step-by-step usage guide
- `docs/source/conf.py` / `index.rst` — Sphinx docs setup
- `docs/IMPLEMENTATION_STATUS.md` / `IMPLEMENTATION_STATUS_V2.md` — internal grammar class tracking

### CI/CD

- GitHub Actions: Black auto-format, pytest + coverage, PyPI release via `python-semantic-release`

---

## In Progress

These features exist partially — either parse-in works but dump is incomplete, or implementation covers only some test cases.

### Grammar Round-Trip (active work area)

The visitor (`antlr_visitor.py`) and grammar classes (`grammar/classes.py`) are the primary targets for round-trip improvements.

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

### ANTLR4 Grammar Limitations (remaining XPect failures)

The 1 remaining conformance failure is an ANTLR grammar issue, not Python code:

| Test | Issue |
|---|---|
| `simpletests/ElementFilter.sysml` | `(as Type)` cast syntax not supported in ANTLR grammar |

### Other Incomplete Items

- **Typed-by in `load_from_grammar`** — Type relationships are not preserved when loading elements from grammar (`usage.py`, marked `#!TODO Typed By`)
- **CHANGELOG** — Not updated since v0.5.3; v0.6.0+ work needs a new entry

### Known Bugs

| Location | Description |
|---|---|
| `definition.py` | Duplicate `elif inner_class == "ActionUsage"` block — dead code |
| `grammar/classes.py` | `PackageBodyElement` name is hardcoded; `!TODO This isn't always the case` |
| `grammar/classes.py` | Identified broken code path; `#!TODO This won't work` |
| `definition.py` (`RootNamespace`) | `load_package_body()` raises `NotImplementedError` for `AliasMember` and `Import` nodes |

---

## Not Started

### High Priority

| Feature | Description |
|---|---|
| State machine bodies | `StateBodyItem`, entry/do/exit action members, `accept X then Y` transitions — blocks 5 state tests |
| Requirement bodies | Requirement-specific body items (`subject`, `require constraint`, `frame`) — blocks 4 requirement tests |
| Analysis case bodies | Subject, objective requirement, result expression — blocks 3 analysis tests |
| `assert constraint` usage | `assertConstraintUsage` ANTLR visitor + class wrapping — blocks 2+ constraint tests |
| Path expressions | ANTLR grammar support for `(path)` syntax covering remaining expression test |
| Element filter casts | ANTLR grammar support for `(as Type)` cast syntax |

### Medium Priority

| Feature | Description |
|---|---|
| Flow connection definition/interface | `flow def` and `flow` in interface bodies — blocks 2 flow tests |
| Connection multiplicity ends | `connect X[0..1] to Y[1]` multiplicity in connector ends — blocks 1 connection test |
| Interface decomposition | End-connector structure in decomposed interfaces — blocks 1 interface test |
| Nested `:>>` redefines in return | `return attribute X : Type { :>> feature = expr; }` — blocks Calculation Usages 2 |
| Typed literal values | `LiteralInteger`, `LiteralReal`, `LiteralString` — needed for typed attribute values beyond `pint` quantities |
| Multiplicity ranges (connect ends) | `[1..5]` or `[*]` on connector end members |

### Low Priority

| Feature | Description |
|---|---|
| ~~Remove textX runtime~~ | **Done** — textX tooling, grammar files, and CI references removed |
| ~~Action parameters via `loads()`~~ | **Done** — action body items (in/out params) now round-trip correctly |
| ~~Binding connectors~~ | **Done** — `bind X = Y` in action/part bodies round-trips correctly |
| Grammar auto-update pipeline | Automated refresh from the OMG KEBNF spec when new releases drop |
| Activity nodes | `ActionNode`, `AssignmentNode`, `ControlNode`, `DecisionNode` |

---

## Conformance Test Suite

Source: **SysML-v2-Pilot-Implementation-2026-03** (`org.omg.sysml.xpect.tests`)
Library: **94 normative files** bundled at `src/sysml2py/library/` (kernel/ systems/ domain/)
Test files: **123 `.sysml` files** under `tests/sysmlv2/`, each with a `.error` sidecar

Run with: `pytest -m conformance`

### Current results (2026-05-16)

**122 / 123 passing (99.2%)**

| Category | Files | Pass | Fail | Pass % |
|---|---|---|---|---|
| `simpletests/` | 37 | 36 | 1 | 97% |
| `validation/valid/` | 34 | 33 | 1 | 97% |
| `validation/invalid/` | 47 | 46 | 1 | 98% |
| `expression/` | 4 | 3 | 1 | 75% |
| `linking/` | 1 | 1 | 0 | 100% |
| **Total** | **123** | **122** | **1** | **99%** |

### Remaining Failures

The single remaining failure is an ANTLR grammar syntax issue, not Python code:

| Test | Error |
|---|---|
| `simpletests/ElementFilter.sysml` | `no viable alternative at input '(as'` — element filter cast syntax not supported in ANTLR grammar |

### Key Fixes (v0.10.0 — 2026-05-16)

| Fix | Tests unblocked |
|---|---|
| Add `get_definition()` to 25+ grammar classes (state actions, requirements, constraints, satisfaction, node declarations) | AssignmentTest, StateTest, RequirementTest, ConstraintTest |
| Add missing grammar classes: `AcceptNodeDeclaration`, `SendNodeDeclaration`, `SenderReceiverPart`, `EmptyParameterMember`, `StateAcceptActionUsage`, `StateSendActionUsage` | StateTest, AssignmentTest |
| Fix visitor bugs: `cud` → `cud_ctx` typo, `ud` uninitialized variable, missing `_visit_send_node_declaration`/`_visit_accept_node_declaration` | RequirementTest, StateTest, EnumerationTest |
| Add `DefinitionElement` handlers for `RequirementUsage`, `SatisfyRequirementUsage`, `VerificationCaseDefinition` | RequirementTest, VerificationTest |
| Fix `PackageBody` to handle `UsageElement` and `DefinitionElement` directly | TradeStudyTest |
| Fix prefix handling to use dynamic class lookup for polymorphic prefix types (`OccurrenceDefinitionPrefix`, `OccurrenceUsagePrefix`, `MemberPrefix`) | ConnectionTest, VariabilityTest, ViewTest |
| Make `RequirementBody`, `DefinitionDeclaration`, `NodeParameterMember`, `EffectBehaviorMember`, `GuardExpressionMember` lenient with `None`/missing values | VariabilityTest, VerificationTest, StateTest |
| Handle variable multiplicity bounds (e.g., `[1..i]`) via `FeatureReferenceExpression` | MultiplicityTest |
| Add `RequirementUsage`, `AssertConstraintUsage`, `SatisfyRequirementUsage` to `definition.py` `load_from_grammar` | RequirementTest, ConstraintTest |
| Add `AnalysisCaseUsage` to top-level visitor `_visit_usage_element_dict` | AnalysisTest |
| Fix `FlowConnectionDefinition` and `ActionDefinition` prefix handling | ConnectionTest, VariabilityTest |

### How to Add New Conformance Tests

1. Place `.sysml` file under `tests/sysmlv2/<category>/`
2. Add companion `.error` file (empty = expects parse success, non-empty = expected error regex)
3. Tests are auto-discovered by `conformance_test.py:_collect()`

---

## Summary Counts

| Category | Count |
|---|---|
| Public API classes (complete) | 27 |
| Public API stubs (parse-only or partial) | 0 |
| Grammar classes with `get_definition()` | ~175+ of 319 |
| Grammar classes missing `get_definition()` | ~144 of 319 |
| Unit + grammar + integration tests | 116 (53 unit + 56 grammar + 7 integration) |
| Grammar round-trip tests passing | **34 / 56 (61%)** |
| Conformance tests (2026-03 XPect suite) | 123 total — **122 passing (99%)** |
| Bundled standard library files | 94 (36 kernel `.kerml` + 21 systems `.sysml` + 37 domain `.sysml`) |
