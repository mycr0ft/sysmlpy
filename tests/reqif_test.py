#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ReqIF interchange bridge (reqif_io).

Uses the anonymized real-world ReqIF sample corpus from
strictdoc-project/reqif (Apache-2.0) when available, downloading nothing:
the fixture below is committed so tests run offline.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import sysmlpy
from sysmlpy import loads
from sysmlpy.reqif_io import (
    ReqIFExportError,
    ReqIFImportError,
    reqif_export,
    reqif_import,
)

pytest.importorskip("reqif", reason="ReqIF bridge needs the 'reqif' package")

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE = REPO_ROOT / "tests" / "fixtures" / "reqif" / "studio_sample.reqif"


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

SMALL_REQIF = """<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
  <THE-HEADER>
    <REQ-IF-HEADER IDENTIFIER="_h">
      <REQ-IF-TOOL-ID>test</REQ-IF-TOOL-ID>
      <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
      <SOURCE-TOOL-ID>test</SOURCE-TOOL-ID>
      <TITLE>small test</TITLE>
    </REQ-IF-HEADER>
  </THE-HEADER>
  <CORE-CONTENT>
    <REQ-IF-CONTENT>
      <DATATYPES>
        <DATATYPE-DEFINITION-XHTML IDENTIFIER="_dt"/>
      </DATATYPES>
      <SPEC-TYPES>
        <SPEC-OBJECT-TYPE IDENTIFIER="_st">
          <SPEC-ATTRIBUTES>
            <ATTRIBUTE-DEFINITION-XHTML IDENTIFIER="_a_text" LONG-NAME="ReqIF.Text">
              <TYPE><DATATYPE-DEFINITION-XHTML-REF>_dt</DATATYPE-DEFINITION-XHTML-REF></TYPE>
            </ATTRIBUTE-DEFINITION-XHTML>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="_a_id" LONG-NAME="ReqIF.ForeignID">
              <TYPE><DATATYPE-DEFINITION-STRING-REF>_dt</DATATYPE-DEFINITION-STRING-REF></TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
          </SPEC-ATTRIBUTES>
        </SPEC-OBJECT-TYPE>
      </SPEC-TYPES>
      <SPEC-OBJECTS>
        <SPEC-OBJECT IDENTIFIER="_o1" LAST-CHANGE="2026-01-01">
          <TYPE><SPEC-OBJECT-TYPE-REF>_st</SPEC-OBJECT-TYPE-REF></TYPE>
          <VALUES>
            <ATTRIBUTE-VALUE-XHTML THE-ORIGINAL-NAME="ReqIF.Text">
              <DEFINITION><ATTRIBUTE-DEFINITION-XHTML-REF>_a_text</ATTRIBUTE-DEFINITION-XHTML-REF></DEFINITION>
              <THE-VALUE><xhtml:div xmlns:xhtml="http://www.w3.org/1999/xhtml">Top requirement</xhtml:div></THE-VALUE>
            </ATTRIBUTE-VALUE-XHTML>
          </VALUES>
        </SPEC-OBJECT>
        <SPEC-OBJECT IDENTIFIER="_o2" LAST-CHANGE="2026-01-01">
          <TYPE><SPEC-OBJECT-TYPE-REF>_st</SPEC-OBJECT-TYPE-REF></TYPE>
          <VALUES>
            <ATTRIBUTE-VALUE-XHTML THE-ORIGINAL-NAME="ReqIF.Text">
              <DEFINITION><ATTRIBUTE-DEFINITION-XHTML-REF>_a_text</ATTRIBUTE-DEFINITION-XHTML-REF></DEFINITION>
              <THE-VALUE><xhtml:div xmlns:xhtml="http://www.w3.org/1999/xhtml">Child requirement</xhtml:div></THE-VALUE>
            </ATTRIBUTE-VALUE-XHTML>
          </VALUES>
        </SPEC-OBJECT>
      </SPEC-OBJECTS>
      <SPECIFICATIONS>
        <SPECIFICATION IDENTIFIER="_spec">
          <TYPE><SPECIFICATION-TYPE-REF>_st</SPECIFICATION-TYPE-REF></TYPE>
          <CHILDREN>
            <SPEC-HIERARCHY IDENTIFIER="_h1">
              <OBJECT><SPEC-OBJECT-REF>_o1</SPEC-OBJECT-REF></OBJECT>
              <CHILDREN>
                <SPEC-HIERARCHY IDENTIFIER="_h2">
                  <OBJECT><SPEC-OBJECT-REF>_o2</SPEC-OBJECT-REF></OBJECT>
                </SPEC-HIERARCHY>
              </CHILDREN>
            </SPEC-HIERARCHY>
          </CHILDREN>
        </SPECIFICATION>
      </SPECIFICATIONS>
    </REQ-IF-CONTENT>
  </CORE-CONTENT>
</REQ-IF>
"""

MODEL_TEXT = """package VehicleSpec {
    requirement def MassRequirement {
        doc /* total mass shall not exceed 2000 kg */
        subject : Vehicle;
    }
    requirement totalMass : MassRequirement {
        doc /* includes battery */
        requirement detail {
            doc /* measure at curb weight */
        }
    }
    part Vehicle;
    action massCheck { doc /* weigh it */ }
}"""


def collect(obj, depth, acc):
    for child in obj:
        if child.__class__.__name__ == "Requirement":
            acc.append((depth, child.name, getattr(child, "doc", None) or ""))
        collect(child, depth + 1, acc)
    return acc


