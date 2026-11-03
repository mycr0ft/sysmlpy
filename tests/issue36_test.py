"""Issue #36 — metadata applications in the interchange `@graph`.

Two shape decisions, both taken against what the implementations actually emit
(the OMG metamodel generated into SysML-v2-API-Services, OpenSysML's
`docs/reference/rdf-mapping.md`, and sysml-toolkit's INTEROP.md):

**D' — the metaclass.** An annotation's SysML metaclass is ``MetadataUsage``
(``MetadataUsage extends ItemUsage, MetadataFeature``), not the bare KerML
``MetadataFeature`` the exporter used to state. Consumers keyed on the SysML
metaclass could not find these nodes.

**B' — the link.** The annotation node carries ``annotatedElement`` pointing at
the element it annotates — the metaclass property, spelled the way both
implementations spell it — plus ``declaredKeyword`` for the sigil the author
wrote (``@`` body form, ``#`` prefix form). No new node type, no edge on the
anchor, nothing added to the identity space.

An annotation with an ``about`` clause names its own targets, so the derived
ownership edge is withheld there: the ``Annotation`` nodes already carry them.
"""

import copy

import pytest

from sysmlpy import loads
from sysmlpy.interchange import from_interchange, qn_registry, to_interchange

BODY = """package P {
  metadata def M { attribute w : Real; }
  part def X { @M { w = 1; } }
}"""

PREFIX = """package P {
  metadata def M;
  #M part def Y;
}"""

NESTED = """package P {
  metadata def M;
  part def Outer { part def Inner { @M { w = 2; } } }
}"""

ABOUT = """package P {
  metadata def M;
  part def A;
  part def B;
  metadata m : M about A, B;
}"""


def _graph(src, **kw):
    return to_interchange(src, **kw)["@graph"]


def _annotation_nodes(graph):
    return [n for n in graph if n.get("@type") == "MetadataUsage"]


def _anchors(src):
    """(annotation node, element node the edge names, by_id) for one model.

    ``qn_registry`` maps a qualified name to its **Identification** node, so the
    element is resolved as "the node whose subtree carries that Identification".
    """
    doc = to_interchange(src, stable_ids=True)
    graph = doc["@graph"]
    by_id = {n["@id"]: n for n in graph if "@id" in n}
    ann = _annotation_nodes(graph)[0]
    target = by_id[ann["annotatedElement"][0]["@id"]]
    return ann, target, by_id, qn_registry(doc)


def _declares(by_id, element_id, identification_id):
    """True when ``element_id``'s subtree contains that Identification node."""
    seen = set()

    def walk(node):
        if node.get("@id") in seen:
            return False
        seen.add(node.get("@id"))
        if node.get("@id") == identification_id:
            return True
        for v in node.values():
            if isinstance(v, dict) and v.get("@id") and walk(by_id[v["@id"]]):
                return True
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and item.get("@id") and \
                            walk(by_id[item["@id"]]):
                        return True
        return False

    return walk(by_id[element_id])


def test_body_annotation_states_metaclass_sigil_and_anchor():
    ann, target, by_id, registry = _anchors(BODY)
    assert ann["@type"] == "MetadataUsage"
    assert ann["declaredKeyword"] == "@"
    assert target["@type"] == "PartDefinition"
    assert _declares(by_id, target["@id"], registry["P.X"])


def test_prefix_annotation_states_the_hash_sigil():
    ann, target, by_id, registry = _anchors(PREFIX)
    assert ann["declaredKeyword"] == "#"
    assert target["@type"] == "PartDefinition"
    assert _declares(by_id, target["@id"], registry["P.Y"])


def test_nested_annotation_anchors_to_the_nearest_element():
    ann, target, by_id, registry = _anchors(NESTED)
    assert _declares(by_id, target["@id"], registry["P.Outer.Inner"])
    assert not _declares(by_id, target["@id"], registry["P.Outer"])


def test_about_clause_withholds_the_derived_edge():
    graph = _graph(ABOUT)
    ann = _annotation_nodes(graph)[0]
    assert "annotatedElement" not in ann
    assert ann["ownedRelationship_about"], "the about targets must stay in the graph"


def test_no_metadata_feature_type_survives_in_the_graph():
    for src in (BODY, PREFIX, NESTED):
        types = {n.get("@type") for n in _graph(src)}
        assert "MetadataFeature" not in types
        assert "MetadataUsage" in types


@pytest.mark.parametrize("src", [BODY, PREFIX, NESTED])
def test_annotations_survive_the_round_trip(src):
    model = loads(src)
    before = [(c.name, [(a.type_name, a.values) for a in c.annotations])
              for pkg in model.children
              for c in getattr(pkg, "children", []) or []
              if getattr(c, "annotations", None)]
    back = from_interchange(to_interchange(model))
    after = [(c.name, [(a.type_name, a.values) for a in c.annotations])
             for pkg in back.children
             for c in getattr(pkg, "children", []) or []
             if getattr(c, "annotations", None)]
    assert after == before
    assert back.dump() == model.dump()


def test_export_is_deterministic_and_ids_are_unchanged_by_the_shape_addition():
    src = "package P { metadata def M; part def Y { attribute z : Real; } }"
    annotated = src.replace("part def Y { attribute z : Real; }",
                            "part def Y { attribute z : Real; @M { w = 1; } }")
    plain = to_interchange(src, stable_ids=True)
    with_ann = to_interchange(annotated, stable_ids=True)
    # adding an annotation must not move any existing element's id
    plain_ids = {n["@id"] for n in plain["@graph"]}
    ann_ids = {n["@id"] for n in with_ann["@graph"]}
    assert plain_ids <= ann_ids
    # and the export stays deterministic
    assert to_interchange(annotated, stable_ids=True)["@graph"] == with_ann["@graph"]


def test_old_documents_still_import():
    """A document written before the shape change (MetadataFeature, no derived
    edge) must keep importing — the alias only applies to MetadataUsage."""
    doc = copy.deepcopy(to_interchange(BODY))
    for node in doc["@graph"]:
        if node.get("@type") == "MetadataUsage":
            node["@type"] = "MetadataFeature"
            node.pop("annotatedElement", None)
            node.pop("declaredKeyword", None)
    model = from_interchange(doc)
    anns = [(a.type_name, a.values) for pkg in model.children
            for c in getattr(pkg, "children", []) or []
            for a in (getattr(c, "annotations", []) or [])]
    assert anns == [("M", {"w": "1"})]


def test_explicit_terms_describe_the_new_properties():
    doc = to_interchange(BODY, explicit_terms=True)
    context = doc["@context"]
    for term in ("annotatedElement", "declaredKeyword", "MetadataUsage"):
        assert term in context
