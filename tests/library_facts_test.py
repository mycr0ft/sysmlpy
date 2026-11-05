# -*- coding: utf-8 -*-
"""Issue #34 — the library-wide facts index.

What is pinned here is the *shape* of the answer the analyzer now gets:

* a facade package re-exports what it imports publicly (``ISQ::mass`` lives in
  ``ISQSpaceTime``, reaches ``ISQ`` through ``public import ISQSpaceTime::*``);
* an ``alias`` is a member (``ISQ::time`` is ``alias time for duration``);
* a declared short name is addressable (``SI::kg``, ``ft``, ``Btu_IT``);
* a *private* import is not re-exported (``ISQ::Real`` is private);
* the KerML half answers too, with operator names unquoted (``VectorFunctions``
  declares ``'+'``);
* the persisted cache is keyed on content + build, and a changed library is a
  miss — never a stale hit.
"""

import json
import time
from pathlib import Path

import pytest

from sysmlpy import library_facts
from sysmlpy.semantic import LibrarySymbolIndex

LIB = Path(__file__).parent.parent / "src" / "sysmlpy" / "library"


@pytest.fixture(scope="module")
def facts():
    return library_facts.get()


# ---------------------------------------------------------------------------
# re-export fixpoint
# ---------------------------------------------------------------------------


def test_facade_reexports_members_declared_elsewhere(facts):
    """ISQ declares three members and re-exports the rest of ISO 80000."""
    isq = facts.namespace("ISQ")
    assert isq is not None
    assert set(isq["members"]) >= {"TemperatureDifferenceValue",
                                   "TemperatureDifferenceUnit",
                                   "temperatureDifference"}
    # declared in ISQSpaceTime, visible through ISQ
    assert "mass" in isq["reexports"] or "mass" in isq["members"]
    assert facts.exists("ISQ::mass") is True
    assert facts.exists("ISQ::speed") is True
    assert facts.exists("ISQ::length") is True


def test_alias_is_a_member(facts):
    """`alias time for duration;` in ISQSpaceTime makes ISQ::time resolve."""
    assert facts.exists("ISQ::time") is True
    owner = facts.namespace("ISQSpaceTime")
    assert owner["members"].get("time") == "Alias"
    assert owner["aliases"]["time"] == "duration"


def test_private_imports_are_not_reexported(facts):
    """ISQ imports ScalarValues::Real privately — it must not leak out."""
    assert facts.exists("ScalarValues::Real") is True
    assert facts.exists("ISQ::Real") is False
    assert facts.exists("SI::Real") is False


def test_chained_public_import_still_reexports(facts):
    """SI re-exports ISQ::* which re-exports ISQSpaceTime's members."""
    assert facts.exists("SI::time") is True


# ---------------------------------------------------------------------------
# short names and the KerML half
# ---------------------------------------------------------------------------


def test_short_names_are_addressable(facts):
    # `attribute <kg> kilogram` in SI
    assert facts.exists("SI::kg") is True
    assert facts.exists("kg") is True
    # quoted declared name, short name is the token: <Btu_IT> 'British thermal unit (IT)'
    assert facts.exists("Btu_IT") is True
    assert facts.exists("ft") is True


def test_kerml_namespaces_answer_with_operator_names(facts):
    vf = facts.namespace("VectorFunctions")
    assert vf is not None
    assert "VectorOf" in vf["members"]
    assert "CartesianVectorOf" in vf["members"]
    # quoting is stripped: the source says `function '+'`
    assert "+" in vf["members"]
    assert facts.exists("VectorFunctions::VectorOf") is True


def test_scalar_values_comes_from_the_kerml_half(facts):
    assert facts.exists("ScalarValues::Real") is True
    assert facts.exists("ScalarValues::Integer") is True


def test_unknown_names_stay_unknown(facts):
    assert facts.exists("ISQ::bogusName") is False
    assert facts.exists("Nope::nope") is False
    assert facts.exists("") is False


# ---------------------------------------------------------------------------
# the resolver integration
# ---------------------------------------------------------------------------


def test_namespace_table_is_a_model_with_facts_fallback(facts):
    """Tables stay model-backed (real elements, nested scopes); name-level truth
    for facade re-exports comes from the facts index instead.

    This split is deliberate: the model path is what a caller descending into a
    namespace needs, while `exists_in_loaded_model` answers the facade question
    (`ISQ::time`) from facts without deriving a table at all.
    """
    table = LibrarySymbolIndex.library_namespace_table("ISQ")
    assert table is not None
    # direct members of the facade package are real elements
    assert "TemperatureDifferenceValue" in table._symbols
    element = table._symbols["TemperatureDifferenceValue"]
    assert getattr(element, "name", None) == "TemperatureDifferenceValue"
    # the re-exported member is name-level truth, not a table entry
    assert LibrarySymbolIndex.exists_in_loaded_model("ISQ::time") is True


def test_short_name_and_member_are_the_same_symbol(facts):
    table = LibrarySymbolIndex.library_namespace_table("SI")
    assert table is not None
    assert "kilogram" in table._symbols
    assert "kg" in table._symbols
    assert table._symbols["kg"] is table._symbols["kilogram"]


