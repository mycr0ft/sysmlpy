"""Issue #25 (CARTA downstream report): kind-less members, variants, enum
values and the reference marker.

Five emission gaps, each pinned across the layers:

* `variant automatic;` / `variant 'six cyl' { }` (keyword-less variant
  members — `VariantUsageElement → VariantReference`) dropped entirely.
  They now build Reference elements with ``is_variant`` set, addressable
  by the referenced chain name (same bare-reference convention as the
  `:>>` forms), and re-emit the `variant` keyword on dump.
* `enum def Color { a; enum b; }` — the enumeration built but its values
  never reached the model (§7.8.2).  Values are now child elements of the
  Enumeration (``EnumeratedValue``, keyword preserved).
* `ref part r : X;` had no ``is_reference`` (§7.6.4 marks a referential
  usage).  The BasicUsagePrefix REF token now sets ``Usage.is_reference``;
  kind-less elements are referential by construction.
* `private ref #M z1;` / `abstract #M z2;` (kind-less usages with a
  prefix chain) dropped.  They now build as Reference elements carrying
  the `#M` metadata annotation and re-emit visibility + `ref`/flags +
  `#M` in source order.
* `abstract z2;` loses its flag on dump (dumps `z2;`) — refPrefix flag
  tokens (abstract/variation/derived/constant) now round-trip.  `constant`
  re-emits as `constant` (the textual keyword; `readonly` is not in the
  grammar — the isReadOnly field name is a historical misnomer).
"""

import os

import pytest

from sysmlpy import loads, parse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARIABILITY_MODEL = os.path.join(
    REPO_ROOT, "..", "third_party", "SysML-v2-Release", "sysml", "src",
    "examples", "Variability Examples", "VehicleVariabilityModel.sysml")


def test_issue25_keywordless_variants_are_elements():
    model = loads("""package P {
  part def D;
  variation part def E :> D {
    variant 'six cyl';
    variant automatic;
    variant part manual;
  }
}""")
    e = model.find_one("E")
    variants = [(c.name, c.is_variant, type(c).__name__)
                for c in e.children]
    assert ("'six cyl'", True, "Reference") in variants, variants
    assert ("automatic", True, "Reference") in variants, variants
    assert ("manual", True, "Part") in variants, variants
    # the referenced chain stays reachable
    auto = model.find_one("automatic")
    assert auto.variant_reference == ["automatic"]


def test_issue25_keywordless_variant_round_trip():
    model = loads("""package P {
  part def D;
  variation part def E :> D {
    variant 'six cyl';
    variant automatic {
      attribute note : String;
    }
  }
}""")
    dump = model.dump()
    assert "variant 'six cyl';" in dump, dump
    # keyword-less with a body keeps body + keyword
    assert "variant automatic {" in dump, dump
    again = loads(dump)
    assert str(again).strip() == dump.strip()
    e2 = again.find_one("E")
    assert [(c.name, c.is_variant) for c in e2.children] == [
        ("'six cyl'", True), ("automatic", True)]


def test_issue25_enum_values_are_children():
    model = loads("package P { enum def Color { a; enum b; } }")
    color = model.find_one("Color")
    assert [(c.name, c.keyword) for c in color.children] == [
        ("a", None), ("b", "enum")], color.children
    # serialization is untouched (the grammar body carries the values)
    dump = model.dump()
    assert "a;" in dump and "enum b;" in dump, dump
    assert str(loads(dump)).strip() == dump.strip()


def test_issue25_ref_part_has_is_reference():
    model = loads("""package P {
  part def X;
  part def D {
    ref part r : X;
    part s;
  }
}""")
    d = model.find_one("D")
    r = model.find_one("r")
    s = model.find_one("s")
    assert r.is_reference is True, r.is_reference
    assert s.is_reference is False, s.is_reference
    d.children == [r, s]  # order preserved (smoke)


def test_issue25_kindless_prefixed_usages():
    model = loads("""package P {
  metadata def M;
  part def D {
    private ref #M z1;
    abstract #M z2;
  }
}""")
    z1 = model.find_one("z1")
    z2 = model.find_one("z2")
    assert z1 is not None and z2 is not None
    assert z1.is_reference is True
    # both carry the #M annotation
    assert [a.type_name for a in z1.annotations] == ["M"]
    assert [a.type_name for a in z2.annotations] == ["M"]
    # and the round trip keeps visibility, ref and metadata in order
    dump = model.dump()
    assert "private ref #M z1;" in dump, dump
    assert "abstract #M z2;" in dump, dump
    again = loads(dump)
    assert [a.type_name for a in again.find_one("z1").annotations] == ["M"]


def test_issue25_refprefix_flags_round_trip():
    model = loads("package P { part def D { abstract z2; constant c1; } }")
    dump = model.dump()
    assert "abstract z2;" in dump, dump
    # `constant` is the textual keyword; `readonly` is not in the grammar
    assert "constant c1;" in dump, dump
    assert str(loads(dump)).strip() == dump.strip()


def test_issue25_kindless_plain_forms_still_work():
    # these shipped earlier — guard against the #25 work regressing them
    model = loads("package P { part def D { ref plain; abstract z2; } }")
    d = model.find_one("D")
    assert [(c.name, type(c).__name__) for c in d.children] == [
        ("plain", "Reference"), ("z2", "Reference")]
    dump = model.dump()
    assert "ref plain;" in dump and "abstract z2;" in dump, dump


def test_issue25_omg_variability_corpus():
    """The OMG VehicleVariabilityModel uses exactly these forms
    (`variant '4cylEngine';`, `variant automaticTransmission;` …)."""
    path = os.path.abspath(VARIABILITY_MODEL)
    if not os.path.exists(path):
        pytest.skip("SysML-v2-Release clone not present")
    with open(path) as f:
        src = f.read()
    model, _issues = parse(src)
    assert model is not None, _issues[:3]
    named = model.find()
    variant_refs = [c for c in named
                    if getattr(c, "variant_reference", None)]
    assert "'4cylEngine'" in [c.name for c in variant_refs], \
        [c.name for c in variant_refs]
    assert {"'6cylEngine'", "manualTransmission", "automaticTransmission"} \
        <= {c.name for c in variant_refs}
    # the `variant` keyword re-emits for the keyword-less members and the
    # file re-parses (pre-existing, out of #25: assert-constraint
    # expression bodies glue on the first dump and are captured as
    # textual representations on re-parse, so this file has no
    # whole-dump identity — pinned here scoped to the variant members)
    dump = model.dump()
    assert "variant '4cylEngine';" in dump
    assert "variant automaticTransmission;" in dump
    model2, _issues2 = parse(dump)
    assert model2 is not None
    named2 = model2.find()
    refs2 = {c.name for c in named2 if getattr(c, "variant_reference", None)}
    assert {"'4cylEngine'", "'6cylEngine'", "manualTransmission",
            "automaticTransmission"} <= refs2