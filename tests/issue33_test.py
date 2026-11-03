"""Issue #33 — parenthesized `^`/`**` exponents were opaque text.

The unary-level paren branch returned None deliberately (to keep grouping),
so `(x^(1/2)+0)` reached the evaluator as one glued identifier and every
calc body using a grouped exponent was unevaluable.  Two further defects sat
behind it:

* ``ExponentiationExpression.dump()`` converted its right operand as another
  ``ExponentiationExpression`` — the grammar says ``unaryExpression`` — so the
  dumper fell back to ``str(dict)``: `x ^ {'name': 'UnaryExpression', ...}`.
  That is the raw-dict leak in SI.sysml / USCustomaryUnits / SIPrefixes.
* ``MultiplicativeExpression.dump()`` joined its operands with ``""``, so
  `tp / (tm * v)` printed as `tp/ (tm* v)`.

The fix represents a group structurally: a ``PrimaryExpression`` whose base is
a ``SequenceExpression`` relationship, which ``BaseExpression`` already dumps
in parentheses.  The group is therefore one operand of whatever encloses it,
and both the dump and the evaluator see the real structure.
"""

import contextlib
import io
import pathlib
import warnings

import pytest

from sysmlpy import loads, parse
from sysmlpy.evaluator import evaluate_calculation
from sysmlpy.semantic import const_fold

LIB = pathlib.Path("/home/jfox/proj/sysmlpy/src/sysmlpy/library")

CALCS = """
package P {
  calc def Sq { in x : ScalarValues::Real; return : ScalarValues::Real = (x^(1/2)+0); }
  calc def Pow2 { in a : ScalarValues::Real; in b : ScalarValues::Real;
                  return : ScalarValues::Real = (a+b)^2; }
  calc def Nested { in x : ScalarValues::Real; in y : ScalarValues::Real;
                    return : ScalarValues::Real = (x*(1+y))^2; }
  calc def Plain { in x : ScalarValues::Real; return : ScalarValues::Real = x^2; }
  calc def Kinetic { in m : ScalarValues::Real; in v : ScalarValues::Real;
                     return : ScalarValues::Real = m*v^2/2; }
  calc def Length { in x : ScalarValues::Real; return = x * 2 [m]; }
}
"""

PREFIX = ("package P { part a; part b; part c; part x; part y; part tp; part tm; "
          "part v; attribute s; ")


def _body(expr):
    model = loads(PREFIX + "assert constraint { " + expr + " } }")
    text = model.dump()
    seg = text.split("assert constraint", 1)[1]
    start = seg.index("{") + 1
    return " ".join(seg[start:seg.index("}", start)].split())


@pytest.fixture(scope="module")
def calcs():
    return loads(CALCS)


@pytest.mark.parametrize("name,args,expected", [
    ("Sq", [9.0], 3.0),
    ("Sq", [16.0], 4.0),
    ("Pow2", [2.0, 3.0], 25.0),
    ("Nested", [2.0, 3.0], 64.0),
    ("Plain", [3.0], 9.0),
    ("Kinetic", [2.0, 3.0], 9.0),
])
def test_parenthesized_exponents_evaluate(calcs, name, args, expected):
    assert evaluate_calculation(calcs, name, args=args) == pytest.approx(expected)


def test_calculation_results_stay_pint_aware(calcs):
    result = evaluate_calculation(calcs, "Length", args=[3.0])
    assert getattr(result, "units", None) is not None
    assert str(result.units) == "meter"
    assert float(result.magnitude) == pytest.approx(6.0)


@pytest.mark.parametrize("expr,expected", [
    ("x^2", "x ^ 2"),
    ("2**3", "2 ** 3"),
    ("(a+b)^2", "(a + b) ^ 2"),
    ("(x^(1/2)+0)", "(x ^ (1 / 2) + 0)"),
    ("(x*(1+y))^2", "(x * (1 + y)) ^ 2"),
    ("s^-1", "s ^ -1"),
    ("tp / (tm * v)", "tp / (tm * v)"),
    ("(a or b) and c", "(a or b) and c"),
    ("a and (b or c)", "a and (b or c)"),
    ("-(2-5)", "-(2 - 5)"),
])
def test_dump_keeps_grouping_and_spacing(expr, expected):
    assert _body(expr) == expected


def test_exponent_dump_has_no_raw_dict():
    for expr in ("x^2", "2**3", "(a+b)^2", "s^-1", "(x*(1/2))^3"):
        body = _body(expr)
        assert "{'name'" not in body, (expr, body)


def test_no_separator_gaps_in_multiplicative_chains():
    """`tp / (tm * v)` must not render as `tp/ (tm* v)`."""
    body = _body("a * b / c")
    assert body == "a * b / c"


def test_grouped_expression_is_a_fixed_point():
    for expr in ("(x^(1/2)+0)", "(x*(1+y))^2", "(a or b) and c", "-(2-5)"):
        first = _body(expr)
        assert _body(first) == first, expr


@pytest.mark.parametrize("text,expected", [
    ("-(2-5)", 3),
    ("2^3", 8),
    ("(2+3)^2", 25),
])
def test_const_fold_through_groups(text, expected):
    model = loads('package P { attribute v : Integer = ' + text + '; }')
    grammar = model.children[0].children[0].grammar
    from sysmlpy.semantic import _find_owned_expressions
    exprs = _find_owned_expressions(grammar.get_definition())
    assert const_fold(exprs[0]) == expected


@pytest.mark.skipif(not (LIB / "domain/Quantities and Units/SI.sysml").exists(),
                   reason="library layout differs")
@pytest.mark.parametrize("rel", [
    "domain/Quantities and Units/SI.sysml",
    "domain/Quantities and Units/SIPrefixes.sysml",
    "domain/Quantities and Units/USCustomaryUnits.sysml",
    "domain/Geometry/ShapeItems.sysml",
])
def test_unit_libraries_dump_cleanly(rel):
    """These four files held the raw-dict leak (1085/35/325/104 occurrences)."""
    buf = io.StringIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with contextlib.redirect_stdout(buf):
            text = loads((LIB / rel).read_text(encoding="utf-8")).dump()
    assert text.count("{'name") == 0
    assert not [ln for ln in buf.getvalue().splitlines() if ln.strip()]
