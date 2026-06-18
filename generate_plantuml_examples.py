#!/usr/bin/env python3
"""Generate all PlantUML example diagrams for documentation."""

import sysmlpy
from sysmlpy.plantuml import (
    as_graphical_rendering, as_general_view, as_package_view,
    as_action_flow_view, as_interconnection_view, as_state_transition_view,
    as_tree_diagram, as_element_table, as_textual_notation,
    as_tabular_view, as_data_value_tabular_view, as_relationship_matrix_view,
)
import subprocess
import os

OUTPUT_DIR = "docs/plantuml-examples"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample model for most examples
VEHICLE_MODEL = sysmlpy.loads("""
package Vehicle {
    part def Wheel {
        attribute radius : Real;
        attribute pressure : Real;
    }
    part def BrakeSystem {
        attribute padThickness : Real;
    }
    part def VehicleAssembly {
        part frontLeft : Wheel;
        part frontRight : Wheel;
        part brakes : BrakeSystem;
    }
    part myVehicle : VehicleAssembly;
}
""")

def generate_puml(name, puml_text):
    """Save PlantUML text and render to PNG."""
    puml_path = os.path.join(OUTPUT_DIR, f"{name}.puml")
    png_path = os.path.join(OUTPUT_DIR, f"{name}.png")
    
    with open(puml_path, 'w') as f:
        f.write(puml_text)
    
    # Render with PlantUML
    try:
        subprocess.run(
            ['java', '-jar', 'plantuml.jar', '-tpng', puml_path],
            cwd='/storage16/home/jfox/sysmlpy',
            check=True,
            capture_output=True
        )
        print(f"✓ Generated {name}.png")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to render {name}: {e.stderr.decode()}")
    except FileNotFoundError:
        print(f"⚠ PlantUML JAR not found, saved {name}.puml only")

print("=" * 60)
print("Generating PlantUML Examples")
print("=" * 60)

# 1. Usage vs Definition
print("\n1. Usage vs Definition")
model1 = sysmlpy.loads("""
package Example {
    part def Engine;
    part myEngine : Engine;
}
""")
generate_puml("01-usage-vs-definition", as_graphical_rendering(model1))

# 2. Relationship Arrows
print("\n2. Relationship Arrows")
model2 = sysmlpy.loads("""
package Example {
    part def Base;
    part def Derived :> Base;
    part def Container {
        part contained : Base;
    }
}
""")
generate_puml("02-relationships", as_graphical_rendering(model2))

# 3. Vehicle Structure (B&W)
print("\n3. Vehicle Structure")
generate_puml("03-vehicle-structure", as_graphical_rendering(VEHICLE_MODEL, style="bw"))

# 4. B&W Style
print("\n4. B&W Style")
generate_puml("04-bw-style", as_general_view(VEHICLE_MODEL, style="bw"))

# 5. Interconnection
print("\n6. Interconnection")
model6 = sysmlpy.loads("""
package System {
    part def Sensor { port output; }
    part def Processor { port input; port output; }
    part def Actuator { port input; }
    part def Controller {
        part s : Sensor;
        part p : Processor;
        part a : Actuator;
        flow f1 from s.output to p.input;
        flow f2 from p.output to a.input;
    }
}
""")
generate_puml("06-interconnection", as_interconnection_view(model6))

# 7. General View
print("\n7. General View")
generate_puml("07-general-view", as_general_view(VEHICLE_MODEL))

# 8. Package View
print("\n8. Package View")
model8 = sysmlpy.loads("""
package VehicleSystem {
    package Powertrain {
        part def Engine;
        part def Transmission;
    }
    package Chassis {
        part def Wheel;
        part def Suspension;
    }
}
""")
generate_puml("08-package-view", as_package_view(model8))

# 9. Action Flow View
print("\n10. Action Flow View")
model13 = sysmlpy.loads("""
package Activity {
    action def Start;
    action def Process;
    action def End;
    action def Main {
        action start : Start;
        action process : Process;
        action end_ : End;
        flow f1 from start to process;
        flow f2 from process to end_;
    }
}
""")
generate_puml("10-action-flow-view", as_action_flow_view(model13))

# 11. State Transition View
print("\n11. State Transition View")
# Note: Current implementation shows state hierarchy. Transitions require
# trigger/guard/effect attributes on transition elements which are not yet
# fully parsed. The diagram shows containment relationships between states.
model14 = sysmlpy.loads("""
package States {
    state def Operational {
        state Idle;
        state Running;
        state Error;
        state Stopped;
    }
}
""")
operational = model14.find('Operational')[0]
generate_puml("11-state-transition-view", as_state_transition_view(model14, focus=operational))

# 12. Tree Diagram
print("\n12. Tree Diagram")
generate_puml("12-tree-diagram", as_tree_diagram(VEHICLE_MODEL))

# 13. Element Table
print("\n13. Element Table")
generate_puml("13-element-table", as_element_table(VEHICLE_MODEL))

# 14. Textual Notation
print("\n14. Textual Notation")
generate_puml("14-textual-notation", as_textual_notation(VEHICLE_MODEL))

# 15. Tabular View
print("\n15. Tabular View")
# Use markdown format for PlantUML 1.2024.7+ compatibility
md = as_tabular_view(VEHICLE_MODEL, output_format="markdown")
with open(os.path.join(OUTPUT_DIR, "15-tabular-view.md"), 'w') as f:
    f.write(md)
print(f"✓ Generated 15-tabular-view.md")

# 16. Data Value View
print("\n16. Data Value View")
md = as_data_value_tabular_view(VEHICLE_MODEL, output_format="markdown")
with open(os.path.join(OUTPUT_DIR, "16-data-value-view.md"), 'w') as f:
    f.write(md)
print(f"✓ Generated 16-data-value-view.md")

# 17. Relationship Matrix
print("\n17. Relationship Matrix")
md = as_relationship_matrix_view(VEHICLE_MODEL, output_format="markdown")
with open(os.path.join(OUTPUT_DIR, "17-relationship-matrix.md"), 'w') as f:
    f.write(md)
print(f"✓ Generated 17-relationship-matrix.md")

# 18. Tabular View (Color) - HTML format for styling
print("\n18. Tabular View (Color)")
html = as_tabular_view(VEHICLE_MODEL, output_format="html", style="color")
with open(os.path.join(OUTPUT_DIR, "18-tabular-view-color.html"), 'w') as f:
    f.write(html)
print(f"✓ Generated 21-tabular-view-color.html")

print("\n" + "=" * 60)
print("Generation complete!")
print("=" * 60)
