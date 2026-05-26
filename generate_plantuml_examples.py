#!/usr/bin/env python3
"""Generate all PlantUML example diagrams for documentation."""

import sysmlpy
from sysmlpy.plantuml import (
    as_graphical_rendering, as_general_view, as_package_view, as_package_diagram_view,
    as_block_definition_view, as_internal_block_diagram, as_parametric_view,
    as_action_flow_view, as_interconnection_view, as_state_transition_view,
    as_tree_diagram, as_element_table, as_textual_notation,
    as_tabular_view, as_data_value_tabular_view, as_relationship_matrix_view,
    as_requirement_view
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

# 5. Requirements
print("\n5. Requirements")
model5 = sysmlpy.loads("""
package Requirements {
    requirement def PerformanceRequirement {
        subject : Part;
        goal : String;
    }
    requirement req1 : PerformanceRequirement {
        subject = Vehicle;
        goal = "Accelerate 0-60 in 5s";
    }
}
""")
generate_puml("05-requirements", as_requirement_view(model5))

# 6. Interconnection
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

# 9. Package Diagram
print("\n9. Package Diagram")
generate_puml("09-package-diagram", as_package_diagram_view(model8))

# 10. Block Definition Diagram (BDD)
print("\n10. Block Definition Diagram")
model10 = sysmlpy.loads("""
package Blocks {
    part def Vehicle {
        attribute mass : Real;
        attribute maxSpeed : Real;
        port powerIn;
        part engine : Engine;
    }
    part def Engine {
        attribute horsepower : Real;
        port powerOut;
    }
}
""")
# Note: BDD view uses PlantUML compartments which may not render in all versions
generate_puml("10-block-definition-view", as_block_definition_view(model10))

# 11. Internal Block Diagram (IBD)
print("\n11. Internal Block Diagram")
model11 = sysmlpy.loads("""
package System {
    part def Sensor { port dataOut; }
    part def Processor { port dataIn; port cmdOut; }
    part def Assembly {
        port input;
        port output;
        part s : Sensor;
        part p : Processor;
        flow f1 from input to s.dataOut;
        flow f2 from s.dataOut to p.dataIn;
        flow f3 from p.cmdOut to output;
    }
}
""")
assembly = model11.find('Assembly')[0]
generate_puml("11-internal-block-diagram", as_internal_block_diagram(model11, focus=assembly))

# 12. Parametric Diagram
print("\n12. Parametric Diagram")
model12 = sysmlpy.loads("""
package Constraints {
    constraint def NewtonsLaw {
        attribute force : Real;
        attribute mass : Real;
        attribute acceleration : Real;
        force = mass * acceleration;
    }
    constraint def KineticEnergy {
        attribute energy : Real;
        attribute mass : Real;
        attribute velocity : Real;
        energy = 0.5 * mass * velocity^2;
    }
}
""")
generate_puml("12-parametric-view", as_parametric_view(model12))

# 13. Action Flow View
print("\n13. Action Flow View")
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
generate_puml("13-action-flow-view", as_action_flow_view(model13))

# 14. State Transition View
print("\n14. State Transition View")
model14 = sysmlpy.loads("""
package States {
    state def Operational {
        state Idle;
        state Running;
        state Error;
    }
}
""")
operational = model14.find('Operational')[0]
generate_puml("14-state-transition-view", as_state_transition_view(model14, focus=operational))

# 15. Tree Diagram
print("\n15. Tree Diagram")
generate_puml("15-tree-diagram", as_tree_diagram(VEHICLE_MODEL))

# 16. Element Table
print("\n16. Element Table")
generate_puml("16-element-table", as_element_table(VEHICLE_MODEL))

# 17. Textual Notation
print("\n17. Textual Notation")
generate_puml("17-textual-notation", as_textual_notation(VEHICLE_MODEL))

# 18. Tabular View
print("\n18. Tabular View")
generate_puml("18-tabular-view", as_tabular_view(VEHICLE_MODEL))

# 19. Data Value View
print("\n19. Data Value View")
generate_puml("19-data-value-view", as_data_value_tabular_view(VEHICLE_MODEL))

# 20. Relationship Matrix
print("\n20. Relationship Matrix")
generate_puml("20-relationship-matrix", as_relationship_matrix_view(VEHICLE_MODEL))

# 21. Tabular View (Color)
print("\n21. Tabular View (Color)")
generate_puml("21-tabular-view-color", as_tabular_view(VEHICLE_MODEL, style="color"))

print("\n" + "=" * 60)
print("Generation complete!")
print("=" * 60)
