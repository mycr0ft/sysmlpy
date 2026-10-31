"""Issue #23 (CARTA downstream report): relationship endpoints on the object model.

`dependency`, `allocation`, `satisfy` and `verify` all parse, and the
*grammar* objects keep the endpoints — only the public element model drops
them:

* `Dependency` was built with ``Dependency()`` and never read
  ``inner_element.clients/.suppliers`` (definition.py, issue #4 branch).
* `Allocation` had no source/target; the grammar's
  ``AllocationUsage.connectorPart`` has carried the ends since issue #5 / PR #6.
* `satisfy R by S;` became a `Requirement` whose `subject`/`verified_by` were
  never touched; `ors` (the requirement) and `ssm` (the satisfying subject)
  were unread.
* `verification def V { objective { verify R; } }` had *no* verify element and
  no `verified_requirements` — the only grammatical home for `verify` is the
  objective's requirement body (`CaseBody → CaseBodyItem → ObjectiveMember →
  ObjectiveRequirementUsage → RequirementBody → RequirementBodyItem(owned…=
  RequirementVerificationMember → VerifyRequirementUsage)`).

`Requirement.requirement` / `.satisfying` and the endpoints are names as
written (`satisfy P::R by S;` stays ``'P::R'``); `*_elements` properties
resolve against the model only when they are asked for.
"""

import pytest

from sysmlpy import loads


MODEL = """
package P {
  part def A;
  part def B;
  part def C;
  part a : A;
  part b : B;
  part c : C;
  requirement def R;
  part def S;
  part def T { satisfy R by S; }
  dependency d from A to B;
  allocation al allocate a to b;
  allocate a to c;
  verification def V { objective { verify R; } }
}
"""


def _one(model, cls, name=None):
    found = [e for e in model.children[0].children
             if type(e).__name__ == cls and (name is None or e.name == name)]
    assert found, [(type(e).__name__, e.name) for e in model.children[0].children]
    return found[0]


def test_issue23_dependency_endpoints():
    model = loads(MODEL)
    dep = _one(model, "Dependency", "d")
    assert dep.clients == ["A"], dep.clients
    assert dep.suppliers == ["B"], dep.suppliers


def test_issue23_dependency_multi_client():
    model = loads("package P { part def A; part def B; "
                  "dependency d from A, B to B; }")
    dep = _one(model, "Dependency", "d")
    assert dep.clients == ["A", "B"]
    assert dep.suppliers == ["B"]


def test_issue23_dependency_unnamed():
    model = loads("package P { part def A; part def B; "
                  "dependency A to B; }")
    dep = _one(model, "Dependency", None)
    assert dep.clients == ["A"]
    assert dep.suppliers == ["B"]


def test_issue23_dependency_endpoints_resolve():
    model = loads("package P { part def A; part def B; "
                  "part a : A; dependency d from a to A; }")
    dep = _one(model, "Dependency", "d")
    # `a` names exactly one element (the usage), `A` exactly one (the
    # definition) — both resolve; ambiguous names would return nothing.
    assert [e.name for e in dep.client_elements] == ["a"]
    assert [e.name for e in dep.supplier_elements] == ["A"]


def test_issue23_allocation_endpoints():
    model = loads(MODEL)
    al = _one(model, "Allocation", "al")
    assert al.source == ["a"], al.source
    assert al.target == ["b"], al.target


def test_issue23_allocation_anonymous_nary():
    model = loads("package P { part def A; part def B; part def C; "
                  "part a : A; part c1 : C; part c2 : C; "
                  "allocate (a, c1, c2); }")
    al = _one(model, "Allocation", None)
    assert al.source == ["a", "c1", "c2"]
    assert al.target == []


def test_issue23_satisfy_requirement_and_satisfying():
    model = loads(MODEL)
    t = model.find_one("T")
    sat = [c for c in t.children
           if getattr(c, "requirement", None) == "R"]
    assert sat, [(type(c).__name__, getattr(c, "name", None)) for c in t.children]
    assert sat[0].satisfying == ["S"]


def test_issue23_satisfy_qualified_reference_stays_as_written():
    model = loads("""
        package LIB { requirement def R2; }
        package P {
          private import LIB::*;
          part def S;
          part def T { satisfy LIB::R2 by S; }
        }
    """)
    t = model.find_one("T")
    sat = [c for c in t.children if getattr(c, "requirement", None)][0]
    assert sat.requirement == "LIB::R2"
    assert sat.satisfying == ["S"]


def test_issue23_satisfy_without_by():
    model = loads("package P { requirement def R; part def T { satisfy R; } }")
    t = model.find_one("T")
    sat = [c for c in t.children if getattr(c, "requirement", None)][0]
    assert sat.satisfying == []


def test_issue23_verification_case_verified_requirements():
    model = loads(MODEL)
    v = model.find_one("V")
    assert v.verified_requirements == ["R"], v.verified_requirements
    assert any(type(c).__name__ == "Verify" and c.requirement == "R"
               for c in v.children), [type(c).__name__ for c in v.children]


def test_issue23_traceability_verified_by():
    from sysmlpy import traceability
    model = loads(MODEL)
    report = traceability.extract_traceability(model)
    trace = report.by_name("R")
    assert trace is not None
    assert "P::V" in trace.verified_by, trace.verified_by


def test_issue23_dump_round_trip_unaffected():
    import sysmlpy
    model = loads(MODEL)
    dump = model.dump()
    again = sysmlpy.parse(dump)[0]
    assert again is not None, sysmlpy.parse(dump)[1]
    assert str(again).strip() == dump.strip()