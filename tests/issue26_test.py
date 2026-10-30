"""Issue #26 (CARTA downstream report): `flow` usages never reach the model.

Reported by a downstream integrator against 0.99.5 as a dump/round-trip
defect (`flow x from a to b;` came out as `flow x from a. to b.;`, which does
not re-parse). Triaged on 0.99.6 the damage was worse: the flow element was
missing from the public tree entirely.

Two independent defects:

* `Package.load_from_grammar`'s body navigation only unwrapped a *wrapped*
  usage member (`PackageMember -> UsageElement -> ...`). A `flow`/`allocation`
  member arrives as a bare `UsageElement` (`UsageElement ->
  OccurrenceUsageElement -> StructureUsageElement -> FlowConnectionUsage`), so
  the navigation fell through to `continue` and the element was never built.
* `FlowEndSubsetting.dump` appended a literal "." to the end's qualified name,
  gluing `p.` / `q.` into the statement; the "." belongs to the
  end/feature-chain separator (`FlowEnd.dump`).
* `FlowConnectionUsage.declaration` is a `FlowConnectionDeclaration`, one level
  deeper than a plain `UsageDeclaration`, so the element kept its uuid name
  instead of the declared one.
"""

from sysmlpy import parse, loads


def _dump(src):
    model = parse(src)[0]
    assert model is not None, parse(src)[1]
    return model, str(model)


FLOW = """package P {
  part def S;
  part def T;
  part p : S;
  part q : T;
  flow x from p to q;
}"""


def test_issue26_flow_is_a_model_element():
    model = parse(FLOW)[0]
    assert model is not None
    names = [(type(e).__name__, e.name) for e in model.children[0].children]
    assert ("Flow", "x") in names, names


def test_issue26_flow_dumps_without_glued_dots():
    _, dump = _dump(FLOW)
    assert "flow x from p to q;" in dump, dump
    assert "p." not in dump and "q." not in dump


def test_issue26_flow_dump_round_trips():
    _, dump = _dump(FLOW)
    again = parse(dump)[0]
    assert again is not None, parse(dump)[1]
    assert str(again).strip() == dump.strip()


def test_issue26_flow_with_port_ends():
    src = """package P {
  port def PD;
  part def A { port pp : PD; }
  part def B { port qq : PD; }
  part a : A; part b : B;
  flow f from a.pp to b.qq;
}"""
    _, dump = _dump(src)
    assert "flow f from a.pp to b.qq;" in dump, dump
    assert parse(dump)[0] is not None


def test_issue26_flow_payload_and_of():
    src = """package P {
  part def S; part def T; part def Fuel;
  part p : S; part q : T;
  flow of Fuel from p to q;
}"""
    model, dump = _dump(src)
    assert "flow" in dump and "from p to q" in dump, dump
    assert parse(dump)[0] is not None


def test_issue26_flow_body_members_survive():
    src = """package P {
  part def S; part def T;
  part p : S; part q : T;
  flow x from p to q { attribute note : String; }
}"""
    model = parse(src)[0]
    assert model is not None
    flow = [c for c in model.children[0].children
            if type(c).__name__ == "Flow"][0]
    assert flow.name == "x"
    assert [(type(c).__name__, c.name) for c in flow.children] == [
        ("Attribute", "note")
    ]
    dump = str(model)
    assert "flow x from p to q {" in dump, dump
    again = parse(dump)[0]
    assert again is not None
    assert str(again).strip() == dump.strip()
