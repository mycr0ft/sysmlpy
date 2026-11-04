"""Issue #41 — a succession vanished when its body had other members.

`part p { first a then b; }` kept the succession; add one sibling and it was
gone from both the element tree and the dump:

    part p { attribute x : Real; first a then b; }

The parse tree and the visitor dict both carried it.  The loss was in the
loader: no child element was built for a `Succession`, and
`Usage._ensure_body` rebuilds a parsed body from `self.children` — so the
member was dropped from the serialization.  (`Alone`, the body had no other
item, so the rebuild had nothing to compare against and the grammar body
survived by accident.)

The fix models a succession the way `Binding` already is: a non-occurrence
usage kept in the element tree, so the body rebuild keeps it and structural
renderers can read its ends.
"""

import pytest

from sysmlpy import loads, parse

ALONE = "package P { part p { first a then b; } }"
MIXED = "package P { part p { attribute x : Real; first a then b; } }"
BEFORE = "package P { part p { first a then b; attribute x : Real; } }"
TWO = "package P { part p { attribute x : Real; first a then b; first b then c; } }"
KEYWORD = "package P { part p { attribute x : Real; succession first a then b; } }"
CHAINED = "package P { part p { attribute x : Real; first a.b then c.d; } }"


def _owner(src):
    return loads(src).children[0].children[0]


def _successions(src):
    return [c for c in _owner(src).children if type(c).__name__ == "Succession"]


@pytest.mark.parametrize("src", [ALONE, MIXED, BEFORE, TWO, KEYWORD, CHAINED])
def test_succession_survives_a_mixed_body(src):
    model = loads(src)
    dump = model.dump()
    assert "first" in dump
    again, warns = parse(dump)
    assert again is not None, warns
    assert again.dump() == dump


def test_succession_is_an_element_child():
    """No silent loss: the succession is in the tree, not only in the text."""
    assert len(_successions(ALONE)) == 1
    assert len(_successions(MIXED)) == 1
    assert len(_successions(BEFORE)) == 1
    assert len(_successions(TWO)) == 2


def test_succession_ends_are_readable():
    (succ,) = _successions(MIXED)
    assert (succ.source, succ.target) == ("a", "b")
    (chained,) = _successions(CHAINED)
    assert (chained.source, chained.target) == ("a.b", "c.d")


def test_succession_parent_and_order():
    owner = _owner(TWO)
    kinds = [type(c).__name__ for c in owner.children]
    assert kinds == ["Attribute", "Succession", "Succession"]
    succs = [c for c in owner.children if type(c).__name__ == "Succession"]
    assert all(s.parent is owner for s in succs)
    assert [(s.source, s.target) for s in succs] == [("a", "b"), ("b", "c")]


def test_succession_keyword_is_preserved():
    assert "succession first a then b;" in loads(KEYWORD).dump()


def test_no_silent_drop_in_a_mixed_body():
    """Every member of the source body appears in the tree and in the dump."""
    src = """package P {
  part p {
    attribute x : Real;
    first a then b;
    ref r : Real;
    item it;
  }
}"""
    model = loads(src)
    dump = model.dump()
    names = [type(c).__name__ for c in _owner(src).children]
    assert "Succession" in names
    for marker in ("attribute x : Real;", "first a then b;", "ref r : Real;", "item it;"):
        assert marker in dump, marker
    again, warns = parse(dump)
    assert again is not None, warns
    assert again.dump() == dump
