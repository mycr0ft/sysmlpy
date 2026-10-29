"""Annex A round-trip regressions (issue draft SYSMLPY_099_ANNEX_A_UPSTREAM_ISSUES).

Reported against 0.99.0 with the SysML-v2-Release Vehicle Example
("SysML v2 Spec Annex A SimpleVehicleModel.sysml"): the dump of a
model whose source parses emits text that no longer parses — defaults
concatenated onto redefined feature names, ``subject ... default``
glued, and interface connect-end multiplicities emitted in a form the
grammar rejects.
"""

from sysmlpy import parse

CASES = {
    # Issue 1: `default` concatenated after a redefinition
    "redefine_default": """package P {
  part def Vehicle {
    attribute cargoMass : Mass;
  }
  part vehicle : Vehicle {
    attribute redefines cargoMass default 0 [kg];
  }
}""",
    # Issue 2: expression-valued default
    "expr_default": """package P {
  part def Vehicle {
    attribute dryMass : Mass;
    attribute fuelMassActual : Mass;
  }
  requirement Requirement {
    subject vehicle : Vehicle;
    attribute redefines massActual default vehicle.dryMass + fuelMassActual;
  }
}""",
    # Issue 3: `subject ... default ...`
    "subject_default": """package P {
  part def Engine {
    action generateTorque;
  }
  part engine1 : Engine;
  requirement TorqueRequirement {
    subject generateTorque default engine1.generateTorque;
  }
}""",
}


def test_redefine_default_survives_roundtrip():
    model = parse(CASES["redefine_default"])[0]
    dump = str(model)
    assert "cargoMass" in dump
    assert "cargoMassdefault" not in dump, dump
    assert "default 0[kg]" in dump
    again = parse(dump)[0]
    assert again is not None
    assert str(again) == dump


def test_expression_default_survives_roundtrip():
    model = parse(CASES["expr_default"])[0]
    dump = str(model)
    assert "massActualdefault" not in dump, dump
    assert "default vehicle.dryMass + fuelMassActual" in dump
    again = parse(dump)[0]
    assert again is not None
    assert str(again) == dump


def test_subject_default_survives_roundtrip():
    model = parse(CASES["subject_default"])[0]
    dump = str(model)
    assert "generateTorquedefault" not in dump, dump
    assert "default engine1.generateTorque" in dump
    again = parse(dump)[0]
    assert again is not None
    assert str(again) == dump


def test_connect_end_multiplicity_roundtrips():
    # Issue 4 (normative leading-multiplicity form, per
    # `connect [0..1] a to [1] b;`): the dump must emit the form the
    # grammar accepts.
    src = "package P {\n  connect [1] a to [1] b;\n}"
    model = parse(src)[0]
    dump = str(model)
    again = parse(dump)[0]
    assert again is not None
    assert str(again) == dump


def test_connect_multiplicity_dump_is_normative():
    # Issue 4's real contract: the Vehicle Example's ends use the
    # normative LEADING multiplicity form (`connect [1] rearWheel1.…
    # to [1] rearAxle.…`, Annex A lines 640/642); the dump must emit
    # the multiplicity BEFORE the chain — the trailing form is
    # deliberately not in the grammar (upstream withdrew it), and a
    # leading parse must survive parse -> dump -> parse.
    src = ("package P {\n"
           "  interface I connect [1] a.p to [1] b.q;\n}")
    model = parse(src)[0]
    dump = str(model)
    assert "a.p" in dump
    # normative order: multiplicity BEFORE the chain reference
    assert "[1] a.p" in dump and "a.p [1]" not in dump, dump
    again = parse(dump)[0]
    assert again is not None
    assert str(again) == dump


def test_withdrawn_trailing_form_is_rejected_deterministically():
    # The form the issue draft quoted (`a [1] to b [1]`) is NOT in the
    # grammar — it is the upstream-withdrawn shape (see AGENTS.md's
    # normative-equivalents note). Pin the rejection so the parser's
    # contract is explicit: a structured syntax error, not a crash.
    import sysmlpy
    model, warns = parse(
        "package P {\n  interface I connect a [1] to b [1];\n}")
    assert model is None
    assert warns and warns[0].startswith("Syntax error at")


def test_annex_a_dump_region_reparses(tmp_path):
    """The dump lines of the Annex A file's Vehicle Configuration B
    (attribute redefines cargoMass default) must reparse."""
    import pathlib
    candidate = pathlib.Path(
        "/home/jfox/proj/SysML-v2-Release/sysml/src/examples/"
        "Vehicle Example/SysML v2 Spec Annex A SimpleVehicleModel.sysml")
    if not candidate.exists():
        import pytest
        pytest.skip("SysML-v2-Release checkout not present")
    model, warns = parse(candidate.read_text(encoding="utf-8"))
    assert model is not None, warns
    dump = str(model)
    assert "cargoMassdefault" not in dump
    assert "massActualdefault" not in dump
    assert "generateTorquedefault" not in dump
    assert "generateTorquedefault" not in dump
    assert dump.count("default 0[kg]") >= 1

def _roundtrip(src, doc_safe=True):
    model = parse(src)[0]
    assert model is not None
    dump = str(model)
    lines = [l for l in dump.splitlines()
             if " ;" in l and not (doc_safe and l.strip().startswith("doc"))]
    assert not lines, f"' ;' terminator drift: {lines[0].strip()}"
    again = parse(dump)[0]
    assert again is not None
    assert str(again) == dump, "dump is not whitespace-stable"


def test_statement_terminator_has_no_space_across_shapes():
    """The empty-body ';' terminator glues to every statement kind; a
    space before ';' was a dump-wide formatting drift introduced while
    fixing the Annex A default concatenation."""
    _roundtrip("package P { part def V { attribute cargoMass : Mass;"
               " action a1; port p; item it; constraint c; rendering rnd;"
               " state s; } }")
    _roundtrip("package P { part def V { calc def cd { return : Real; } } }")
    _roundtrip("package P { requirement r; view v; viewpoint vp; concern cn;"
               " metadata m; allocation a; case c1; }")
    _roundtrip("package P { connect [1] a.p to [1] b.q; }")
    _roundtrip("package P { interface I : X;"
               " interface J connect [1] a.p to [1] b.q;"
               " interface K connect [1] lug ::> a.w to [5] b.p; }")
    _roundtrip("package P { part def Wheel; allocation def A"
               " { end :>> source : Wheel; end :>> target : Wheel;"
               " allocate source.p to target.q; } }")
    _roundtrip("package P { part def V { end :>> sub : Wheel; } }")
