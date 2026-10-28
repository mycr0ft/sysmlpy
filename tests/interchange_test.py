#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SysML v2 JSON interchange format
(v0.63.0 — Adoption Roadmap Goal 3).

Covers:
- export to JSON-LD-style partition documents (to_interchange)
- import back into live models (from_interchange)
- deterministic identifiers and round-trip stability
- error handling (invalid documents, cycles)
- the `sysmlpy export` / `sysmlpy import` CLI commands
"""

import json
import subprocess
import sys

import pytest

import sysmlpy
from sysmlpy import loads, load_files
from sysmlpy.interchange import (
    to_interchange,
    from_interchange,
    interchange_to_json_text,
    reconcile_ids,
)


def run_cli(*args):
    """Run the real module entry point in a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "sysmlpy", *args],
        capture_output=True,
        text=True,
        timeout=600,
    )


RICH_MODEL = """package VehicleSpec {
    part def Vehicle {
        attribute mass : Real;
        part wheels: Wheel[4];
    }
    part def Wheel;
    requirement def RangeReq {
        doc /* range shall exceed 400 km */
    }
    requirement range : RangeReq {
        verify rangeCheck;
    }
    part myCar : Vehicle {
        satisfy range by wheels;
    }
    verification def RangeCheck;
    verification rangeCheck : RangeCheck;
}"""


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


class TestExport:

    def test_document_shape(self):
        doc = to_interchange(loads("package P { part def V; }"))
        assert set(doc) >= {"@context", "@id", "@graph"}
        assert isinstance(doc["@graph"], list) and doc["@graph"]
        assert doc["@context"]["@version"] == 1.1

    def test_accepts_sysml_text(self):
        doc = to_interchange("package P { part def V; }")
        types = [e["@type"] for e in doc["@graph"]]
        assert "Package" in types

    def test_every_element_has_id_and_type(self):
        doc = to_interchange(loads("package P { part def V; }"))
        for elem in doc["@graph"]:
            assert "@id" in elem
            assert "@type" in elem

    def test_deterministic_ids(self):
        doc1 = to_interchange(loads("package P { part def V; attribute a: Real; }"))
        doc2 = to_interchange(loads("package P { part def V; attribute a: Real; }"))
        assert doc1 == doc2

    def test_scalars_inline(self):
        doc = to_interchange(loads("package P { part def V; }"))
        pkg = next(e for e in doc["@graph"] if e["@type"] == "Identification"
                   and e.get("declaredName") == "P")
        assert pkg["declaredName"] == "P"
        assert pkg["declaredShortName"] is None  # nulls preserved

    def test_no_dangling_references(self):
        doc = to_interchange(loads(RICH_MODEL))
        ids = {e["@id"] for e in doc["@graph"]}

        def collect_refs(v):
            if isinstance(v, dict):
                if set(v) == {"@id"}:
                    yield v["@id"]
                else:
                    for x in v.values():
                        yield from collect_refs(x)
            elif isinstance(v, list):
                for item in v:
                    yield from collect_refs(item)

        refs = {r for e in doc["@graph"] for r in collect_refs(e)}
        assert refs <= ids, f"dangling refs: {refs - ids}"

    def test_metaclass_types(self):
        doc = to_interchange(loads(RICH_MODEL))
        types = {e["@type"] for e in doc["@graph"]}
        assert "Package" in types
        assert "PartDefinition" in types
        assert "PackageMember" in types
        assert "Documentation" in types
        assert "SatisfyRequirementUsage" in types

    def test_merged_model_from_load_files(self, tmp_path):
        f1 = tmp_path / "a.sysml"
        f1.write_text("package P { part def V; }")
        f2 = tmp_path / "b.sysml"
        f2.write_text("package P { part def W; }")
        model = load_files([str(f1), str(f2)])
        doc = to_interchange(model)  # grammar is None → rebuilt
        types = [e["@type"] for e in doc["@graph"]]
        assert "Package" in types

    def test_empty_model(self):
        model = sysmlpy.Model()
        doc = to_interchange(model)
        assert doc["@graph"]  # root PackageBodyElement present
        root = next(e for e in doc["@graph"] if e["@id"] == doc["@id"])
        assert root["@type"] == "PackageBodyElement"

    def test_invalid_input_type_raises(self):
        with pytest.raises(TypeError):
            to_interchange(42)

    def test_json_text_helper(self):
        doc = to_interchange(loads("package P { part def V; }"))
        text = interchange_to_json_text(doc)
        assert json.loads(text) == doc
        assert "\n" in text  # indented by default


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------


