#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SysML v2 JSON interchange for sysmlpy (v0.63.0 — Adoption Roadmap Goal 3).

Exports a loaded model to a JSON-LD-style *partition interchange*
document in the style of the SysML v2 spec's JSON exchange format, and
imports such a document back into a live :class:`~sysmlpy.definition.Model`
— losslessly, with deterministic element identifiers.

Document shape::

    {
      "@context": {"@version": 1.1, "@vocab": "..."},
      "@id": "id:root",
      "@graph": [
        {"@id": "id:pkg-1", "@type": "Package", "declaredName": "P",
         "ownedRelationship": [{"@id": "id:rel-1"}]},
        {"@id": "id:rel-1", "@type": "OwningMembership",
         "ownedRelatedElement": {"@id": "id:part-1"}},
        {"@id": "id:part-1", "@type": "PartDefinition", ...},
        ...
      ]
    }

Design notes:

- **Flat graph.** Every element (packages, relationships, declarations,
  bodies, ...) appears exactly once in ``@graph``; structural properties
  reference other elements by ``{"@id": ...}``.  Scalars (``declaredName``,
  ``declaredShortName``, keywords, ...) are kept inline.  ``null`` values
  are preserved so the export/rebuild is shape-exact.
- **``@type``** is the SysML v2 abstract-syntax metaclass name, exactly
  as the parser's internal dictionary uses it (``Package``,
  ``OwningMembership``, ``PartDefinition``, ...).
- **Deterministic ``@id``s.**  Element identifiers are ``uuid5`` derived
  from the element's position in the model tree, so exporting the same
  model twice yields byte-identical JSON (diff-friendly, ties into
  semantic model diff — roadmap Goal 8).
- **Round-trip.**  ``from_interchange(to_interchange(model))`` rebuilds
  the internal dictionary shape-exactly and constructs a live ``Model``
  through the same grammar-class path as a fresh parse
  (``Model._load_definition``).

The ``@vocab`` IRI space is sysmlpy-owned.  No OMG-published JSON-LD
context file exists to bundle (checked against the SysML v2 pilot
implementation, which carries none), so v0.85.0 makes the vocabulary
configurable and adds an explicit per-property term-definition builder
(:func:`build_jsonld_context`): documents can carry full
``<vocabulary>#<property>`` IRIs for every property and metaclass, in
the OMG JSON-LD vocabulary style, and import side normalizes IRI-keyed
properties back to local names.

Public surface:

