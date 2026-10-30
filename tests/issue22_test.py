"""Issue #22 (failys): DUPLICATE_NAME false positive across namespaces.

The reporter's model holds ``attribute description : String;`` in
``part def Template``, ``part def Component``, ``connection def
Connector`` and ``part def Composite`` — four *different* namespaces —
plus ``:>> description = …;`` members inside the two usages ``aComposite``
and ``aConnection``. ``sysmlpy analyze`` reported

    error: DUPLICATE_NAME: Duplicate name 'description' in namespace

Cause: ``SymbolTable`` created a child scope only for definitions and
packages, so the members declared in a *usage's* body (``aComposite``,
``aConnection``) were registered in the enclosing package's scope and two
same-named members looked like siblings of ARCH. In KerML ``Type``
specializes ``Namespace``: every typing element, usage included, is the
namespace of the members it owns. ``owns_namespace`` now decides this
once, for all six walkers (symbol table, reference collector, identifier
and duplicate checks).

Cross-checked against OpenSysML (Open-MBEE's Go toolchain, built from
~/proj/third_party/OpenSysML): ``sysml -validate`` on the reporter's file
reports no duplicate-name diagnostic — it does flag two genuine issues
sysmlpy does not check yet (connections with no ``connect`` ends, and
``ref template`` redeclaring an inherited member without ``:>>``).

The check itself still fires where the semantics demand it: two members of
one namespace, at package or definition level, are still errors.
"""

from sysmlpy import loads, analyze

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
  private import Connections::*;

  part sharedTemplate : RefinedTemplate;

  part def FromArchObjt :> Component {
    :>> description = "FromArchObjt";
    part aTemplate subsets templates : RefinedTemplate;
  }

  part def ToArchObjt :> Component {
    :>> description = "ToArchObjt";
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


def _duplicates(src: str) -> list:
    return [i for i in analyze(loads(src)) if i.code == "DUPLICATE_NAME"]


def test_issue22_reporter_model_has_no_duplicate_name():
    found = _duplicates(REPRO)
    assert not found, [i.message for i in found]


def test_issue22_same_member_name_in_two_usages_is_not_a_duplicate():
    src = (
        "package P { part def T; "
        "part a : T { attribute n : String; } "
        "part b : T { attribute n : String; } }"
    )
    assert not _duplicates(src)


def test_issue22_usage_body_is_its_own_namespace():
    # A usage owns its members: the same name may be declared in two usages,
    # and a real clash inside ONE usage body is still reported, naming it.
    src = (
        "package P { part def T; part a : T {"
        " attribute n : String; attribute n : String; } }"
    )
    found = _duplicates(src)
    assert len(found) == 1, [i.message for i in found]
    assert "a" in found[0].message, found[0].message


def test_issue22_duplicate_in_one_definition_still_reported():
    src = "package P { part def T { attribute x : String; attribute x : String; } }"
    found = _duplicates(src)
    assert len(found) == 1, [i.message for i in found]
    assert "'x'" in found[0].message


def test_issue22_duplicate_in_package_still_reported():
    src = "package P { part def A; part def A; }"
    found = _duplicates(src)
    assert len(found) == 1, [i.message for i in found]
    assert "'A'" in found[0].message
