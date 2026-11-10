# -*- coding: utf-8 -*-
"""Cross-tool portability pins for the GTRI bug report of 2026-11-09.

The four repro files live in ``tests/fixtures/gtri_2026_11/`` verbatim.  For
each one, this module pins sysmlpy's verdict (parse + analyze) and — when an
OpenSysML checkout is available next to this repo
(``~/proj/third_party/OpenSysML`` with a built ``bin/sysml``) — the OpenSysML
verdict, so the two tools' deltas stay on the record:

* QualifiedAllocation.sysml — sysmlpy resolves the qualified sibling-package
  allocation endpoint; OpenSysML rejects it (``Couldn't resolve reference to
  Feature 'Architecture::Source'``).  Documented divergence: sysmlpy shares
  its resolver with typings, where the same spelling is silent.
* QualifiedAllocationImported.sysml — both tools clean.
* SingleItemInterface.sysml — both tools flag it (issue #44; message is
  OpenSysML's verbatim).
* TypedAllocation.sysml — sysmlpy resolves the definition ends and the
  nested allocate (issue #43).

When OpenSysML is present the module also greps the OpenSysML stderr for the
expected diagnostic signatures; when absent the OpenSysML half skips.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

import sysmlpy
from sysmlpy import analyze, loads

FIXTURES = Path(__file__).parent / "fixtures" / "gtri_2026_11"

# Reference checkout: ~/proj/third_party/OpenSysML-reference — a pinned
# origin/develop worktree of the OpenSysML clone, rebuilt when its verdicts
# matter (see sysmlpy-development skill).  Prefer its binary; the plain
# checkout's bin/sysml (0.8.x, Sep 2026) predates both diagnostics and
# accepts everything, which would pin a meaningless "both accept".
_OPENSYSML_REFERENCE = Path.home() / "proj" / "third_party" / "OpenSysML-reference" / "bin" / "sysml"
_OPENSYSML_WORKTREE = Path.home() / "proj" / "third_party" / "OpenSysML" / "bin" / "sysml"
OPENSYSML_BIN = (_OPENSYSML_REFERENCE if _OPENSYSML_REFERENCE.is_file()
                 else _OPENSYSML_WORKTREE)


def _fixture(name):
    return FIXTURES / name


def _sysmlpy_verdict(path):
    model = loads(path.read_text())
    return analyze(model)


def _opensysml_available():
    return OPENSYSML_BIN.is_file()


def _opensysml_verdict(path):
    """(clean, output) of `bin/sysml -validate <file>`.

    Exit codes are unreliable across versions (0.12.x reports the verdict in
    the text), so 'clean' is derived from the printed verdict line.
    """
    if not _opensysml_available():
        pytest.skip("OpenSysML checkout not built (bin/sysml)")
    run = subprocess.run(
        [str(OPENSYSML_BIN), "-validate", str(path)],
        capture_output=True, text=True, timeout=120,
    )
    out = run.stdout + run.stderr
    clean = "no errors" in out
    return clean, out


# --------------------------------------------------------------------------
# sysmlpy verdicts (always pinned)
# --------------------------------------------------------------------------

def test_qualified_allocation_sysmlpy_resolves():
    """sysmlpy treats the qualified sibling-package allocation endpoint as
    resolvable — same spelling is silent for typings, resolver is shared.
    OpenSysML disagrees; see test_qualified_allocation_opensysml_rejects."""
    issues = _sysmlpy_verdict(_fixture("QualifiedAllocation.sysml"))
    assert [i.code for i in issues if i.severity == "error"] == []


def test_qualified_allocation_imported_both_clean():
    issues = _sysmlpy_verdict(_fixture("QualifiedAllocationImported.sysml"))
    assert [i.code for i in issues if i.severity == "error"] == []


def test_single_item_interface_sysmlpy_flags():
    issues = _sysmlpy_verdict(_fixture("SingleItemInterface.sysml"))
    assert "RELATED_ELEMENTS" in [i.code for i in issues]


def test_typed_allocation_sysmlpy_resolves():
    issues = _sysmlpy_verdict(_fixture("TypedAllocation.sysml"))
    assert [i.code for i in issues if i.severity == "error"] == []


def test_version_pins_repro_env():
    assert sysmlpy.__version__ >= "0.106.0"


# --------------------------------------------------------------------------
# OpenSysML cross-checks (skip when the checkout/binary is absent)
#
# Verdicts measured against OpenSysML 0.12.1-998-gddc4a547fe (origin/develop,
# 2026-11-09 worktree /tmp/osml-develop): QualifiedAllocation REJECTED
# (connector-end-referent on both ends), QualifiedAllocationImported
# REJECTED (same), SingleItemInterface REJECTED (related-elements, message
# verbatim), TypedAllocation accepted.
# --------------------------------------------------------------------------

def test_qualified_allocation_opensysml_rejects():
    clean, out = _opensysml_verdict(_fixture("QualifiedAllocation.sysml"))
    assert not clean, out
    assert "connector-end-referent" in out, out


def test_qualified_allocation_imported_opensysml_rejects():
    """Also rejected on current develop — the e-mail's claim that the
    imported form 'makes OpenSysML accept the test' doesn't hold on
    0.12.1-998-gddc4a547fe; both endpoints still fail with
    connector-end-referent.  Record the delta either way."""
    clean, out = _opensysml_verdict(
        _fixture("QualifiedAllocationImported.sysml"))
    if clean:
        pytest.skip("OpenSysML now accepts the imported form — update this pin")


def test_single_item_interface_opensysml_flags():
    clean, out = _opensysml_verdict(_fixture("SingleItemInterface.sysml"))
    assert not clean, out
    assert "Must have at least two related elements" in out, out


def test_typed_allocation_opensysml_accepts():
    clean, out = _opensysml_verdict(_fixture("TypedAllocation.sysml"))
    assert clean, out