def test_get_symbols_is_a_superset_of_the_old_index(facts):
    symbols = LibrarySymbolIndex.get_symbols(None)
    for name in ("ScalarValues::Real", "ISQ::LengthValue", "ISQ::mass",
                 "SI::kg", "VectorFunctions::VectorOf"):
        assert name in symbols, name


def test_symbols_from_facts_are_cheap_when_cached(facts):
    """`get_symbols` used to cost 29.6 s warm (a line scrape per file)."""
    LibrarySymbolIndex.clear_cache()
    start = time.perf_counter()
    LibrarySymbolIndex.get_symbols(None)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"facts path should be cache-speed, took {elapsed:.1f}s"


def test_shipped_snapshot_matches_this_build_and_library():
    """The packaged snapshot is what keeps a first run cheap.

    Building the facts from source costs ~276 s on a machine with no DFA cache
    (each parse pays DFA construction), against 0.2 s to read the snapshot — so
    a stale snapshot silently costs every new user four minutes.  Regenerate with
    `python scripts/gen_library_facts.py` after a version bump or a library edit.
    """
    path = library_facts.snapshot_path()
    assert path.exists(), "run scripts/gen_library_facts.py"
    payload = json.loads(path.read_text())
    assert payload["build"] == library_facts.build_id(), \
        "version bumped without regenerating the snapshot"
    expected = library_facts.set_digest(library_facts._library_files(None))
    assert payload["digest"] == expected, \
        "library changed without regenerating the snapshot"
    assert payload["version"] == library_facts.FACTS_VERSION
    assert "ISQ" in payload["facts"]


def test_snapshot_is_used_for_the_bundled_library(tmp_path, monkeypatch):
    """A cold process reads the snapshot instead of building."""
    monkeypatch.setenv(library_facts.CACHE_ENV, str(tmp_path))
    start = time.perf_counter()
    facts = library_facts.load(None)
    elapsed = time.perf_counter() - start
    assert "ISQ" in facts
    assert elapsed < 5.0, f"snapshot path should be fast, took {elapsed:.1f}s"
    assert not list(tmp_path.glob("facts-*.json")), \
        "a snapshot hit must not write a cache record"


def test_snapshot_does_not_apply_to_a_custom_library(tmp_path, monkeypatch):
    """Custom roots have their own digest — the snapshot is never used for them."""
    monkeypatch.setenv(library_facts.CACHE_ENV, str(tmp_path))
    custom = tmp_path / "custom"
    custom.mkdir()
    (custom / "CustomTypes.kerml").write_text(
        "package CustomTypes { part def CustomPart; }")
    facts = library_facts.load([custom], force=True)
    assert "CustomTypes" in facts
    assert "ISQ" not in facts


# ---------------------------------------------------------------------------
# cache identity
# ---------------------------------------------------------------------------


def test_cache_key_separates_builds_and_content(tmp_path, monkeypatch):
    monkeypatch.setenv(library_facts.CACHE_ENV, str(tmp_path))
    digest = library_facts.set_digest(sorted(LIB.rglob("*.sysml"))[:3])
    path = library_facts._cache_path(digest)
    assert path is not None
    assert library_facts.build_id() in path.name
    assert digest[:16] in path.name
    # a different set digest cannot collide with the same record
    other = library_facts.set_digest(sorted(LIB.rglob("*.sysml"))[-3:])
    assert library_facts._cache_path(other) != path


def test_cache_can_be_switched_off(monkeypatch):
    monkeypatch.setenv(library_facts.CACHE_ENV, "off")
    assert library_facts.cache_dir() is None
    assert library_facts._cache_path("deadbeef" * 4) is None


def test_cached_record_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv(library_facts.CACHE_ENV, str(tmp_path))
    small = tmp_path / "lib"
    small.mkdir()
    (small / "Tiny.sysml").write_text(
        "package Tiny { private import ScalarValues::Real; "
        "attribute a : Real; part def B; }")

    first = library_facts.load([small], force=True)
    assert "Tiny" in first
    assert set(first["Tiny"]["members"]) == {"a", "B"}
    written = list(tmp_path.glob("facts-*.json"))
    assert written, "a record was persisted"

    payload = json.loads(written[0].read_text())
    assert payload["build"] == library_facts.build_id()
    assert payload["version"] == library_facts.FACTS_VERSION

    # second load is the cache, not a rebuild
    second = library_facts.load([small])
    assert second.keys() == first.keys()


def test_corrupt_record_is_a_miss_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setenv(library_facts.CACHE_ENV, str(tmp_path))
    small = tmp_path / "lib2"
    small.mkdir()
    (small / "Tiny2.sysml").write_text("package Tiny2 { part def C; }")
    library_facts.load([small], force=True)
    for path in tmp_path.glob("facts-*.json"):
        path.write_text("{not json")
    rebuilt = library_facts.load([small])
    assert "Tiny2" in rebuilt
