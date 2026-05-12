# sysml2py — Project Status

Current version: **v0.6.0** (note: `pyproject.toml` still reads `0.5.3` — needs sync)

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
  - Full ANTLR4 visitor (`antlr_visitor.py`, ~3,300 lines) converting parse tree to internal dict representation
  - Supports comments, documentation blocks, and annotating elements
  - Supports Case, AnalysisCase, and VerificationCase definitions

### Grammar Classes with `get_definition()`

The following grammar classes now have `get_definition()` for serialization:

- `InterfaceDefinition`, `InterfaceBody`, `InterfaceBodyItem`, `InterfaceUsage`
- `AnnotatingElement`, `CommentSysML`, `Annotation`, `Documentation`
- `ActionUsage`
- `LiteralString`, `LiteralReal`, `LiteralInfinity`

### Test Coverage

| Test file | Count | Scope |
|---|---|---|
| `tests/class_test.py` | 53 tests | Programmatic API unit tests |
| `tests/grammar_test.py` | 56 tests | Grammar round-trip (parse → dump) |
| `tests/main_test.py` | 7 tests | `load`/`loads`/`load_grammar` integration |
| `tests/conformance_test.py` | 123 tests | OMG XPect parse conformance suite |

Round-trip tests cover: packages, parts, items, attributes, ports, connections, flows, interfaces, actions, states, expressions, calculations, constraints, requirements, analysis cases, and use cases.

### Documentation

- `README.md` — installation, basic usage examples
- `docs/source/quickstart.md` — step-by-step usage guide
- `docs/source/conf.py` / `index.rst` — Sphinx docs setup
- `docs/IMPLEMENTATION_STATUS.md` / `IMPLEMENTATION_STATUS_V2.md` — internal grammar class tracking (see note below)

### CI/CD

- GitHub Actions: Black auto-format, pytest + coverage, PyPI release via `python-semantic-release`

---

## In Progress

These features exist partially — either parse-in works but dump is broken, or implementation is incomplete.

### Public API Stubs (parse works, `dump()` broken)

These classes are instantiated during `Package.load_from_grammar()` and hold the grammar tree, but have no rich `dump()` / `get_definition()` implementation. They can be loaded from SysML text but cannot be serialized back.

| Class | SysML Keyword(s) |
|---|---|
| `State` | `state def` / `state` |
| `Constraint` | `constraint def` / `constraint` |
| `Connection` | `connection def` / `connection` |
| `Flow` | `flow connection def` / `flow` |
| `Calculation` | `calc def` / `calc` |
| `Enumeration` | `enum def` |
| `Allocation` | `allocation def` / `allocation` |
| `Metadata` | `metadata def` / `metadata` |
| `Rendering` | `rendering def` / `rendering` |
| `Individual` | `individual def` / `individual` |
| `FlowDef` | `flow def` |
| `View` | `view def` / `view` |
| `Viewpoint` | `viewpoint def` / `viewpoint` |
| `Concern` | `concern def` / `concern` |
| `Case` | `case def` / `case` |
| `AnalysisCase` | `analysis def` / `analysis` |
| `VerificationCase` | `verification def` / `verification` |

### Internal Grammar Classes

Of the 319 internal grammar classes in `grammar/classes.py`, approximately 145 have `get_definition()` implemented. The remaining ~174 lack serialization and cannot round-trip to text.

### ANTLR4 Grammar Limitations (remaining XPect failures)

The 3 remaining conformance failures are ANTLR grammar issues, not Python code gaps:

| Test | Issue |
|---|---|
| `expression/PathExpressions.sysml` | Path expression syntax not supported in ANTLR grammar |
| `simpletests/ElementFilter.sysml` | `(as Type)` cast syntax not supported |
| `validation/invalid/MetadataUsage_Invalid.sysml` | ANTLR grammar gap |

### Other Incomplete Items

- **Action parameters via `loads()`** — In/out parameters only work for programmatic construction; loading an action with parameters from SysML text is broken
- **Typed-by in `load_from_grammar`** — Type relationships are not preserved when loading elements from grammar (`usage.py`, marked `#!TODO Typed By`)
- **CHANGELOG** — Not updated since v0.5.3; v0.6.0 work (ANTLR4 migration, new public API classes, conformance suite) is now documented
- **Version sync** — `__init__.py` says `0.6.0`, `pyproject.toml` still says `0.5.3`

### Known Bugs

| Location | Description |
|---|---|
| `definition.py` | Duplicate `elif inner_class == "ActionUsage"` block — dead code |
| `grammar/classes.py` | `PackageBodyElement` name is hardcoded; `!TODO This isn't always the case` |
| `grammar/classes.py` | Identified broken code path; `#!TODO This won't work` |
| `definition.py` (`RootNamespace`) | `load_package_body()` raises `NotImplementedError` for `AliasMember` and `Import` nodes |
| repo root + `tests/` | `temp.txt` etc. scratch files — leftover artifacts to clean up |

---

## Not Started

### High Priority

