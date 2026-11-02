"""Issue #30: allocation usages and definitions keep their body members.

Before the fix the visitor hardcoded an empty ``DefinitionBody`` for
``allocationUsage`` and all three loaders assigned ``element.grammar``
directly instead of calling ``load_from_grammar`` — so every body member of
``allocate p to q { attribute note : String; }`` (and of
``allocation def AD { ... }``) was absent from both the public tree and the
dump, silently.

Layers pinned here: visitor dict → grammar object → public element children
→ dump → re-parse → dump.
"""

from sysmlpy import loads, load_grammar, parse


USAGE_BODY = """
package P {
  part def A; part def B;
  part p : A; part q : B;
  allocate p to q {
    attribute note : String;
    ref target = q;
  }
}
"""

DEF_BODY = """
package P {
  allocation def Alloc {
    attribute tag : String;
  }
}
"""

NESTED = """
package P {
  part def A; part def B;
  part p : A; part q : B;
  part def Other {
    allocate p to q {
      attribute inner : String;
    }
  }
}
"""


def _allocations(model):
    return [el for el in model.find() if type(el).__name__ == "Allocation"]


def _child_names(element):
    return [(type(c).__name__, getattr(c, "name", None)) for c in element.children]


def test_issue30_usage_body_members_reach_the_model():
    model = loads(USAGE_BODY)
    allocation = _allocations(model)[0]
    assert _child_names(allocation) == [("Attribute", "note"), ("Reference", "target")]
    # endpoints from #23 still read from the grammar
    assert allocation.source == ["p"] and allocation.target == ["q"]


def test_issue30_definition_body_members_reach_the_model():
    model = loads(DEF_BODY)
    allocation = _allocations(model)[0]
    assert allocation.name == "Alloc"
    assert _child_names(allocation) == [("Attribute", "tag")]


def test_issue30_nested_usage_body_members_reach_the_model():
    # allocation usage inside a part def body (Usage.load_from_grammar path)
    model = loads(NESTED)
    nested = [a for a in _allocations(model) if a.parent is not None
              and type(a.parent).__name__ == "Part"]
    assert len(nested) == 1
    assert _child_names(nested[0]) == [("Attribute", "inner")]


def test_issue30_visitor_dict_carries_the_body():
    # the dict layer must not hand back an empty DefinitionBody
    d = load_grammar(USAGE_BODY)

    def walk(node, out):
        if isinstance(node, dict):
            if node.get("name") == "AllocationUsage":
                out.append(node)
            for v in node.values():
                walk(v, out)
        elif isinstance(node, list):
            for v in node:
                walk(v, out)

    found = []
    walk(d, found)
    assert found, "AllocationUsage dict present"
    items = found[0]["body"]["body"]["ownedRelatedElement"]
    assert items, "body items survived the visitor"


def test_issue30_dump_keeps_bodies_and_re_parses():
    for src in (USAGE_BODY, DEF_BODY, NESTED):
        model = loads(src)
        first = model.dump()
        # the members are in the dumped text, not just the model
        assert "attribute note" in first or "attribute tag" in first or "attribute inner" in first
        # no double space before the body brace (AllocationUsage.dump join)
        assert "to q  {" not in first
        reparsed, issues = parse(first)
        assert reparsed is not None and not issues, issues
        assert reparsed.dump() == first, "dump must be a fixed point"


def test_issue30_empty_bodies_unchanged():
    src = """
package P {
  part def A; part def B; part p : A; part q : B;
  allocate p to q;
  allocation def Empty;
}
"""
    model = loads(src)
    assert [a.children for a in _allocations(model)] == [[], []]
    dumped = model.dump()
    assert "allocate p to q;" in dumped and "allocation def Empty;" in dumped
    reparsed, issues = parse(dumped)
    assert reparsed is not None and not issues, issues
    assert reparsed.dump() == dumped
