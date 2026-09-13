# -*- coding: utf-8 -*-
"""ReqIF interchange bridge (v0.90.0 — requirements interchange).

Two directions:

**Import** — a ReqIF file (real-world flavors: ReqIF Studio, DOORS,
Polarion, Eclipse RMF, Sparx EA) becomes sysmlpy requirements:

    from sysmlpy import loads, reqif_import
    text = reqif_import("requirements.reqif")   # SysML v2 text
    model = loads(text)                         # requirements with hierarchy
    model.dump()                                # ...or keep as text

Each ReqIF SpecObject ("Requirement Type") becomes a nested
``requirement``; the SpecHierarchy tree becomes requirement ownership;
``ReqIF.Text`` becomes the requirement's ``doc`` comment (XHTML
stripped); other attributes (``ReqIF.ForeignID`` etc.) are folded into
the doc comment so nothing is lost.

**Export** — requirements in a model to ReqIF XML:

    from sysmlpy import loads, reqif_export
    model = loads(sysml_text)
    reqif_export(model, "requirements.reqif")

Hierarchy comes from requirement ownership; ``doc`` comments become
``ReqIF.Text``.

Requires the optional ``reqif`` package (``pip install reqif``), the
strictdoc-project ReqIF parser/unparser — chosen after a parser bake-off
on real-world ReqIF flavors (it parsed 7/7 anonymized vendor samples;
pyreqif failed 2/7 and is unmaintained since 2021).
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

__all__ = [
    "reqif_import",
    "reqif_import_model",
    "reqif_export",
    "ReqIFImportError",
    "ReqIFExportError",
]


class ReqIFImportError(ValueError):
    """The ReqIF document could not be parsed into sysmlpy requirements."""


class ReqIFExportError(ValueError):
    """The model could not be exported to ReqIF."""


# ---------------------------------------------------------------------------
# shared text helpers
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_xhtml(value: str) -> str:
    """Extract readable text from an XHTML fragment (ReqIF.Text values)."""
    if not value:
        return ""
    text = _TAG_RE.sub(" ", value)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _slug(name: str, used: set, fallback_prefix: str = "req") -> str:
    """Make a unique SysML-safe identifier from a display name."""
    base = re.sub(r"[^A-Za-z0-9_]", "_", name or "").strip("_") or fallback_prefix
    if not base[0].isalpha() and base[0] != "_":
        base = "r_" + base
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}_{n}"
        n += 1
    used.add(candidate)
    return candidate


def _require_reqif_lib():
    try:
        from reqif.parser import ReqIFParser  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ReqIFImportError(
            "ReqIF support needs the optional 'reqif' package "
            "(pip install reqif)"
        ) from exc
    from reqif.parser import ReqIFParser

    return ReqIFParser


# ---------------------------------------------------------------------------
# import: ReqIF -> SysML v2 text
# ---------------------------------------------------------------------------


def _attribute_lookup(spec_types: Iterable[Any]) -> Dict[str, str]:
    """Map attribute-definition ref -> long name, across all spec types."""
    names: Dict[str, str] = {}
    for st in spec_types or []:
        for a in getattr(st, "attribute_definitions", None) or []:
            names[a.identifier] = a.long_name or ""
    return names


def _attr_value(spec_object: Any, names: Dict[str, str], long_name: str) -> str:
    """First attribute value whose definition's long name matches."""
    for a in getattr(spec_object, "attributes", None) or []:
        if names.get(a.definition_ref) == long_name:
            v = a.value
            if isinstance(v, bytes):
                v = v.decode("utf-8", "replace")
            return v or ""
    return ""


