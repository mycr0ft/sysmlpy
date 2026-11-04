"""Issue #40 — the last four things keeping library dumps from round-tripping.

1. `Actions.sysml`: a succession's `perform` target was dropped, leaving a bare
   `then ;` that does not parse.  The visitor's behavior-member dispatch had no
   `performActionUsage` branch at all.
2. `SampledFunctions.sysml`: preserved expression text collapsed newlines, so a
   trailing `//` comment swallowed the rest of the line on the next parse.
3. `VerificationCases.sysml`: `_respace_ternary_glue` re-spaced already-spaced
   text, adding one space per round trip (`if  cond  ? …`).
4. `AnalysisCases.sysml` / `Cases.sysml`: `case c1 : CD;` / `analysis a1 : AD;`
   were "Unknown class" skips that printed to stdout — and the case-usage
   declaration (name + typing) was never read.

The acceptance criterion is the sweep at the bottom: every `.sysml` file in
`src/sysmlpy/library` loads, dumps, re-parses to the same text, contains no raw
dicts, and prints nothing.
"""

import contextlib
import io
import pathlib
import warnings

import pytest

from sysmlpy import loads, parse
from sysmlpy.evaluator import _respace_ternary_glue

LIB = pathlib.Path("/home/jfox/proj/sysmlpy/src/sysmlpy/library")


def _roundtrip(text):
    model = loads(text)
    first = model.dump()
    again, warns = parse(first)
    assert again is not None, warns
    return model, first, again.dump()


# --- 1. `then perform body;` -------------------------------------------------
PERFORM = """package P {
  action def Body;
  action def A {
    then perform body;
    then assign index := index + 1;
  }
}"""


def test_succession_perform_target_is_kept():
    model, first, second = _roundtrip(PERFORM)
    assert "then perform body;" in first
    assert "then ;" not in first
    assert first == second


def test_perform_member_reaches_the_grammar():
    from sysmlpy import load_grammar

    grammar = load_grammar(PERFORM)
    assert "PerformActionUsage" in repr(grammar)


# --- 2. preserved text must not collapse newlines ---------------------------
COMMENTED_BODY = """package P {
  attribute samples : Real [0..*];
  assert constraint {
    (1..size(samples)-1)->forAll { in i; samples#(i) < samples#(i+1) } or
    // strictly increasing
    (1..size(samples)-1)->forAll { in i; samples#(i) > samples#(i+1) }
  }
}"""


def test_preserved_comment_does_not_swallow_the_next_operand():
    model, first, second = _roundtrip(COMMENTED_BODY)
    assert "// strictly increasing" in first
    assert first == second
    assert 'language "English"' not in first


# --- 3. ternary re-spacing must be idempotent ------------------------------
@pytest.mark.parametrize("text,expected", [
    ("ifx>0?1.0else2.0", "if x>0 ? 1.0 else 2.0"),
    ("if passing ? 1 else 2", "if passing ? 1 else 2"),
    ("if  passing  ? 1 else 2", "if passing ? 1 else 2"),
])
def test_ternary_respacing_is_idempotent(text, expected):
    assert _respace_ternary_glue(text) == expected
    assert _respace_ternary_glue(expected) == expected


def test_ternary_round_trip_keeps_single_spaces():
    src = ("package P { attribute passing : Boolean; "
           "attribute x : Integer = if passing ? 1 else 2; }")
    _, first, second = _roundtrip(src)
    line = [ln for ln in first.splitlines() if "if " in ln][0]
    assert "if passing ? 1 else 2" in line
    assert "if  " not in line and "  ?" not in line
    assert first == second


# --- 4. case / analysis-case usages ---------------------------------------
CASES = """package P {
  case def CD;
  case c1 : CD;
  analysis def AD;
  analysis a1 : AD;
  verification def VD;
  verification v1 : VD;
}"""


def test_case_usages_load_with_names_and_round_trip(capsys):
    model, first, second = _roundtrip(CASES)
    assert first == second
    names = [getattr(c, "name", None) for c in model.children[0].children]
    assert names == ["CD", "c1", "AD", "a1", "VD", "v1"]
    assert "case c1 : CD;" in first
    assert "analysis a1 : AD;" in first
    assert capsys.readouterr().out == "", "loading must not print"


# --- acceptance sweep -----------------------------------------------------
@pytest.mark.skipif(not LIB.exists(), reason="library layout differs")
def test_whole_library_round_trips():
    """Every shipped library file: clean dump, clean reparse, silent, fixed point."""
    files = sorted(LIB.rglob("*.sysml"))
    assert len(files) > 40, f"expected the full library, found {len(files)} files"
    problems = []
    for path in files:
        buf = io.StringIO()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with contextlib.redirect_stdout(buf):
                    first = loads(path.read_text(encoding="utf-8")).dump()
        except Exception as exc:
            problems.append(f"{path.name}: load failed ({type(exc).__name__}: {exc})")
            continue
        if "{'name" in first:
            problems.append(f"{path.name}: raw dict in dump")
        if [ln for ln in buf.getvalue().splitlines() if ln.strip()]:
            problems.append(f"{path.name}: printed on dump")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with contextlib.redirect_stdout(io.StringIO()):
                    again, warns = parse(first)
                    if again is None:
                        problems.append(f"{path.name}: reparse failed {warns[:1]}")
                        continue
                    second = again.dump()
        except Exception as exc:
            problems.append(f"{path.name}: reparse raised {type(exc).__name__}")
            continue
        if second != first:
            problems.append(f"{path.name}: not a fixed point")
    assert not problems, "\n".join(problems)
