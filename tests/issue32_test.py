"""Issue #32 — keyword-less variant members kept their body at grammar level.

`variant 'six cyl' { attribute note : String; }` built the variant Reference
(the v0.100.1 fix) but `Reference.load_from_grammar` returned before the shared
body dispatch, so the variant exposed **zero** children while its grammar (and
therefore its dump) carried the members.

Fix: the body-member dispatch in ``Usage.load_from_grammar`` is now
``Usage._load_body_members``; the VariantReference branch unpacks its
``UsageBody → DefinitionBody`` items the same way the usage path does and loads
them through that dispatch.
"""

import pathlib

import pytest

from sysmlpy import loads, parse

WITH_BODY = """package P {
  variation part def E {
    variant 'six cyl' {
      attribute note : String;
      part inner : E;
    }
  }
}"""

CORPUS = pathlib.Path(
    "/home/jfox/proj/third_party/SysML-v2-Release/sysml/src/examples/"
    "Variability Examples/VehicleVariabilityModel.sysml")


def _variation_def(model):
    return model.children[0].children[0]


def test_variant_body_members_become_children():
    element = _variation_def(loads(WITH_BODY))
    variant = element.children[0]
    assert type(variant).__name__ == "Reference"
    assert variant.name == "'six cyl'"
    assert [type(c).__name__ for c in variant.children] == ["Attribute", "Part"]
    assert [c.name for c in variant.children] == ["note", "inner"]


def test_variant_body_members_are_parented_to_the_variant():
    variant = _variation_def(loads(WITH_BODY)).children[0]
    assert all(c.parent is variant for c in variant.children)


def test_variant_body_round_trips():
    model = loads(WITH_BODY)
    first = model.dump()
    assert "attribute note : String;" in first
    assert "part inner : E;" in first
    model2, warns = parse(first)
    assert model2 is not None, warns
    assert model2.dump() == first
    # and the reloaded tree has the members again
    variant = _variation_def(model2).children[0]
    assert [c.name for c in variant.children] == ["note", "inner"]


def test_bodyless_variant_stays_childless():
    model = loads("package P { variation part def E { variant automatic; } }")
    variant = _variation_def(model).children[0]
    assert type(variant).__name__ == "Reference"
    assert variant.name == "automatic"
    assert variant.children == []


def test_variant_member_keeps_its_variant_marker():
    variant = _variation_def(loads(WITH_BODY)).children[0]
    assert variant.is_variant is True


def test_action_body_variants_load_as_children():
    """`variation action g : A { variant g1; }` — ActionBodyItem ->
    VariantUsageMember was never dispatched, so the variants existed only in
    the grammar (dump ok, element tree empty)."""
    src = """package P {
  action def A;
  action vary : A {
    variation action gen : A {
      variant gen4;
      variant gen6;
    }
  }
}"""
    model = loads(src)
    found = []

    def walk(element):
        for child in getattr(element, "children", []) or []:
            if getattr(child, "name", None) == "gen":
                found.append(child)
            walk(child)

    walk(model)
    gen = found[0]
    assert [(type(c).__name__, c.name) for c in gen.children] == [
        ("Reference", "gen4"), ("Reference", "gen6")]
    assert all(c.is_variant for c in gen.children)
    dump = model.dump()
    assert "variant gen4;" in dump and "variant gen6;" in dump
    model2, warns = parse(dump)
    assert model2 is not None, warns
    assert model2.dump() == dump


def test_nested_partial_variant_body():
    src = """package P {
  variation part def E {
    variant 'four cyl' { attribute note : String; }
    variant 'six cyl' { attribute note : String; attribute torque : Real; }
  }
}"""
    element = _variation_def(loads(src))
    assert [len(v.children) for v in element.children] == [1, 2]


@pytest.mark.skipif(not CORPUS.exists(), reason="SysML-v2-Release checkout not present")
def test_corpus_variants_load_with_children():
    """VehicleVariabilityModel mixes keyword-less `variant X` and
    `variant port p;` members; both must load and dump as before."""
    source = CORPUS.read_text(encoding="utf-8")
    model = loads(source)
    dump = model.dump()
    assert "variant port autoPort1;" in dump
    # comments in the source mention "variant" twice; count code only
    code_lines = [ln for ln in source.splitlines() if not ln.strip().startswith("//")]
    assert dump.count("variant") == "\n".join(code_lines).count("variant")
    model2, warns = parse(dump)
    assert model2 is not None, warns
    assert model2.dump() == dump

    variants = []

    def walk(element):
        for child in getattr(element, "children", []) or []:
            if type(child).__name__ == "Reference" and getattr(child, "is_variant", False):
                variants.append(child)
            walk(child)

    walk(model)
    assert variants, "no variant elements loaded"
    # the port-typed variants carry their port children
    assert any(v.children for v in variants)
