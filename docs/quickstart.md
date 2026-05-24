Quick Start
==========

This guide explains sysmlpy through working examples derived from the test suite.

Installation
------------

::

    pip install sysmlpy

Or from source::

    pip install -e .


Basic Workflow
-------------

sysmlpy provides two-way translation between SysML v2 text and Python objects:

1. **Parse SysML text → Python object** using ``load_grammar()``
2. **Build Python object → SysML text** using ``.dump()``

::

    from sysmlpy import Package, load_grammar as loads
    from sysmlpy.formatting import classtree

    # Parse text to Python
    text = "package Rocket;"
    pkg = loads(text)
    
    # Python to text
    output = classtree(pkg).dump()
    # → "package Rocket;"

Packages
--------

Create a package::

    from sysmlpy import Package

    p = Package()._set_name("Rocket")
    print(p.dump())
    # → "package Rocket;"

Package with body::

    p = Package(name="Rocket")
    p._set_child(Package(name="Engine"))
    print(p.dump())
    # → package Rocket {
    #        package Engine;
    #     }

Short names (alias IDs)::

    p = Package(name="Rocket", shortname="'3.1'")
    print(p.dump())
    # → package <'3.1'> Rocket;

Items
-----

Create an item usage::

    from sysmlpy import Item

    i = Item(name="Fuel")
    print(i.dump())
    # → item Fuel;

Item definition::

    i = Item(definition=True, name="Fuel")
    print(i.dump())
    # → item def Fuel;

Items with children::

    i = Item(name="Fuel")
    i._set_child(Item(name="Oxidizer"))
    print(i.dump())
    # → item Fuel {
    #        item Oxidizer;
    #     }

Parts
-----

Parts work like items::

    from sysmlpy import Part

    p = Part(name="Engine")
    print(p.dump())
    # → part Engine;

Attributes
-----------

Attributes with values::

    from sysmlpy import Attribute, ureg

    a = Attribute(name="mass")
    a.set_value(100 * ureg.kilogram)
    print(a.dump())
    # → attribute mass = 100 [kilogram];

Composite structures::

    from sysmlpy import Part, Attribute

    p = Part(name="Stage1")
    p._set_child(Attribute(name="mass"))
    p._set_child(Attribute(name="thrust"))
    print(p.dump())
    # → part Stage1 {
    #        attribute mass;
    #        attribute thrust;
    #     }

Actions
-------

Actions (activities) can be defined with input and output parameters::

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

References
----------

References can reference other elements::

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

Typing (Subclassing)
------------------

An item can be typed by a definition::

    from sysmlpy import Item

    # Create definition
    fuel_def = Item(definition=True, name="Fuel")
    
    # Create usage typed by definition
    hydrogen = Item(name="Hydrogen")
    hydrogen._set_typed_by(fuel_def)
    print(hydrogen.dump())
    # → item Hydrogen : Fuel;

Model
-----

A Model contains packages::

    from sysmlpy import Model, Package

    m = Model()
    m._set_child(Package(name="Rocket"))
    m._set_child(Package(name="Payload"))
    print(m.dump())
    # → package Rocket;
    #     package Payload;

Loading full text
-----------------

Parse complete SysML text::

    from sysmlpy import Model

    text = """package Rocket {
           item def Fuel;
           item Hydrogen : Fuel;
        }"""

    model = Model().load(text)
    print(model.dump())

Reference
---------

For more examples, see the test files in ``tests/class_test.py``.

Python Representation
------------------

All classes have ``__repr__`` that returns constructor-style output::

    from sysmlpy import Package, Item, Part, Attribute, Action, Reference

    p = Package(name='Rocket')
    print(repr(p))
    # → Package(name='Rocket')

    i = Item(definition=True, name='Fuel')
    print(repr(i))
    # → Item(definition=True, name='Fuel')

    part = Part(name='Engine')
    print(repr(part))
    # → Part(name='Engine')

    attr = Attribute(name='mass')
    print(repr(attr))
    # → Attribute(name='mass')

Anonymous elements show a UUID until named::

    from sysmlpy import Package
    p = Package()
    print(repr(p))
    # → Package(name='a1b2c3d4-...')  # UUID

Storage Backends
----------------

sysmlpy provides a unified storage protocol with multiple backends::

    from sysmlpy.store import create_store

    # In-memory (default, zero dependencies)
    store = create_store("memory")

    # NetworkX graph (analysis, shortest paths, centrality)
    store = create_store("networkx")

    # Kuzu embedded graph DB (disk persistence, Cypher queries)
    store = create_store("kuzu", database="/tmp/model.db")

    # Cayley remote graph DB (HTTP API, BoltDB/LevelDB backends)
    store = create_store("cayley", host="localhost", port=64210)

