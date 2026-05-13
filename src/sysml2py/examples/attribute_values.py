"""Examples: Attribute Values, Types, and Complex Objects

This document explains how sysml2py handles different types of attribute values:
- Simple values (strings, numbers)
- Pint quantities with units
- Tuples and lists (partial support)
"""

from sysml2py import loads, Part, Attribute
from sysml2py.usage import ureg

# =============================================================================
# 1. Simple Values
# =============================================================================

# Strings
model = loads('''
package Example {
    attribute name : String = "Tesla";
}
''')
attr = model.children[0].children[0]
print(f"String: {attr.name} = {attr.get_value()}")

# Integers
model = loads('''
package Example {
    attribute count : Integer = 42;
}
''')
attr = model.children[0].children[0]
print(f"Integer: {attr.name} = {attr.get_value()}")

# Reals
model = loads('''
package Example {
    attribute price : Real = 49999.99;
}
''')
attr = model.children[0].children[0]
print(f"Real: {attr.name} = {attr.get_value()}")

# =============================================================================
# 2. Pint Quantities with Units
# =============================================================================

model = loads('''
package Example {
    part def Vehicle {
        attribute mass : Real = 1000 [kilogram];
        attribute speed : Real = 60 [mile/hour];
        attribute height : Real = 1.5 [meter];
    }
}
''')

vehicle = model.children[0].children[0]

for attr in vehicle.children:
    val = attr.get_value()
    print(f"{attr.name} = {val}")
    if hasattr(val, 'magnitude'):
        print(f"  magnitude: {val.magnitude}")
        print(f"  units: {val.units}")

# =============================================================================
# 3. Setting Values Programmatically
# =============================================================================

attr = Attribute()
attr._set_name("weight")

# With pint Quantity
attr.set_value(1500 * ureg.kilogram)
print(f"\nAfter setting: {attr.get_value()}")

# =============================================================================
# 4. Tuples and Lists (LIMITED SUPPORT)
# =============================================================================

# NOTE: The ANTLR4 grammar has partial support for sequences.
# Curly braces {} with commas do not currently parse.
# Workaround: Use multiple single-value attributes and combine in code.

# Workaround approach:
model = loads('''
package Example {
    part def Vehicle {
        attribute color1 : String = "red";
        attribute color2 : String = "green";
        attribute color3 : String = "blue";
    }
}
''')

vehicle = model.children[0].children[0]
colors = []
for child in vehicle.children:
    if isinstance(child, Attribute):
        try:
            colors.append(child.get_value())
        except:
            pass
print(f"\nColors as list: {colors}")

# =============================================================================
# 5. Type Resolution
# =============================================================================

# The type is stored in the grammar structure.
# typedby may not be populated during load_from_grammar (known issue).

model = loads('''
package Example {
    part def Vehicle {
        attribute mass : Real;
        attribute name : String;
    }
}
''')

vehicle = model.children[0].children[0]

for attr in vehicle.children:
    # Access grammar to see type info
    print(f"{attr.name}: grammar type = {type(attr.grammar).__name__}")

# =============================================================================
# 6. Attribute Multiplicity
# =============================================================================

# Attributes can have multiplicity like Real[3] for arrays
# The type information is stored in the grammar but not yet exposed via Python API

model = loads('''
package Example {
    attribute coords : Real[3];
}
''')
attr = model.children[0].children[0]
print(f"\nAttribute: {attr.name}")

# =============================================================================
# 7. Nested Attribute Bodies
# =============================================================================

# Attributes can contain nested elements (rare but valid)
model = loads('''
package Example {
    part def Vehicle {
        attribute sensors {
            attribute temperature : Real;
            attribute pressure : Real;
        }
    }
}
''')

vehicle = model.children[0].children[0]
sensors = vehicle.children[0]
print(f"\n{sensors.name} children: {[c.name for c in sensors.children]}")