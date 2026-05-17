# sysmlpy Tutorial

A guide to using `sysmlpy` — a pure Python library for constructing and parsing SysML v2.0 models.

## Installation

```bash
pip install sysmlpy
```

## Quick Start

```python
from sysmlpy import loads, Model, Package, Part, Attribute, ureg

# Parse SysML text
model = loads("""
package MyModel {
    part def Engine;
    part engine1: Engine {
        attribute mass = 100 [kg];
    }
}
""")

# Or build programmatically
p = Part(name="Stage_1", shortname="'3.1'")
a = Attribute(name="mass")
a.set_value(100 * ureg.kilogram)
p._set_child(a)
print(p.dump())
# → part <'3.1'> Stage_1 { attribute mass = 100 [kilogram]; }
```

## Architecture

`sysmlpy` has three layers:

1. **Public API** (`usage.py`) — Python classes you use directly: `Part`, `Item`, `Action`, `State`, etc.
2. **Grammar Layer** (`grammar/classes.py`) — ~319 internal classes that mirror the ANTLR parse tree. Used for round-trip parsing.
3. **ANTLR Parser** (`antlr/`, `antlr_visitor.py`) — Parses SysML v2 text into an internal dict, then into grammar objects.

```
SysML text → ANTLR Lexer/Parser → Visitor → dict → Grammar Classes → Public API Classes
```

## SysML v2 to Python Mapping

### Base Classes

| Python Class | Role | Key Methods |
|---|---|---|
| `Searchable` | Mixin — `find()`, `all()`, typed property accessors | `find(name, type, recursive)`, `parts`, `actions`, `states`, etc. |
| `Usage` | Base for all usage/definition wrappers | `dump()`, `load_from_grammar()`, `_set_child()`, `_set_typed_by()`, `_set_specializes()`, `_set_subsets()`, `_set_redefines()` |
| `Model` | Root container | `load(s)`, `dump()` |
| `Package` | Namespace container | `load_from_grammar()`, `dump()` |
| `Transition` | State machine transition (standalone) | `load_from_grammar()`, `source`, `trigger`, `guard`, `target`, `effect` |

### Structural Elements

| Python Class | SysML Keywords | Def/Usage | Grammar Class | `load_from_grammar` |
|---|---|---|---|---|
| `Part` | `part`, `part def` | Both | `PartUsage`, `PartDefinition` | Yes |
| `Item` | `item`, `item def` | Both | `ItemUsage`, `ItemDefinition` | Yes |
| `Attribute` | `attribute`, `attribute def` | Both | `AttributeUsage`, `AttributeDefinition` | Yes |
| `Port` | `port`, `port def` | Both | `PortUsage`, `PortDefinition` | Yes |
| `Connection` | `connection`, `connection def` | Both | `ConnectionUsage`, `ConnectionDefinition` | Yes (via Package) |
| `Flow` | `flow`, `flow def` | Both | `FlowConnectionUsage`, `FlowConnectionDefinition` | Yes (via Package) |
| `FlowDef` | `flow def` | Def only | `FlowDefinition` | No |
| `Allocation` | `allocation`, `allocation def` | Both | `AllocationUsage`, `AllocationDefinition` | Yes (via Package) |
| `Individual` | `individual`, `individual def` | Both | `IndividualUsageSimple`, `IndividualDefinition` | Yes (via Package) |

### Behavioral Elements

| Python Class | SysML Keywords | Def/Usage | Grammar Class | `load_from_grammar` |
|---|---|---|---|---|
| `Action` | `action`, `action def` | Both | `ActionUsage`, `ActionDefinition` | Yes (custom) |
| `State` | `state`, `state def` | Both | `StateUsage`, `StateDefinition` | Yes (custom) |
| `Transition` | `transition`, `then`, `entry` | N/A | `TransitionUsage`, `TargetTransitionUsage` | Yes (standalone) |

### Requirements

| Python Class | SysML Keywords | Def/Usage | Grammar Class | `load_from_grammar` |
|---|---|---|---|---|
| `Requirement` | `requirement`, `requirement def` | Both | `RequirementUsage`, `RequirementDefinition` | Yes (via Package) |
| `UseCase` | `use case`, `use case def` | Both | `UseCaseUsage`, `UseCaseDefinition` | Yes (via Package) |

### Cases

| Python Class | SysML Keywords | Def/Usage | Grammar Class | `load_from_grammar` |
|---|---|---|---|---|
| `Case` | `case`, `case def` | Both | `CaseUsage`, `CaseDefinition` | Yes (via Package) |
| `AnalysisCase` | `analysis`, `analysis def` | Both | `AnalysisCaseUsage`, `AnalysisCaseDefinition` | Yes (via Package) |
| `VerificationCase` | `verification`, `verification case def` | Both | `VerificationCaseUsage`, `VerificationCaseDefinition` | Yes (via Package) |

### Constraints & Calculations

