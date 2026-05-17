# ANTLR4 Parser for SysML v2

## Overview

sysmlpy now includes an experimental **ANTLR4-based parser** as an alternative to the textX parser. This provides a pure Python implementation that can parse SysML v2.0 using grammars derived from the official OMG specification.

## Why ANTLR4?

The original textX parser requires manual conversion from the official XText grammar (used in the OMG SysML v2 Pilot Implementation). This is labor-intensive and can drift from the official specification.

The ANTLR4 approach:
- Uses grammars auto-generated from the official OMG KEBNF specification
- Grammar version tracks the OMG release (e.g., v2026.03.0 for 2026-03 release)
- Provides a pure Python alternative to Java/TypeScript-based SysMLv2 parsers

## Project Structure

```
src/sysmlpy/
├── antlr_parser.py       # Core ANTLR4 parsing functions
├── antlr_visitor.py      # Convert parse tree to Python classes
├── antlr/                 # Generated ANTLR4 parser (auto-generated)
│   ├── SysMLv2Lexer.py
│   ├── SysMLv2Parser.py
│   ├── SysMLv2ParserVisitor.py
│   └── ...
└── grammar/antlr4/         # Grammar source files
    ├── SysMLv2Lexer.g4
    ├── SysMLv2Parser.g4
    └── examples/          # Test files
```

## Usage

### Using the ANTLR4 Parser

```python
from sysmlpy import load_antlr, loads, load_grammar

# Load from file
with open('model.sysml', 'r') as f:
    model = load_antlr(f)

# Load from string
model = loads('''
package VehicleModel {
    part def Vehicle {
        attribute mass : Real;
    }
}
''')

# Get raw grammar dictionary
grammar_dict = load_grammar('package Test;')

# Print the model
print(model.dump())
```

### Round-trip Support

The ANTLR4 parser supports round-trip parsing:

```python
from sysmlpy import loads

# Parse SysML
model = loads('package Test { part def Vehicle; }')

# Dump to string
output = model.dump()

# Parse again - should produce identical output
model2 = loads(output)
assert output == model2.dump()
```

### Choosing the Parser

All public API functions now use the ANTLR4 parser:

```python
from sysmlpy import loads  # ANTLR4-based (default)
```

## Grammar Sources

The ANTLR4 grammar is sourced from [daltskin/sysml-v2-grammar](https://github.com/daltskin/sysml-v2-grammar), which automatically generates ANTLR4 grammars from the OMG SysML v2 specification KEBNF files.

- **Current grammar version:** v2026.03.0
- **OMG release:** 2026-03
- **Source:** [Systems-Modeling/SysML-v2-Release](https://github.com/Systems-Modeling/SysML-v2-Release)

## What's Supported

The following SysML v2 constructs work with the ANTLR4 parser:

- Package definitions
- Part definitions and usages
- Attribute definitions and usages
- Item definitions and usages
- Port definitions and usages
- Requirement definitions
- Use case definitions

## Known Limitations

1. **Some complex elements** - Requirements, UseCases, and Ports with full bodies may have partial support
2. **Round-trip fidelity** - Some whitespace/formatting differences may occur
3. **Grammar drift** - The auto-generated grammar may have minor differences from the official OMG specification

## Updating the Grammar

To update to a newer OMG release:

```bash
# Download the latest grammar release from daltskin/sysml-v2-grammar
# Or regenerate from the OMG KEBNF specification

# Regenerate the Python parser
java -jar antlr-4.13.2-complete.jar -Xexact-output-dir \
    -o src/sysmlpy/antlr \
    -visitor -listener -Dlanguage=Python3 \
    src/sysmlpy/grammar/antlr4/SysMLv2Lexer.g4 \
    src/sysmlpy/grammar/antlr4/SysMLv2Parser.g4
```

## Comparison: textX vs ANTLR4

| Feature | textX | ANTLR4 |
|---------|-------|--------|
| Grammar source | Manual XText conversion | Auto-generated from OMG KEBNF |
| Grammar updates | Labor-intensive | Automated |
| Parse performance | Good | Good |
| Error messages | Good | Excellent |
| Python-only | Yes | Yes |
| Round-trip support | Full | Partial |
| Specification tracking | Manual | Automatic |

## Future Work

1. Complete support for all SysML v2 constructs
2. Improve round-trip fidelity
3. Add conformance tests against OMG test suite
4. Consider making ANTLR4 the default parser
5. Remove textX dependency once ANTLR4 is stable