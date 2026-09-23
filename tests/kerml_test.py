"""KerML parsing tests for pytest discovery.

The three battery scripts (parse / visitor / init) assert via
sys.exit(1) on failure and print per-check PASS/FAIL lines; running
them as subprocesses keeps them runnable standalone AND under pytest.
"""
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE.parent / "src"
VENV_PY = "/home/jfox/.cache/pypoetry/virtualenvs/sysmlpy-VrdXgKoh-py3.13/bin/python"


def _run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [VENV_PY, str(HERE / "kerml_batteries" / script)],
        capture_output=True, text=True, timeout=600,
        cwd=str(HERE.parent),
    )


def test_kerml_parse_battery():
    """Syntax cases + full .kerml corpus through kerml.parse()."""
    r = _run("parse_battery.py")
    assert r.returncode == 0, f"parse battery failed:\n{r.stdout}\n{r.stderr}"


def test_kerml_visitor_battery():
    """Structure extraction cases + corpus through parse_to_dict."""
    r = _run("visitor_battery.py")
    assert r.returncode == 0, f"visitor battery failed:\n{r.stdout}\n{r.stderr}"


def test_kerml_init_battery():
    """Package exports + SysML coexistence."""
    r = _run("init_battery.py")
    assert r.returncode == 0, f"init battery failed:\n{r.stdout}\n{r.stderr}"


def test_kerml_symbol_index_battery():
    """Hybrid LibrarySymbolIndex: .kerml parsed + .sysml regex."""
    r = _run("symbol_index_battery.py")
    assert r.returncode == 0, f"symbol-index battery failed:\n{r.stdout}\n{r.stderr}"


def test_kerml_corpus_recovery_battery():
    """Sweep-failure categories re-verified: .kerml corpus, connect [1],
    Annex A SimpleVehicleModel."""
    r = _run("corpus_recovery_battery.py")
    assert r.returncode == 0, f"corpus-recovery battery failed:\n{r.stdout}\n{r.stderr}"