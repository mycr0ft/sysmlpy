"""Issue #29: interface ends are first-class children and keep their typing.

Before this, `interface def I { end e1 : PD; }` built an `Interface` with
**zero children** — the ends lived only in ``Interface.ends`` as
``(name, None, None)`` tuples — and the dump degraded to ``end e1;`` because
``_ensure_body`` re-emitted the name and dropped everything else.  The
``connect`` form also carried a literal newline in its keyword
(``interface ib connect\\n a to b;``).

The pins below cover the model, the dump fixed point, the ``::>`` chain, and
the programmatic API (which used to raise AttributeError on ``Model.dump()``
because ``Interface.grammar`` stayed None).
"""

from sysmlpy import Interface, InterfaceEnd, Model, Package, loads, parse


REPORTER_MODEL = """
package P {
  port def PD;
  interface def I {
    end e1 : PD;
    end e2 : PD;
  }
  part a; part b;
  interface ia : I;
  interface ib connect a to b;
}
"""

FULL_MODEL = """
package P {
  port def PD;
  part part1 { port p; }
  interface def I {
    end e1 : PD;
    end e2 : PD [1..*];
    end e3 ::> part1.p;
    end e4 : PD [0..1] ordered nonunique;
  }
  interface usageWithBody : I {
    end u1 : PD;
  }
}
"""


def _interfaces(model):
    return [el for el in model.find() if type(el).__name__ == "Interface"]


def _end_children(interface):
    return [c for c in interface.children if type(c).__name__ == "InterfaceEnd"]


def test_issue29_ends_are_children_with_typing():
    model = loads(REPORTER_MODEL)
    iface = next(i for i in _interfaces(model) if i.name == "I")
    ends = _end_children(iface)
    assert [e.name for e in ends] == ["e1", "e2"]
    assert [e.typed_by_name for e in ends] == ["PD", "PD"]
    # the legacy tuple view keeps working, now with the type filled in
    assert iface.ends == [("e1", "PD", None), ("e2", "PD", None)]


def test_issue29_dump_keeps_end_typing():
    model = loads(REPORTER_MODEL)
    dumped = model.dump()
    assert "end e1 : PD;" in dumped
    assert "end e2 : PD;" in dumped
    reparsed, issues = parse(dumped)
    assert reparsed is not None and not issues, issues
    assert reparsed.dump() == dumped, "dump must be a fixed point"


def test_issue29_multiplicity_and_flags_round_trip():
    dumped = loads(FULL_MODEL).dump()
    assert "end e2 : PD [1..*];" in dumped
    assert "end e4 : PD [0..1] ordered nonunique;" in dumped
    reparsed, issues = parse(dumped)
    assert reparsed is not None and not issues, issues
    assert reparsed.dump() == dumped
    iface = next(i for i in _interfaces(reparsed) if i.name == "I")
    mults = {e.name: e.multiplicity for e in _end_children(iface)}
    assert mults["e2"] == "[1..*]"
    assert mults["e4"] == "[0..1] ordered nonunique"


def test_issue29_reference_chain_survives():
    model = loads(FULL_MODEL)
    iface = next(i for i in _interfaces(model) if i.name == "I")
    e3 = next(e for e in _end_children(iface) if e.name == "e3")
    assert e3.reference == "part1.p"
    dumped = model.dump()
    assert "end e3 ::> part1.p;" in dumped
    reparsed, issues = parse(dumped)
    assert reparsed is not None and not issues, issues
    iface2 = next(i for i in _interfaces(reparsed) if i.name == "I")
    e3b = next(e for e in _end_children(iface2) if e.name == "e3")
    assert e3b.reference == "part1.p"
    # *_elements resolution is lazy and unambiguous-only (issue #23 rule)
    assert [el.name for el in e3b.reference_elements] == ["part1"]
    assert [el.name for el in e3b.typed_elements] == []


def test_issue29_interface_usage_body_ends():
    model = loads(FULL_MODEL)
    usage = next(i for i in _interfaces(model) if i.name == "usageWithBody")
    assert usage.is_definition is False
    assert [e.name for e in _end_children(usage)] == ["u1"]
    assert "end u1 : PD;" in model.dump()


def test_issue29_connect_form_is_single_line():
    dumped = loads(REPORTER_MODEL).dump()
    assert "connect a to b;" in dumped
    assert "connect\n" not in dumped
    reparsed, issues = parse(dumped)
    assert reparsed is not None and not issues, issues


def test_issue29_programmatic_interface_dumps_into_a_model():
    # pre-existing: Interface.grammar was None, so Model.dump() raised
    # AttributeError: 'NoneType' object has no attribute 'get_definition'
    for definition in (True, False):
        iface = Interface(definition=definition, name="I")
        iface.add_end("e1", "PD")
        end = InterfaceEnd("e2", "PD", "[1..*]", "part1.p")
        end.parent = iface
        iface.children.append(end)
        pkg = Package(name="P")
        pkg.children.append(iface)
        iface.parent = pkg
        model = Model()
        model.children.append(pkg)
        pkg.parent = model
        dumped = model.dump()
        assert "end e1 : PD;" in dumped, dumped
        assert "end e2 : PD [1..*] ::> part1.p;" in dumped, dumped
        reparsed, issues = parse(dumped)
        assert reparsed is not None and not issues, issues
        assert reparsed.dump() == dumped
