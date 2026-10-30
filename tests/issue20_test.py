"""Issue #20 (failys): `analyze` reports UNDEFINED_SYMBOL inside a body.

Reporter's model: package ARCH does ``private import LIB::*;`` and types a
part inside ``part def ArchObjt`` with ``RefinedTemplate`` — resolvable at
package level (``part sharedTemplate : RefinedTemplate;`` was fine) but
reported as ``UNDEFINED_SYMBOL`` inside the definition body.

Cause: ``SymbolTable.lookup`` suppressed *privately* imported members
whenever the lookup came from a child scope — but walking up the parent
chain means the lookup originates INSIDE the importing namespace.  KerML
1.0 (7.2.5.4) restricts a private import's visibility OUTSIDE the
namespace ("none of the imported memberships become globally visible
outside of the root namespace"), not inside its own body.  Cross-namespace
visibility is governed by import re-export, which only propagates
public/protected imports, so a sibling namespace still cannot see another
namespace's private imports.

Also pinned here: a name that resolves as a member of an enclosing usage's
*type* is a model symbol, not a standard-library fallback (the bundled
library index carries member names such as VectorFunctions::VectorOf::
components, so bare-name matching produced a bogus IMPLICIT_LIBRARY_IMPORT
warning for the model's own feature).
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
}

package ARCH {
  private import ScalarValues::*;
  private import LIB::*;

  part def ArchObjt :> Component {
    :>> description = "ArchObjt";
    part aTemplate subsets templates : RefinedTemplate;
  }
}
"""


def _analyze(src=REPRO):
    model = loads(src)
    return analyze(model)


def test_issue20_private_import_visible_inside_nested_definition():
    issues = _analyze()
    undefined = [i for i in issues if i.code == "UNDEFINED_SYMBOL"]
    assert not undefined, [i.message for i in undefined]


def test_issue20_explicit_import_suppresses_implicit_library_warning():
    # ScalarValues::* is imported explicitly (privately) in both packages, so
    # the IMPLICIT_LIBRARY_IMPORT warning for String is wrong.
    issues = _analyze()
    implicit = [i for i in issues if i.code == "IMPLICIT_LIBRARY_IMPORT"]
    assert not implicit, [i.message for i in implicit]


def test_issue20_private_import_still_invisible_to_sibling():
    # Guard: relaxing visibility inside the namespace must not leak it out.
    model = loads("""
        package P {
            part def BaseType;
        }
        package Q {
            private import P::BaseType;
            part x : BaseType;
        }
        package R {
            part y : BaseType;
        }
    """)
    issues = analyze(model)
    assert any(
        i.code == "UNDEFINED_SYMBOL" and "BaseType" in i.message for i in issues
    ), [i.message for i in issues]


def test_issue20_private_import_visible_to_child_package():
    # A nested package is "within" the importing namespace (KerML 7.2.5.4).
    model = loads("""
        package P {
            part def BaseType;
        }
        package Q {
            private import P::BaseType;
            package Inner {
                part x : BaseType;
            }
        }
    """)
    issues = analyze(model)
    assert not [i for i in issues if i.code == "UNDEFINED_SYMBOL"], [
        i.message for i in issues
    ]


def test_issue20_context_member_beats_library_simple_name():
    # "components" is a feature of Composite (the type of aComposite), not a
    # standard library type — the regex-scraped library index lists it from
    # a doc comment.
    model = loads("""
        package P {
            part def Component;
            part def Composite {
                part components : Component [1..*];
            }
            part aComposite : Composite {
                part oneObject subsets components : Component;
            }
        }
    """)
    issues = analyze(model)
    relevant = [
        i for i in issues
        if "components" in (i.message or "") + (i.reference or "")
    ]
    assert not relevant, [i.message for i in relevant]
