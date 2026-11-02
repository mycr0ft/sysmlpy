"""Issue #34: resolver truth comes from loaded library models.

The analyzer's library fallback used to answer "does the name exist?"  by
membership in a *scraped index* — with no semantics.  Three noise classes
rode on that (re-export facades like ``ISQ`` → ``ISQBase``; star-imported
members like `import SI::*` + bare `kg` unit SHORT names; scraped doc
words).  The fallback now resolves through actually-LOADED library models
(``LibrarySymbolIndex.exists_in_loaded_model``) before the index.

Bounds (documented in docs/v0.102-library-model-resolution.md):
only .sysml sources model-load this phase (the .kerml half waits for the
KerML DFA cache, #35 — their names still resolve through the scraped
fallback); the candidate file set comes from a leaf→file fingerprint
built during the same cached index pass the resolver always paid.
"""

from sysmlpy import analyze, loads
from sysmlpy.semantic import LibrarySymbolIndex, SemanticAnalyzer

import pytest

# one cold index + load pass for the whole module (the caches are the
# point of issue #34 — clearing per test would repurchase the 80 s index
# pass every test)
@pytest.fixture(scope="module", autouse=True)
def _fresh_index():
    yield


def _analyze_text(src):
    model = loads(src)
    assert model is not None
    findings = analyze(model)
    return model, [f.code for f in findings]


def test_issue34_facade_member_resolves_through_loaded_model():
    # ISQ is a facade: `LengthValue` re-exports from ISQBase
    assert LibrarySymbolIndex.exists_in_loaded_model("LengthValue") is True


def test_issue34_unit_short_names_resolve():
    # `kg` and `Gy` are SHORT names of SI members (<kg> kilogram / <Gy> gray)
    assert LibrarySymbolIndex.exists_in_loaded_model("kg") is True
    assert LibrarySymbolIndex.exists_in_loaded_model("Gy") is True
    assert LibrarySymbolIndex.exists_in_loaded_model("kilogram") is True


def test_issue34_bogus_names_stay_false():
    assert LibrarySymbolIndex.exists_in_loaded_model(
        "DefinitelyNotALibrarySymbol") is False
    # and the cache makes the repeat exact and instant
    assert LibrarySymbolIndex.exists_in_loaded_model(
        "DefinitelyNotALibrarySymbol") is False


def test_issue34_facade_typing_no_noise():
    # the facade resolves through the loaded model (the ISQ facade
    # re-exports ISQBase members; only truth decides)
    model, _codes = _analyze_text(
        "package P { private import ISQ::*; attribute a : LengthValue; }")
    # typing noise for the facade-resolved member must not appear;
    # the import-chain visibility warning needs the persisted-table
    # follow-up (plan step 6) and stays out of this pin's guarantees
    undefined = [c for c in _codes if c == "UNDEFINED_SYMBOL"]
    assert not undefined, _codes


def test_issue34_kerml_names_resolve_from_the_loaded_source():
    # VectorOf lives in a .kerml source (VectorFunctions).  Step 7 (0.102.6)
    # builds a symbol table from the KerML visitor dict, so the loaded-model
    # answer is TRUE now — the scraped index still carries the name as the
    # callers' fallback.
    assert LibrarySymbolIndex.exists_in_loaded_model("VectorOf") is True
    assert "VectorFunctions::VectorOf" in LibrarySymbolIndex.get_symbols(None)


def test_issue34_loaded_models_cached_per_process():
    LibrarySymbolIndex.exists_in_loaded_model("LengthValue")
    before = dict(LibrarySymbolIndex._loaded_models)
    assert before, "candidate model loaded and cached"
    LibrarySymbolIndex.exists_in_loaded_model("LengthValue")
    assert LibrarySymbolIndex._loaded_models == before, \
        "no reload on the warm path"


def test_issue34_fingerprint_is_lexical_no_index_pass():
    """The fingerprint must not require the scraped index's .kerml parse.

    That parse costs ~55 s cold and sits on the LSP diagnostics path; the
    lexical walk (~0.3 s) is what keeps a cold analysis inside the LSP
    subprocess' 120 s budget.  Pinned here because the cheap path is
    invisible to the other tests (they warm the index first).
    """
    LibrarySymbolIndex.clear_cache()
    assert LibrarySymbolIndex._cache is None, "cold start"
    fp = LibrarySymbolIndex._fingerprint_for(None)
    # SI's unit members: the declared name and its SHORT name in `<>`
    assert "kilogram" in fp and "kg" in fp
    assert "LengthValue" in fp          # ISQBase declares it
    assert LibrarySymbolIndex._cache is None, \
        "fingerprint built without the .kerml index pass"