| Feature | Description |
|---|---|
| Package imports | `import Package::*;` — `Import` and `AliasMember` grammar classes need `get_definition()` and `RootNamespace.load_package_body()` stubs filled in |
| Full `dump()` for stub classes | Implement `get_definition()` on `State`, `Constraint`, `Connection`, `Flow`, `Calculation`, `Enumeration` (currently parse-in only — see In Progress above) |
| Path expressions | ANTLR grammar support for `(path)` syntax covering remaining expression test |
| Element filter casts | ANTLR grammar support for `(as Type)` cast syntax |

### Medium Priority

| Feature | Description |
|---|---|
| Typed literal values | `LiteralInteger`, `LiteralReal`, `LiteralString` — needed for typed attribute values beyond `pint` quantities |
| Enumerated values | `EnumeratedValue` — enum literal values within `enum def` bodies |
| Type relationship classes | `FeatureTyping`, `FeatureSpecialization`, `OwnedFeatureTyping`, `OwnedSubsetting` — rich serializable type/specialization relationships |
| Multiplicity ranges | `MultiplicityRange` — `[1..5]` or `[*]` multiplicity on features |
| Requirement subjects | `SubjectUsage`, `SubjectMember` — `subject` element inside requirement definitions |
| `ReferenceUsage` dump | `ReferenceUsage` grammar class `get_definition()` (the `Reference` public class wraps this; serialization path is incomplete) |

### Low Priority

| Feature | Description |
|---|---|
| State machine details | `StateBodyItem`, `TransitionUsage`, `EffectBehaviorUsage` (do/entry/exit behaviors), guard expressions |
| Requirement satisfaction | `SatisfyRequirementUsage` — `satisfy requirement X by Y;` |
| Use case objectives | `ObjectiveRequirementUsage` |
| Connector internals | `ConnectorEnd`, `FlowFeature`, `BindingConnector` serialization |
| Activity nodes | `ActionNode`, `AssignmentNode`, `ControlNode`, `DecisionNode` |
| ~~Remove textX runtime~~ | **Done** — textX tooling, grammar files, and CI references removed |
| Grammar auto-update pipeline | Automated refresh from the OMG KEBNF spec when new releases drop |

---

## Conformance Test Suite

Source: **SysML-v2-Pilot-Implementation-2026-03** (`org.omg.sysml.xpect.tests`)
Library: **94 normative files** bundled at `src/sysml2py/library/` (kernel/ systems/ domain/)
Test files: **123 `.sysml` files** under `tests/sysmlv2/`, each with a `.error` sidecar

Run with: `pytest -m conformance`

### Current Results (2026-05-12)

**120 / 123 passing (97.6%)**

| Category | Files | Pass | Fail | Pass % |
|---|---|---|---|---|
| `simpletests/` | 37 | 35 | 2 | 95% |
| `validation/valid/` | 34 | 33 | 1 | 97% |
| `validation/invalid/` | 47 | 46 | 1 | 98% |
| `expression/` | 4 | 3 | 1 | 75% |
| `linking/` | 1 | 1 | 0 | 100% |
| **Total** | **123** | **120** | **3** | **98%** |

### Remaining Failures

All 3 failures are ANTLR grammar syntax issues, not Python code gaps:

| Test | Error |
|---|---|
| `expression/PathExpressions.sysml` | `mismatched input '{' expecting ...` — path expression grammar rule not covered |
| `simpletests/ElementFilter.sysml` | `no viable alternative at input '(as'` — element filter cast syntax not supported |
| `validation/invalid/MetadataUsage_Invalid.sysml` | ANTLR syntax error — metadata usage grammar gap |

### Key Fixes (2026-05-12 update from 41% → 98%)

| Fix | Tests unblocked |
|---|---|
| Skip non-Package `DefinitionElement`s in `Model.load()` (e.g., `AnnotatingElement`) | CommentTest, MultiplicityTest, Relationship_invalid_relatedElement1 |
| Add `InterfaceBody.get_definition()`, handle `InterfaceBody` body name | InterfaceUsage (valid + invalid), ConjugationTest |
| Handle `RequirementDefinition(None)` and guard None declaration | RequirementUsage (valid + invalid), RequirementSubject, RequirementTest, Verification (×2), AnalysisTest, SemanticMetadata_valid |
| Auto-wrap bare top-level definitions in synthetic package | DecisionTest, ControlNodeTest |

### How to Add New Conformance Tests

1. Place `.sysml` file under `tests/sysmlv2/<category>/`
2. Add companion `.error` file (empty = expects parse success, non-empty = expected error regex)
3. Tests are auto-discovered by `conformance_test.py:_collect()`

---

## Summary Counts

| Category | Count |
|---|---|
| Public API classes (complete) | 12 |
| Public API stubs (parse only) | 17 |
| Grammar classes with `get_definition()` | ~145 of 319 |
| Grammar classes missing `get_definition()` | ~174 of 319 |
| Unit + grammar + integration tests | 116 (53 unit + 56 grammar + 7 integration) |
| Conformance tests (2026-03 XPect suite) | 123 total — **120 passing (98%)** |
| Bundled standard library files | 94 (36 kernel `.kerml` + 21 systems `.sysml` + 37 domain `.sysml`) |
