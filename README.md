# sysmlpy
[![PyPI version](https://badge.fury.io/py/sysmlpy.svg)](https://badge.fury.io/py/sysmlpy)[![PyPI status](https://img.shields.io/pypi/status/sysmlpy.svg)](https://pypi.python.org/pypi/sysmlpy/)[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

## Description
sysmlpy is an open source pure Python library for constructing python-based
classes consistent with the [SysML v2.0 standard](https://github.com/Systems-Modeling/SysML-v2-Release).

This project began as a fork of the sysml2py project by [Christopher
Cox](https://github.com/chriscox-westfall). Since April 2026 [Jon Fox](mailto:jon.fox@drfox.com) 
decided to complete coverage of all SysMLv2 features over two months of weekends,
and dropped the textX parser in favor of [an ANTLR4 parser grammar](https://github.com/daltskin/sysml-v2-grammar) and
changed our unit library to pint.
The project had diverged so much from sysml2py that a new name, sysmlpy, was selected.

![Lines of Code Over Time](loc_history.svg)

**v0.17.0:** 100% test suite pass rate (487/487). Cayley graph database storage backend via HTTP API. Full grammar round-trip coverage (56/56 tests). Programmatic API consistency fixes. NetworkXStore bug fix.

**v0.16.0:** 100% grammar round-trip test coverage (56/56). Analysis case usage, trade study, calculation redefinition, and case body member support. Import visibility defaults to private per SysML v2 spec.

**v0.15.0:** ISQ unit validation (300+ type-to-dimension mappings), US Customary unit support (21 custom definitions), PlantUML diagram generation with stereotype-based styling, and comprehensive API documentation.

## Requirements
sysmlpy requires the following Python packages:
- [pyyaml](https://github.com/yaml/pyyaml)
- [pint](https://github.com/hgrecco/pint)
- [antlr4-python3-runtime](https://github.com/antlr/antlr4)

### Optional Dependencies
- [networkx](https://networkx.org/) — graph analysis backend (install with `pip install sysmlpy[graph]`)
- [kuzu](https://kuzudb.com/) — embedded graph database with disk persistence and Cypher queries (install with `pip install sysmlpy[kuzu]`)
- [cayley](https://cayley.io/) — graph database via HTTP API, supports BoltDB/LevelDB backends (install with `pip install sysmlpy[cayley]`)
- [PlantUML](https://plantuml.com/) **v1.2020.0+** — diagram rendering (requires Java + PlantUML JAR or [PlantUML server](https://www.plantuml.com/plantuml)). The generator uses `<style>` blocks and `skinparam` stereotype selectors introduced in v1.2020.

## Installation

Multiple installation methods are supported by sysmlpy, including:

|                             **Logo**                              | **Platform** |                                    **Command**                                    |
|:-----------------------------------------------------------------:|:------------:|:---------------------------------------------------------------------------------:|
|       ![PyPI logo](https://simpleicons.org/icons/pypi.svg)        |     PyPI     |                        ``python -m pip install sysmlpy``                        |
|       ![PyPI logo](https://simpleicons.org/icons/pypi.svg)        |     PyPI     |                 ``python -m pip install sysmlpy[graph]`` (with graph analysis)                  |
|       ![PyPI logo](https://simpleicons.org/icons/pypi.svg)        |     PyPI     |              ``python -m pip install sysmlpy[cayley]`` (with Cayley graph DB)              |
|     ![GitHub logo](https://simpleicons.org/icons/github.svg)      |    GitHub    | ``python -m pip install https://github.com/mycr0ft/sysmlpy/archive/refs/heads/main.zip`` |

## Documentation

Documentation can be found [here.](https://mycr0ft.github.io/sysmlpy/)

### Basic Usage

The code below will create a part called Stage 1, with a shortname of <'3.1'>
referencing a specific requirement or document. It has a mass attribute of 100
kg. It has a thrust attribute of 1000 N. These attributes are created and placed
as a child of the part. Next, we recall the part value for thrust and add 199 N.
Finally, we can dump the output from this class.
```
  from sysmlpy import Attribute, Part, ureg

  a = Attribute(name='mass')
  a.set_value(100 * ureg.kilogram)
  b = Attribute(name='thrust')
  b.set_value(1000 * ureg.newton)
  c = Part(name="Stage_1", shortname="'3.1'")
  c._set_child(a)
  c._set_child(b)
  v = "Stage_1.thrust"
  c._get_child(v).set_value(c._get_child(v).get_value() + 199 * ureg.newton)
  print(c.dump())
```

It will output the following:
```
  part <'3.1'> Stage_1 {
    attribute mass= 100 [kilogram];
    attribute thrust= 1199.0 [newton];
  }
```

The package is able to handle Items, Parts, and Attributes.

```
a = Part(name='camera')
b = Item(name='lens')
d = Attribute(name='mass')
c = Part(name='sensor')
c._set_child(a)
c._set_child(b)
a._set_child(d)
print(c.dump())
```

will return:
```
part sensor {
   part camera {
      attribute mass;
   }
   item lens;
}
```

Actions
-------

Actions (activities) can be defined with input and output parameters::

```
from sysmlpy import Action

# Action definition with typed inputs/outputs
a = Action(definition=True, name='Focus')
a.add_input('scene', 'Scene')
a.add_output('image', 'Image')
print(a.dump())
# → action def Focus { in scene : Scene; out image : Image; }

# Action usage with references
b = Action(name='TakePicture')
b.add_input('scene')
b.add_output('picture')
print(b.dump())
# → action TakePicture { in scene; out picture; }
```

References
----------

References can reference other elements::

```
from sysmlpy import Reference, Item

# Simple reference
r = Reference(name='driver')
print(r.dump())
# → ref driver;

# Reference with type
person = Item(name='Person')
r2 = Reference(name='driver')
r2.set_type(person)
print(r2.dump())
# → ref driver : Person;

# Reference redefinition
r3 = Reference(name='payload', redefines=True)
r3.set_type(person)
print(r3.dump())
# → ref :>> payload : Person;
```

## Grammar Round-Trip

`loads()` parses SysML v2 text and `classtree()` converts the result back to text. This round-trip is the basis for the grammar test suite.

```python
from sysmlpy import loads
from sysmlpy.formatting import classtree

text = """package 'Action Example' {
    action def Focus { in scene : Scene; out image : Image; }
    action def Shoot { in image: Image; out picture : Picture; }

    action def TakePicture {
        in item scene : Scene;
        out item picture : Picture;

        bind focus.scene = scene;

        action focus : Focus { in scene; out image; }

        flow focus.image to shoot.image;

        first focus then shoot;

        action shoot : Shoot { in image; out picture; }

        bind shoot.picture = picture;
    }
}"""

model = loads(text)
tree = classtree(model)
print(tree.dump())
```

**100% of the 56 grammar round-trip tests pass** (56/56), covering packages, parts, items, ports, interfaces, binding connectors, flow connections, all action forms (definition, shorthand, succession, decomposition), expressions, calculations, constraints, state definitions, requirements, analysis cases, and trade studies.

## Storage Backends

sysmlpy provides a unified `Store` protocol with multiple backend implementations. All backends support the same API: `put`, `get`, `delete`, `children`, `parents`, `relationships`, `query`, `has`, `ids`, `clear`, plus graph traversal methods (`descendants`, `ancestors`, `path`).

```python
from sysmlpy.store import create_store

# In-memory (default, zero dependencies)
store = create_store("memory")

# NetworkX graph (analysis, shortest paths, centrality)
store = create_store("networkx")

# Kuzu embedded graph DB (disk persistence, Cypher queries)
store = create_store("kuzu", database="/tmp/model.db")

# Cayley remote graph DB (HTTP API, BoltDB/LevelDB backends)
store = create_store("cayley", host="localhost", port=64210)
```

### InMemoryStore

Dict-based backend with O(1) lookups. Zero external dependencies. Ideal for testing and small models.

### NetworkXStore

Graph backend using NetworkX `MultiDiGraph`. Enables graph analysis algorithms:

```python
from sysmlpy.store import NetworkXStore

store = NetworkXStore()
store.put(eid, {"name": "Engine", "sysml_type": "part"})

# Graph analysis
components = store.connected_components()
centrality = store.centrality()
cycles = store.cycles()
stats = store.stats()  # nodes, edges, density, avg_degree
subgraph = store.subgraph([eid1, eid2])
store.export_graphml("model.graphml")
```

### KuzuStore

Embedded graph database with disk persistence. Uses Cypher for queries. Data survives across process restarts.

```python
from sysmlpy.store import KuzuStore

# Persistent database
store = KuzuStore(database="/path/to/model.db")

# In-memory mode
store = KuzuStore()
```

### CayleyStore

Remote graph database backend communicating with a [Cayley](https://cayley.io/) server over HTTP. Supports any Cayley backend (BoltDB, LevelDB, in-memory). Uses the quad model (subject, predicate, object, label) for flexible data representation.

```python
from sysmlpy.store import CayleyStore

# Connect to local Cayley server
store = CayleyStore()

# Custom host/port with namespace isolation
store = CayleyStore(host="cayley.example.com", port=64210, label="my_project")

# Graph analysis
store.put(eid, {"name": "Wheel", "sysml_type": "part"})
descendants = store.descendants(root_id)
ancestors = store.ancestors(leaf_id)
path = store.path(source_id, target_id)
components = store.connected_components()
cycles = store.cycles()
centrality = store.centrality()
store.export_graphml("model.graphml")
```

**Running Cayley with Docker:**

```bash
# In-memory backend
docker run -p 64210:64210 --rm cayley/cayley

# Persistent BoltDB backend
docker run -p 64210:64210 -v /data:/data --rm cayley/cayley -db boltdb -dbpath /data/cayley.db
```

**Quad Model:** Elements are stored as quads where the subject is the element UUID, predicates are property names (e.g., `name`, `sysml_type`), and objects are property values. Relationships are stored as quads where the predicate is the relationship type (e.g., `parent_child`, `typed_by`). Labels provide namespace isolation for multi-tenant scenarios.

## PlantUML Visualizations

Generate SysML v2 structure diagrams from parsed models using the built-in PlantUML generator. Definitions render with sharp corners and usage elements with rounded corners. Relationships are differentiated by arrow style, thickness, and color — following the [official SysML v2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Release) approach.

```python
from sysmlpy import loads
from sysmlpy.plantuml import PlantUMLGenerator

text = """package Vehicle {
    part def Wheel {
        attribute radius : LengthValue;
        attribute pressure : PressureValue;
    }

    part def BrakeSystem {
        attribute padThickness : LengthValue;
    }

    part def VehicleAssembly {
        part frontLeft : Wheel;
        part frontRight : Wheel;
        part brakes : BrakeSystem;
    }

    part myVehicle : VehicleAssembly;
}"""

model = loads(text)
gen = PlantUMLGenerator(model, title="Vehicle Structure")
print(gen.generate())
```

Produces PlantUML source that renders as:

```plantuml
@startuml
skinparam RoundCorner 0
skinparam rectangle<<(D,#8B4513) part def>> {
    RoundCorner 0
    BackgroundColor #FFF8F0
    BorderColor #8B4513
}
skinparam rectangle<<(P,#32CD32) part>> {
    RoundCorner 15
    BackgroundColor #F0FFF0
    BorderColor #32CD32
}

title Vehicle Structure

rectangle "Wheel" as Wheel <<(D,#8B4513) part def>>
rectangle "BrakeSystem" as BrakeSystem <<(D,#8B4513) part def>>
rectangle "VehicleAssembly" as VehicleAssembly <<(D,#8B4513) part def>>
rectangle "myVehicle" as myVehicle <<(P,#32CD32) part>>

VehicleAssembly *-- frontLeft : owns
VehicleAssembly *-- frontRight : owns
VehicleAssembly *-- brakes : owns
myVehicle --:|> VehicleAssembly : types

legend right
  <b>Legend</b>
  |= Element |= Notation |
  | <<(D,#8B4513) part def>> | Definition (type) |
  | <<(P,#32CD32) part>> | Usage (instance) |
  | --:|> | Feature typing |
  | *-- | Composite containment |
endlegend
@enduml
```

### Filtering and Focus

The generator supports filtering to highlight specific elements:

```python
# Show only elements related to 'myVehicle'
gen = PlantUMLGenerator(model, focus="myVehicle")

# Show a custom set of elements
gen = PlantUMLGenerator(model, elements=["Wheel", "BrakeSystem"])

# Limit nesting depth
gen = PlantUMLGenerator(model, max_depth=2)
```

See [`docs/plantuml-examples/`](docs/plantuml-examples/) for 9 rendered examples covering usage vs definition, relationships, vehicle structure, requirements, interconnections, state machines, and activity diagrams.

## Conformance

**100% of 123 OMG XPect conformance tests pass** (123/123).

## License
sysmlpy is released under the MIT license, hence allowing commercial use of the library.
