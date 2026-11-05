# -*- coding: utf-8 -*-
"""Issue #42 — metadata bodies: applications survive, values are structured.

Before this, `@M { w = z; }` disappeared from `dump()` while `@M { w = 1; }`
survived — the annotation lived on ``element.annotations`` (issue #24) but the
dump is generated from the grammar tree, which had no member for it, and the
body's values were only ever kept as text.  Three things are pinned here:

1. every application reaches the model, whatever its value's form;
2. the dump states it back, in the form the author used (`@`, `#`, `metadata`);
3. the interchange graph carries each body feature as a `ReferenceUsage` with a
   `FeatureValue` and an expression tree, so `M.w` is readable without
   re-parsing a string.
"""

import pytest

import sysmlpy
from sysmlpy.interchange import from_interchange, to_interchange

SRC_REFERENCE = """package P {
  metadata def M { attribute w : Real; }
  part def X { attribute z : Real; @M { w = z; } }
}"""

SRC_LITERAL = """package P {
  metadata def M { attribute w : Real; attribute u : Real; }
  part def X { @M { w = 1; u = 2.5; } }
}"""

SRC_CHAIN = """package P {
  metadata def M { attribute w : Real; }
  part def X { @M { w = a.b; } }
}"""

SRC_ARITH = """package P {
  metadata def M { attribute w : Real; }
  part def X { attribute z : Real; @M { w = z + 1; } }
}"""

SRC_EMPTY = """package P {
  metadata def M { }
  part def X { @M; }
}"""

SRC_HASH = """package P {
  metadata def M { }
  part def X { #M; }
}"""

SRC_NAMED = """package P {
  metadata def M { attribute w : Real; }
  part def X { metadata app : M { w = 2; } }
}"""

SRC_USAGE_BODY = """package P {
  metadata def M { attribute w : Real; }
  part def X { part p { @M { w = 1; } } }
}"""

SRC_ABOUT = """package P {
  metadata def M { }
  part def X;
  part def Y { @M about X; }
}"""


def _first(model, name):
    for child in model.children[0].children:
        if child.name == name:
            return child
    raise AssertionError(f"no element {name}")


def _round_trips(src):
    """loads → dump → loads → dump is a fixed point."""
    first = sysmlpy.loads(src).dump()
    second = sysmlpy.loads(first).dump()
    assert first == second, f"not a fixed point:\n{first}\n---\n{second}"
    return first


# ---------------------------------------------------------------------------
# the model keeps the application
# ---------------------------------------------------------------------------


def test_reference_valued_annotation_reaches_the_model():
    """The reporter's case: `w = z;` is a feature reference, not a literal."""
    model = sysmlpy.loads(SRC_REFERENCE)
    x = _first(model, "X")
    assert len(x.annotations) == 1
    annotation = x.annotations[0]
    assert annotation.type_name == "M"
    assert annotation.values == {"w": "z"}


def test_reference_value_keeps_a_structured_expression():
    """`values` stays the author's text; `value_expressions` is the structure."""
    model = sysmlpy.loads(SRC_REFERENCE)
    annotation = _first(model, "X").annotations[0]
    assert "w" in annotation.value_expressions
    expression = annotation.value_expressions["w"]
    assert expression["name"] == "ValuePart"
    assert expression["ownedRelationship"][0]["name"] == "FeatureValue"


@pytest.mark.parametrize("src", [SRC_REFERENCE, SRC_LITERAL, SRC_CHAIN,
                                 SRC_ARITH, SRC_EMPTY, SRC_HASH, SRC_NAMED,
                                 SRC_USAGE_BODY, SRC_ABOUT])
def test_every_application_round_trips(src):
    _round_trips(src)


# ---------------------------------------------------------------------------
# the dump states it back
# ---------------------------------------------------------------------------


def test_reference_annotation_survives_the_dump():
    text = _round_trips(SRC_REFERENCE)
    assert "@M {w=z;}" in text


def test_literal_values_survive_the_dump():
    text = _round_trips(SRC_LITERAL)
    assert "@M {w=1;u=2.5;}" in text


def test_arithmetic_value_survives_the_dump():
    text = _round_trips(SRC_ARITH)
    assert "@M {w=z+1;}" in text


def test_empty_body_annotation_is_not_duplicated():
    """The parsed body already carries `@M;` — injecting it again printed twice."""
    text = _round_trips(SRC_EMPTY)
    assert text.count("@M") == 1
    assert "@ M" not in text, "sigil must bind to the type"


def test_hash_form_survives():
    text = _round_trips(SRC_HASH)
    assert "#M;" in text


def test_metadata_keyword_form_survives():
    text = _round_trips(SRC_NAMED)
    assert "metadata app : M {w=2;}" in text


def test_annotation_inside_a_nested_usage_body():
    text = _round_trips(SRC_USAGE_BODY)
    assert "@M {w=1;}" in text


def test_about_clause_survives():
    text = _round_trips(SRC_ABOUT)
    assert "@M about X;" in text


# ---------------------------------------------------------------------------
# the graph carries structured values
# ---------------------------------------------------------------------------


def test_graph_carries_body_features_as_reference_usages():
    """OpenSysML shape: `ReferenceUsage` with `sysml:value` (not a text blob)."""
    model = sysmlpy.loads(SRC_ARITH)
    document = to_interchange(model, stable_ids=True)
    by_id = {node["@id"]: node for node in document["@graph"]}

    annotations = [n for n in document["@graph"]
                   if n.get("@type") == "MetadataUsage"]
    assert annotations, "the annotation is in the graph"
    annotation = annotations[0]
    assert annotation["bodyFeatures"], "body members are nodes"

    feature = by_id[annotation["bodyFeatures"][0]["@id"]]
    assert feature["@type"] == "ReferenceUsage"
    assert feature["declaredName"] == "w"
    assert feature["value"] == "z+1"

    value = by_id[feature["featureValue"]["@id"]]
    assert value["@type"] == "FeatureValue"
    expression = by_id[value["ownedRelatedElement"]["@id"]]
    assert expression["@type"] == "OwnedExpression"
    assert "expression" in expression


def test_graph_still_states_the_annotation_edge_and_sigil():
    model = sysmlpy.loads(SRC_LITERAL)
    document = to_interchange(model, stable_ids=True)
    annotation = [n for n in document["@graph"]
                  if n.get("@type") == "MetadataUsage"][0]
    assert annotation["declaredKeyword"] == "@"
    assert annotation["annotatedElement"], "anchor edge from issue #36"


def test_graph_import_round_trip_is_unchanged():
    model = sysmlpy.loads(SRC_ARITH)
    document = to_interchange(model, stable_ids=True)
    rebuilt = from_interchange(document)
    assert rebuilt.dump() == model.dump()