All backends share the same API::

    from sysmlpy.store import new_id

    eid = new_id()
    store.put(eid, {"name": "Engine", "sysml_type": "part"})
    data = store.get(eid)       # → {"name": "Engine", "sysml_type": "part"}
    store.has(eid)              # → True
    store.delete(eid)           # → True

    # Query elements
    results = store.query(sysml_type="part")
    results = store.query(name="Engine*")  # wildcard

    # Graph traversal
    store.descendants(root_id)
    store.ancestors(leaf_id)
    store.path(source_id, target_id)

CayleyStore communicates with a running Cayley server over HTTP, storing elements as quads (subject, predicate, object, label). Run Cayley with Docker::

    # In-memory backend
    docker run -p 64210:64210 --rm cayley/cayley

    # Persistent BoltDB backend
    docker run -p 64210:64210 -v /data:/data --rm cayley/cayley -db boltdb -dbpath /data/cayley.db

Multi-File Projects
-------------------

sysmlpy supports loading multiple SysML files into a shared model with automatic
cross-file import resolution.

Load multiple files::

    from sysmlpy import load_files, analyze

    model = load_files([
        'models/Shared/Types.sysml',
        'models/SystemGateway/SystemGatewayMain.sysml',
    ])
    issues = analyze(model)

Packages with the same name are automatically merged::

    # types1.sysml: package Types { part def Engine; }
    # types2.sysml: package Types { part def Wheel; }
    model = load_files(['types1.sysml', 'types2.sysml'])
    # Both Engine and Wheel are in the same Types package

Load an entire project directory::

    from sysmlpy import load_project

    # Load all .sysml and .kerml files recursively
    model = load_project('models/')

    # Load from an entry point (only reachable files)
    model = load_project('models/', entry='models/main.sysml')

Load a file with automatic dependency resolution::

    from sysmlpy import load_with_dependencies

    model = load_with_dependencies(
        'models/SystemGateway/SystemGatewayMain.sysml',
        search_paths=['models/SystemGateway', 'models/Shared'],
    )

Standard library imports (ScalarValues, ISQ, etc.) are validated when a library
path is provided::

    import sysmlpy
    library_path = '/path/to/sysmlpy/library'
    model = load_files(['main.sysml'], library=library_path)

PlantUML View Renderings
------------------------

sysmlpy provides five view rendering functions for generating PlantUML diagrams,
all defaulting to black-and-white output suitable for journal articles::

    from sysmlpy.plantuml import (
        as_graphical_rendering,
        as_interconnection_diagram,
        as_tree_diagram,
        as_element_table,
        as_textual_notation,
    )

    model = sysmlpy.loads("package P { part def Engine { port intake; } }")

    # Graphical: elements as shapes with relationship arrows (default B&W)
    print(as_graphical_rendering(model))

    # Tree: nested containers showing hierarchy
    print(as_tree_diagram(model))

    # Element table: tabular listing
    print(as_element_table(model))

    # Textual notation: indented text in a note
    print(as_textual_notation(model))

    # Interconnection: focus on connectors and flows
    print(as_interconnection_diagram(model))

All rendering functions accept ``style="color"`` for colored output and
``custom_style`` for user-defined PlantUML style overrides::

    puml = as_tree_diagram(model, custom_style=[
        'skinparam defaultFontSize 14',
        'skinparam rectangle { LineThickness 2.5 }',
    ])

Stylistic Checks
----------------

The ``analyze()`` function now includes stylistic checks that warn about
naming convention violations and file-package mismatches::

    from sysmlpy import loads, analyze

    model = loads("package mypkg { part def engine; }")

    # Default: stylistic checks enabled
    issues = analyze(model)
    # → NAMING_CONVENTION warnings for 'mypkg', 'engine'

    # With filename check
    issues = analyze(model, filename="Engine.sysml")
    # → FILE_PACKAGE_MISMATCH warning for 'mypkg' vs 'Engine'

    # Disable stylistic checks
    issues = analyze(model, style_checks=False)

Naming conventions enforced:

- **Definitions** (``part def``, ``action def``, etc.): PascalCase (``Engine``)
- **Usages** (``part``, ``action``, etc.): camelCase (``myEngine``)
- **Packages**: PascalCase (``MyPackage``)
- **Attributes**: camelCase (``powerLevel``)
- **Ports**: camelCase (``intakePort``)

All stylistic issues have severity ``"warning"`` rather than ``"error"``,
so they don't block validation but still highlight potential issues.