"""Relationship endpoints and metadata applications — the issue #23/#24 API.

Downstream report (CARTA): a SysML v2 → program-roadmap tool reading
``sysmlpy.parse()`` + the element object model had to re-implement name
lookup in a ~300-line source-text scanner because

* `dependency` / `allocation` / `satisfy` / `verify` kept their endpoints on
  the grammar object only, and
* metadata applications (`@M { … }`, `#M` prefix, `metadata … about`) were
  not attached to the annotated elements at all.

Endpoints are names as written (what you would expect from the source text);
`*_elements` resolves them against the model lazily and only for
unambiguous names.  Metadata applications record the applied definition
(`type_name`), the `about` targets (names as written) and the braced-body
values as text.

Run: python examples/metadata_and_endpoints.py
"""

import sys

from sysmlpy import Model

MODEL = """package P {
  metadata def Planning { attribute owner : String; }

  part def A;
  part def B;
  requirement def R;
  part def S;
  part def T {
    satisfy R by S;
  }
  #Planning part def Tracked;
  part def Monitored { @Planning { owner = 'ops'; } }
  metadata plan1 : Planning about Tracked;

  dependency d from A to B;
  allocation al allocate A to B;
  verification def V { objective { verify R; } }
}"""


def _walk(el):
    """Depth-first walk of the element tree (Model has no walk() today)."""
    yield el
    for child in getattr(el, "children", None) or []:
        yield from _walk(child)


def main():
    model = Model()
    model.load(MODEL)

    pkg = model.children[0]
    print("== endpoints (names as written; *_elements resolve unambiguous names)")
    for el in _walk(model):
        kind = type(el).__name__
        if kind == "Dependency":
            print(f"  dependency {el.name}: {el.clients} -> {el.suppliers}"
                  f"  (resolved: {[e.name for e in el.client_elements]}"
                  f" -> {[e.name for e in el.supplier_elements]})")
        elif kind == "Allocation" and el.name is not None:
            print(f"  allocation {el.name}: {el.source} -> {el.target}")
        elif getattr(el, "is_satisfy", False):
            print(f"  satisfy (inside {el.parent.name}):"
                  f" requirement={el.requirement} satisfying={el.satisfying}"
                  f" resolved={[e.name for e in el.satisfy_elements()]}")

    case = model.find_one("V")
    print("== verification")
    print(f"  {case.name}.verified_requirements = {case.verified_requirements}")
    print(f"  verify elements: {[c.requirement for c in case.children
                                     if type(c).__name__ == 'Verify']}")

    print("== traceability reads the same data (no text scanning)")
    from sysmlpy import traceability
    report = traceability.extract_traceability(model)
    for req in report.requirements:
        print(f"  {req.qualified_name}: satisfied_by={req.satisfied_by}"
              f" verified_by={req.verified_by}")

    print("== metadata applications")
    tracked = model.find_one("Tracked")
    monitored = model.find_one("Monitored")
    print(f"  #Planning part def Tracked -> annotations:"
          f" {[(a.type_name, a.values) for a in tracked.annotations]}")
    print(f"  part def Monitored @Planning {{ owner = 'ops'; }} ->"
          f" {[(a.type_name, a.values) for a in monitored.annotations]}")
    plan1 = model.find_one("plan1")
    print(f"  plan1: type={plan1.type_name} about={plan1.annotated}"
          f"  (resolved: {[e.name for e in plan1.annotated_elements]})")


if __name__ == "__main__":
    main()