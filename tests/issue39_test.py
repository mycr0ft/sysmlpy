"""Issue #39 — a binding connector lost its `binding` keyword and multiplicity.

`binding [1] bind [0..*] base.edges = [0..*] be;` (ShapeItems.sysml) came back as

    binding  bind [0..*] base.edges = [0..*] be ;      first dump: [1] gone
    bind [0..*] base.edges = [0..*] be ;               second dump: keyword gone

Three separate causes:

* the connector's usage-declaration multiplicity was never read by the visitor;
* ``BindingConnector.dump()`` appended the (empty, anonymous) declaration as its
  own token, producing the double space and letting the keyword look accidental;
* a bare ``bind ...`` (no ``binding`` prefix) was indistinguishable from
  ``binding bind ...``, so the dumper either invented or dropped the keyword.

The connector's ``usageBody`` was also hardcoded empty, so members inside
``binding ... { members }`` were dropped.
"""

import pathlib
import warnings

import pytest

from sysmlpy import loads, parse

LIB = pathlib.Path("/home/jfox/proj/sysmlpy/src/sysmlpy/library")
SHAPE_ITEMS = LIB / "domain/Geometry/ShapeItems.sysml"


def _dump(inner):
    model = loads("package P { part p { " + inner + " } }")
    return model.dump()


def _bind_lines(dump):
    return [ln.strip() for ln in dump.splitlines() if "bind" in ln]


@pytest.mark.parametrize("inner,expected", [
    ("binding [1] bind a.b = c;", "binding [1] bind a.b = c;"),
    ("binding [0..1] bind a.b = c;", "binding [0..1] bind a.b = c;"),
    ("binding bind a.b = c;", "binding bind a.b = c;"),
    ("bind a.b = c;", "bind a.b = c;"),
    ("binding [1] bind [0..*] a.b = [0..*] c;",
     "binding [1] bind [0..*] a.b = [0..*] c;"),
])
def test_binding_keyword_and_multiplicity_survive(inner, expected):
    assert _bind_lines(_dump(inner)) == [expected]


@pytest.mark.parametrize("inner", [
    "binding [1] bind a.b = c;",
    "binding [0..1] bind a.b = c;",
    "binding bind a.b = c;",
    "bind a.b = c;",
    "binding [1] bind a.b = c { attribute note : Real; }",
])
def test_binding_dump_is_a_fixed_point(inner):
    dump = _dump(inner)
    model, warns = parse(dump)
    assert model is not None, warns
    assert model.dump() == dump


def test_binding_body_members_are_kept():
    dump = _dump("binding [1] bind a.b = c { attribute note : Real; }")
    assert "attribute note : Real;" in dump


def test_bare_bind_does_not_gain_the_binding_keyword():
    assert _bind_lines(_dump("bind a.b = c;")) == ["bind a.b = c;"]


@pytest.mark.parametrize("inner,expected", [
    ("first a then b;", "first a then b;"),
    ("succession first a then b;", "succession first a then b;"),
    ("succession first [0..1] a then [0..1] b;",
     "succession first [0..1] a then [0..1] b;"),
])
def test_succession_keyword_is_preserved_not_invented(inner, expected):
    """`Succession.dump()` had the same empty-token bug as the binding
    connector, and the (optional) `succession` keyword was unconditional."""
    dump = _dump(inner)
    lines = [ln.strip() for ln in dump.splitlines() if "then" in ln]
    assert lines == [expected]
    assert "  " not in lines[0]


@pytest.mark.skipif(not (LIB / "systems/Flows.sysml").exists(),
                    reason="library layout differs")
def test_flows_dump_is_a_fixed_point():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = loads((LIB / "systems/Flows.sysml").read_text(encoding="utf-8")).dump()
    assert "succession  first" not in first
    model, warns = parse(first)
    assert model is not None, warns
    assert model.dump() == first


@pytest.mark.skipif(not SHAPE_ITEMS.exists(), reason="library layout differs")
def test_corpus_shape_items_round_trips():
    """The file that reported this: 5+ binding connectors with multiplicities."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = loads(SHAPE_ITEMS.read_text(encoding="utf-8")).dump()
    assert "binding [1] bind" in first
    assert "{'name" not in first
    model, warns = parse(first)
    assert model is not None, warns
    assert model.dump() == first


@pytest.mark.skipif(not (LIB / "domain/Quantities and Units/SI.sysml").exists(),
                    reason="library layout differs")
@pytest.mark.parametrize("rel", [
    "domain/Quantities and Units/SI.sysml",
    "domain/Quantities and Units/SIPrefixes.sysml",
    "domain/Quantities and Units/USCustomaryUnits.sysml",
    "domain/Geometry/ShapeItems.sysml",
])
def test_quantities_and_geometry_libraries_round_trip(rel):
    """All four files that leaked raw dicts in 0.102.7 are now fixed points."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = loads((LIB / rel).read_text(encoding="utf-8")).dump()
    assert "{'name" not in first
    model, warns = parse(first)
    assert model is not None, warns
    assert model.dump() == first
