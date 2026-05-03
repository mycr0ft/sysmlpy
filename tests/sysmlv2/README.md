# SysML v2 Conformance Test Suite

This directory contains parse-conformance test fixtures sourced from the
**SysML-v2-Pilot-Implementation-2026-03** reference implementation
(`org.omg.sysml.xpect.tests`).

## Directory Layout

```
sysmlv2/
  simpletests/          38 files — one per SysML construct (ActionTest, PartTest, …)
  validation/
    valid/              29 files — semantically valid SysML (XPECT noErrors)
    invalid/            41 files — semantically invalid SysML (XPECT errors → …)
  expression/            4 files — expression / arithmetic tests
  linking/               1 file  — name-resolution test
```

Each `.sysml` file has a matching `.error` sidecar file.

## `.error` File Format

| Content | Meaning |
|---------|---------|
| Empty (or only `#` comment lines) | `loads(text)` must succeed without raising any exception |
| First non-comment line | Regex matched against the exception raised by `loads()` |

```
# Lines starting with '#' are comments and are ignored by the test runner.
#
# Example for a file whose syntax is intentionally broken:
# SysMLSyntaxError
#
# Empty files (like all current files) mean: expect a clean parse.
```

## Why all `.error` files start empty

All 123 `.sysml` files are **syntactically valid SysML** — they are official OMG
reference test fixtures. sysml2py currently performs syntax parsing only (no
semantic validation). From sysml2py's perspective the expected behaviour for
every file is "parse without error", so all `.error` files start empty.

Tests that currently **fail** reveal parser gaps to fix. As sysml2py improves,
more tests will pass.

The `validation/invalid/` files contain **semantically** invalid SysML with
inline `// XPECT errors --> "..."` annotations showing what the reference
implementation reports.  Once sysml2py adds semantic validation, those
`.error` files will be populated with the corresponding validation-error
messages.

## Running the Suite

```bash
# Run conformance tests only
pytest -m conformance

# Verbose — shows each file name
pytest -m conformance -v

# Run just one category
pytest tests/sysmlv2/simpletests/ -m conformance

# Exclude conformance from a normal run
pytest -m "not conformance"
```

## Updating an `.error` File

When a file that previously caused a parse error now parses cleanly (because
the underlying parser gap was fixed), **clear the `.error` file** to mark it
as passing:

```bash
echo -n "" > tests/sysmlv2/simpletests/ImportTest.error
```

When sysml2py gains semantic validation and a `validation/invalid/` file should
raise a specific error, add the expected message to its `.error` file:

```
# PartUsage_invalid.error
SysMLValidationError.*occurrence definitions
```

## Source and License

**Source:** [Systems-Modeling/SysML-v2-Pilot-Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation),
tag `2026-03`, project `org.omg.sysml.xpect.tests`.

The Eclipse `XPECT_SETUP` boilerplate blocks have been stripped from each file.
The SysML body and inline `// XPECT` annotation comments are preserved verbatim.

**License:** The `.sysml` files are copyright © Object Management Group (OMG)
and distributed under LGPL-3.0.