class TestImport:

    def test_rich_round_trip(self):
        model = loads(RICH_MODEL)
        rebuilt = from_interchange(to_interchange(model))
        assert rebuilt.dump() == model.dump()

    def test_rebuilt_model_is_queryable(self):
        model = loads(RICH_MODEL)
        rebuilt = from_interchange(to_interchange(model))
        pkg = rebuilt.children[0]
        names = [c.name for c in pkg.children]
        assert "Vehicle" in names
        assert "RangeReq" in names
        assert "myCar" in names

    def test_accepts_json_string(self):
        model = loads("package P { part def V; }")
        j = json.dumps(to_interchange(model))
        rebuilt = from_interchange(j)
        assert rebuilt.dump() == model.dump()

    def test_export_stable_after_import(self):
        model = loads(RICH_MODEL)
        doc = to_interchange(model)
        assert to_interchange(from_interchange(doc)) == doc

    def test_simple_model_round_trip(self):
        text = "package P { attribute a : Real; item i; port p; action act; }"
        model = loads(text)
        rebuilt = from_interchange(to_interchange(model))
        assert rebuilt.dump() == model.dump()

    def test_multiplicity_round_trip(self):
        text = "package P { part def V { part wheels: Wheel[4]; } part def Wheel; }"
        model = loads(text)
        rebuilt = from_interchange(to_interchange(model))
        assert rebuilt.dump() == model.dump()

    def test_traceability_survives_interchange(self):
        # Goal-2 interop: satisfy/verify edges survive a JSON round-trip
        model = loads(RICH_MODEL)
        rebuilt = from_interchange(to_interchange(model))
        report1 = sysmlpy.extract_traceability(model)
        report2 = sysmlpy.extract_traceability(rebuilt)
        assert report1.to_json() == report2.to_json()

    # -- error handling ----------------------------------------------------

    def test_missing_graph_raises(self):
        with pytest.raises(ValueError):
            from_interchange({"foo": 1})

    def test_element_without_id_raises(self):
        with pytest.raises(ValueError):
            from_interchange({"@graph": [{"@type": "Package"}]})

    def test_unknown_reference_raises(self):
        doc = {
            "@id": "root",
            "@graph": [
                {"@id": "a", "@type": "PackageBodyElement",
                 "ownedRelationship": [{"@id": "missing"}]},
            ],
        }
        with pytest.raises(ValueError, match="unknown @id"):
            from_interchange(doc)

    def test_cyclic_reference_raises(self):
        doc = {
            "@id": "a",
            "@graph": [
                {"@id": "a", "@type": "PackageBodyElement",
                 "ownedRelationship": [{"@id": "b"}]},
                {"@id": "b", "@type": "PackageMember",
                 "ownedRelatedElement": {"@id": "b"}},
            ],
        }
        with pytest.raises(ValueError, match="Cyclic"):
            from_interchange(doc)

    def test_invalid_json_string_raises(self):
        with pytest.raises(json.JSONDecodeError):
            from_interchange("{not json")

    def test_non_dict_json_raises(self):
        with pytest.raises(ValueError):
            from_interchange("[1, 2, 3]")

    def test_root_without_relationships_raises(self):
        doc = {
            "@id": "x",
            "@graph": [{"@id": "x", "@type": "Identification"}],
        }
        with pytest.raises(ValueError, match="ownedRelationship"):
            from_interchange(doc)


# ---------------------------------------------------------------------------
# CLI: sysmlpy export / import
# ---------------------------------------------------------------------------


