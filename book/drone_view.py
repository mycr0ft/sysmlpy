"""Generate a General View (BDD-style) of the drone model."""

from sysmlpy import load, as_general_view

with open("book/drone.sysml") as f:
    model = load(f)

puml = as_general_view(model, style="bw", include_legend=False, show_multiplicity=True)
print(puml)

with open("book/drone_gv.puml", "w") as f:
    f.write(puml)
print("Wrote book/drone_gv.puml")