| Python Class | SysML Keywords | Def/Usage | Grammar Class | `load_from_grammar` |
|---|---|---|---|---|
| `Constraint` | `constraint`, `constraint def` | Both | `ConstraintUsage`, `ConstraintDefinition` | Yes (via Package) |
| `Calculation` | `calc`, `calc def` | Both | `CalculationUsage`, `CalculationDefinition` | Yes (via Package) |

### Views & Viewpoints

| Python Class | SysML Keywords | Def/Usage | Grammar Class | `load_from_grammar` |
|---|---|---|---|---|
| `View` | `view`, `view def` | Both | `ViewUsage`, `ViewDefinition` | Yes (via Package) |
| `Viewpoint` | `viewpoint`, `viewpoint def` | Both | `ViewpointUsage`, `ViewpointDefinition` | Yes (via Package) |
| `Concern` | `concern`, `concern def` | Both | `ConcernUsage`, `ConcernDefinition` | Yes (via Package) |

### Metadata & Rendering

| Python Class | SysML Keywords | Def/Usage | Grammar Class | `load_from_grammar` |
|---|---|---|---|---|
| `Metadata` | `metadata`, `metadata def` | Both | `MetadataUsage`, `MetadataDefinition` | Yes (via Package) |
| `Rendering` | `rendering`, `rendering def` | Both | `RenderingUsage`, `RenderingDefinition` | Yes (via Package) |
| `Enumeration` | `enum def` | Def only | `EnumerationDefinition` | Yes (via Package) |

### Custom (No Grammar Backing)

| Python Class | SysML Keywords | Notes |
|---|---|---|
| `Interface` | `interface`, `interface def` | Custom Python implementation, grammar wrapper only |
| `Message` | `message` | Custom Python implementation |
| `Reference` | `ref` | Custom Python implementation |
| `DefaultReference` | `in`/`out`/`inout ref` | Grammar-backed via `DefaultReferenceUsage` |

## Usage Examples

### Building Parts Programmatically

```python
from sysmlpy import Part, Item, Attribute, ureg

# Create a sensor part with children
sensor = Part(name="sensor")
camera = Part(name="camera")
lens = Item(name="lens")
mass = Attribute(name="mass")
mass.set_value(100 * ureg.kilogram)

camera._set_child(mass)
sensor._set_child(camera)
sensor._set_child(lens)

print(sensor.dump())
# part sensor {
#     part camera {
#         attribute mass = 100 [kilogram];
#     }
#     item lens;
# }
```

### Actions with Inputs and Outputs

```python
from sysmlpy import Action

# Action definition
a = Action(definition=True, name="Focus")
a.add_input("scene", "Scene")
a.add_output("image", "Image")
print(a.dump())
# → action def Focus { in scene : Scene; out image : Image; }

# Action usage
b = Action(name="TakePicture")
b.add_input("scene")
b.add_output("picture")
print(b.dump())
# → action TakePicture { in scene; out picture; }
```

### References

```python
from sysmlpy import Reference, Item

# Simple reference
r = Reference(name="driver")
print(r.dump())
# → ref driver;

# Typed reference
person = Item(name="Person")
r2 = Reference(name="driver")
r2.set_type(person)
print(r2.dump())
# → ref driver : Person;

# Reference redefinition
r3 = Reference(name="payload", redefines=True)
r3.set_type(person)
print(r3.dump())
# → ref :>> payload : Person;
```

### Parsing and Round-Trip

```python
from sysmlpy import loads
from sysmlpy.formatting import classtree

text = """package 'Action Example' {
    action def Focus { in scene : Scene; out image : Image; }
    action TakePicture {
        in item scene : Scene;
        out item picture : Picture;
        action focus : Focus { in scene; out image; }
    }
}"""

model = loads(text)
tree = classtree(model)
print(tree.dump())
```

### State Machines

```python
from sysmlpy import State

# State definition
s = State(definition=True, name="Running")
print(s.dump())
# → state def Running;

# State with transitions (via grammar)
model = loads("""
package States {
    state def Engine {
        state off;
        state on {
            entry start;
            do run;
            exit stop;
        }
        transition off to on if key_turned;
    }
}
""")
```

### Requirements

```python
from sysmlpy import Requirement

r = Requirement(definition=True, name="PowerRequirement")
r.set_doc("The system shall provide sufficient power.")
r.add_constraint("Power output >= 1000W")
print(r.dump())
```

### Working with Units

```python
from sysmlpy import Attribute, ureg

a = Attribute(name="thrust")
a.set_value(1000 * ureg.newton)
print(a.get_value())  # 1000 newton
a.set_value(a.get_value() + 199 * ureg.newton)
print(a.dump())  # attribute thrust = 1199.0 [newton];
```

## Loading Functions

| Function | Description |
|---|---|
| `loads(text)` | Parse SysML v2 text string into a `Model` |
| `load(file)` | Parse SysML v2 file into a `Model` |
| `load_grammar(text)` | Parse into grammar dict (internal) |
| `load_antlr(text)` | Explicit ANTLR4 parsing path |
| `load_grammar_antlr(text)` | Parse into grammar dict via ANTLR4 |

## Conformance

**100% of 123 OMG XPect conformance tests pass** (123/123).

Run the full suite:
```bash
pytest -m conformance
```
