"""Issue #21 (failys): connection-usage members dropped from the dumped model.

Reporter's model: a ``connection`` usage with a declaration body

    connection aConnection subsets connectors : Connection {
      :>> description = "aConnection";
      ref template = sharedTemplate;
    } connect oneObject to anotherObject;

dumped as bare ``connection aConnection : Connection;`` — the subsets
clause, the whole body and (for ``connection connectors : Connector
[1..*];``) the multiplicity all vanished.

Three independent drop sites, all in the visitor:

* ``_make_nested_connection_usage_dict`` (connection inside a definition
  body) used ``_build_specialization_from_fsp``, a duplicate helper that
  understood typings only and hardcoded ``multiplicity: None``.
* both connection builders hardcoded an empty ``DefinitionBody`` — a
  ``connectionUsage`` hangs its body off ``ctx.usageBody()`` directly,
  which ``_get_usage_body_items`` never reaches.
* ``_make_reference_usage_dict`` read ``usage.valuePart()`` although the
  value part rides on ``usage.usageCompletion()``, so ``ref template =
  sharedTemplate;`` lost its value.

Pinned here end-to-end (parse → dump → re-parse), plus the dump-glue
nits the reporter's quoted output showed (``:>templates``, ``:>  T``,
``= "x" ;``).
"""

from sysmlpy import parse


REPRO = """package LIB {
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

  connection def Connector {
    end from_component : Component;
    end to_component : Component;
    attribute description : String;
    ref template : Template;
  }

  part def Composite {
    attribute description : String;
    part components : Component [1..*];
    connection connectors : Connector [1..*];
  }
}

package ARCH {
  private import ScalarValues::*;
  private import LIB::*;

  part sharedTemplate : RefinedTemplate;

  part def FromArchObjt :> Component {
    :>> description = "FromArchObjt";
    part aTemplate subsets templates : RefinedTemplate;
  }

  part aComposite : Composite {
    :>> description = "aComposite";
    part oneObject subsets components : Component;
    part anotherObject subsets components : Component;

    connection aConnection subsets connectors : Connection {
      :>> description = "aConnection";
      ref template = sharedTemplate;
    } connect oneObject to anotherObject;

  }
}
"""


def _dump(src=REPRO):
    model = parse(src)[0]
    assert model is not None, parse(src)[1]
    return str(model)


def test_issue21_connection_usage_body_survives_dump():
    dump = _dump()
    assert "connection aConnection" in dump
    assert 'description = "aConnection"' in dump, dump
    assert "ref template = sharedTemplate;" in dump, dump


def test_issue21_connection_usage_subsets_and_multiplicity_survive_dump():
    dump = _dump()
    # subsets clause of the connection usage
    assert "aConnection :> connectors : Connection" in dump, dump
    # multiplicity of a connection usage with no body
    assert "connection connectors : Connector [1..*];" in dump, dump


def test_issue21_connection_body_is_in_semantic_tree():
    model = parse(REPRO)[0]
    assert model is not None
    found = {}

    def _walk(o):
        name = getattr(o, "name", None)
        if name in ("aConnection", "connectors"):
            found[name] = o
        for c in getattr(o, "children", ()) or ():
            _walk(c)

    _walk(model)
    assert set(found) == {"aConnection", "connectors"}, sorted(found)
    kids = [getattr(c, "name", None) for c in found["aConnection"].children]
    assert "description" in kids, kids
    assert "template" in kids, kids


def test_issue21_dump_is_round_trip_stable():
    dump = _dump()
    again = parse(dump)[0]
    assert again is not None, parse(dump)[1]
    assert str(again).strip() == dump.strip()


def test_issue21_ref_value_member_survives_round_trip():
    src = ("package P { part def T; part def C { ref t = sharedT; }"
           " part sharedT : T; }")
    dump = _dump(src)
    assert "ref t = sharedT;" in dump, dump
    again = parse(dump)[0]
    assert again is not None, parse(dump)[1]
    assert "ref t = sharedT;" in str(again)


def test_issue21_dump_glue_spacing():
    dump = _dump()
    # no glued subsetting keyword, no doubled space after subclassification,
    # no space before the member terminator
    assert ":>templates" not in dump
    assert ":>  Component" not in dump
    assert ':>> description = "aComposite" ;' not in dump
    assert "part aTemplate :> templates : RefinedTemplate;" in dump
    assert "part def FromArchObjt :> Component {" in dump
    assert ':>> description = "aComposite";' in dump
