# sysmlpy

A pure Python implementation for parsing SysML v2.0 models.
Uses the ANTLR4 parser for full SysML v2 grammar support.

## Version

**v0.17.0** — 100% test suite pass rate (487/487). Cayley graph database storage backend via HTTP API. Full grammar round-trip coverage (56/56 tests). Programmatic API consistency fixes. NetworkXStore bug fix.

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

## Author

Authored by [Jon Fox](https://github.com/mycr0ft)

## License

MIT License — see [LICENSE](LICENSE) for details.