def reqif_import(path: str) -> str:
    """Import a ReqIF file as SysML v2 text.

    Parameters
    ----------
    path : str
        Path to the ReqIF (or RIF) XML file.

    Returns
    -------
    str
        SysML v2 text with one ``requirement`` per SpecObject, nested by
        SpecHierarchy.  Load it with :func:`sysmlpy.loads` or write it to
        a ``.sysml`` file.

    Raises
    ------
    ReqIFImportError
        If the file cannot be parsed or contains no importable content.
    """
    ReqIFParser = _require_reqif_lib()
    try:
        bundle = ReqIFParser.parse(str(path))
    except Exception as exc:
        raise ReqIFImportError(f"could not parse ReqIF file: {exc}") from exc

    try:
        content = bundle.core_content.req_if_content
    except AttributeError as exc:
        raise ReqIFImportError("ReqIF file has no CORE-CONTENT") from exc

    spec_objects = {so.identifier: so for so in content.spec_objects or []}
    names = _attribute_lookup(content.spec_types or [])

    lines: List[str] = ["package ImportedRequirements {"]
    emitted = 0
    used_names: set = set()

    def render(spec_children: Iterable[Any], depth: int) -> None:
        nonlocal emitted
        pad = "    " * (depth + 1)
        for node in spec_children or []:
            so = getattr(node, "spec_object", None)
            so_obj = spec_objects.get(so)
            emitted += 1
            chapter = ""
            text = ""
            foreign = ""
            if so_obj is not None:
                chapter = _strip_xhtml(
                    _attr_value(so_obj, names, "ReqIF.ChapterName")
                )
                text = _strip_xhtml(_attr_value(so_obj, names, "ReqIF.Text"))
                foreign = _strip_xhtml(
                    _attr_value(so_obj, names, "ReqIF.ForeignID")
                )
            name = _slug(chapter or foreign or "", used_names)
            lines.append(pad + f"requirement {name} {{")
            if foreign:
                lines.append(pad + f"    doc /* ForeignID: {foreign} */")
            label = chapter or text
            if label:
                lines.append(pad + f"    doc /* {label} */")
            render(getattr(node, "children", None) or [], depth + 1)
            lines.append(pad + "}")

    for spec in content.specifications or []:
        render(getattr(spec, "children", None) or [], 0)

    lines.append("}")
    if emitted == 0:
        raise ReqIFImportError("no requirements found in the ReqIF file")
    return "\n".join(lines) + "\n"


def reqif_import_model(path: str):
    """Import a ReqIF file directly as a loaded sysmlpy Model."""
    import sysmlpy as _sysmlpy

    return _sysmlpy.loads(reqif_import(path))


# ---------------------------------------------------------------------------
# export: sysmlpy Model -> ReqIF XML
# ---------------------------------------------------------------------------


def _collect_requirements(model: Any) -> List[Tuple[int, Any]]:
    """Requirements as (depth, object) in pre-order, from any model level."""
    out: List[Tuple[int, Any]] = []

    def walk(obj: Any, depth: int) -> None:
        for child in obj:
            cls = child.__class__.__name__
            if cls == "Requirement":
                out.append((depth, child))
            if cls in ("Requirement", "Package"):
                walk(child, depth + 1)

    for pkg in model:
        walk(pkg, 0)
    return out


def _parent_of(obj: Any) -> Optional[Any]:
    return getattr(obj, "parent", None)


