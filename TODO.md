# sysml2py TODO

See [STATUS.md](STATUS.md) for the full completed / in-progress / not-started breakdown.

## Immediate / High Priority

- [ ] Sync version: `pyproject.toml` still says `0.5.3`, code is `0.6.0`
- [ ] Fix remaining 3 ANTLR grammar issues: PathExpressions, ElementFilter `(as Type)`, MetadataUsage
- [ ] Implement `Import` / `AliasMember` so package imports round-trip
- [ ] Fix Action parameter loading via `loads()` (programmatic-only right now)
- [ ] Fix typed-by preservation in `load_from_grammar` (`usage.py:459`)
- [ ] Implement `get_definition()` on `State`, `Constraint`, `Connection`, `Flow`, `Calculation`, `Enumeration`

## Known Bugs

- [ ] Duplicate `elif inner_class == "ActionUsage"` dead-code block in `definition.py`
- [ ] `RootNamespace` hardcoded `PackageBodyElement` name (`grammar/classes.py`)
- [ ] Broken code path at `grammar/classes.py`
- [ ] Remove leftover `temp.txt` files from repo root and `tests/`

## Completed

- [x] `Reference` class — `ref name;`, `ref name : Type;`, `ref :>> name : Type;`
- [x] ANTLR4 parser — now the default parser (OMG grammar v2026.03.0)
- [x] `Action` in/out parameters (programmatic construction)
- [x] `Requirement`, `UseCase`, `Interface`, `Message` public API classes
- [x] Conformance suite: 50/123 (41%) → 120/123 (98%) passing
- [x] `InterfaceBody` / `InterfaceBodyItem` / `InterfaceDefinition` / `InterfaceUsage` serialization
- [x] `AnnotatingElement` / `CommentSysML` / `Annotation` / `Documentation` grammar classes
- [x] `ActionUsage.get_definition()` — action serialization
- [x] `LiteralString` / `LiteralReal` / `LiteralInfinity.get_definition()`
- [x] `RequirementDefinition(None)` handling for definition=True constructor
- [x] Auto-wrapping bare definitions in synthetic package
- [x] Documentation + comment ANTLR visitor support
- [x] Case / AnalysisCase / VerificationCase definition visitors
