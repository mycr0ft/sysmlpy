"""Issue #27 (decision): object-model identity for unnamed elements.

**Decision (2026-10-31, documented in docs/stable-identities.md §option D):**

* anonymous members keep ``name = None`` — no minted uuids of any kind;
  a uuid in ``name`` would (a) churn per parse (uuid4 status quo), and
  (b) serialise as declared content if it were position/content-derived
  (a name is a SysML slot, not an identity slot).
* durable identity comes from **UUIDv5 in the id slot**:
  ``sysmlpy.stable_ids(model)`` / ``element.stable_id`` derive
  content-addressed ids with the SAME keys the ``stable_ids=True``
  interchange export hashes. Declared (named) elements agree *exactly*
  with the exported ``@id`` (pinned below); anonymous members use the
  same scheme with the public-tree structural path (documented bound:
  the JSON flattener walks dict-tree wrapper nodes, so the strings
  differ while both stay stable under the same edit classes).
* the ``Model`` root keeps its documented per-parse uuid — it is not a
  member, is filtered by ``_MODEL_NAME_RE`` everywhere, and never
  serialises as content.
"""

import re

from sysmlpy import loads, stable_ids, to_interchange

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}"
                      r"-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _members(model):
    out = []

    def walk(el):
        if el is not model:
            out.append(el)
        for c in getattr(el, "children", None) or []:
            walk(c)
    walk(model)
    return out


def test_issue27_anonymous_members_keep_name_none():
    model = loads("""package P {
  part def A; part def B;
  part a : A { part p; }
  part b : B { part q; }
  connect a.p to b.q;
  verification def V { objective { verify Q; } }
  requirement def Q;
}""")
    names = [(type(c).__name__, c.name) for c in _members(model)]
    anonymous = [n for n in names if n[1] is None]
    # the connection and the verify member are anonymous — and STAY None
    assert ("Connection", None) in anonymous, names
    assert ("Verify", None) in anonymous, names
    # nothing in the tree carries a fresh uuid4 name any more
    uuid_names = [n for n in names if n[1] and _UUID_RE.match(str(n[1]))]
    assert uuid_names == [], uuid_names


def test_issue27_no_churn_across_parses():
    src = """package P {
  part def A; part def B;
  part a : A { part p; }
  part b : B { part q; }
  connect a.p to b.q;
}"""
    m1 = loads(src)
    m2 = loads(src)
    # per-parse uuid churn is gone: the only uuid left is the Model root
    assert _UUID_RE.match(str(m1.name)) and _UUID_RE.match(str(m2.name))
    member_names_1 = sorted(type(c).__name__ + "|" + str(c.name)
                            for c in _members(m1))
    member_names_2 = sorted(type(c).__name__ + "|" + str(c.name)
                            for c in _members(m2))
    assert member_names_1 == member_names_2
    # and the object-model ids agree across parses (content-addressed)
    by_name1 = {type(c).__name__ + "|" + str(c.name): stable_ids(m1)[c]
                for c in _members(m1) if c.name}
    by_name2 = {type(c).__name__ + "|" + str(c.name): stable_ids(m2)[c]
                for c in _members(m2) if c.name}
    assert by_name1 == by_name2


def test_issue27_named_ids_agree_with_interchange_export():
    model = loads("""package P {
  part def Engine {
    attribute power : ScalarValues::Real;
    ref fuel;
  }
  part car : Engine;
}""")
    ids = stable_ids(model)
    graph_ids = {n["@id"] for n in to_interchange(model, stable_ids=True)["@graph"]}
    for el, sid in ids.items():
        if getattr(el, "name", None):  # declared elements agree exactly
            assert sid in graph_ids, (el, sid)


def test_issue27_stable_id_property_matches_map():
    model = loads("""package P {
  part def Engine;
  part car : Engine { attribute mass = 100 [kg]; }
}""")
    ids = stable_ids(model)
    car = model.find_one("car")
    mass = model.find_one("mass")
    assert car.stable_id == ids[car]
    assert mass.stable_id == ids[mass]


def test_issue27_same_name_siblings_distinct():
    model = loads("""package P {
  part def Engine;
  part def Engine;
  part a : Engine; part b : Engine;
}""")
    ids = stable_ids(model)
    engines = [c for c in model.children[0].children
               if type(c).__name__ == "Part" and c.name == "Engine"]
    parts = [c for c in model.children[0].children
             if type(c).__name__ == "Part" and c.name in ("a", "b")]
    assert len(engines) == 2 and len(parts) == 2
    all_ids = [ids[c] for c in engines] + [ids[c] for c in parts]
    assert len(set(all_ids)) == 4  # every pair distinct


def test_issue27_anonymous_ids_deterministic_per_shape():
    model = loads("""package P {
  part def A; part def B;
  part a : A { part p; }
  part b : B { part q; }
  connect a.p to b.q;
}""")
    ids = stable_ids(model)
    conn = [c for c in model.children[0].children
            if type(c).__name__ == "Connection"][0]
    # the same-shape re-parse yields the same id for the connection and
    # every other member (deterministic derivation)
    m2 = loads(model.dump())
    ids2 = stable_ids(m2)
    c2 = [c for c in m2.children[0].children
          if type(c).__name__ == "Connection"][0]
    assert ids[conn] == ids2[c2]
    # and every named member too
    for el in _members(model):
        if not getattr(el, "name", None):
            continue
        m2_el = [c for c in _members(m2)
                 if type(c).__name__ == type(el).__name__
                 and c.name == el.name]
        assert m2_el and ids[el] == ids2[m2_el[0]], el