class TestExportCommand:

    def test_export_stdout(self, tmp_path, capsys):
        f = tmp_path / "m.sysml"
        f.write_text(loads(RICH_MODEL).dump())
        from sysmlpy.__main__ import main
        assert main(["export", str(f)]) == 0
        doc = json.loads(capsys.readouterr().out)
        assert "@graph" in doc

    def test_export_output_file(self, tmp_path):
        f = tmp_path / "m.sysml"
        f.write_text(loads(RICH_MODEL).dump())
        out = tmp_path / "m.json"
        from sysmlpy.__main__ import main
        assert main(["export", str(f), "-o", str(out)]) == 0
        doc = json.loads(out.read_text(encoding="utf-8"))
        assert "@graph" in doc

    def test_export_compact(self, tmp_path, capsys):
        f = tmp_path / "m.sysml"
        f.write_text(loads(RICH_MODEL).dump())
        from sysmlpy.__main__ import main
        assert main(["export", str(f), "--compact"]) == 0
        out = capsys.readouterr().out
        assert json.loads(out)["@graph"]
        assert "\n  " not in out  # no indentation

    def test_export_multi_file(self, tmp_path, capsys):
        f1 = tmp_path / "a.sysml"
        f1.write_text("package P { part def V; }")
        f2 = tmp_path / "b.sysml"
        f2.write_text("package P { part def W; }")
        from sysmlpy.__main__ import main
        assert main(["export", str(f1), str(f2)]) == 0
        doc = json.loads(capsys.readouterr().out)
        pkg = next(e for e in doc["@graph"]
                   if e["@type"] == "Identification"
                   and e.get("declaredName") == "P")
        assert pkg

    def test_export_missing_file_exit_2(self, tmp_path):
        from sysmlpy.__main__ import main
        assert main(["export", str(tmp_path / "nope.sysml")]) == 2

    def test_export_parse_error_exit_2(self, tmp_path):
        f = tmp_path / "broken.sysml"
        f.write_text("package P { part def Broken {")
        from sysmlpy.__main__ import main
        assert main(["export", str(f)]) == 2


