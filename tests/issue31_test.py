"""Issue #31 — `assert constraint` bodies glued operators on the first dump.

Three defects, all in the expression emitter's text/chain handling:

1. ``_unwrap_to_layer`` gave the OR / XOR layers the operand class of the
   wrong precedence level, so ``a xor b`` put a whole OrExpression chain dict
   into XorExpression.operand; the dumper stringified it
   (``a xor {'name': 'OrExpression', ...}``).
2. A parenthesized group (``(a and b) xor c``) fell through every emitter
   branch to the lossy text fallback — the whole expression became one
   FeatureReference name.
3. The text fallback used ``ctx.getText()``, which concatenates tokens:
   ``(a or b) and c`` became ``(aorb)andc`` — not even re-parseable.

The pins below cover each, plus the OMG corpus file that reported it.
"""

import pathlib
import re

import pytest

from sysmlpy import loads, parse

CORPUS = pathlib.Path(
    "/home/jfox/proj/third_party/SysML-v2-Release/sysml/src/examples/"
    "Variability Examples/VehicleVariabilityModel.sysml")

# Operator TOKENS only — used to prove the dump kept every operator the source
# had (and nothing more).
_OP_RE = re.compile(
    r"==|!=|<=|>=|(?<![\w.])xor(?![\w])|(?<![\w.])and(?![\w])|"
    r"(?<![\w.])or(?![\w])|(?<![\w.])not(?![\w])|(?<![\w.])implies(?![\w])")

PREFIX = "package P { part a; part b; part c; part d; part e; part f; part g; part h;"


def _body(src_text):
    """The assert-constraint body text of a dump (whitespace-normalised)."""
    seg = src_text.split("assert constraint", 1)[1]
    start = seg.index("{") + 1
    end = seg.index("}", start)
    return " ".join(seg[start:end].split())


def _dump_body(expr):
    model = loads(PREFIX + " assert constraint { " + expr + " } }")
    return _body(model.dump())


@pytest.mark.parametrize("expr", [
    "a xor b",
    "a or b",
    "a implies b",
    "a or b xor c",
    "a and b or c",
])
def test_loose_boolean_layers_keep_their_operand_class(expr):
    """XOR/OR/IMPLIES must not leak a foreign chain dict into the dump."""
    body = _dump_body(expr)
    assert "{'name'" not in body, body
    assert _OP_RE.findall(body) == _OP_RE.findall(expr)


def test_group_that_only_repeats_precedence_is_flattened():
    """`(A and B) xor (C and D)` — `and` already binds tighter than `xor`,
    so the parens are redundant and the chain carries the grouping."""
    expr = "(a == b and c == d) xor (e == f and g == h)"
    body = _dump_body(expr)
    assert "{'name'" not in body
    assert "language" not in body
    assert _OP_RE.findall(body) == _OP_RE.findall(expr)
    # and the flattened form re-parses to the same dump (fixed point)
    again = _dump_body(body)
    assert again == body


def test_group_that_decides_the_grouping_keeps_its_parens():
    """`(a or b) and c` cannot be expressed by the layer chain: the fallback
    must keep the parens AND the spaces."""
    body = _dump_body("(a or b) and c")
    assert body == "(a or b) and c"
    assert "(aorb)" not in body


def test_text_fallback_uses_source_text_not_token_glue():
    body = _dump_body("a and (b or c)")
    assert body == "a and (b or c)"
    assert "aand(" not in body


def test_expression_table_is_idempotent():
    table = [
        "a and b", "a xor b", "a or b", "a implies b",
        "a == b and c == d",
        "a == b and c == d xor e == f and g == h",
        "(a == b and c == d) xor (e == f and g == h)",
        "(a or b) and c", "a and (b or c)",
        "not a and b",
    ]
    for expr in table:
        first = _dump_body(expr)
        second = _dump_body(first)
        assert second == first, (expr, first, second)


@pytest.mark.skipif(not CORPUS.exists(), reason="SysML-v2-Release checkout not present")
def test_corpus_vehicle_variability_model_round_trips():
    """The reporting file: three xor-of-ands assert bodies."""
    source = CORPUS.read_text(encoding="utf-8")
    model = loads(source)
    first = model.dump()

    assert "language \"English\"" not in first      # no captured-text body
    assert _OP_RE.findall(first) == _OP_RE.findall(source)
    assert first.count("assert constraint") == source.count("assert constraint")

    model2, warns = parse(first)
    assert model2 is not None, warns
    assert model2.dump() == first


SI = pathlib.Path(
    "/home/jfox/proj/sysmlpy/src/sysmlpy/library/domain/Quantities and Units/SI.sysml")


@pytest.mark.skipif(not SI.exists(), reason="library checkout layout differs")
def test_dump_writes_nothing_to_stdout(capsys):
    """Operand-class probing is control flow, not a diagnostic: dumping a
    library full of `s ^ -1` unit expressions must not print anything."""
    with open(SI, encoding="utf-8") as fh:
        model = loads(fh.read())
    model.dump()
    assert capsys.readouterr().out == ""