- :func:`to_interchange` — ``Model`` or SysML text → interchange dict
- :func:`from_interchange` — interchange dict / JSON text → ``Model``
- :func:`interchange_to_json_text` / convenience formatting helpers
- :func:`build_jsonld_context` — explicit property/metaclass IRI map
- :func:`INTERCHANGE_VOCABULARY` — default vocabulary IRI (constant)
"""

from __future__ import annotations

import json as _json
import re as _re
import uuid as _uuid
from collections import Counter as _Counter
from pathlib import Path as _Path

__all__ = [
    "INTERCHANGE_CONTEXT",
    "INTERCHANGE_VOCABULARY",
    "INTERCHANGE_NAMESPACE",
    "STABLE_NAMESPACE",
    "to_interchange",
    "from_interchange",
    "interchange_to_json_text",
    "reconcile_ids",
    "build_jsonld_context",
]

#: JSON-LD context emitted with every document.  Property names are the
#: SysML v2 abstract-syntax property names used by the parser; the
#: vocabulary IRI is sysmlpy-owned.  Pass ``vocabulary=...`` to
#: :func:`to_interchange` / :func:`build_jsonld_context` to emit IRIs
#: under a different (e.g. OMG-published) vocabulary instead.
INTERCHANGE_CONTEXT = {
    "@version": 1.1,
    "@vocab": "https://github.com/mycr0ft/sysmlpy/interchange#",
}

#: Default vocabulary IRI every property/metaclass term resolves
#: against (same space as :data:`INTERCHANGE_CONTEXT` ``@vocab``).
INTERCHANGE_VOCABULARY = INTERCHANGE_CONTEXT["@vocab"]

#: UUID namespace for deterministic element identifiers.
INTERCHANGE_NAMESPACE = _uuid.uuid5(
    _uuid.NAMESPACE_URL, "https://github.com/mycr0ft/sysmlpy/interchange"
)

# SysML metaclass -> internal KerML metaclass, on import (issue #36).
_IMPORT_TYPE_ALIASES = {"MetadataUsage": "MetadataFeature"}
# Properties that an export DERIVES and an import must not replay as data.
_DERIVED_ON_IMPORT = {"MetadataUsage": ("annotatedElement",)}

_REF_KEYS = ("@id", "@type")


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


def _child_id(parent_id: str, key: str, index: int) -> str:
    """Deterministic identifier for the child at ``parent.key[index]``."""
    return "sysml:" + str(
        _uuid.uuid5(INTERCHANGE_NAMESPACE, f"{parent_id}|{key}|{index}")
    )


# ---------------------------------------------------------------------------
# stable (content-addressed) identifiers — L2 idempotency
# ---------------------------------------------------------------------------

#: UUID namespace for content-addressed ``stable_ids=True`` identifiers
#: (distinct from :data:`INTERCHANGE_NAMESPACE` so the two schemes never
#: collide even in theory).
STABLE_NAMESPACE = _uuid.uuid5(
    _uuid.NAMESPACE_URL,
    "https://github.com/mycr0ft/sysmlpy/interchange/stable-ids",
)


def _identification_of(node: dict):
    """The ``Identification`` node declared *by* this element, if any.

    The parser models names as ``Identification`` dicts nested under
    ``declaration``/``definition`` nodes; usages nest theirs under
    ``declaration.declaration.identification``.  A recursive search
    finds any shape without hard-coding the path — but it must not
    descend through the containment edges (``ownedRelatedElement``,
    ``body``): a wrapper (``PackageMember``, ``DefinitionElement``…)
    merely *contains* named elements and must not claim their names.
    Descending into them would let the root claim every name in the
    model, corrupting every identity path.
    """
    if not isinstance(node, dict):
        return None
    if node.get("name") == "Identification":
        return node
    for k, v in node.items():
        if k in ("ownedRelatedElement", "body"):
            continue  # containment edges: names below belong to children
        if isinstance(v, list):
            for item in v:
                found = _identification_of(item)
                if found is not None:
                    return found
        elif isinstance(v, dict):
            found = _identification_of(v)
            if found is not None:
                return found
    return None


class _StableIdAssigner:
    """Content-addressed ``@id`` assignment over the visitor-dict tree.

    An element's id hashes its *identity path*: the chain of declared
    names from the root down to the nearest declared ancestor, plus the
    element's own declared name (if any) and ``@type``.  Concretely:

    - Named element: ``uuid5(STABLE_NAMESPACE, qn + "|" + type)``
      where ``qn`` is the dot-joined declared names of the element and
      all its declared ancestors (e.g. ``P.Engine.power``).
    - Unnamed element below a declared ancestor: hashes the anchor QN,
      the structural path from that ancestor (dictionary keys +
      sibling indexes), and the ``@type`` — so it moves only if the
      structure *between* it and its named ancestor changes, never when
      unrelated siblings elsewhere shift indexes.
    - Root: hashes the tree path under the fixed ``"root"`` anchor.

    **Explicit ids (Phase 2b):** a ``doc /* @id: … */`` comment on the
    element overrides derivation entirely — "never re-mint over an
    explicit id".  Harvested from the public element tree (`.doc`)
    before flattening and keyed by declared QN path
    (:func:`_harvest_doc_ids`); duplicate claims of one id raise.

    Same-name sibling collisions (two ``part def Engine`` under one
    parent) share a base hash; the occurrence index among content-key
    siblings is appended so ids stay unique.  Elements in a collision
    group shift when a group sibling is inserted before them — the
    documented degradation for L2 (see docs/stable-identities.md).
    """

    def __init__(self, explicit_ids: "dict | None" = None):
        #: base content-key -> next occurrence index
        self._occurrence: dict = {}
        #: declared QN path (dot-joined str) -> explicit id from
        #: ``doc /* @id: … */`` comments (Phase 2b — overrides
        #: derivation entirely)
        self._explicit: dict = dict(explicit_ids or {})
        #: explicit id value -> adopting declared QN path (duplicate
        #: claims of the same id from different elements raise)
        self._id_owner: dict = {}
        #: ('adopted', qn_str, struct_path) — one node of each identity
        #: path adopts; wrapper re-visits keep derived ids
        self._adopted: set = set()
        #: deduped declared QN path -> stable @id (Identification
        #: nodes only; consumed by :func:`qn_registry` — the P3
        #: Vee-join side table)
        self._qn_registry: dict = {}
        #: registry occurrence counter for same-name sibling groups
        self._registry_occurrence: dict = {}

    def id_for(self, node: dict, qn_path: tuple, struct_path: tuple) -> str:
        ident = _identification_of(node) if isinstance(node, dict) else None
        own_name = (ident or {}).get("declaredName")
        type_name = node.get("name") if isinstance(node, dict) else None
        # Explicit-id lookup: match the SHORT declared path — qn_path
        # accumulates the element's own name once per nested
        # declaration/identification wrapper level (PackageDeclaration →
        # DefinitionDeclaration → …), so 'P' arrives as 'P',
        # 'P.P', … 'P.P.P'.  The harvested doc-id key ('P') therefore
        # matches a *suffix-deduped* qn: dedupe consecutive repeats and
        # collapse to the minimal unique path.
        qn_str = _dedupe_repeat_tail(qn_path, own_name)
        if qn_str and own_name and qn_str in self._explicit and \
                qn_str.rsplit(".", 1)[-1] == own_name and \
                type_name == "Identification":
            # Adoption: the node carrying the Identification whose
            # DEDUPED path equals the harvest key adopts the explicit
            # id ('Car' → 'TR', 'Car.Engine' → 'EN').  Repeat-tail
            # collapsing means Identification 'Car' arrives as
            # 'Car.Car'/'Car.Car.Car' while 'Car' alone is the Package
            # node — both collapse to the key, so gate on the node
            # being an Identification (Package and PackageDeclaration
            # keep derived ids — probe2j, Phase 2b build).
            #
            # Uniqueness is enforced on the ID VALUE, not per QN key:
            # two different elements claiming the same explicit id
            # ('P'→X and 'Q'→X) collide here (probe2l) — a hard export
            # error, not a silent duplicate.
            explicit = self._explicit[qn_str]
            prior_owner = self._id_owner.get(explicit)
            if prior_owner is None:
                self._id_owner[explicit] = qn_str
                # doc-carried explicit ids ride the registry too
                self._qn_registry[qn_str] = explicit
                return explicit
            if prior_owner != qn_str:
                raise ValueError(
                    f"Duplicate explicit @id claim: {explicit} declared "
                    f"by both '{prior_owner}' and '{qn_str}'")
            return explicit
            # prior_owner == qn_str: re-visit of the same element —
            # fall through to derived id below (element ids stay unique
            # in the graph).
        else:
            explicit = None
        if explicit:
            return explicit
        if own_name:
            qn = "|".join(qn_path + (own_name,))
            key = f"{qn}|{type_name}"
            # Record the deduped declared path for the QN registry
            # (:func:`qn_registry` — the P3 Vee-join maps SysML
            # qualified names to interchange @ids).  Only meaningful
            # for Identification nodes (the declared element);
            # wrappers (PackageDeclaration / DefinitionDeclaration)
            # carry derived ids and are skipped.
            if type_name == "Identification":
                deduped = _dedupe_repeat_tail(qn_path, own_name)
            else:
                deduped = None
        else:
            deduped = None
            key = "root" if not qn_path and not struct_path else (
                "|".join(qn_path) + "||" + _struct_text(struct_path)
                + f"|{type_name}"
            )
        n = self._occurrence.get(key, 0)
        self._occurrence[key] = n + 1
        if n:
            key = f"{key}|#{n}"
        node_id = "sysml:" + str(_uuid.uuid5(STABLE_NAMESPACE, key))
        if deduped and type_name == "Identification" and own_name:
            # v0.101.0: the registry records the ACTUAL node id for every
            # occurrence.  The first entry keys the deduped QN plainly;
            # same-name sibling groups key `deduped#<index>` (index over
            # the registry-dup counter, offset by the first occurrence
            # which already took the plain key).  This branch previously
            # stored a `...` placeholder for duplicate-name groups.
            if deduped not in self._qn_registry:
                self._qn_registry[deduped] = node_id
            else:
                dn = self._registry_occurrence.get(deduped, 0)
                self._registry_occurrence[deduped] = dn + 1
                self._qn_registry[f"{deduped}#{dn + 1}"] = node_id
        return node_id


def _dedupe_repeat_tail(qn_path: tuple, own_name: "str | None") -> str:
    """Minimal declared-name path for explicit-id lookup.

    The visitor dict nests wrappers (``PackageDeclaration``,
    ``DefinitionDeclaration``, ``Identification``) that each repeat the
    element's own declaredName, so the flattener delivers
    ``('P','P','P')``-style paths.  Dedupe *consecutive repeats* and
    take the result — 'P.P.P' and 'P' both reduce to 'P', 'P.Engine'
    stays 'P.Engine'.  (Regular id derivation is untouched: it uses
    ``qn_path`` + separators directly and never collides because the
    hash keys include the structural path for unnamed nodes.)
    """
    seq = qn_path + ((own_name,) if own_name else ())
    out: list = []
    for seg in seq:
        if seg and (not out or out[-1] != seg):
            out.append(seg)
    # collapse nested repeats of the SAME name chain ('P','P' ← level
    # nesting) while keeping genuinely distinct segments
    return ".".join(out)


_ID_IN_DOC = _re.compile(r"@id:\s*([^\s*/]+)")


def _harvest_doc_ids(model) -> "dict | None":
    """Harvest explicit ids from ``doc /* @id: … */`` comments.

    Walks the *public* element tree (``.doc`` is populated on every
    element kind) and maps each element's declared qualified-name path
    to the id claimed in its doc comment.  Keys match the assigner's
    identity paths (both are chains of declared names; the Model
    root's per-parse uuid name is skipped).  Returns ``None`` when no
    element claims an id, so the flag stays inert on plain models.
    """
    found: dict = {}

    def _walk(el, stack: tuple):
        name = getattr(el, "doc_name", None)
        if name is None:
            name = getattr(el, "name", None)
        if name is not None and not _MODEL_NAME_RE.match(str(name)):
            stack = stack + (str(name),)
        doc = getattr(el, "doc", None)
        if doc:
            m = _ID_IN_DOC.search(str(doc))
            if m:
                qn = " ".join(stack) if False else ".".join(stack)
                found[qn] = m.group(1).strip()
            elif str(doc).strip().startswith("@id:"):
                m2 = _re.match(r"@id:\s*([^\s*/]+)", str(doc).strip())
                if m2 and stack:
                    found[".".join(stack)] = m2.group(1).strip()
        for child in getattr(el, "children", []):
            _walk(child, stack)

    _walk(model, ())
    return found or None


_MODEL_NAME_RE = _re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}"
                             r"-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _struct_text(struct_path: tuple) -> str:
    return ">".join(f"{key}:{i}" for key, i in struct_path)


def stable_ids(model):
    """Object-model mirror of the stable interchange ``@id`` scheme.

    Returns **{element: "sysml:<uuid5>"}** covering every member of
    *model* (the Model root itself is not a member and is not mapped).

    Derivation mirrors :class:`_StableIdAssigner` (the ``stable_ids=True``
    exporter) key-for-key:

    - **declared (named) elements** join through the exporter's own QN
      registry (``#qn_registry``): their id is the ``@id`` of the
      element's Identification node in
      ``to_interchange(model, stable_ids=True)`` — exact agreement with
      the export by construction, including nested members and
      same-name sibling groups (v0.101.0 fixed the registry's
      duplicate-name entries, which stored a `...` placeholder instead
      of the second occurrence's id).
    - **same-name sibling groups** take an occurrence index exactly like
      the exporter (per identical key), so plain reparse and sibling
      insertion elsewhere behave the same on both sides.
    - **anonymous members** (``name is None`` — the issue #27 change:
      no member carries a uuid4 name any more) hash the nearest declared
      ancestor path plus the structural path (``children:<index>``
      chains from the root) — the object-model analogue of the exporter's
      dict-tree structural path. Documented bound: the JSON flattener
      walks the rebuilt dict tree (wrapper levels included), so an
      anonymous member's *string* differs between JSON and object model —
      both are content-addressed and stable under the same edit classes;
      declared-element agreement is the load-bearing contract.
    - the per-parse ``Model`` root uuid is skipped (it never serializes
      as member content).

    Typical use::

        ids = sysmlpy.stable_ids(model)          # {element: "sysml:…"}
        ids[part]                                # → "sysml:…"

    Convenience: every element exposes ``.stable_id`` (walks to its root
    and reads this map — O(n) per access; iterate ``stable_ids(model)``
    directly for bulk work).

    See ``docs/stable-identities.md`` (option D, "object-model mirror")
    for the decision record (issue #27)."""

    mapping = {}
    occurrence = {}

    # Named elements join through the exporter's own QN registry (every
    # registry id IS the node @id in the stable export — exact agreement).
    # v0.101.0 also fixed the registry's duplicate-name entries, which
    # stored a `...` placeholder instead of the second occurrence's id.
    registry = qn_registry(to_interchange(model, stable_ids=True))

    def _type_name(el):
        g = getattr(el, "grammar", None)
        if g is not None:
            return type(g).__name__
        return type(el).__name__

    def _walk(el, qn_path, struct_path):
        name = getattr(el, "name", None)
        # uuid-looking names (the Model root's per-parse uuid) never count
        # as declared names — same skip the doc-id harvest applies
        named = bool(name and not _MODEL_NAME_RE.match(str(name)))
        tname = _type_name(el)
        if named:
            qn = ".".join(qn_path + (str(name),))
            n = occurrence.get(qn, 0)
            occurrence[qn] = n + 1
            key = qn if n == 0 else f"{qn}#{n}"
            if key in registry:
                mapping[el] = registry[key]
            else:
                # defensive fallback: derive in the graph-node form
                raw = "|".join(qn_path + (str(name),)) + "|" + tname
                mapping[el] = ("sysml:"
                               + str(_uuid.uuid5(STABLE_NAMESPACE, raw)))
            child_qn = qn_path + (str(name),)
        else:
            if el is not model:
                key = ("|".join(qn_path) + "||" + _struct_text(struct_path)
                       + f"|{tname}")
                n = occurrence.get(key, 0)
                occurrence[key] = n + 1
                if n:
                    key = f"{key}|#{n}"
                mapping[el] = "sysml:" + str(_uuid.uuid5(STABLE_NAMESPACE, key))
            child_qn = qn_path
        for i, ch in enumerate(getattr(el, "children", None) or []):
            _walk(ch, child_qn, struct_path + (("children", i),))

    _walk(model, (), ())
    return mapping


def stable_id_for(model, element):
    """Single-element convenience: the stable id of *element* in *model*.

    Computes (and would recompute, per call) the full
    :func:`stable_ids` map — bulk callers should hold the map and read
    it. Walks up the parent chain if *element* is a nested child.
    """
    root = element
    seen = 0
    while getattr(root, "parent", None) is not None and seen < 64:
        root = root.parent
        seen += 1
    if root is not model and getattr(model, "parent", None) is not None:
        root = model
    return stable_ids(root).get(element)


# Metaclasses whose nodes are SysML *elements* — the things an annotation can be
# attached to.  In this exporter's vocabulary the KerML cores ``Definition`` and
# ``Usage`` are reached as children of a ``<Kind>Definition`` / ``<Kind>Usage``
# and are NOT elements themselves, so they are excluded; every membership, body,
# body item and ``*Element`` wrapper is a structural node, not an element.
_ELEMENT_EXACT = {"Package"}
_NON_ELEMENT_EXACT = {"Definition", "Usage"}


def _is_element_node_name(name) -> bool:
    if not isinstance(name, str) or not name:
        return False
    if name in _ELEMENT_EXACT:
        return True
    if name in _NON_ELEMENT_EXACT:
        return False
    return name.endswith("Definition") or name.endswith("Usage")


def _flatten(node: dict, parent_id: str, key: str, index: int,
             graph: list, assigner: "_StableIdAssigner | None" = None,
             parent_qn: tuple = (), parent_struct: tuple = (),
             anchor_id: "str | None" = None) -> str:
    """Recursively flatten a visitor-dict node into the graph.

    With ``assigner=None`` (default) ids are position-derived
    (``_child_id``).  With an :class:`_StableIdAssigner`, ids are
    content-addressed: named elements hash their qualified-name path,
    unnamed elements hash the nearest named anchor plus the structural
    path from it — see :class:`_StableIdAssigner`.

    Returns the ``@id`` assigned to this node.
    """
    if assigner is not None:
        struct_path = parent_struct + ((key, index),)
        elem_id = assigner.id_for(node, parent_qn, struct_path)
        ident = _identification_of(node)
        own_name = (ident or {}).get("declaredName")
        child_qn = parent_qn + ((own_name,) if own_name else ())
        child_struct = struct_path
    else:
        elem_id = _child_id(parent_id, key, index)
        child_qn = ()
        child_struct = ()
    # An annotation is owned by the nearest enclosing ELEMENT (its body, or its
    # prefix for `#M part def Y;`); that element is its `annotatedElement`
    # (issue #36 — the shape OpenSysML and sysml-toolkit emit).
    child_anchor = elem_id if _is_element_node_name(node.get("name")) else anchor_id

    elem = {"@id": elem_id, "@type": node.get("name")}
    for k, v in node.items():
        if k == "name":
            continue  # captured as @type
        elem[k] = _flatten_value(v, elem_id, k, graph,
                                 assigner=assigner, parent_qn=child_qn,
                                 parent_struct=child_struct,
                                 anchor_id=child_anchor)
    if node.get("name") == "MetadataFeature":
        # The SysML metaclass of an annotation is MetadataUsage (it IS a
        # MetadataFeature: `MetadataUsage extends ItemUsage, MetadataFeature`),
        # so pilot-shaped consumers find it under the name they expect.
        elem["@type"] = "MetadataUsage"
        # An `about` clause names its own targets, so the derived ownership edge
        # would state something false — the Annotation nodes carry those
        # targets instead (issue #36).
        has_about = bool(node.get("ownedRelationship_about"))
        if anchor_id and not has_about:
            elem["annotatedElement"] = [{"@id": anchor_id}]
    graph.append(elem)
    return elem_id


def _flatten_value(v, elem_id: str, key: str, graph: list,
                   assigner: "_StableIdAssigner | None" = None,
                   parent_qn: tuple = (), parent_struct: tuple = (),
                   anchor_id: "str | None" = None):
    """Flatten one property value: dicts become @id refs, scalars inline."""
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, dict):
        return {"@id": _flatten(v, elem_id, key, 0, graph,
                                assigner=assigner, parent_qn=parent_qn,
                                parent_struct=parent_struct,
                                anchor_id=anchor_id)}
    if isinstance(v, list):
        out = []
        for i, item in enumerate(v):
            if isinstance(item, dict):
                out.append({"@id": _flatten(item, elem_id, key, i, graph,
                                            assigner=assigner,
                                            parent_qn=parent_qn,
                                            parent_struct=parent_struct,
                                            anchor_id=anchor_id)})
            else:
                out.append(item)
        return out
    # Unknown value type — keep it inline (best effort).
    return v


def build_jsonld_context(document=None, *, vocabulary=None,
                         properties=None, types=None):
    """Build an explicit JSON-LD context mapping names to IRIs.

    Every SysML v2 property name and metaclass ``@type`` value maps to
    ``<vocabulary>#<name>`` — the OMG JSON-LD vocabulary convention —
    so the document is self-describing for RDF / JSON-LD tooling
    without relying on ``@vocab`` alone.

    Parameters
    ----------
    document : dict, optional
        Derive the property and type name lists from an interchange
        document (its ``@graph`` is scanned).
    vocabulary : str, optional
        Vocabulary IRI base (default :data:`INTERCHANGE_VOCABULARY`).
        Point this at an OMG-published SysML vocabulary IRI when one
        is available; no normative OMG context file currently exists
        to bundle, so the mapping stays configurable by design.
    properties, types : iterable of str, optional
        Explicit name lists (override ``document`` derivation).

    Returns
    -------
    dict
        ``{"@version": 1.1, "@vocab": ..., "prop": {"@id": ...}, ...}``
    """
    vocab = (vocabulary or INTERCHANGE_VOCABULARY).rstrip("/#")
    if properties is None or types is None:
        doc_props, doc_types = _document_terms(document)
        if properties is None:
            properties = sorted(doc_props)
        if types is None:
            types = sorted(doc_types)
    context = {
        "@version": 1.1,
        "@vocab": vocab + "#",
    }
    for prop in properties:
        if not str(prop).startswith("@"):
            context[str(prop)] = {"@id": f"{vocab}#{prop}"}
    for type_name in types:
        context[str(type_name)] = {"@id": f"{vocab}#{type_name}"}
    return context


def _document_terms(document):
    """Property names and ``@type`` values used inside a document."""
    props = set()
    types = set()
    if not isinstance(document, dict):
        return props, types
    for elem in document.get("@graph", []) or []:
        if not isinstance(elem, dict):
            continue
        type_name = elem.get("@type")
        if isinstance(type_name, str):
            types.add(type_name)
        for key, value in elem.items():
            if key.startswith("@"):
                continue
            props.add(key)
            # nested structures may carry further property names
            _collect_terms(value, props)
    return props, types


def _collect_terms(value, props):
    if isinstance(value, dict):
        for k, v in value.items():
            if not str(k).startswith("@"):
                props.add(k)
            _collect_terms(v, props)
    elif isinstance(value, list):
        for item in value:
            _collect_terms(item, props)


def _extract_properties(source):
    """Derive property/type names for term generation from a source."""
    try:
        document = to_interchange(source)
    except Exception:
        return None, None
    props, types = _document_terms(document)
    return props, types


def to_interchange(source, *, vocabulary=None, explicit_terms=False,
                   stable_ids=False, reconcile_with=None, doc_ids=False):
    """Export a model to the SysML v2 JSON interchange representation.

    Parameters
    ----------
    source : Model or str
        Either a loaded model (``sysmlpy.loads(...)`` / ``load_files(...)``
        / programmatically built) or SysML v2 source text (parsed fresh).
    vocabulary : str, optional
        Vocabulary IRI for the ``@vocab`` mapping (default
        :data:`INTERCHANGE_VOCABULARY`).
    explicit_terms : bool
        When true, the ``@context`` additionally carries explicit
        ``property → <vocabulary>#property`` term definitions for
        every property and metaclass in the document (see
        :func:`build_jsonld_context`).
    stable_ids : bool
        When true, ``@id``s are **content-addressed** (L2 idempotency):
        named elements hash their qualified-name path and ``@type``,
        unnamed elements hash the nearest named ancestor plus the
        structural path from it.  Inserting or reordering unrelated
        siblings elsewhere in the document then leaves every
        untouched element's id unchanged — with the default
        position-derived ids those ids all shift.  Same-name sibling
        groups (two ``part def Engine`` under one parent) are
        disambiguated by occurrence index; ids inside such a group do
        shift on group-local insertion.  See
        ``docs/stable-identities.md`` for the full analysis.
    reconcile_with : dict or str, optional
        A previous export (document dict or JSON text of one) to adopt
        ids from — see :func:`reconcile_ids`.  Implies
        ``stable_ids=True`` (reconciled re-exports must replay the
        same id scheme the registry was written with).  The typical
        workflow keeps the *previous* export file as the registry::

            if Path("model.json").exists():
                doc = to_interchange(model, reconcile_with="model.json")
            else:
                doc = to_interchange(model, stable_ids=True)
            Path("model.json").write_text(interchange_to_json_text(doc))

    doc_ids : bool
        When true (implies ``stable_ids=True``), honor **explicit ids**
        carried in the model's own text: a ``doc /* @id: <id> */``
        comment on any element fixes that element's ``@id`` for its
        declared qualified-name lifetime — derivation never overrides
        it, and it survives *any* edit (ancestor renames, re-nesting,
        moving between files) because it is written into the source.
        Two elements claiming the same id raise ``ValueError``.  This
        is the source-carried identity mechanism (Phase 2b,
        ``docs/stable-identities.md`` option C).

    Returns
    -------
    dict
        JSON-LD-style document: ``@context``, root ``@id`` and a flat
        ``@graph`` of elements.
    """
    from sysmlpy.definition import Model

    if isinstance(source, Model):
        # Export from the *raw parser dict*, not the grammar classes'
        # ``get_definition()`` output: the class serialization normalizes
        # the tree (adds ``ownedRelationship`` keys, unwraps
        # ``OccurrenceUsageElement``), which changes how classes
        # re-dispatch on import (e.g. satisfy wrappers were lost).
        # ``dump()`` is the canonical serialization — re-parsing it gives
        # the same dictionary shape a fresh parse produces.
        try:
            text = source.dump()
        except ValueError:
            text = ""  # empty model (dump raises "no elements to output")
        if not text.strip():
            root_dict = {
                "name": "PackageBodyElement",
                "ownedRelationship": [],
            }
        else:
            from sysmlpy import load_grammar
            root_dict = load_grammar(text)
    elif isinstance(source, str):
        from sysmlpy import load_grammar
        root_dict = load_grammar(source)
    else:
        raise TypeError(
            "to_interchange expects a Model or SysML text, "
            f"not {source.__class__.__name__}"
        )

    graph: list = []
    explicit = None
    if doc_ids:
        # Harvest explicit ids from the model's own doc comments.  Needs
        # the public element tree — a re-parsed Model (source was str /
        # dump text) is walked the same as a passed-in Model.
        model_obj = source if hasattr(source, "children") else None
        if model_obj is None:
            try:
                model_obj = source  # caller passed a Model-like object
            except Exception:
                model_obj = None
        if model_obj is not None:
            explicit = _harvest_doc_ids(model_obj)
    if doc_ids and not (stable_ids or reconcile_with):
        stable_ids = True  # explicit ids ride the stable-id machinery
    assigner = (_StableIdAssigner(explicit_ids=explicit)
                if (stable_ids or reconcile_with) else None)
    root_id = _flatten(root_dict, "root", "ownedRelationship", 0, graph,
                       assigner=assigner)
    context = dict(INTERCHANGE_CONTEXT)
    if vocabulary:
        context["@vocab"] = vocabulary.rstrip("/#") + "#"
    if explicit_terms:
        context = build_jsonld_context(
            {"@graph": graph}, vocabulary=vocabulary
        )
    document = {
        "@context": context,
        "@id": root_id,
        "@graph": graph,
    }
    if reconcile_with is not None:
        document = reconcile_ids(document, reconcile_with)
    document["#qn_registry"] = dict(assigner._qn_registry) if assigner else {}
    return document


def qn_registry(document: dict) -> dict:
    """Extract the qualified-name -> @id side table from an export.

    Keyed by the DEDUPED declared qualified-name path
    (``SaturnV.Engine.thrust``) — exactly the keys doc-id harvesting
    and element navigation use, so callers can join a SysML model's
    named elements to their stable interchange ``@id``s without
    re-deriving hash chains.  The mapping is captured at export time
    (Identification nodes only; unnamed wrapper nodes are not
    declared elements and carry no registry entry).

    The side table rides under the ``"#qn_registry"`` key of the same
    document ``to_interchange`` returns (non-standard key, stripped by
    ``interchange_to_json_text``'s consumers that filter on ``@``-
    prefixed keys; keep it out of any byte-comparison assertions that
    pin historic formats — those must slice the graph and context
    only).

    Returns
    -------
    dict
        ``{ "SaturnV.Engine.thrust": "sysml:<uuid5>", ... }`` — empty
        when the export was position-id (``stable_ids=False``): the
        position scheme has no QN identity to expose.
    """
    reg = document.get("#qn_registry")
    return dict(reg) if isinstance(reg, dict) else {}


# ---------------------------------------------------------------------------
# id registry reconciliation — L3 identity across edits (Phase 2 sidecar)
# ---------------------------------------------------------------------------


def _remap_refs(value, remap: dict):
    """Rewrite every ``{"@id": old}`` ref to ``{"@id": new}``.  Top-level
    element ids are rewritten by :func:`reconcile_ids` directly; this
    walks nested property values (references, chains) so adopted ids
    are consistent everywhere the document is rebuilt from."""
    if isinstance(value, dict):
        if set(value.keys()) == {"@id"}:
            new_id = remap.get(value["@id"])
            if new_id is not None:
                value["@id"] = new_id
            return
        for v in value.values():
            _remap_refs(v, remap)
    elif isinstance(value, list):
        for item in value:
            _remap_refs(item, remap)


def reconcile_ids(document: dict, registry) -> dict:
    """Adopt element ids from a previous interchange export (the registry).

    The registry is a previously exported document (``to_interchange``
    output, as dict or JSON text) whose ``@graph`` maps ``@id`` to
    ``(declaredName, @type)``.  Every element of ``document`` whose
    ``(declaredName, @type)`` matches **exactly one** registry entry —
    and exactly one same-key element in ``document`` — inherits the
    registry's ``@id`` instead of its freshly derived one.  This is the
    mechanism that keeps ids stable across edits that re-mint derived
    ids (ancestor renames, re-nesting): identity follows the declared
    name wherever the name survives the edit.

    Matching is deliberately **injective**:

    - the key must be unique on BOTH sides — when the model grows a
      second ``PartDefinition`` while the registry has one, neither is
      matched (a naive many-to-one adoption produced duplicate ids in
      every rename-plus-insert scenario during the design spike);
    - an old id already adopted by an earlier element is never adopted
      again (first match wins in registry order);
    - unmatched elements keep their freshly derived ids and become new
      registry entries when the document is written back out.

    Intended workflow (the export file doubles as the registry)::

        document = to_interchange(model, stable_ids=True)
        if Path("model.json").exists():
            document = reconcile_ids(document, Path("model.json"))
        Path("model.json").write_text(interchange_to_json_text(document))

    Parameters
    ----------
    document : dict
        A freshly exported document (``to_interchange`` output).
    registry : dict or str
        The previous export: a document dict or a JSON string (the
        text form loads the sidecar file directly).

    Returns
    -------
    dict
        ``document`` with adopted ids (modified in place and returned).
    """
    if isinstance(registry, (_Path, str)):
        # Accept a filesystem path to a registry file (including
        # ``Path`` objects), OR the previous export as JSON text /
        # document dict.  A str that names an existing, plausibly
        # small file loads from disk; anything else is JSON text.
        # (A str is only treated as a path if its length is a sane
        # filename length — JSON documents can be megabytes.)
        if isinstance(registry, _Path) or (
                isinstance(registry, str) and len(registry) < 4097
                and "\n" not in registry and _Path(registry).exists()):
            registry = _Path(registry).read_text(encoding="utf-8-sig")
        registry = _json.loads(registry)
    if not isinstance(registry, dict):
        raise ValueError(
            "registry must be an interchange document dict or JSON "
            f"string, got {type(registry).__name__}")
    old_graph = registry.get("@graph")
    new_graph = document.get("@graph")
    if not isinstance(old_graph, list) or not isinstance(new_graph, list):
        raise ValueError("both documents need an @graph array")

    def _key(e):
        return (e.get("declaredName"), e.get("@type"))

    old_counts = _Counter(_key(e) for e in old_graph)
    new_counts = _Counter(_key(e) for e in new_graph)
    by_key: dict = {}
    for e in old_graph:
        k = _key(e)
        # unique on BOTH sides — injective matching (see docstring)
        if k in old_counts and old_counts[k] == 1 and new_counts.get(k) == 1 \
                and k not in by_key:
            by_key[k] = e["@id"]
    used: set = set()

    # id re-map for refs: a matched element's *derived* id (assigned
    # during this export) must yield to the adopted registry id in
    # EVERY nested ``{"@id": ...}`` reference too — element ids are
    # only the top level; typed-by references, target refs and child
    # chains all point at the derived ids and would dangle after a
    # top-level-only rewrite.
    remap: dict = {}
    for e in new_graph:
        k = _key(e)
        old_id = by_key.get(k)
        if old_id is not None and old_id not in used:
            used.add(old_id)
            derived_id = e["@id"]
            e["@id"] = old_id
            remap[derived_id] = old_id

    if remap:
        for e in new_graph:
            _remap_refs(e, remap)

    # QN side table rides the same adoption: keys carry the NEW
    # declared paths (the document's own names), values adopt the
    # registry's old ids — remapped exactly like every other ref, so
    # the registry stays graph-accurate after adoption (probe: the
    # rename scenario — 'Ares.Engine' must map to doc1's Engine id).
    side = document.get("#qn_registry")
    if isinstance(side, dict) and remap:
        for k in list(side):
            new_id = remap.get(side[k])
            if new_id is not None:
                side[k] = new_id
    return document


def interchange_to_json_text(document: dict, *, indent: int = 2) -> str:
    """Serialize an interchange document to a JSON string."""
    return _json.dumps(document, indent=indent)


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------


def _is_ref(v) -> bool:
    return isinstance(v, dict) and set(v.keys()) == {"@id"}


def _rebuild(ref: dict, by_id: dict, stack: tuple = ()) -> dict:
    """Rebuild the internal-dict node referenced by ``ref``."""
    elem_id = ref["@id"]
    if elem_id in stack:
        raise ValueError(f"Cyclic element reference detected: {elem_id}")
    elem = by_id.get(elem_id)
    if elem is None:
        raise ValueError(f"Interchange document references unknown @id: {elem_id}")
    type_name = elem.get("@type")
    # `MetadataUsage` is the SysML metaclass an export states for an annotation;
    # internally the same node is a KerML MetadataFeature, and its
    # `annotatedElement` edge is DERIVED from ownership (issue #36), so neither
    # may reach the rebuild dict.
    derived = set()
    if type_name in _IMPORT_TYPE_ALIASES:
        type_name = _IMPORT_TYPE_ALIASES[type_name]
        derived = set(_DERIVED_ON_IMPORT.get(elem.get("@type"), ()))
    node = {"name": type_name}
    for k, v in elem.items():
        if k in _REF_KEYS or k in derived:
            continue
        node[k] = _rebuild_value(v, by_id, stack + (elem_id,))
    return node


def _rebuild_value(v, by_id: dict, stack: tuple):
    if _is_ref(v):
        return _rebuild(v, by_id, stack)
    if isinstance(v, list):
        return [
            _rebuild(i, by_id, stack) if _is_ref(i) else i for i in v
        ]
    return v


def from_interchange(data, *, vocabulary=None) -> "Model":
    """Import a SysML v2 JSON interchange document into a live Model.

    Parameters
    ----------
    data : dict or str
        The interchange document (as produced by :func:`to_interchange`),
        either as a dict or as a JSON string.  Documents whose property
        keys are written as full IRIs (``<vocab>#<property>`` — see
        :func:`build_jsonld_context`) are normalized automatically when
        the IRI prefix matches the document's ``@vocab`` or the
        ``vocabulary`` argument.
    vocabulary : str, optional
        Vocabulary IRI to recognize when normalizing IRI-keyed
        properties (in addition to the document's own ``@vocab``).

    Returns
    -------
    Model
    """
    from sysmlpy.definition import Model

    if isinstance(data, str):
        data = _json.loads(data)
    if not isinstance(data, dict):
        raise ValueError(
            "Interchange document must be a dict or JSON string, "
            f"got {type(data).__name__}"
        )
    graph = data.get("@graph")
    if not isinstance(graph, list):
        raise ValueError("Interchange document has no @graph array")

    # Normalize IRI-keyed property names (external JSON-LD documents
    # write <vocab>#<prop>; the internal dict uses bare names).
    vocabs = _context_vocabularies(data, vocabulary)
    if vocabs:
        graph = [_normalize_keys(elem, vocabs) for elem in graph]
        data = {**data, "@graph": graph}

    root_ref = data.get("@id")
    if root_ref is None:
        # Fall back to the first element that is not referenced by others.
        referenced = {
            v["@id"]
            for elem in graph
            for v in _walk_refs(elem)
            if isinstance(v, dict) and "@id" in v
        }
        roots = [e["@id"] for e in graph if isinstance(e, dict) and "@id" in e and e["@id"] not in referenced]
        if not roots:
            raise ValueError("Cannot determine root element of document")
        root_ref = roots[0]
    # @id values themselves can be IRI-keyed in external documents
    root_ref = _strip_vocabulary(root_ref, vocabs)

    by_id = {}
    for elem in graph:
        if not isinstance(elem, dict) or "@id" not in elem:
            raise ValueError("Every @graph element needs an @id")
        by_id[elem["@id"]] = elem

    root = _rebuild({"@id": root_ref}, by_id)
    relationships = root.get("ownedRelationship")
    if relationships is None:
        raise ValueError(
            "Root element carries no ownedRelationship — not a model document"
        )

    model = Model()
    return model._load_definition(relationships)


def _context_vocabularies(data, extra=None):
    """Vocabulary IRIs to normalize against (document @vocab + extras)."""
    vocabs = set()
    context = data.get("@context")
    if isinstance(context, dict):
        vocab = context.get("@vocab")
        if isinstance(vocab, str) and "#" in vocab:
            vocabs.add(vocab)
    if isinstance(extra, str):
        vocabs.add(extra.rstrip("/#") + "#")
    return vocabs


def _normalize_keys(elem, vocabs):
    """Strip known vocabulary prefixes from property/type keys."""
    if isinstance(elem, dict):
        out = {}
        for key, value in elem.items():
            if key == "@type" and isinstance(value, str):
                out[key] = _strip_vocabulary(value, vocabs)
            else:
                out[_strip_vocabulary(key, vocabs)] = \
                    _normalize_keys(value, vocabs)
        return out
    if isinstance(elem, list):
        return [_normalize_keys(item, vocabs) for item in elem]
    return elem


def _strip_vocabulary(key, vocabs):
    if isinstance(key, str) and "#" in key:
        for vocab in vocabs:
            if key.startswith(vocab):
                return key[len(vocab):]
    return key


def _walk_refs(elem: dict):
    """Yield every ``{"@id": ...}`` ref reachable from *elem*'s properties."""
    for v in elem.values():
        yield from _walk_refs_value(v)


def _walk_refs_value(v):
    if _is_ref(v):
        yield v
    elif isinstance(v, list):
        for item in v:
            yield from _walk_refs_value(item)
    elif isinstance(v, dict):
        for item in v.values():
            yield from _walk_refs_value(item)