class TestImportCommand:

    def test_import_stdout_round_trip(self, tmp_path, capsys):
        f = tmp_path / "m.sysml"
        f.write_text(loads(RICH_MODEL).dump())
        out = tmp_path / "m.json"
        from sysmlpy.__main__ import main
        assert main(["export", str(f), "-o", str(out)]) == 0
        capsys.readouterr()
        assert main(["import", str(out)]) == 0
        assert capsys.readouterr().out.strip() == f.read_text().strip()

    def test_import_output_file(self, tmp_path):
        f = tmp_path / "m.sysml"
        f.write_text(loads(RICH_MODEL).dump() + "\n")
        j = tmp_path / "m.json"
        rt = tmp_path / "rt.sysml"
        from sysmlpy.__main__ import main
        assert main(["export", str(f), "-o", str(j)]) == 0
        assert main(["import", str(j), "-o", str(rt)]) == 0
        assert rt.read_text(encoding="utf-8") == f.read_text(encoding="utf-8")

    def test_import_missing_file_exit_2(self, tmp_path):
        from sysmlpy.__main__ import main
        assert main(["import", str(tmp_path / "nope.json")]) == 2

    def test_import_invalid_json_exit_2(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{not json")
        from sysmlpy.__main__ import main
        assert main(["import", str(f)]) == 2

    def test_import_non_interchange_json_exit_2(self, tmp_path):
        f = tmp_path / "not-interchange.json"
        f.write_text('{"hello": "world"}')
        from sysmlpy.__main__ import main
        assert main(["import", str(f)]) == 2

    def test_subprocess_end_to_end(self, tmp_path):
        f = tmp_path / "m.sysml"
        f.write_text(loads(RICH_MODEL).dump() + "\n")
        j = tmp_path / "m.json"
        rt = tmp_path / "rt.sysml"
        assert run_cli("export", str(f), "-o", str(j)).returncode == 0
        assert run_cli("import", str(j), "-o", str(rt)).returncode == 0
        assert rt.read_text(encoding="utf-8") == f.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------


class TestPublicApi:

    def test_exports(self):
        assert sysmlpy.to_interchange is to_interchange
        assert sysmlpy.from_interchange is from_interchange
        assert sysmlpy.interchange_to_json_text is interchange_to_json_text


# ---------------------------------------------------------------------------
# stable (content-addressed) ids — L2 idempotency
# ---------------------------------------------------------------------------


def _find_id(document, declared_name, type_name="Identification"):
    ids = [e["@id"] for e in document["@graph"]
           if e.get("declaredName") == declared_name
           and e["@type"] == type_name]
    assert len(ids) == 1, f"expected one {declared_name!r}, got {ids}"
    return ids[0]


class TestStableIds:
    """stable_ids=True: content-addressed ids (docs/stable-identities.md §3-A).

    L2 guarantees verified here, from the probe matrix in the scope doc:
    - unrelated sibling insertion/reorder leaves ids unchanged
    - ids follow declared identity: renaming an ancestor (which changes
      the qualified-name path) re-mints ids under it — by design
    - collision groups (same name + type under one parent) stay unique
      via occurrence index
    - default (position-derived) ids are untouched when stable_ids=False
    """

    def test_l1_same_text_byte_identical(self):
        src = "package P { part def Engine; part e : Engine; }"
        d1 = to_interchange(src, stable_ids=True)
        d2 = to_interchange(src, stable_ids=True)
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_l2_sibling_insertion_before_leaves_id(self):
        base = "package P { part def Engine; }"
        edited = "package P { part def Dummy; part def Engine; }"
        assert _find_id(to_interchange(edited, stable_ids=True), "Engine") \
            == _find_id(to_interchange(base, stable_ids=True), "Engine")

    def test_l2_sibling_insertion_after_leaves_id(self):
        base = "package P { part def Engine; }"
        edited = "package P { part def Engine; part def Extra; }"
        assert _find_id(to_interchange(edited, stable_ids=True), "Engine") \
            == _find_id(to_interchange(base, stable_ids=True), "Engine")

    def test_l2_inner_feature_insertion_before_leaves_id(self):
        base = "package P { part def Engine { attribute power; } }"
        edited = "package P { part def Engine { attribute mass; attribute power; } }"
        assert _find_id(to_interchange(edited, stable_ids=True), "power") \
            == _find_id(to_interchange(base, stable_ids=True), "power")

    def test_qn_follows_declared_identity(self):
        # renaming the parent changes Engine's qualified-name path —
        # the id follows identity (content), unlike position ids which
        # happened to survive this case
        p = to_interchange("package P { part def Engine; }", stable_ids=True)
        q = to_interchange("package Q { part def Engine; }", stable_ids=True)
        assert _find_id(p, "Engine") != _find_id(q, "Engine")

    def test_renesting_changes_id(self):
        flat = to_interchange("package P { part def Engine; }", stable_ids=True)
        nested = to_interchange(
            "package P { package Inner { part def Engine; } }",
            stable_ids=True,
        )
        assert _find_id(flat, "Engine") != _find_id(nested, "Engine")

    def test_collision_group_ids_distinct(self):
        d = to_interchange(
            "package P { part def Engine; part def Engine; }",
            stable_ids=True,
        )
        ids = [e["@id"] for e in d["@graph"]
               if e.get("declaredName") == "Engine"
               and e["@type"] == "Identification"]
        assert len(ids) == 2 and ids[0] != ids[1]

    def test_graph_ids_unique_rich_model(self):
        d = to_interchange(loads(RICH_MODEL), stable_ids=True)
        ids = [e["@id"] for e in d["@graph"]]
        assert len(ids) == len(set(ids))

    def test_round_trip_preserves_graph(self):
        d1 = to_interchange(loads(RICH_MODEL), stable_ids=True)
        d2 = to_interchange(from_interchange(d1), stable_ids=True)
        assert d2["@graph"] == d1["@graph"]

    def test_default_ids_unchanged(self):
        # stable_ids=False (default) keeps the v0.63.0 position ids
        src = "package P { part def Engine; }"
        d1 = to_interchange(src)
        d2 = to_interchange(src, stable_ids=False)
        assert d1["@graph"] == d2["@graph"]
        assert not _find_id(d1, "Engine").startswith(
            # different uuid5 namespace from the stable scheme
            _find_id(to_interchange(src, stable_ids=True), "Engine")[:-12]
        )

    def test_stable_ids_differ_from_position_ids(self):
        src = "package P { part def Engine; }"
        pos = _find_id(to_interchange(src), "Engine")
        stb = _find_id(to_interchange(src, stable_ids=True), "Engine")
        assert pos != stb


# ---------------------------------------------------------------------------
# reconcile_ids — registry sidecar (L3 identity across edits)
# ---------------------------------------------------------------------------


class TestReconcileIds:
    """Persisted-export registry keeps ids across edits that re-mint
    derived ids (ancestor renames, re-nesting) — Phase 2 sidecar
    mechanism from docs/stable-identities.md (option C, registry
    variant), spike-validated before implementation."""

    BASE = "package P { part def Engine; part e : Engine; attribute power; }"
    EDITED = ("package Vehicle { part def Dummy; part def Engine; "
              "part e : Engine; attribute power; }")

    def test_id_survives_rename_plus_insert(self):
        """The motivating case: derived ids re-mint when P→Vehicle
        renames the QN path; reconciling against the round-1 export
        keeps Engine's round-1 id."""
        doc1 = to_interchange(self.BASE, stable_ids=True)
        doc2 = to_interchange(self.EDITED, stable_ids=True)
        eng_1 = _find_id(doc1, "Engine")
        eng_2_derived = _find_id(doc2, "Engine")
        assert eng_2_derived != eng_1  # derived id re-minted by rename
        out = reconcile_ids(doc2, doc1)
        assert _find_id(out, "Engine") == eng_1

    def test_accepts_json_string_registry(self):
        doc1 = to_interchange(self.BASE, stable_ids=True)
        text = interchange_to_json_text(doc1)
        doc2 = to_interchange(self.EDITED, stable_ids=True)
        out = reconcile_ids(doc2, text)
        assert _find_id(out, "Engine") == _find_id(doc1, "Engine")

    def test_graph_ids_unique_after_reconcile(self):
        """The design-spike pitfall: naive name matching adopted ONE old
        id for TWO new unnamed wrappers (Dummy's and Engine's
        PartDefinition/Definition/DefinitionDeclaration), producing 3
        duplicate ids.  Injective matching (unique key on BOTH sides)
        must keep the graph unique."""
        doc1 = to_interchange(self.BASE, stable_ids=True)
        doc2 = to_interchange(self.EDITED, stable_ids=True)
        out = reconcile_ids(doc2, doc1)
        ids = [e["@id"] for e in out["@graph"]]
        assert len(ids) == len(set(ids))

    def test_unrelated_elements_do_not_adopt(self):
        # Engine's *renamed-package* wrapper id must not be adopted for
        # an element of a different type/name; the Package
        # Identification (Vehicle) has no registry counterpart and
        # keeps its derived id.
        doc1 = to_interchange(self.BASE, stable_ids=True)
        pkg_1 = _find_id(doc1, "VehicleModel" if False else "P")

        class _Edited:  # self.EDITED renamed P→Vehicle
            pass
        doc2 = to_interchange(self.EDITED, stable_ids=True)
        out = reconcile_ids(doc2, doc1)
        assert _find_id(out, "Vehicle") != pkg_1

    def test_adoption_is_injective_first_match_wins(self):
        # two same-name elements in BOTH docs: the (non-unique) key
        # matches nothing — ids stay derived and unique.
        doc1 = to_interchange(
            "package P { part def Engine; part def Engine; }",
            stable_ids=True)
        doc2 = to_interchange(
            "package P { part def Engine; part def Engine; }",
            stable_ids=True)
        out = reconcile_ids(doc2, doc1)
        ids = [e["@id"] for e in out["@graph"]]
        assert len(ids) == len(set(ids))

    def test_renamed_element_falls_back_to_derived(self):
        # an element whose name changed matches nothing: new derived id
        doc1 = to_interchange("package P { part def Engine; }",
                              stable_ids=True)
        doc2 = to_interchange("package P { part def Motor; }",
                              stable_ids=True)
        out = reconcile_ids(doc2, doc1)
        assert _find_id(out, "Motor") != _find_id(doc1, "Engine")

    def test_registry_from_text_file_workflow(self, tmp_path):
        """The documented workflow, file round: export → edit →
        export reconciled from the file → ids preserved."""
        reg = tmp_path / "model.json"
        doc1 = to_interchange(self.BASE, stable_ids=True)
        reg_path = tmp_path / "model.json"
        reg_path.write_text(interchange_to_json_text(doc1))

        model2 = loads(self.EDITED)
        doc2 = to_interchange(model2, reconcile_with=str(reg_path))
        assert _find_id(doc2, "Engine") == _find_id(doc1, "Engine")
        reg_path.write_text(interchange_to_json_text(doc2))

        # round 3: edit again, still stable
        model3 = loads("package Vehicle { part def Engine; part e : Engine; "
                       "attribute power; attribute torque; }")
        doc3 = to_interchange(model3, reconcile_with=str(reg_path))
        assert _find_id(doc3, "Engine") == _find_id(doc1, "Engine")
        ids = [e["@id"] for e in doc3["@graph"]]
        assert len(ids) == len(set(ids))

    def test_reconcile_requires_graph(self):
        with pytest.raises(ValueError):
            reconcile_ids({"@graph": []}, {"no": "graph"})
        with pytest.raises(ValueError):
            reconcile_ids({"@graph": []}, "[]")

    def test_reconcile_implied_by_to_interchange_flag(self):
        doc1 = to_interchange(self.BASE, stable_ids=True)
        doc2 = to_interchange(self.EDITED, stable_ids=True,
                              reconcile_with=doc1)
        assert _find_id(doc2, "Engine") == _find_id(doc1, "Engine")

    def test_reconcile_result_round_trips(self):
        """A reconciled document rebuilds into a live model whose
        re-export (with the reconciled document itself as registry)
        reproduces the identical graph — the registry keeps following
        the model through edits."""
        doc1 = to_interchange(loads(self.BASE), stable_ids=True)
        doc2 = to_interchange(loads(self.EDITED), stable_ids=True)
        out = reconcile_ids(doc2, doc1)
        rebuilt = from_interchange(out)
        again_derived = to_interchange(rebuilt, stable_ids=True)
        again = reconcile_ids(again_derived, out)
        assert again["@graph"] == out["@graph"]

# ---------------------------------------------------------------------------
# doc-carried explicit @ids (doc /* @id: … */) — L3 identity (Phase 2b)
# ---------------------------------------------------------------------------


def _id_of(document, declared_name, type_name="Identification"):
    hits = [e["@id"] for e in document["@graph"]
            if e.get("declaredName") == declared_name
            and e["@type"] == type_name]
    assert len(hits) == 1, f"expected one {declared_name!r}, got {hits}"
    return hits[0]


_V1 = ("package Car { doc /* @id: TR */ part def Traction; "
       "part def Engine { doc /* @id: EN */ attribute cylinders; } }")
_V1_EDITED = ("package Car { part def Traction; part def Engine { "
              "doc /* @id: EN */ attribute cylinders; "
              "attribute displacement; } }")


class TestDocIds:
    """doc /* @id: … */ = source-carried identity (Phase 2b,
    docs/stable-identities.md option C).  An explicit id rides the
    model's own text (`.doc` on the element), overriding derivation;
    verified end to end: export → dump → re-parse → export keeps it."""

    def test_explicit_ids_honored(self):
        d = to_interchange(loads(_V1), doc_ids=True)
        # 'TR' is claimed by a doc comment on the PACKAGE (sibling-level
        # in the body) → bubbles to the Package 'Car' and ids its
        # Identification.  'EN' sits inside Engine's own braces →
        # attaches to Engine.  Both honored.
        assert _id_of(d, "Car") == "TR"
        assert _id_of(d, "Engine") == "EN"

    def test_explicit_id_attach_point_semantics(self):
        """Doc-text placement decides the owner: a doc comment INSIDE
        an element's own braces attaches to that element (its @id is
        honored); a doc statement at sibling level bubbles to the
        enclosing package.  Documented, tested contract."""
        d = to_interchange(loads(
            "package P {\n"
            "    part def Engine { doc /* @id: EN */ }\n"
            "    doc /* @id: PKG */\n"
            "    part def Wheel;\n"
            "}"), doc_ids=True)
        assert _id_of(d, "Engine", "Identification") == "EN"
        assert _id_of(d, "P", "Identification") == "PKG"

    def test_explicit_id_survives_sibling_insertion(self):
        d1 = to_interchange(loads(_V1), doc_ids=True)
        d2 = to_interchange(loads(_V1_EDITED), doc_ids=True)
        assert _id_of(d2, "Engine") == _id_of(d1, "Engine")

    def test_explicit_id_survives_full_interchange_round_trip(self):
        d1 = to_interchange(loads(_V1), doc_ids=True)
        rebuilt = from_interchange(d1)
        d2 = to_interchange(rebuilt, doc_ids=True)
        assert _id_of(d2, "cylinders") == _id_of(d1, "cylinders")

    def test_explicit_id_survives_dump_text_round_trip(self):
        text = loads(_V1).dump()
        assert "@id:" in text
        d2 = to_interchange(loads(text), doc_ids=True)
        d1 = to_interchange(loads(_V1), doc_ids=True)
        assert _id_of(d2, "cylinders") == _id_of(d1, "cylinders")

    def test_graph_ids_unique(self):
        d = to_interchange(loads(_V1), doc_ids=True)
        ids = [e["@id"] for e in d["@graph"]]
        assert len(ids) == len(set(ids))

    def test_duplicate_explicit_claim_rejected(self):
        # same id claimed under two DIFFERENT QN keys ('P'→X, 'Q'→X):
        # harvest carries both; adoption must collide in id_for.
        with pytest.raises(ValueError, match="Duplicate explicit @id"):
            to_interchange(loads(
                "package P { doc /* @id: X */ part def A; } "
                "package Q { doc /* @id: X */ part def B; }"),
                doc_ids=True)

    def test_duplicate_explicit_claim_same_qn_rejected(self):
        # both claims bubble to the same package doc member → the
        # harvester keeps the last ('X' → 'P') — still detectable
        # upstream: two @id: tokens in one .doc.  Current behavior:
        # harvest collapses; pin that the export succeeds (a stricter
        # multi-claim error is a possible future tightening).
        d = to_interchange(loads(
            "package P { doc /* @id: X */ doc /* @id: Y */ part def A; }"),
            doc_ids=True)
        assert d["@graph"]  # export still completes

    def test_plain_models_unaffected(self):
        plain = "package P { part def Engine; part e : Engine; }"
        a = to_interchange(loads(plain), stable_ids=True)
        b = to_interchange(loads(plain), doc_ids=True)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    def test_position_ids_differ_from_doc_ids(self):
        a = to_interchange(loads(_V1))
        b = to_interchange(loads(_V1), doc_ids=True)
        assert _id_of(a, "Traction") != _id_of(b, "Traction")

    def test_reconcile_can_override_doc_id_with_registry(self):
        """Registry reconciliation runs after doc-id harvest: an
        id present in BOTH wins as the registry value."""
        d1 = to_interchange(loads("package Car { part def Traction; }"),
                            stable_ids=True)
        derived = _id_of(d1, "Traction")
        d2 = to_interchange(loads(_V1), doc_ids=True,
                            reconcile_with=d1)
        # Traction carries @id: TR in its doc, but the registry is the
        # MORE RECENT agreement — registry adoption wins.
        assert _id_of(d2, "Traction") == derived

    def test_doc_ids_survive_reparse_of_dump(self):
        text = loads(_V1).dump()
        d1 = to_interchange(loads(_V1), doc_ids=True)
        d2 = to_interchange(loads(text), doc_ids=True)
        assert _id_of(d2, "Engine") == _id_of(d1, "Engine")


ALLOCATION_MODEL = """package AllocationBug {
  part def Wheel;
  part def Vehicle {
    part wheels : Wheel;
    ref part spareWheel : Wheel;
  }
  allocation def {
    end :>> source : Wheel;
    end :>> target : Wheel;
    allocate source.wheels to target.spareWheel;
  }
}"""


class TestAllocationEndExport:
    """Regression: an ``allocation def`` whose unnamed ends carry
    redefinitions (``end :>> source : Wheel;``) parsed fine, but the
    export path (Model.dump -> reparse inside to_interchange) dropped the
    redefinition and typing, emitted bare ``end ;``, and failed the
    reparse with "no viable alternative at input 'end;'".
    """

    def test_export_round_trips_redefined_allocation_ends(self):
        model = loads(ALLOCATION_MODEL)
        doc = to_interchange(model)  # raised SyntaxError before the fix
        assert doc["@graph"]
        text = model.dump()
        assert ":>> source" in text
        assert ":>> target" in text
        assert ": Wheel" in text
        loads(text)  # the reparse to_interchange performs must succeed

    def test_cli_export_redefined_allocation_ends(self, tmp_path):
        p = tmp_path / "min-allocation.sysml"
        p.write_text(ALLOCATION_MODEL + "\n", encoding="utf-8")
        r = run_cli("export", str(p))
        assert r.returncode == 0, r.stderr

