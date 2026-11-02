"""Issue #34 step 5: imports resolve against the loaded library model.

Phase 1+2 (v0.102.0) made the *existence* question answer on a loaded model
(`exists_in_loaded_model`).  Step 5 does the same for import **visibility**:
a `private import SI::*` now imports the members the loaded `SI` model really
declares — including declared SHORT names (`<kg> kilogram`), which no name
list carried — instead of a scraped qualified-name prefix scan.

Gate effect (bundled library + fixtures, 99 files): errors 3369 → 1183 and
warnings 2961 → 1706, with every other code unchanged — see the CHANGELOG.
"""

from sysmlpy import analyze, loads
from sysmlpy.semantic import LibrarySymbolIndex, SymbolTable

import pytest


def _codes(src):
    model = loads(src)
    assert model is not None
    return [f.code for f in analyze(model)]


def test_step5_star_import_of_units_resolves_short_names():
    # `<kg>` is a SHORT name of SI's `kilogram` member: a scraped name index
    # never had it, so `[kg]` was reported as an implicit library reference.
    model = loads("""
package P {
  private import ScalarValues::*;
  private import SI::*;
  attribute mass : Real = 3.0 [kg];
}
""")
    findings = analyze(model)
    codes = [f.code for f in findings]
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" not in codes, findings
    # the unit short name is imported now; nothing may flag `kg`
    refs = [getattr(f, "reference", None) for f in findings]
    assert "kg" not in refs, findings
    assert codes == [], findings


def test_step5_facade_members_via_import_still_use_truth_fallback():
    # ISQ is a facade re-exporting ISQBase; a SHALLOW table intentionally does
    # not walk the facade's own imports (that walk cost 248 s cold — see the
    # issue).  The documented residual: the import-suggestion warning for a
    # facade-re-exported name survives, while the reference itself resolves
    # through exists_in_loaded_model — so no UNRESOLVED_* / UNDEFINED_SYMBOL.
    findings = analyze(loads("""
package P {
  private import ScalarValues::*;
  private import ISQ::*;
  private import SI::*;
  part def Wheel {
    attribute mass : LengthValue = 3.0 [kg];
  }
}"""))
    codes = [f.code for f in findings]
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" not in codes, findings
    assert "UNDEFINED_SYMBOL" not in codes, findings
    # only the facade class may remain, and it must name a re-exported member
    implicit = [f for f in findings if f.code == "IMPLICIT_LIBRARY_IMPORT"]
    assert all(getattr(f, "reference", None) in
               ("LengthValue", "ThermodynamicTemperature", "Real")
               for f in implicit), findings


def test_step5_table_carries_short_names():
    table = LibrarySymbolIndex.library_namespace_table("SI")
    assert table is not None
    assert "kilogram" in table._symbols
    assert "kg" in table._symbols, "declared SHORT name is a name"
    # both spellings resolve to the same element
    assert table._symbols["kg"] is table._symbols["kilogram"]


def test_step5_table_members_are_elements_not_strings():
    table = LibrarySymbolIndex.library_namespace_table("SI")
    assert table is not None
    element = table._symbols["kilogram"]
    assert getattr(element, "name", None) == "kilogram"


def test_step5_kerml_only_namespaces_keep_the_scraped_fallback():
    # VectorFunctions lives in a .kerml source (no semantic model load yet,
    # step 7) — the import must still resolve through the scraped index.
    assert LibrarySymbolIndex.library_namespace_table("VectorFunctions") is None
    codes = _codes("""
package P {
  private import VectorFunctions::*;
  attribute v : VectorOf;
}
""")
    assert "IMPLICIT_LIBRARY_IMPORT" not in codes, codes


def test_step5_user_model_short_names_are_registered():
    # the short-name registration is not library-specific: `attribute <x> …`
    # is a name for every table build, so `x` resolves in its own namespace.
    model = loads("""
package P {
  attribute <x> length : Real = 1.0;
  attribute doubled : Real = x * 2;
}
""")
    table = SymbolTable()
    table.build_from_model(model, None)
    pkg = table._children["P"]
    assert "x" in pkg._symbols and "length" in pkg._symbols
    codes = [f.code for f in analyze(model)]
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" not in codes, codes


def test_step5_unknown_namespace_still_warns():
    # guard against "resolve everything": a namespace no library source
    # defines must keep the advisory finding.
    codes = _codes("""
package P {
  private import NoSuchLibraryNamespace::*;
  attribute a : Real;
}
""")
    assert codes, "an import of a nonexistent namespace must still be flagged"
