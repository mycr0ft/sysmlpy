#!/usr/bin/env python3
"""PoC: SysML v2 interconnection view rendered through sysmlpy's
diagramboxes adapter (boxes_view.as_interconnection_view_boxes).

A small vehicle-powertrain model: a `part vehicle` block containing
two typed part usages (fuel tank, engine), a reference usage (fuel
level), attribute usages, and port usages each with item definitions;
a typed internal connection (feed) and a package-level connection
(levelSignal) reaching the reference member.

Renders BOTH diagramboxes paths for the same Diagram content model:
  figv2_interconnection.txt  — terminal braille (drawille)
  figv2_interconnection.svg  — SVG (converted to .png by inkscape)
under /home/jfox/proj/sysml-distilled/reproduced/.

All model text is the user's own work.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sysmlpy.boxes_view import (            # noqa: E402
    as_interconnection_view_boxes,
    render_interconnection_view_boxes,
    render_interconnection_view_boxes_svg,
)

OUT_DIR = "/home/jfox/proj/sysml-distilled/reproduced"

MODEL = """
package VehiclePowertrain {
    item def Fuel;
    port def FuelSupply { out item fuel : Fuel; }
    port def FuelDemand { in item fuel : Fuel; }
    part def FuelTank { port supply : FuelSupply; attribute capacity : Real; }
    part def Engine { in port demand : FuelDemand; attribute power : Real; }
    part vehicle {
        part tank : FuelTank;
        part engine : Engine;
        ref fuelLevel;
        attribute ratio : Real;
        connection feed : FuelLine connect tank.supply to engine.demand;
    }
    ref telematicsUnit;
    connection levelSignal connect vehicle.fuelLevel to telematicsUnit;
}
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    braille = render_interconnection_view_boxes(MODEL)
    svg = render_interconnection_view_boxes_svg(MODEL, scale=2.0)
    base = os.path.join(OUT_DIR, "figv2_interconnection")
    with open(base + ".txt", "w") as f:
        f.write(braille)
    with open(base + ".svg", "w") as f:
        f.write(svg)
    # sanity checks: every expected element string present in the SVG
    expected = ("vehicle", "tank", "engine", "fuelLevel", "telematicsUnit",
                "supply", "demand", "feed : FuelLine", "levelSignal",
                "+ power : Real", "+ ratio : Real")
    missing = [t for t in expected if t not in svg]
    assert not missing, f"missing in svg: {missing}"
    subprocess.run(
        ["inkscape", base + ".svg", "--export-type=png",
         "--export-filename=" + base + ".png"],
        check=True, capture_output=True)
    # verify the diagram content model as well
    d = as_interconnection_view_boxes(MODEL)
    names = {n.name for n in d.nodes}
    assert names == {"vehicle", "tank", "engine", "fuelLevel",
                     "telematicsUnit"}, names
    vehicle = next(n for n in d.nodes if n.name == "vehicle")
    tank = next(n for n in d.nodes if n.name == "tank")
    assert tank.parent is vehicle
    assert [p.direction for p in tank.ports] == ["out"]
    print("PoC written:", base + ".txt/.svg/.png")


if __name__ == "__main__":
    main()