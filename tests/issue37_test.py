"""Issue #37: qualified references to enum members reached through an import.

``InterfaceType::required`` — the head ``InterfaceType`` is visible only
through ``private import LIB::*``, i.e. it lives in the importing scope's
``_imported_symbols`` while its MEMBER table belongs to the defining
package (``LIB::InterfaceType``).  A qualified-name descent that asked
"where is this name visible" therefore never reached the member table and
reported the enum value as unresolved (from both the value-owning port and
the redefining reference, hence two findings per use).
"""

import pytest

from sysmlpy import analyze, loads
from sysmlpy.semantic import SymbolTable

ENUM_MODEL = """
package LIB {
  enum def InterfaceType {
    provided;
    required;
  }
  port def ComponentInterface {
    attribute type : InterfaceType;
  }
  part def Component {
    port interfaces : ComponentInterface [1..*];
  }
}
package ARCH {
  private import LIB::*;
  part def FromArchObjt :> Component {
    port anInterface subsets interfaces : ComponentInterface {
      ::> type = InterfaceType::required;
    }
  }
  part def ToArchObjt :> Component {
    port anInterface subsets interfaces : ComponentInterface {
      ::> type = InterfaceType::provided;
    }
  }
}
"""


def _codes(src):
    model = loads(src)
    assert model is not None, "model must parse"
    return [f.code for f in analyze(model)]


def test_issue37_enum_value_through_star_import_resolves():
    codes = _codes(ENUM_MODEL)
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" not in codes, codes
    assert codes == [], codes


def test_issue37_enum_value_through_named_import_resolves():
    codes = _codes("""
package LIB { enum def E { a; b; } }
package ARCH {
  private import LIB::E;
  part def Holder { attribute e : E = E::b; }
}
""")
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" not in codes, codes


def test_issue37_enum_value_in_own_package_resolves():
    codes = _codes("""
package P {
  enum def E { a; b; }
  attribute x : E = E::a;
}
""")
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" not in codes, codes


def test_issue37_missing_enum_member_is_still_reported():
    # the fix follows the namespace; it must not swallow a bogus member
    codes = _codes("""
package LIB { enum def E { a; } }
package ARCH {
  private import LIB::*;
  attribute e : E = E::nope;
}
""")
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" in codes, codes


def test_issue37_symbol_table_descends_into_imported_namespace():
    model = loads(ENUM_MODEL)
    symtab = SymbolTable()
    symtab.build_from_model(model, [])
    arch = symtab._children["ARCH"]
    port = arch._children["FromArchObjt"]._children["anInterface"]
    enum_el = port.lookup("InterfaceType")
    assert enum_el is not None
    scope = port._scope_for_member("InterfaceType", enum_el)
    assert scope is not None, "member table found through the import"
    assert "required" in scope._symbols and "provided" in scope._symbols
    # and the qualified-name resolver returns the member, not just 'found'
    resolved = symtab._resolve_qualified_name("InterfaceType::required", port)
    assert type(resolved).__name__ == "EnumeratedValue", resolved
    assert getattr(resolved, "name", None) == "required"
