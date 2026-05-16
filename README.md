# sysml2py
[![PyPI version](https://badge.fury.io/py/sysml2py.svg)](https://badge.fury.io/py/sysml2py)[![PyPI status](https://img.shields.io/pypi/status/sysml2py.svg)](https://pypi.python.org/pypi/sysml2py/)[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

## Description
sysml2py is an open source pure Python library for constructing python-based
classes consistent with the [SysML v2.0 standard](https://github.com/Systems-Modeling/SysML-v2-Release).

This is a fork of the original project by [Christopher Cox](https://github.com/chriscox-westfall),
authored by [Jon Fox](mailto:jon.fox@drfox.com) at [mycr0ft/sysml2py](https://github.com/mycr0ft/sysml2py).

**v0.10.0:** 99% conformance test pass rate (122/123). Full state machine, requirement, constraint, and analysis case support. ANTLR4 parser with complete visitor.

## Requirements
sysml2py requires the following Python packages:
- [pyyaml](https://github.com/yaml/pyyaml)
- [pint](https://github.com/hgrecco/pint)
- [antlr4-python3-runtime](https://github.com/antlr/antlr4)

## Installation

Multiple installation methods are supported by sysml2py, including:

|                             **Logo**                              | **Platform** |                                    **Command**                                    |
|:-----------------------------------------------------------------:|:------------:|:---------------------------------------------------------------------------------:|
|       ![PyPI logo](https://simpleicons.org/icons/pypi.svg)        |     PyPI     |                        ``python -m pip install sysml2py``                        |
|     ![GitHub logo](https://simpleicons.org/icons/github.svg)      |    GitHub    | ``python -m pip install https://github.com/mycr0ft/sysml2py/archive/refs/heads/main.zip`` |

## Documentation

Documentation can be found [here.](https://mycr0ft.github.io/sysml2py/)

### Basic Usage

The code below will create a part called Stage 1, with a shortname of <'3.1'>
referencing a specific requirement or document. It has a mass attribute of 100
kg. It has a thrust attribute of 1000 N. These attributes are created and placed
as a child of the part. Next, we recall the part value for thrust and add 199 N.
Finally, we can dump the output from this class.
```
  from sysml2py import Attribute, Part, ureg

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
from sysml2py import Action

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
from sysml2py import Reference, Item

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
from sysml2py import loads
from sysml2py.formatting import classtree

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

**61% of the 56 grammar round-trip tests currently pass** (34/56), covering packages, parts, items, ports, interfaces, binding connectors, flow connections, all action forms (definition, shorthand, succession, decomposition), expressions, calculations, and constraints.

## Conformance

**99% of 123 OMG XPect conformance tests pass** (122/123). The single remaining failure (`ElementFilter.sysml`) is an ANTLR grammar limitation, not a Python code gap.

## License
sysml2py is released under the MIT license, hence allowing commercial use of the library.
