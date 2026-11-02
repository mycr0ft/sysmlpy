"""Issue #35: the KerML parser shares the persistent DFA cache.

Before this, ``dfa_cache`` covered only the SysML parser, so every KerML
corpus / library-index run re-derived the prediction structures from
scratch (Occurrences.kerml ~11-14 s cold vs ~3 s warm).

The cache is per grammar family: each target has its own key and file
(``dfa-<key>.pkl`` for SysML, ``dfa-kerml-<key>.pkl`` for KerML), so a
SysML grammar change can never invalidate — let alone corrupt — the KerML
cache.  These pins cover the key/file separation, the load/save lifecycle,
the exit-time re-save that makes a multi-file walk converge, and the
"cache problems never break parsing" contract.
"""

import os
import subprocess
import sys

import pytest

from sysmlpy import dfa_cache
from sysmlpy.kerml import kerml

KERML_SRC = """
package P {
  private import ScalarValues::*;
  class C {
    feature x : Real;
  }
}
"""


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path):
    dfa_cache.set_dfa_cache(enabled=True, directory=str(tmp_path))
    dfa_cache.reset_for_tests()
    yield
    dfa_cache.set_dfa_cache(enabled=None, directory=None)
    dfa_cache.reset_for_tests()


def test_targets_include_kerml():
    assert "kerml" in dfa_cache.targets()
    assert "sysml" in dfa_cache.targets()


def test_keys_and_files_are_per_target():
    k_sysml = dfa_cache.cache_key("sysml")
    k_kerml = dfa_cache.cache_key("kerml")
    assert k_sysml != k_kerml, "ATN digests differ per grammar"
    # the SysML file keeps its historical name (existing caches stay valid)
    assert dfa_cache.cache_file("sysml").endswith("dfa-%s.pkl" % k_sysml[:16])
    assert dfa_cache.cache_file("kerml").endswith(
        "dfa-kerml-%s.pkl" % k_kerml[:16])


def test_kerml_save_then_load_in_process(tmp_path):
    kerml.parse(KERML_SRC)          # warm some DFA states
    assert dfa_cache.save_dfa_cache(target="kerml") is True
    assert dfa_cache.stats("kerml")["saved"] is True
    dfa_cache.reset_for_tests()
    assert dfa_cache.load_dfa_cache(target="kerml") is True
    assert dfa_cache.stats("kerml")["loaded"] is True
    assert dfa_cache.stats("kerml")["file_states"] > 0


def test_sysml_target_unaffected_by_kerml_cache():
    dfa_cache.save_dfa_cache(target="kerml")
    kerml_file = dfa_cache.cache_file("kerml")
    sysml_file = dfa_cache.cache_file("sysml")
    assert kerml_file != sysml_file
    assert not os.path.exists(sysml_file), "kerml save writes only its own file"
    assert dfa_cache.stats("sysml")["loaded"] is False


def test_disabled_flag_skips_kerml_cache():
    dfa_cache.set_dfa_cache(enabled=False)
    dfa_cache.reset_for_tests()
    assert dfa_cache.load_dfa_cache(target="kerml") is False
    assert dfa_cache.save_dfa_cache(target="kerml") is False
    # parsing still works with the cache off
    kerml.parse(KERML_SRC)


def test_kerml_parse_never_raises_on_cache_errors(monkeypatch):
    # a broken cache_file must not break the parse (speed only)
    monkeypatch.setattr(dfa_cache, "cache_file",
                        lambda *a, **k: "/proc/impossible/dir/x.pkl")
    with pytest.warns(UserWarning, match="DFA cache"):
        dfa_cache.save_dfa_cache(target="kerml")
    kerml.parse(KERML_SRC)


def test_exit_resave_persists_a_multi_file_walk(tmp_path):
    """The atexit hook must store states warmed AFTER the first save.

    A single parse saves early; the exit hook then supersedes the file with
    the strictly warmer DFA (that is what makes the library-index walk over
    ~36 .kerml files converge instead of persisting the first file only).
    """
    script = f"""
import json, os, sys
sys.path.insert(0, {os.path.abspath('src')!r})
os.environ["SYSMLPY_DFA_CACHE"] = {str(tmp_path)!r}
from sysmlpy import dfa_cache
dfa_cache.reset_for_tests()
from sysmlpy.semantic import LibrarySymbolIndex
syms = LibrarySymbolIndex.get_symbols(None)
print(json.dumps({{"symbols": len(syms)}}))
"""
    proc = subprocess.run([sys.executable, "-c", script],
                          capture_output=True, text=True, timeout=900)
    assert proc.returncode == 0, proc.stderr[-800:]
    files = [f for f in os.listdir(tmp_path) if f.startswith("dfa-kerml-")]
    assert files, "kerml cache written"
    size = os.path.getsize(os.path.join(tmp_path, files[0]))
    # the first-file save alone was ~1 MB; the whole corpus needs several
    assert size > 4 * 1024 * 1024, f"cache file only {size} bytes"

    # and a second process loads it instead of re-deriving
    script2 = script.replace('"symbols": len(syms)',
                             '"symbols": len(syms), "loaded": '
                             'dfa_cache.stats("kerml")["loaded"]')
    proc2 = subprocess.run([sys.executable, "-c", script2],
                           capture_output=True, text=True, timeout=900)
    assert proc2.returncode == 0, proc2.stderr[-800:]
    assert '"loaded": true' in proc2.stdout, proc2.stdout[-300:]
