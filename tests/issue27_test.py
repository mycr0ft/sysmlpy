"""Issue #27 (CARTA downstream report): three small downstream papercuts.

* `dfa_cache` read ``SYSSMLPY_DFA_CACHE`` (three S) — a misspelling that never
  matches the package name.  ``SYSMLPY_DFA_CACHE`` is now canonical and the old
  spelling is still honoured as an alias.
* ``traceability.satisfied_by`` held the satisfy subject exactly as written
  (usually a short name) while ``qualified_name`` was qualified, so equal short
  names in different packages collided downstream.  Unambiguous references are
  now recorded as qualified names.

The third item in that report (``verified_by`` empty for ``verify`` inside an
objective) needs the verify-endpoint work in issue #23 — there is no Verify
element to read yet — and is pinned there instead.
"""

import os

import pytest

from sysmlpy import dfa_cache, loads
from sysmlpy import traceability


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in ("SYSMLPY_DFA_CACHE", "SYSSMLPY_DFA_CACHE"):
        monkeypatch.delenv(name, raising=False)


def test_issue27_canonical_env_var_disables_cache(monkeypatch):
    monkeypatch.setenv("SYSMLPY_DFA_CACHE", "off")
    assert dfa_cache._env_disabled() is True


def test_issue27_canonical_env_var_sets_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("SYSMLPY_DFA_CACHE", str(tmp_path))
    assert dfa_cache._env_disabled() is False
    assert dfa_cache._env_directory() == str(tmp_path)


def test_issue27_legacy_misspelling_still_honoured(monkeypatch):
    monkeypatch.setenv("SYSSMLPY_DFA_CACHE", "off")
    assert dfa_cache._env_disabled() is True


def test_issue27_canonical_wins_over_legacy(monkeypatch, tmp_path):
    monkeypatch.setenv("SYSMLPY_DFA_CACHE", str(tmp_path))
    monkeypatch.setenv("SYSSMLPY_DFA_CACHE", "off")
    assert dfa_cache._env_disabled() is False
    assert dfa_cache._env_directory() == str(tmp_path)


def test_issue27_satisfied_by_is_qualified():
    model = loads("""
        package P {
            part def S;
            requirement def R;
            part def T { satisfy R by S; }
        }
    """)
    report = traceability.extract_traceability(model)
    trace = [t for t in report.requirements if t.name == "R"][0]
    assert trace.qualified_name == "P::R"
    assert trace.satisfied_by == ["P::S"], trace.satisfied_by


def test_issue27_ambiguous_short_name_stays_as_written():
    # Two different `S` in two packages: qualifying either would be a guess.
    model = loads("""
        package P { part def S; }
        package Q { part def S; }
        package R {
            requirement def Req;
            part def T { satisfy Req by S; }
        }
    """)
    report = traceability.extract_traceability(model)
    trace = [t for t in report.requirements if t.name == "Req"][0]
    assert trace.satisfied_by == ["S"], trace.satisfied_by
