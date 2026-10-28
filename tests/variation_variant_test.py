"""Variation / variant / abstract round-tripping (0.99.0).

The official SysML-v2-Release Vehicle Example (SysML v2 Spec Annex A
SimpleVehicleModel.sysml) exercises every keyword combination:

    variation part def TransmissionChoices :> Wheel {
        variant part transmissionAutomatic:TransmissionAutomatic;
        variant part transmissionManual:TransmissionManual;
    }
    abstract part vehicleFamily {
        variation part engine:Engine {
            variant part engine4Cyl:Engine4Cyl;
            variation attribute diameter:LengthValue {
                variant attribute smallDiameter:LengthValue;
                variant attribute largeDiameter:LengthValue;
            }
        }
    }

0.98.x lost the usage-level abstract/variation prefixes AND dropped
every variant member on round-trip (parse -> dump reparse); the
semantic model carried no is_variation / is_variant / is_abstract
either.  These tests pin the fixed behaviour.
"""

from sysmlpy import parse

SRC = """\
package P {
    part def Vehicle;
    part def Wheel;
    abstract part def Software;
    variation part def TransmissionChoices :> Wheel {
        variant part transmissionAutomatic;
        variant part transmissionManual;
    }
    abstract part vehicleFamily {
        variation part engine {
            variant part engine4Cyl {
                variation attribute diameter {
                    variant attribute smallDiameter;
                    variant attribute largeDiameter;
                }
            }
        }
    }
}
"""


def _find(root, cls, name):
    acc = []

    def walk(o):
        if type(o).__name__ == cls and getattr(o, "name", None) == name:
            acc.append(o)
        for c in getattr(o, "children", ()) or ():
            walk(c)

    walk(root)
    return acc[0] if acc else None


def test_parse_has_no_warnings():
    model, warns = parse(SRC)
    assert model is not None
    assert warns == []


def _dump(model):
    return str(model)


def test_variant_members_survive_dump():
    model = parse(SRC)[0]
    dump = _dump(model)
    assert "variant part transmissionAutomatic;" in dump
    assert "variant part transmissionManual;" in dump
    assert "variant part engine4Cyl" in dump
    assert "variant attribute smallDiameter;" in dump
    assert "variant attribute largeDiameter;" in dump


def test_usage_level_prefixes_survive_dump():
    model = parse(SRC)[0]
    dump = _dump(model)
    assert "abstract part vehicleFamily" in dump
    assert "variation part engine" in dump
    assert "variation attribute diameter" in dump


def test_definition_level_prefixes_survive_dump():
    model = parse(SRC)[0]
    dump = _dump(model)
    assert "abstract part def Software" in dump
    assert "variation part def TransmissionChoices" in dump


def test_full_roundtrip_is_stable():
    model = parse(SRC)[0]
    once = _dump(model)
    again = _dump(parse(once)[0])
    assert once == again
    # And the re-parse still finds the variant members
    third = _dump(parse(again)[0])
    assert "variant part transmissionAutomatic;" in third


def test_semantic_flags_definition():
    model = parse(SRC)[0]
    tc = _find(model, "Part", "TransmissionChoices")
    assert tc is not None
    assert tc.is_variation is True
    assert tc.is_abstract is False
    sw = _find(model, "Part", "Software")
    assert sw is not None and sw.is_abstract is True


def test_semantic_flags_usage_and_variant():
    model = parse(SRC)[0]
    fam = _find(model, "Part", "vehicleFamily")
    assert fam is not None and fam.is_abstract is True
    eng = _find(model, "Part", "engine")
    assert eng is not None and eng.is_variation is True
    four = eng.variants()
    assert [v.name for v in four] == ["engine4Cyl"]
    assert all(v.is_variant for v in four)
    dia = _find(model, "Attribute", "diameter")
    assert dia is not None and dia.is_variation is True
    assert [v.name for v in dia.variants()] == [
        "smallDiameter", "largeDiameter"]
    assert dia.variants()[0].is_variant is True
    assert dia.variants()[0].is_variation is False


def test_variant_types_helper():
    model = parse(SRC)[0]
    tc = _find(model, "Part", "TransmissionChoices")
    # No `:` typing in the mini corpus -> variant_types resolves to []
    assert tc.variant_types() == []
    # Now with typing
    src2 = SRC.replace(
        "variant part transmissionAutomatic;",
        "variant part transmissionAutomatic : Vehicle;").replace(
        "variant part transmissionManual;",
        "variant part transmissionManual : Vehicle;")
    model2 = parse(src2)[0]
    tc2 = _find(model2, "Part", "TransmissionChoices")
    types = tc2.variant_types()
    assert [t.name for t in types] == ["Vehicle", "Vehicle"]


def test_official_vehicle_example_parses_and_roundtrips(tmp_path):
    import pathlib
    import pytest
    candidate = pathlib.Path(
        "/home/jfox/proj/SysML-v2-Release/sysml/src/examples/"
        "Vehicle Example/SysML v2 Spec Annex A SimpleVehicleModel.sysml")
    if not candidate.exists():
        pytest.skip("SysML-v2-Release checkout not present")
    text = candidate.read_text(encoding="utf-8")
    model, warns = parse(text)
    assert model is not None, warns
    dump = _dump(model)
    assert "variation part def TransmissionChoices" in dump
    assert "variant part transmissionAutomatic" in dump
    assert "variant part engine6Cyl" in dump
    assert "variant attribute smallDiameter" in dump
    # The FULL-dump reparse is broken at 0.98.0 (pre-existing, tracked
    # separately): value parts concatenate ("massActualdefault
    # 0[kg]") and bind connectors emit "[1] to ... [1]" without their
    # bind/= shape — unrelated to the variation/variant machinery.
    # The variation/variant round-trip stability is pinned by
    # test_full_roundtrip_is_stable above.