# sysmlpy

A pure Python implementation for parsing SysML v2.0 models.
Uses the ANTLR4 parser for full SysML v2 grammar support.

## Version

**v0.20.0** — Full OCL well-formedness validation: duplicate names, cyclic specialization, subsetting/redefinition compatibility, part/port definition compatibility, feature chain validation, multiplicity bounds checking. Supertype/inheritance resolution. Standard library symbol index (88 files, ~1,417 symbols). Import visibility enforcement (private/public/protected). 90 semantic tests, 288 total tests passing.

## Quick Links

- [Tutorial](TUTORIAL.md) — comprehensive guide with class mapping tables
- [Quick Start](quickstart.md) — basic usage examples
- [Status](STATUS.md) — conformance results and round-trip coverage
- [Changelog](CHANGELOG.md) — release history
- [TODO](TODO.md) — planned work

## Installation

```bash
pip install sysmlpy
```

With graph analysis support:

```bash
pip install sysmlpy[graph]
```

With Cayley graph database support:

```bash
pip install sysmlpy[cayley]
```

## Basic Usage

```python
from sysmlpy import loads, Part, Attribute

# Parse SysML text
model = loads("""
package Rocket {
    part Engine {
        attribute mass = 100 [kg];
    }
}
""")

# Navigate
engine = model.find(name='Engine', recursive=True)
print(engine.dump())

# Build programmatically
p = Part(name='Stage1')
p._set_child(Attribute(name='mass'))
print(p.dump())
```

## Storage Backends

sysmlpy provides a unified `Store` protocol with four backend implementations:

| Backend | Dependencies | Persistence | Use Case |
|---------|-------------|-------------|----------|
| `InMemoryStore` | None | Volatile | Testing, small models |
| `NetworkXStore` | networkx | Volatile | Graph analysis, centrality, cycles |
| `KuzuStore` | kuzu | Disk (optional) | Embedded graph DB, Cypher queries |
| `CayleyStore` | requests | Server-managed | Remote graph DB, multi-tenant |

```python
from sysmlpy.store import create_store

store = create_store("memory")       # In-memory dict
store = create_store("networkx")     # NetworkX graph
store = create_store("kuzu", database="/tmp/model.db")  # Embedded DB
store = create_store("cayley")       # Remote Cayley server
```

All backends share the same API: `put`, `get`, `delete`, `children`, `parents`, `relationships`, `query`, `has`, `ids`, `clear`, plus graph traversal (`descendants`, `ancestors`, `path`).

## Conformance

**100% of 123 OMG XPect conformance tests pass** (123/123).

## Semantic Analysis

Run `analyze(model)` to validate a parsed model against SysML v2 well-formedness rules:

```python
from sysmlpy import loads, analyze

model = loads("package P { part x : MissingType; }")
issues = analyze(model)
for issue in issues:
    print(f"[{issue.severity}] {issue.code}: {issue.message}")
```

The analyzer checks:

| Code | Rule |
|------|------|
| `UNDEFINED_SYMBOL` | Reference to a non-existent type or feature |
| `DUPLICATE_NAME` | Two members with the same name in a scope |
| `CYCLIC_SPECIALIZATION` | A type specializing itself (directly or indirectly) |
| `INCOMPATIBLE_SUBSETTING` | Subsetting reference to undefined feature |
| `INCOMPATIBLE_REDEFINITION` | Redefinition reference to undefined feature |
| `INCOMPATIBLE_PART_DEFINITION` | Part typed by non-PartDefinition |
| `INCOMPATIBLE_PORT_DEFINITION` | Port typed by non-PortDefinition |
| `INCOMPATIBLE_FEATURE_CHAIN` | Feature chain with incompatible types |
| `INVALID_MULTIPLICITY_BOUNDS` | Lower bound > upper bound (e.g., `[5..2]`) |
| `UNRESOLVED_IMPORT` | Import target does not exist |

Import visibility is enforced: `private` (default) limits symbols to the importing scope, `public` re-exports to siblings and children, and `protected` is visible to children only.

## Author

Authored by [Jon Fox](https://github.com/mycr0ft)

## License

MIT License — see [LICENSE](LICENSE) for details.
