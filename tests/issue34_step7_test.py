"""Issue #34 step 7: the `.kerml` half of the library answers on truth.

Before this, a `.kerml` source could only be *scraped*: `exists_in_loaded_model`
returned False for its names by design, and `library_namespace_table` filtered
its candidates to `.sysml`, so `import VectorFunctions::*` resolved through the
regex index (doc-comment noise included).

KerML has no public ``Model`` loader, but its ``parse_to_dict`` output is
already name-shaped — ``name`` carries the declaration KIND, ``declaredName`` /
``declaredShortName`` the identifiers, ``children`` the nested members — so a
symbol table is built directly from that dict (DFA-cached parsing, #35).
"""

from sysmlpy import analyze, loads
from sysmlpy.semantic import LibrarySymbolIndex

import pytest


def test_step7_kerml_namespace_table_has_members():
    table = LibrarySymbolIndex.library_namespace_table("VectorFunctions")
    assert table is not None, "a .kerml source must answer now"
    assert "VectorOf" in table._symbols
    assert "CartesianVectorOf" in table._symbols
    # operator-named functions keep their quoted spelling stripped
    assert "+" in table._symbols


def test_step7_kernel_namespaces_resolve():
    for qn, member in (("ScalarValues", "Integer"),
                       ("Collections", "Collection")):
        table = LibrarySymbolIndex.library_namespace_table(qn)
        assert table is not None, qn
        assert member in table._symbols, (qn, sorted(table._symbols)[:8])


def test_step7_kerml_members_are_symbol_stand_ins():
    table = LibrarySymbolIndex.library_namespace_table("VectorFunctions")
    symbol = table._symbols["VectorOf"]
    assert getattr(symbol, "name", None) == "VectorOf"
    assert getattr(symbol, "kind", None), "the declaring kind is kept"


def test_step7_exists_in_loaded_model_answers_for_kerml():
    assert LibrarySymbolIndex.exists_in_loaded_model("VectorOf") is True
    assert LibrarySymbolIndex.exists_in_loaded_model("VectorValue") is True
    assert LibrarySymbolIndex.exists_in_loaded_model(
        "DefinitelyNotALibrarySymbol") is False


def test_step7_nested_kerml_member_is_found():
    # a function's parameters live under the function's namespace, not the
    # package's symbol dict — the existence check walks nested tables
    table = LibrarySymbolIndex.library_namespace_table("VectorFunctions")
    functions = [name for name in table._symbols if name in ("isZeroVector",)]
    assert functions, sorted(table._symbols)
    assert "v" in table._children["isZeroVector"]._symbols


def test_step7_doc_comment_words_are_not_symbols():
    # the regex scraper over-reported doc-comment words; the dict carries
    # only declared names
    table = LibrarySymbolIndex.library_namespace_table("VectorFunctions")
    for word in ("defines", "abstract", "functions", "corresponding"):
        assert word not in table._symbols, word


def test_step7_kerml_import_resolves_members_in_analysis():
    model = loads("""
package P {
  private import VectorFunctions::*;
  attribute v : VectorOf;
}
""")
    codes = [f.code for f in analyze(model)]
    assert "IMPLICIT_LIBRARY_IMPORT" not in codes, codes
    assert "UNRESOLVED_EXPRESSION_IDENTIFIER" not in codes, codes
