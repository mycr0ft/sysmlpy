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

### Test Coverage

| Test file | Count | Scope |
|---|---|---|
| `tests/class_test.py` | 53 tests | Programmatic API unit tests |
| `tests/grammar_test.py` | 56 tests | Grammar round-trip (parse → dump) |
| `tests/main_test.py` | 7 tests | `load`/`loads`/`load_grammar` integration |

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

Of the 319 internal grammar classes in `grammar/classes.py`, approximately 130 have `get_definition()` implemented. The remaining ~187–190 lack serialization and cannot round-trip to text.

### ANTLR4 Migration

- ANTLR4 is now the default parser
- textX has been removed; only ANTLR4 is used for parsing
- The `grammar/classes.py` hierarchy remains as the intermediate representation, populated by the ANTLR visitor

### Other Incomplete Items

- **Action parameters via `loads()`** — In/out parameters only work for programmatic construction; loading an action with parameters from SysML text is broken (`TODO.md`)
- **Typed-by in `load_from_grammar`** — Type relationships are not preserved when loading elements from grammar (`usage.py:459`, marked `#!TODO Typed By`)
- **CHANGELOG** — Not updated since v0.5.3; v0.6.0 work (ANTLR4 migration, new public API classes) is undocumented
- **Version sync** — `__init__.py` says `0.6.0`, `pyproject.toml` still says `0.5.3`

### Known Bugs

| Location | Description |
|---|---|
| `definition.py:373–380` | Duplicate `elif inner_class == "ActionUsage"` block — dead code |
| `grammar/classes.py:98` | `PackageBodyElement` name is hardcoded; `!TODO This isn't always the case` |
| `grammar/classes.py:6374` | Identified broken code path; `#!TODO This won't work` |
| `definition.py` (`RootNamespace`) | `load_package_body()` raises `NotImplementedError` for `AliasMember` and `Import` nodes |
| repo root + `tests/` | `temp.txt` scratch files — leftover artifacts to clean up |

---

## Not Started

### High Priority

| Feature | Description |
|---|---|
| Package imports | `import Package::*;` — `Import` and `AliasMember` grammar classes need `get_definition()` and `RootNamespace.load_package_body()` stubs filled in |
| Documentation/Comments | `documentation` blocks and `comment` elements (`Documentation`, `CommentSysML` grammar classes) |
| Typed literal values | `LiteralInteger`, `LiteralReal`, `LiteralString` — needed for typed attribute values beyond `pint` quantities |
| Full `dump()` for stub classes | Implement `get_definition()` on `State`, `Constraint`, `Connection`, `Flow`, `Calculation`, `Enumeration` (currently parse-in only — see In Progress above) |

### Medium Priority

| Feature | Description |
|---|---|
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

### Baseline Results (2026-04-22)

**50 / 123 passing (40.7%)**

| Category | Files | Pass | Fail | Pass % |
|---|---|---|---|---|
| `simpletests/` | 37 | 10 | 27 | 27% |
| `validation/valid/` | 34 | 17 | 17 | 50% |
| `validation/invalid/` | 47 | 22 | 25 | 47% |
| `expression/` | 4 | 0 | 4 | 0% |
| `linking/` | 1 | 1 | 0 | 100% |
| **Total** | **123** | **50** | **73** | **41%** |

### Passing Tests (baseline)

**simpletests** (10/37): `AliasTest`, `AnnotationTest`, `CommentTest`, `ImportTest`,
`MetadataTest`, `OccurrenceTest`, `RootPackageTest`, `TradeStudyTest`, `UseCaseTest`, `ViewTest`

**linking** (1/1): `GlobalQualification`

**validation/valid** (17/34): `ActionUsage`, `BindingConnector_path`, `BindingConnector_redefined`,
`BindingConnector_simple`, `CalculationUsage`, `Connector1–3`, `ConstraintUsage`,
`Expose_Visibility`, `IndividualUsage`, `PortUsage`, `RedefinitionDiamond0/2`,
`RedefinitionHopthrough`, `StateUsage`, `Subsetting_UniquenessConformance_Invalid`

**validation/invalid** (22/47): `ActionUsage_invalid`, `AllocationUsage_Invalid`,
`BindingConnector_invalid0/2/3/redefine`, `CalculationUsage_Invalid2`,
`ConnectionUsage_Invalid`, `ConstraintUsage_Invalid`, `Feature_invalid_noType`,
`FlowConnectionUsage_Invalid`, `Import_Visibility_Invalid`, `IndividualUsage_Invalid`,
`PortionUsage_Invalid`, `RedefinitionDiamond1_invalid`, `RedefinitionDiamond_Invalid`,
`Relationship_invalid_relatedElement0/1`, `SemanticMetadata_invalid`,
`StateSubactions_invalid`, `TransitionUsage_invalid`, `ViewRendering_invalid`

### Top Failure Causes

| Error | Affected tests (approx.) |
|---|---|
| `KeyError: 'completion'` — `UsageCompletion` missing from parsed tree | ~40 |
| `AttributeError: 'Definition' object has no attribute 'completion'` | ~20 |
| `KeyError: 'body'` — missing body in grammar class dispatch | ~10 |
| Other (`KeyError: 'value'`, `AttributeError`, etc.) | ~3 |

The dominant failure (`completion` key missing) is a known gap in how the ANTLR4
visitor builds `Usage` grammar objects — the `UsageCompletion` node is not always
emitted into the dictionary when a usage has no explicit body/value. Fixing this
single issue would likely unblock a large fraction of the failing tests.

---

## Summary Counts

| Category | Count |
|---|---|
| Public API classes (complete) | 12 |
| Public API stubs (parse only) | 17 |
| Grammar classes with `get_definition()` | ~130 of 319 |
| Grammar classes missing `get_definition()` | ~187 of 319 |
| Unit + grammar + integration tests | 116 (53 unit + 56 grammar + 7 integration) |
| Conformance tests (2026-03 XPect suite) | 123 total — **50 passing (41%)** |
| Bundled standard library files | 94 (36 kernel `.kerml` + 21 systems `.sysml` + 37 domain `.sysml`) |
