# sysmlpy

A pure Python implementation for parsing SysML v2.0 models.
Uses the ANTLR4 parser for full SysML v2 grammar support.

## Version

**v0.12.0** — 100% conformance test pass rate (123/123).
Storage abstraction layer with in-memory and NetworkX graph backends.

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

## Conformance

**100% of 123 OMG XPect conformance tests pass** (123/123).

## Author

Authored by [Jon Fox](https://github.com/mycr0ft)

## License

MIT License — see [LICENSE](LICENSE) for details.
