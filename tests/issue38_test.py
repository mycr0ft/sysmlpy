"""Issue #38 — multiple redefinitions were dumped without their comma.

`redefines` is a comma list in SysML (``attribute :>> A::x, B::x;``), but
``Redefinitions.dump()`` joined the targets with a plain space::

    attribute :>> ThermodynamicTemperatureUnit::quantityDimension TemperatureDifferenceUnit::quantityDimension {

which the grammar rejects, so SI.sysml / USCustomaryUnits / ShapeItems never
round-tripped.  ``References`` (``::>``) had the mirror-image bug: that operator
repeats per target and the grammar rejects a comma list.
"""

import pathlib
import warnings

import pytest

from sysmlpy import loads, parse

LIB = pathlib.Path("/home/jfox/proj/sysmlpy/src/sysmlpy/library")

PREFIX = "package P { "


def _lines(src):
    model = loads(PREFIX + src + " }")
    dump = model.dump()
    return model, dump


def _dump_line(dump, token):
    return [ln.strip() for ln in dump.splitlines() if token in ln][0]


@pytest.mark.parametrize("src,token,expected", [
    ("attribute :>> A::x, B::x;", ":>>", "attribute :>> A::x, B::x;"),
    ("attribute :>> A::x, B::x : Real;", ":>>", "attribute :>> A::x, B::x : Real;"),
    ("attribute y :>> A::x, B::x;", ":>>", "attribute y :>> A::x, B::x;"),
    ("attribute :>> A::x;", ":>>", "attribute :>> A::x;"),
])
def test_redefinition_list_keeps_its_commas(src, token, expected):
    _, dump = _lines(src)
    assert _dump_line(dump, token) == expected


@pytest.mark.parametrize("src,expected", [
    ("attribute ::> A ::> B;", "attribute ::> A ::> B;"),
    ("attribute ::> A;", "attribute ::> A;"),
])
def test_reference_list_repeats_the_operator(src, expected):
    """The grammar accepts `::> A ::> B`, not `::> A, B`."""
    _, dump = _lines(src)
    assert _dump_line(dump, "::>") == expected


@pytest.mark.parametrize("src", [
    "attribute :>> A::x, B::x;",
    "attribute :>> A::x, B::x : Real;",
    "attribute y :>> A::x, B::x;",
    "part p :>> A::q, B::q;",
    "attribute ::> A ::> B;",
    "part p { attribute :>> A::x, B::x; }",
])
def test_redefinition_dump_is_a_fixed_point(src):
    model, dump = _lines(src)
    model2, warns = parse(dump)
    assert model2 is not None, warns
    assert model2.dump() == dump


def test_no_space_joined_redefinition_survives():
    """The regression shape: `:>> A::x B::x` (no comma) must never be emitted."""
    _, dump = _lines("attribute :>> A::x, B::x { }")
    assert ":>> A::x B::x" not in dump


@pytest.mark.skipif(not (LIB / "domain/Quantities and Units/SI.sysml").exists(),
                    reason="library layout differs")
@pytest.mark.parametrize("rel", [
    "domain/Quantities and Units/SI.sysml",
    "domain/Quantities and Units/SIPrefixes.sysml",
    "domain/Quantities and Units/USCustomaryUnits.sysml",
])
def test_redefinition_heavy_library_files_round_trip(rel):
    """These three could not be re-parsed before #38."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        source = (LIB / rel).read_text(encoding="utf-8")
        first = loads(source).dump()
    assert ":>>" in first
    model, warns = parse(first)
    assert model is not None, warns
    assert model.dump() == first
