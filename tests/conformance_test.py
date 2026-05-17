"""
SysML v2 Parse Conformance Tests
=================================
Source: SysML-v2-Pilot-Implementation-2026-03 (org.omg.sysml.xpect.tests)
License: LGPL-3.0

Each .sysml file under tests/sysmlv2/ is a test case.  The companion .error
file controls what the test asserts:

  Empty .error file  → loads(text) must succeed without raising any exception.
  Non-empty .error   → first non-comment line is matched against the exception
                       raised by loads(). Lines starting with '#' are ignored.

All 123 .sysml files are syntactically valid SysML (they are official OMG
reference test fixtures).  The .error files are empty to start with because
sysmlpy currently performs syntax parsing only.  As semantic validation is
added, the .error files for tests/sysmlv2/validation/invalid/ will be
populated with the expected validation-error messages.

Run this suite:
    pytest -m conformance
    pytest -m conformance -v
    pytest -m conformance tests/sysmlv2/simpletests/  (one subdirectory)

Skip this suite (e.g., during normal development):
    pytest -m "not conformance"
"""

import pathlib
import pytest
from sysmlpy import loads

SYSMLV2_DIR = pathlib.Path(__file__).parent / "sysmlv2"


def _collect():
    """Yield pytest.param objects for every .sysml file under SYSMLV2_DIR."""
    for sysml_file in sorted(SYSMLV2_DIR.rglob("*.sysml")):
        # Skip Jupyter checkpoint files
        if ".ipynb_checkpoints" in str(sysml_file):
            continue
        rel = str(sysml_file.relative_to(SYSMLV2_DIR))
        yield pytest.param(sysml_file, id=rel)


@pytest.mark.conformance
@pytest.mark.parametrize("sysml_file", list(_collect()))
def test_parses_without_error(sysml_file):
    """Parse the .sysml file with sysmlpy and assert against the .error file.

    An empty .error file means the file should parse cleanly.
    A non-empty .error file provides an expected exception message (regex).
    """
    error_file = sysml_file.with_suffix(".error")

    # Read expected error (skip comment lines)
    expected_error = ""
    if error_file.exists():
        lines = [
            line
            for line in error_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        expected_error = lines[0] if lines else ""

    text = sysml_file.read_text(encoding="utf-8")

    if expected_error:
        with pytest.raises(Exception, match=expected_error):
            loads(text)
    else:
        # Should parse without raising any exception
        loads(text)
