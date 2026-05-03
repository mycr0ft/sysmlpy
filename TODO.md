# sysml2py TODO

See [STATUS.md](STATUS.md) for the full completed / in-progress / not-started breakdown.

## Immediate / High Priority

- [ ] Sync version: `pyproject.toml` still says `0.5.3`, code is `0.6.0`
- [ ] Update `CHANGELOG.md` to document v0.6.0 changes (ANTLR4 migration, new API classes)
- [ ] Implement `Import` / `AliasMember` so package imports round-trip
- [ ] Implement `Documentation` / `CommentSysML` grammar classes
- [ ] Fix Action parameter loading via `loads()` (programmatic-only right now)
- [ ] Fix typed-by preservation in `load_from_grammar` (`usage.py:459`)

## Known Bugs

- [ ] Duplicate `elif inner_class == "ActionUsage"` dead-code block in `definition.py:373`
- [ ] `RootNamespace` hardcoded `PackageBodyElement` name (`grammar/classes.py:98`)
- [ ] Broken code path at `grammar/classes.py:6374`
- [ ] Remove leftover `temp.txt` files from repo root and `tests/`

## Completed

- [x] `Reference` class — `ref name;`, `ref name : Type;`, `ref :>> name : Type;`
- [x] ANTLR4 parser — now the default parser (OMG grammar v2026.03.0)
- [x] `Action` in/out parameters (programmatic construction)
- [x] `Requirement`, `UseCase`, `Interface`, `Message` public API classes
