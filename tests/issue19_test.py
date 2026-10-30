"""Issue #19 (failys/Sha-mal Faily): `:>> attr = value;` members dropped.

A declaration-attached feature value (`:>> description = "ArchObjt";`)
inside a `part def` body parses but vanished from `model.dump()`
whenever it shared its body with a sibling (e.g. the following
`part aTemplate subsets templates : RefinedTemplate;`). The parse
dict always kept the DefaultReferenceUsage; the shared body flatten
had no `DefaultReferenceUsage` dispatch, so the member was not
rebuilt. Also regression-covers the plain `ref value` members that
ride the same class.
"""

from sysmlpy import parse, loads

FULL = """package LIB {
  private import ScalarValues::*;

  part def Template {
    attribute short_code : String;
    attribute description : String;
  }

  part def RefinedTemplate :> Template {
    :>> short_code = "RT";
    :>> description = "Refined Template";
  }

  part def Component {
    attribute description : String;
    part templates : Template [1..*];
  }
}

package ARCH {
  private import ScalarValues::*;
  private import LIB::*;

  part def ArchObjt :> Component {
    :>> description = "ArchObjt";
    part aTemplate subsets templates : RefinedTemplate;
  }
}"""


def test_issue19_value_member_survives_dump():
    model = parse(FULL)[0]
    assert model is not None
    dump = str(model)
    assert 'description = "ArchObjt"' in dump
    # and the reparsed model keeps it too
    again = parse(dump)[0]
    assert again is not None
    assert 'description = "ArchObjt"' in str(again)


def test_issue19_value_member_is_a_semantic_child():
    model = parse(FULL)[0]
    found = []

    def _walk(o):
        if getattr(o, "name", None) == "ArchObjt":
            found.append(o)
        for c in getattr(o, "children", ()) or ():
            _walk(c)

    _walk(model)
    assert found, "ArchObjt missing from the semantic tree"
    arch = found[0]
    kids = [(type(c).__name__, getattr(c, "name", ""))
            for c in arch.children]
    names = [n for _, n in kids]
    assert "description" in names, kids
    assert "aTemplate" in names, kids
    # the value member navigates as a reference whose type is the
    # redefined feature (helper contract from the Vehicle-Example work)
    ref = [c for c in arch.children
           if getattr(c, "name", "") == "description"][0]
    assert ref._typed_by_name == "description"


def test_issue19_sibling_alone_forms_roundtrip():
    # alone, and in both orders with a nested part
    for src in ("package P { part def C { attribute description : String; }"
                " part def R :> C { :>> description = \"x\"; } }",
                "package P { part def C { attribute description : String; }"
                " part def R :> C { :>> description = \"x\"; part t : C; } }",
                "package P { part def C { attribute description : String; }"
                " part def R :> C { part t : C; :>> description = \"x\"; } }"):
        model = parse(src)[0]
        assert model is not None
        dump = str(model)
        assert 'description = "x"' in dump, dump
        again = parse(dump)[0]
        assert again is not None
        assert str(again) == dump