def _collect(obj, depth, acc):
    return collect(obj, depth, acc)


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------


class TestReqIFImport:
    def test_small_file_import(self, tmp_path: Path) -> None:
        src = tmp_path / "small.reqif"
        src.write_text(SMALL_REQIF, encoding="utf-8")

        text = reqif_import(str(src))

        assert "requirement" in text
        model = loads(text)
        reqs = collect(model, 0, [])
        assert len(reqs) == 2
        # nesting: _o2 is a child of _o1 in the hierarchy
        # (depth 0 = package, so requirements start at depth 1)
        assert [d for d, _, _ in reqs] == [1, 2]
        # doc comments carry the stripped ReqIF.Text
        assert any("Top requirement" in doc for _, _, doc in reqs)
        assert any("Child requirement" in doc for _, _, doc in reqs)

    def test_xhtml_is_stripped(self, tmp_path: Path) -> None:
        src = tmp_path / "small.reqif"
        src.write_text(SMALL_REQIF, encoding="utf-8")
        text = reqif_import(str(src))
        assert "<xhtml:div>" not in text
        assert "Top requirement" in text

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ReqIFImportError):
            reqif_import(str(tmp_path / "missing.reqif"))

    def test_garbage_file_raises(self, tmp_path: Path) -> None:
        src = tmp_path / "garbage.reqif"
        src.write_text("this is not xml", encoding="utf-8")
        with pytest.raises(ReqIFImportError):
            reqif_import(str(src))

    def test_real_world_studio_sample(self) -> None:
        if not SAMPLE.exists():
            pytest.skip("studio_sample.reqif fixture not present")
        text = reqif_import(str(SAMPLE))
        model = loads(text)
        reqs = collect(model, 0, [])
        # 138 hierarchy nodes in the original sample
        # (model walk: package = depth 0, requirements start at 1, so the
        # ReqIF's 3-level hierarchy shows as max depth 4)
        assert len(reqs) == 138
        depths = [d for d, _, _ in reqs]
        assert max(depths) == 4


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


class TestReqIFExport:
    def test_export_and_reimport(self, tmp_path: Path) -> None:
        model = loads(MODEL_TEXT)
        out = tmp_path / "export.reqif"

        reqif_export(model, str(out))

        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "REQ-IF" in content
        assert "<SPEC-OBJECT" in content

        # round-trip: re-import preserves requirement count and nesting
        text = reqif_import(str(out))
        model2 = loads(text)
        reqs = _collect(model2, 0, [])
        assert len(reqs) == 3  # totalMass, detail + MassRequirement def? see below
        depths = [d for d, _, _ in reqs]
        assert depths == sorted(depths) or depths[0] == 0

    def test_export_includes_doc_text(self, tmp_path: Path) -> None:
        model = loads(MODEL_TEXT)
        out = tmp_path / "export.reqif"
        reqif_export(model, str(out))
        content = out.read_text(encoding="utf-8")
        assert "total mass shall not exceed 2000 kg" in content

    def test_export_model_without_requirements_raises(self, tmp_path: Path) -> None:
        model = loads("package Empty { part p; }")
        with pytest.raises(ReqIFExportError):
            reqif_export(model, str(tmp_path / "out.reqif"))


# ---------------------------------------------------------------------------
# full round-trip on the real-world sample
# ---------------------------------------------------------------------------


class TestFullRoundTrip:
    def test_reqif_to_model_to_reqif(self, tmp_path: Path) -> None:
        if not SAMPLE.exists():
            pytest.skip("studio_sample.reqif fixture not present")

        # 1. ReqIF -> model
        text = reqif_import(str(SAMPLE))
        model = loads(text)
        reqs = _collect(model, 0, [])
        assert len(reqs) == 138

        # 2. model -> ReqIF
        out = tmp_path / "reexport.reqif"
        reqif_export(model, str(out))

        # 3. ReqIF -> model again
        text2 = reqif_import(str(out))
        model2 = loads(text2)
        reqs2 = _collect(model2, 0, [])

        # structure preserved exactly
        assert [d for d, _, _ in reqs2] == [d for d, _, _ in reqs]
        assert len(reqs2) == 138

    def test_cli_reqif_import_export(self, tmp_path: Path) -> None:
        if not SAMPLE.exists():
            pytest.skip("studio_sample.reqif fixture not present")
        sysml_text = tmp_path / "out.sysml"
        reqif_out = tmp_path / "roundtrip.reqif"
        reimported = tmp_path / "reimported.sysml"

        r1 = subprocess.run(
            [sys.executable, "-m", "sysmlpy", "reqif-import", str(SAMPLE),
             "-o", str(sysml_text)],
            capture_output=True, text=True, timeout=600,
        )
        assert r1.returncode == 0, r1.stderr

        r2 = subprocess.run(
            [sys.executable, "-m", "sysmlpy", "reqif-export", str(sysml_text),
             "-o", str(reqif_out)],
            capture_output=True, text=True, timeout=600,
        )
        assert r2.returncode == 0, r2.stderr
        assert reqif_out.exists()

        r3 = subprocess.run(
            [sys.executable, "-m", "sysmlpy", "reqif-import", str(reqif_out),
             "-o", str(reimported)],
            capture_output=True, text=True, timeout=600,
        )
        assert r3.returncode == 0, r3.stderr
        assert "requirement" in reimported.read_text(encoding="utf-8")