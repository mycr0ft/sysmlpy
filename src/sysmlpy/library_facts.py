#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Library-wide symbol facts for the analyzer (issue #34).

The resolver needs to answer, for the *shipped* library: "does namespace N
declare or re-export member M?"  Building that answer per namespace (the earlier
`library_namespace_table` approach) was both slow — 248 s cold, because each
table resolved its own imports recursively — and wrong for facades: `ISQ` owns
only a few declarations and re-exports the rest through twelve `public import X::*`
lines, so `ISQ::time` looked undefined.

This module builds the answer once, the way the two implementations that do this
well build it:

* **OpenSysML** parses every library file, registers them in one library-wide
  index, then runs `ExpandWildcardImports()` — a purge/derive fixpoint over the
  importers until re-exports settle ("a facade package re-exports what another
  library package declares").
* **The OMG release** ships the same information precomputed as the
  `sysml.library.xmi.implied` variant, where implied relationships — including
  import-derived membership — are materialized so consumers never derive them.

Both persist *derived* data, not the model: the OMG's plain XMI is 25 MB and its
implied variant 120 MB, whereas OpenSysML caches only per-symbol facts and
re-parses.  We follow OpenSysML: facts are names and structure, no declarations
and no scopes.

Cache key = library content digest + set digest + build id + format version,
so a stale record is never found (a miss) rather than invalidated — again
OpenSysML's recipe (see their `libs/cache.go` and `buildid.go`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

FACTS_VERSION = 1

#: Environment variable naming the cache directory.  The DFA cache's variable
#: (`SYSMLPY_DFA_CACHE`) names a *directory* too, but mixing the two would make
#: one cache's "off" switch disable the other, so this one is separate.
CACHE_ENV = "SYSMLPY_LIBRARY_CACHE"

# Keys whose subtrees belong to a member's own declaration.  A member's nested
# body is NOT searched: its declarations belong to the nested element.
_DECL_KEYS = ("declaration", "definition", "usage", "identification", "prefix",
              "specialization", "fcspecialization")

# Member kinds we index.  A body member is a dict whose ``name`` is one of these
# (the visitor's metaclass names); anything else (memberships, elements,
# wrappers) is traversed for nested members instead.
_MEMBER_KINDS = frozenset({
    "Package", "PartDefinition", "PartUsage", "ItemDefinition", "ItemUsage",
    "AttributeDefinition", "AttributeUsage", "PortDefinition", "PortUsage",
    "ActionDefinition", "ActionUsage", "StateDefinition", "StateUsage",
    "CalculationDefinition", "CalculationUsage", "ConstraintDefinition",
    "ConstraintUsage", "RequirementDefinition", "RequirementUsage",
    "InterfaceDefinition", "InterfaceUsage", "ConnectionDefinition",
    "ConnectionUsage", "FlowDefinition", "FlowUsage", "AllocationDefinition",
    "AllocationUsage", "MetadataDefinition", "MetadataUsage", "MetadataFeature",
    "EnumerationDefinition", "EnumerationUsage", "EnumeratedValue",
    "ViewDefinition", "ViewUsage", "ViewpointDefinition", "ViewpointUsage",
    "RenderingDefinition", "RenderingUsage", "ConcernDefinition", "ConcernUsage",
    "UseCaseDefinition", "UseCaseUsage", "VerificationCaseDefinition",
    "VerificationCaseUsage", "AnalysisCaseDefinition", "AnalysisCaseUsage",
    "CaseDefinition", "CaseUsage", "ReferenceUsage", "DefaultReferenceUsage",
    "VariantReference", "BindingConnector", "Succession", "IndividualDefinition",
    "IndividualUsage", "OccurrenceDefinition", "OccurrenceUsage",
    "StructureDefinition", "StructureUsage", "BehaviorDefinition",
    "BehaviorUsage", "AssociationDefinition", "AssociationUsage",
    "ClassDefinition", "ClassUsage", "DataTypeDefinition", "DataTypeUsage",
    "FunctionDefinition", "FunctionUsage", "PredicateDefinition",
    "PredicateUsage", "BooleanExpression", "LiteralInteger", "LiteralReal",
    "LiteralString", "LiteralBoolean", "Import", "AliasMember",
    # KerML visitor-dict kinds
    "Class", "DataType", "Datatype", "Feature", "Function", "Classifier",
    "Type", "Structure", "Behavior", "Association", "Metaclass", "Enumeration",
})


# ---------------------------------------------------------------------------
# cache location / key
# ---------------------------------------------------------------------------


def cache_dir() -> Optional[Path]:
    """Cache directory, or None when caching is switched off.

    ``SYSMLPY_LIBRARY_CACHE=off`` disables it (benchmarks use that, and so does
    any caller that wants a guaranteed cold build).
    """
    value = os.environ.get(CACHE_ENV)
    if value and value.strip().lower() in ("off", "0", "no", "false", "none"):
        return None
    if value:
        return Path(value).expanduser()
    base = os.environ.get("XDG_CACHE_HOME")
    root = Path(base) if base else Path.home() / ".cache"
    return root / "sysmlpy" / "library-facts"


def build_id() -> str:
    """Identity of the code that produced a record (part of the cache key)."""
    from sysmlpy import __version__
    return f"{__version__}+f{FACTS_VERSION}"


def set_digest(paths: Iterable[Path]) -> str:
    """Digest of the whole library *set*.

    Per-file content is not enough: a fact can depend on a sibling (a re-export
    follows an import declared elsewhere), so the set digest is part of the key
    for every record — the same reasoning as OpenSysML's cache key.
    """
    h = hashlib.sha256()
    for path in sorted(Path(p) for p in paths):
        h.update(path.name.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _cache_path(digest: str) -> Optional[Path]:
    directory = cache_dir()
    if directory is None:
        return None
    return directory / f"facts-{build_id()}-{digest[:16]}.json"


# ---------------------------------------------------------------------------
# extraction
# ---------------------------------------------------------------------------


def _new_ns() -> dict:
    """A fresh namespace record."""
    return {"members": {}, "reexports": {}, "children": [], "imports": [],
            "shortnames": {}, "aliases": {}}


def _is_name(name: Any) -> bool:
    """True when *name* can be a declared name.

    Library sources legitimately use quoted identifiers — ``attribute <Btu_IT>
    'British thermal unit (IT)'`` — where the declared name is a quoted phrase
    and the *short* name is the token references use.  So quoted names are
    accepted here; what is rejected is documentation text that leaked through as
    a name (newlines, tabs, or an entire paragraph).
    """
    if not isinstance(name, str) or not name.strip():
        return False
    if any(ch in name for ch in "\r\n\t"):
        return False
    return len(name) <= 120


def _clean_name(name: Any) -> Any:
    """Declared name with its SysML quoting removed (``'+'`` → ``+``)."""
    if isinstance(name, str) and len(name) >= 2 and name[0] == name[-1] and name[0] in "'\"":
        return name[1:-1]
    return name


def _identification_of(node: Any) -> Dict[str, str]:
    """The declared name/short name of a declaration-shaped dict.

    Searches only declaration keys, so a nested member's Identification (which
    lives under a body) is never mistaken for this element's own.
    """
    found = {"name": None, "shortname": None}

    def walk(value, depth):
        if depth > 6 or not isinstance(value, dict):
            return False
        if value.get("name") == "Identification":
            if value.get("declaredName"):
                found["name"] = value["declaredName"]
            if value.get("declaredShortName") and not found["shortname"]:
                found["shortname"] = value["declaredShortName"]
            return True
        for key in _DECL_KEYS:
            child = value.get(key)
            if isinstance(child, dict) and walk(child, depth + 1):
                return True
        return False

    walk(node, 0)
    return found


def _qualified_name_of(node: Any) -> Optional[str]:
    """`QualifiedName.names` (or a plain string) as an `A::B` string."""
    if not isinstance(node, dict):
        return None
    names = node.get("names") or node.get("parts")
    if isinstance(names, str):
        return names
    if isinstance(names, (list, tuple)) and names:
        return "::".join(str(n) for n in names if n)
    return None


def _walk_container(node: Any, qn: str, facts: Dict[str, dict], depth: int = 0) -> None:
    """Register every namespace under ``node`` and its members."""
    if depth > 60 or node is None:
        return
    if isinstance(node, list):
        for item in node:
            _walk_container(item, qn, facts, depth + 1)
        return
    if not isinstance(node, dict):
        return

    kind = node.get("name")
    if "children" in node and ("declaredName" in node or "declaredShortName" in node):
        # KerML dialect (issue #34 step 7): the visitor emits a name-shaped dict —
        # ``{"name": "package", "declaredName": "P", "children": [...]}`` — with
        # no imports in it (those are harvested lexically by the caller).
        name = node.get("declaredName") if _is_name(node.get("declaredName")) else None
        is_package = kind in ("package", "library package", "namespace")
        if name and is_package:
            child_qn = f"{qn}::{name}" if qn else name
            namespace = facts.setdefault(child_qn, _new_ns())
            if qn:
                parent = facts.setdefault(qn, _new_ns())
                if name not in parent["children"]:
                    parent["children"].append(name)
            _walk_container(node.get("children"), child_qn, facts, depth + 1)
            return
        if name:
            container = facts.setdefault(qn, _new_ns())
            name = _clean_name(name)
            container["members"][name] = kind or "feature"
            short = node.get("declaredShortName")
            if _is_name(short):
                container["shortnames"][_clean_name(short)] = name
            # nested features of this member resolve under its own scope
            _walk_container(node.get("children"), f"{qn}::{name}" if qn else name,
                            facts, depth + 1)
            return
        _walk_container(node.get("children"), qn, facts, depth + 1)
        return
    if kind == "AliasMember":
        # `alias time for duration;` — the alias name is a member of the
        # namespace, and it is how `ISQ::time` resolves (ISQSpaceTime).
        name = node.get("memberName")
        target = _qualified_name_of(node.get("memberElement"))
        container = facts.setdefault(qn, {"members": {}, "reexports": {},
                                          "children": [], "imports": [],
                                          "shortnames": {}, "aliases": {}})
        if name and _is_name(name):
            container["members"][name] = "Alias"
            if target:
                container.setdefault("aliases", {})[name] = target
            if node.get("memberShortName"):
                container["shortnames"][node["memberShortName"]] = name
        _walk_body(node, qn, container, facts, depth)
        return
    if kind in _MEMBER_KINDS:
        declared = _identification_of(node)
        name = declared["name"] if _is_name(declared["name"]) else None
        is_package = kind in ("Package", "LibraryPackage", "Namespace")
        if name and is_package:
            child_qn = f"{qn}::{name}" if qn else name
            namespace = facts.setdefault(child_qn, _new_ns())
            if qn:
                parent = facts.setdefault(qn, _new_ns())
                if name not in parent["children"]:
                    parent["children"].append(name)
            # a package's own body is walked under its qualified name
            _walk_body(node, child_qn, namespace, facts, depth)
            return
        if name:
            # a non-package member belongs to the current namespace
            container = facts.setdefault(qn, _new_ns())
            name = _clean_name(name)
            container["members"][name] = kind
            if declared["shortname"] and _is_name(declared["shortname"]):
                container["shortnames"][_clean_name(declared["shortname"])] = name
        # a kind-less/nested definition still has a body worth walking
        _walk_body(node, qn, facts.setdefault(qn, _new_ns()), facts, depth)
        return

    # wrappers / memberships / elements: keep looking for members and imports
    for key, value in node.items():
        if key == "name":
            continue
        _walk_container(value, qn, facts, depth + 1)


def _import_record(node: Dict[str, Any]) -> Optional[dict]:
    """(visibility, target, star, recursive) for one ``Import`` dict."""
    rel = node.get("ownedRelationship")
    rel = rel[0] if isinstance(rel, list) and rel else rel
    if not isinstance(rel, dict):
        return None
    prefix = rel.get("prefix") or {}
    visibility_node = (prefix or {}).get("visibility") or {}
    visibility = ("public" if visibility_node.get("public") else
                  "protected" if visibility_node.get("protected") else "private")
    if rel.get("name") == "NamespaceImport":
        namespace = rel.get("namespace") or {}
        target = _qualified_name_of(namespace.get("namespace"))
        if not target:
            return None
        return {"visibility": visibility, "target": target, "star": True,
                "recursive": bool(namespace.get("isRecursive"))}
    membership = rel.get("membership") or {}
    target = _qualified_name_of(membership.get("importedMembership") or {})
    if not target:
        return None
    return {"visibility": visibility, "target": target, "star": False,
            "recursive": False}


def _collect_imports(body: Any, namespace: dict, depth: int = 0) -> None:
    """Imports declared *directly* in a body — never inside a nested element's
    own body, which is that element's scope, and never recursively, which made
    the walk quadratic (691 s for the library instead of ~45 s)."""
    if depth > 3 or body is None:
        return
    if isinstance(body, list):
        for item in body:
            _collect_imports(item, namespace, depth + 1)
        return
    if not isinstance(body, dict):
        return
    if body.get("name") == "Import":
        record = _import_record(body)
        if record and record not in namespace["imports"]:
            namespace["imports"].append(record)
        return
    for key, value in body.items():
        if key in ("name", "body", "completion"):
            continue
        if isinstance(value, (dict, list)):
            _collect_imports(value, namespace, depth + 1)


def _walk_body(node: Dict[str, Any], qn: str, namespace: dict,
               facts: Dict[str, dict], depth: int) -> None:
    """Collect imports of this element and descend into its body members."""
    body = node.get("body") or node.get("completion")
    if body is None:
        return
    _collect_imports(body, namespace)
    _walk_container(body, qn, facts, depth + 1)


# ---------------------------------------------------------------------------
# the fixpoint
# ---------------------------------------------------------------------------

#: Bound on re-export derivation rounds before a full re-derivation.  A build
#: from an empty re-export state only adds, so it settles; the bound protects
#: against a pathological import cycle.
EXPANSION_ROUNDS = 16


def _expand_once(facts: Dict[str, dict], only: Optional[Iterable[str]] = None) -> bool:
    """One derive pass: re-exports of N := public star-imports' visible members."""
    changed = False
    targets = list(only) if only is not None else list(facts)
    for qn in targets:
        namespace = facts.get(qn)
        if namespace is None:
            continue
        derived: Dict[str, str] = {}
        for imp in namespace["imports"]:
            if not imp["star"] or imp["visibility"] != "public":
                continue
            source = facts.get(imp["target"])
            if source is None:
                continue
            # A star import brings members into scope **with their short names**:
            # `attribute <L> length` in ISQBase makes `ISQ::L` legal after
            # `public import ISQBase::*` (library files then write `isq.L`).
            for name, kind in source["members"].items():
                derived.setdefault(name, kind)
            for short, member in source["shortnames"].items():
                derived.setdefault(short, source["members"].get(member, "ShortName"))
            for name, kind in source["reexports"].items():
                derived.setdefault(name, kind)
            if imp["recursive"]:
                for child in source["children"]:
                    child_ns = facts.get(f"{imp['target']}::{child}")
                    if child_ns:
                        for name, kind in child_ns["members"].items():
                            derived.setdefault(name, kind)
                        for name, kind in child_ns["reexports"].items():
                            derived.setdefault(name, kind)
        # A namespace never re-exports its own declarations as imports.
        derived = {n: k for n, k in derived.items() if n not in namespace["members"]}
        if derived != namespace["reexports"]:
            namespace["reexports"] = derived
            changed = True
    return changed


def expand_reexports(facts: Dict[str, dict]) -> None:
    """Derive public re-exports to a fixpoint (ISQ → ISQBase → …)."""
    for _ in range(EXPANSION_ROUNDS):
        if not _expand_once(facts):
            return
    # Did not settle incrementally: derive everything from an empty state.
    for namespace in facts.values():
        namespace["reexports"] = {}
    for _ in range(EXPANSION_ROUNDS * 2):
        if not _expand_once(facts):
            return


# ---------------------------------------------------------------------------
# build / load
# ---------------------------------------------------------------------------


def _library_files(lib_roots) -> list:
    from sysmlpy.semantic import LibrarySymbolIndex
    paths = []
    for root in LibrarySymbolIndex._resolve_roots(lib_roots):
        root = Path(root)
        if not root.is_dir():
            continue
        for ext in ("*.kerml", "*.sysml"):
            paths.extend(root.rglob(ext))
    return sorted(set(paths))


def _extract_file_facts(path_str: str) -> Optional[Dict[str, dict]]:
    """Facts fragment for one library file (module-level: picklable for workers).

    Returns a facts mapping holding only what this file declares, so the parent
    can merge fragments and run the re-export fixpoint once.  ``None`` means the
    file contributed nothing.
    """
    path = Path(path_str)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fragment: Dict[str, dict] = {}
    if path_str.endswith(".kerml"):
        from sysmlpy.kerml import kerml as kerml_mod
        try:
            document = kerml_mod.parse_to_dict(text)
        except Exception:
            _register_lexical(path, fragment)
            return fragment or None
        before = set(fragment)
        _walk_container(document, "", fragment, 0)
        _attach_lexical_imports(text, fragment, set(fragment) - before)
    else:
        from sysmlpy import load_grammar
        try:
            document = load_grammar(text)
        except Exception:
            _register_lexical(path, fragment)
            return fragment or None
        _walk_container(document, "", fragment, 0)
    return fragment or None


def _merge_fragments(fragments: Iterable[Optional[Dict[str, dict]]]) -> Dict[str, dict]:
    """Union per-file fragments into one facts mapping."""
    merged: Dict[str, dict] = {}
    for fragment in fragments:
        if not fragment:
            continue
        for qn, record in fragment.items():
            target = merged.setdefault(qn, _new_ns())
            target["members"].update(record["members"])
            target["reexports"].update(record.get("reexports") or {})
            for child in record["children"]:
                if child not in target["children"]:
                    target["children"].append(child)
            for imp in record["imports"]:
                if imp not in target["imports"]:
                    target["imports"].append(imp)
            target["shortnames"].update(record.get("shortnames") or {})
            target["aliases"].update(record.get("aliases") or {})
    return merged


def _workers() -> int:
    """Worker count for the parallel extract.

    Parsing is CPU-bound and independent per file, and the reference
    implementations do the same (OpenSysML's ``LoadAll`` runs ``parse()`` over
    all library files in parallel).  ``SYSMLPY_LIBRARY_WORKERS`` overrides;
    ``1`` keeps it serial, which is also the automatic fallback.
    """
    value = os.environ.get("SYSMLPY_LIBRARY_WORKERS")
    if value:
        try:
            return max(1, int(value))
        except ValueError:
            return 1
    return min(8, os.cpu_count() or 1)


def build(lib_roots=None) -> Dict[str, dict]:
    """Extract facts from every library source (no model, no element tree)."""
    paths = [str(p) for p in _library_files(lib_roots)]
    workers = _workers()
    fragments: list = []
    if workers > 1 and len(paths) > 1:
        try:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=workers) as pool:
                fragments = list(pool.map(_extract_file_facts, paths, chunksize=1))
        except Exception:
            fragments = []  # no pool here (restricted sandbox, spawn cost, …)
    if not fragments:
        fragments = [_extract_file_facts(p) for p in paths]
    facts = _merge_fragments(fragments)
    expand_reexports(facts)
    return facts


def _register_lexical(path: Path, facts: Dict[str, dict]) -> None:
    """Fallback for a source the parser rejects: harvest names tolerantly.

    A library file written against the wrong grammar — a ``.kerml`` carrying
    SysML notation, say — still declares names that user models import.  The
    resolver must know the namespace exists even when the parser cannot build a
    document for it, so the scraped harvester fills the gap (the same tolerant
    path the analyzer used before the facts index).
    """
    from sysmlpy.semantic import LibrarySymbolIndex
    symbols: set[str] = set()
    try:
        LibrarySymbolIndex._extract_from_file(Path(path), symbols)
    except Exception:
        return
    for qualified in symbols:
        parts = [p for p in qualified.split("::") if p]
        if not parts:
            continue
        qn = ""
        for part in parts[:-1]:
            child = f"{qn}::{part}" if qn else part
            parent = facts.setdefault(qn, _new_ns())
            if part not in parent["children"]:
                parent["children"].append(part)
            facts.setdefault(child, _new_ns())
            qn = child
        facts.setdefault(qn, _new_ns())["members"].setdefault(parts[-1], "Lexical")


_KERML_IMPORT_RE = re.compile(
    r"^\s*(?P<vis>private|protected|public)\s+import\s+"
    r"(?P<target>[A-Za-z_][\w]*(?:::[A-Za-z_][\w]*)*)"
    r"\s*(?P<star>::\*)?\s*;", re.MULTILINE)


def _attach_lexical_imports(text: str, facts: Dict[str, dict],
                            new_qns: Iterable[str]) -> None:
    """KerML's visitor dict carries no imports (step 7), so read them from text.

    Kernel library files declare one top-level package, so the file's imports
    belong to it.  ``public import A::*`` makes the package re-export A's
    members; ``private import A::B`` is a single-member import.
    """
    packages = [qn for qn in new_qns if facts.get(qn)]
    if not packages:
        return
    namespace = facts[min(packages, key=lambda qn: qn.count("::"))]
    for match in _KERML_IMPORT_RE.finditer(text):
        record = {
            "visibility": match.group("vis"),
            "target": match.group("target"),
            "star": bool(match.group("star")),
            "recursive": False,
        }
        if record not in namespace["imports"]:
            namespace["imports"].append(record)


def load(lib_roots=None, *, force: bool = False) -> Dict[str, dict]:
    """Facts for the shipped library, from cache when possible."""
    paths = _library_files(lib_roots)
    digest = set_digest(paths)
    cache_file = _cache_path(digest)
    if cache_file is not None and not force and cache_file.exists():
        try:
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            if payload.get("build") == build_id() and payload.get("digest") == digest:
                return payload["facts"]
        except Exception:
            pass  # a corrupt record is a miss, never a crash
    facts = build(lib_roots)
    if cache_file is not None:
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = cache_file.with_suffix(".tmp")
            tmp.write_text(json.dumps({
                "build": build_id(),
                "digest": digest,
                "version": FACTS_VERSION,
                "facts": facts,
            }), encoding="utf-8")
            tmp.replace(cache_file)
        except Exception:
            pass  # caching is best-effort
    return facts


def clear() -> None:
    """Drop cached records (tests, benchmarks)."""
    directory = cache_dir()
    if directory is None or not directory.exists():
        return
    for path in directory.glob("facts-*.json"):
        try:
            path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# queries
# ---------------------------------------------------------------------------


class LibraryFacts:
    """Query wrapper over a facts mapping."""

    def __init__(self, facts: Dict[str, dict]):
        self.facts = facts

    # -- namespaces -----------------------------------------------------
    def namespace(self, qn: str) -> Optional[dict]:
        return self.facts.get(qn)

    def members(self, qn: str) -> Dict[str, str]:
        ns = self.facts.get(qn)
        return dict(ns["members"]) if ns else {}

    def visible_members(self, qn: str) -> Dict[str, str]:
        """Direct members plus publicly re-exported ones."""
        ns = self.facts.get(qn)
        if not ns:
            return {}
        out = dict(ns["members"])
        for name, kind in ns["reexports"].items():
            out.setdefault(name, kind)
        return out

    def children(self, qn: str) -> list:
        ns = self.facts.get(qn)
        return list(ns["children"]) if ns else []

    # -- names ----------------------------------------------------------
    def resolve(self, name: str) -> Optional[str]:
        """Qualified name of the namespace that declares or re-exports *name*."""
        if name in self.facts:
            return name
        for qn, ns in self.facts.items():
            if name in ns["members"] or name in ns["reexports"]:
                return qn
            if name in ns["shortnames"]:
                return qn
        return None

    def exists(self, ref: str) -> bool:
        """True when *ref* names a namespace, member or re-export."""
        if not ref:
            return False
        if ref in self.facts:
            return True
        if "::" in ref:
            head, _, tail = ref.rpartition("::")
            ns = self.facts.get(head)
            if ns is None:
                return False
            tail = _clean_name(tail)
            if tail in ns["members"] or tail in ns["reexports"]:
                return True
            # a short name is a member reference too: `SI::<kg> kilogram` makes
            # `SI::kg` a legal way to name it.
            return tail in ns.get("shortnames", {})
        return self.resolve(ref) is not None

    def shortname_owner(self, shortname: str) -> Optional[str]:
        for qn, ns in self.facts.items():
            if shortname in ns["shortnames"]:
                return qn
        return None


_CACHE: Dict[str, LibraryFacts] = {}


def get(lib_roots=None, *, force: bool = False) -> LibraryFacts:
    """Process-cached :class:`LibraryFacts` for the given roots."""
    key = "|".join(str(Path(p)) for p in lib_roots) if lib_roots else ""
    if force:
        _CACHE.pop(key, None)
    if key not in _CACHE:
        _CACHE[key] = LibraryFacts(load(lib_roots, force=force))
    return _CACHE[key]