def reqif_export(model: Any, path: str) -> str:
    """Export a model's requirements to ReqIF 1.0 XML.

    Parameters
    ----------
    model : Model
        A loaded model (``sysmlpy.loads(...)`` / ``load_files(...)``).
    path : str
        Destination ``.reqif`` file path.

    Returns
    -------
    str
        The destination path (for chaining).

    Raises
    ------
    ReqIFExportError
        If the model has no requirements or the ReqIF library is missing.
    """
    _require_reqif_lib()

    requirements = _collect_requirements(model)
    if not requirements:
        raise ReqIFExportError("the model contains no requirements to export")

    import importlib

    # ---- spec object type: one XHTML attribute "ReqIF.Text" ---------------
    reqif_spec_object_type = importlib.import_module(
        "reqif.models.reqif_spec_object_type"
    )
    reqif_spec_object = importlib.import_module("reqif.models.reqif_spec_object")
    reqif_data_type = importlib.import_module("reqif.models.reqif_data_type")
    reqif_spec_hierarchy = importlib.import_module(
        "reqif.models.reqif_spec_hierarchy"
    )
    reqif_specification = importlib.import_module("reqif.models.reqif_specification")
    reqif_reqif_header = importlib.import_module("reqif.models.reqif_reqif_header")
    reqif_namespace_info = importlib.import_module(
        "reqif.models.reqif_namespace_info"
    )
    reqif_core_content = importlib.import_module("reqif.models.reqif_core_content")
    reqif_req_if_content = importlib.import_module(
        "reqif.models.reqif_req_if_content"
    )
    reqif_bundle = importlib.import_module("reqif.reqif_bundle")
    reqif_object_lookup = importlib.import_module("reqif.object_lookup")
    reqif_unparser = importlib.import_module("reqif.unparser")

    type_id = "_sysmlpy-requirement-type"
    datatype_id = "_sysmlpy-xhtml-datatype"
    attr_id = "_sysmlpy-text-attribute"

    text_datatype = reqif_data_type.ReqIFDataTypeDefinitionXHTML(
        identifier=datatype_id,
        long_name="XHTML",
    )
    text_attribute = reqif_spec_object_type.SpecAttributeDefinition(
        attribute_type=reqif_spec_object_type.SpecObjectAttributeType.XHTML,
        identifier=attr_id,
        datatype_definition=datatype_id,
        long_name="ReqIF.Text",
        editable="true",
    )
    spec_type = reqif_spec_object_type.ReqIFSpecObjectType(
        identifier=type_id,
        long_name="sysmlpy Requirement",
        attribute_definitions=[text_attribute],
    )

    # ---- spec objects -----------------------------------------------------
    spec_objects = []
    spec_object_ref_by_id_obj: Dict[int, str] = {}
    for index, (_, req) in enumerate(requirements, start=1):
        ref = f"_sysmlpy-req-{index:04d}"
        spec_object_ref_by_id_obj[id(req)] = ref
        doc = getattr(req, "doc", None) or ""
        value = f"<xhtml:div>{html.escape(doc)}</xhtml:div>" if doc else (
            "<xhtml:div></xhtml:div>"
        )
        attribute = reqif_spec_object.SpecObjectAttribute(
            attribute_type=reqif_spec_object_type.SpecObjectAttributeType.XHTML,
            definition_ref=attr_id,
            value=value,
        )
        spec_objects.append(
            reqif_spec_object.ReqIFSpecObject.create(
                identifier=ref,
                spec_object_type=type_id,
                attributes=[attribute],
            )
        )

    # ---- hierarchy: requirement ownership nesting --------------------------
    nodes_by_id_obj: Dict[int, Any] = {}
    for index, (_, req) in enumerate(requirements, start=1):
        node = reqif_spec_hierarchy.ReqIFSpecHierarchy(
            identifier=f"_sysmlpy-hier-{index:04d}",
            spec_object=spec_object_ref_by_id_obj[id(req)],
            level=1,  # hierarchy levels are 1-based in the ReqIF unparser
            children=[],
        )
        nodes_by_id_obj[id(req)] = node
    roots = []
    for depth, req in requirements:
        node = nodes_by_id_obj[id(req)]
        parent = _parent_of(req)
        if (
            parent is not None
            and parent.__class__.__name__ == "Requirement"
            and id(parent) in nodes_by_id_obj
        ):
            nodes_by_id_obj[id(parent)].children.append(node)
        else:
            roots.append(node)

    # ---- specification + bundle --------------------------------------------
    specification = reqif_specification.ReqIFSpecification(
        identifier="_sysmlpy-specification",
        long_name="sysmlpy requirements",
        children=list(roots),
    )

    data_type_lookup = {datatype_id: text_datatype}
    spec_type_lookup = {type_id: spec_type}
    spec_object_lookup = {so.identifier: so for so in spec_objects}

    content = reqif_req_if_content.ReqIFReqIFContent(
        data_types=[text_datatype],
        spec_types=[spec_type],
        spec_objects=spec_objects,
        spec_relations=None,
        specifications=[specification],
        spec_relation_groups=None,
    )
    core_content = reqif_core_content.ReqIFCoreContent(req_if_content=content)
    namespace_info = reqif_namespace_info.ReqIFNamespaceInfo(
        original_reqif_tag_dump=None,
        doctype_is_present=False,
        encoding="UTF-8",
        namespace="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd",
        configuration=None,
        namespace_id=None,
        namespace_xhtml="http://www.w3.org/1999/xhtml",
        schema_namespace=None,
        schema_location=None,
        language=None,
    )
    header = reqif_reqif_header.ReqIFReqIFHeader(
        identifier="_sysmlpy-header",
        creation_time=None,
        repository_id=None,
        req_if_tool_id="sysmlpy",
        req_if_version="1.0",
        source_tool_id="sysmlpy",
        title="sysmlpy requirements export",
    )
    lookup = reqif_object_lookup.ReqIFObjectLookup(
        data_types_lookup=data_type_lookup,
        spec_types_lookup=spec_type_lookup,
        spec_objects_lookup=spec_object_lookup,
        spec_relations_parent_lookup={},
    )
    bundle = reqif_bundle.ReqIFBundle(
        namespace_info=namespace_info,
        req_if_header=header,
        core_content=core_content,
        tool_extensions_tag_exists=False,
        lookup=lookup,
        exceptions=[],
    )

    xml_text = reqif_unparser.ReqIFUnparser.unparse(bundle)
    with open(path, "w", encoding="utf-8") as stream:
        stream.write(xml_text if xml_text.endswith("\n") else xml_text + "\n")
    return path