#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semantic analysis for SysML v2 models.

Provides undefined symbol detection by building a symbol table from the
parsed model tree and cross-referencing all qualified name references.
"""

from __future__ import annotations

import dataclasses
import os
import re
from pathlib import Path
from typing import Any, Optional


@dataclasses.dataclass
class SemanticIssue:
    """A single semantic issue found during analysis."""

    severity: str
    code: str
    message: str
    element: Any = None
    reference: str = ""


# ---------------------------------------------------------------------------
# Library Symbol Index
# ---------------------------------------------------------------------------

# Regex patterns for extracting symbols from library files
_PACKAGE_RE = re.compile(
    r'(?:standard\s+library\s+)?package\s+(\w+)\s*\{',
    re.IGNORECASE,
)
_DEFINITION_RE = re.compile(
    r'(?:abstract\s+)?'
    r'(?:datatype|class|metaclass|attribute\s+def|part\s+def|item\s+def|port\s+def|'
    r'action\s+def|state\s+def|constraint\s+def|calc\s+def|requirement\s+def|'
    r'interface\s+def|connection\s+def|flow\s+def|enumeration\s+def|enum\s+def|'
    r'use\s+case\s+def|case\s+def|analysis\s+case\s+def|verification\s+case\s+def|'
    r'view\s+def|viewpoint\s+def|concern\s+def|allocation\s+def|metadata\s+def|'
    r'rendering\s+def|individual\s+def|feature\s+def|reference\s+def|'
    r'structure\s+def|behavior\s+def|occurrence\s+def|assertion\s+def|'
    r'typedef|classifier)\s+'
    r"""(['"]?\w+['"]?)""",
    re.IGNORECASE,
)


class LibrarySymbolIndex:
    """Index of all symbols defined in the standard library.

    Scans .kerml and .sysml files to extract package-qualified symbol names.
    Results are cached to avoid repeated file I/O.
    """

    _cache: Optional[frozenset[str]] = None
    _library_root: Optional[Path] = None

    @classmethod
    def get_symbols(cls, library_root: Optional[Path] = None) -> frozenset[str]:
        """Return all known library symbol names as qualified strings.

        Parameters
        ----------
        library_root : Path, optional
            Root directory of the standard library. Defaults to the bundled
            library shipped with sysmlpy.

        Returns
        -------
        frozenset[str]
            Set of qualified names like ``"ScalarValues::Integer"``,
            ``"ISQ::LengthValue"``, etc.
        """
        if cls._cache is not None:
            return cls._cache

        root = library_root or cls._default_library_root()
        if root is None or not root.is_dir():
            # Fall back to minimal hardcoded set
            cls._cache = _KNOWN_LIBRARY_SYMBOLS
            return cls._cache

        symbols = set()
        for ext in ("*.kerml", "*.sysml"):
            for filepath in root.rglob(ext):
                cls._extract_from_file(filepath, symbols)

        cls._cache = frozenset(symbols)
        return cls._cache

    @classmethod
    def _default_library_root(cls) -> Optional[Path]:
        """Find the bundled library directory."""
        try:
            import sysmlpy
            pkg_path = Path(sysmlpy.__file__).parent
            lib_path = pkg_path / "library"
            if lib_path.is_dir():
                return lib_path
        except ImportError:
            pass

        # Fallback: relative to this module
        module_path = Path(__file__).parent
        lib_path = module_path / "library"
        if lib_path.is_dir():
            return lib_path

        return None

    @classmethod
    def _extract_from_file(cls, filepath: Path, symbols: set[str]) -> None:
        """Extract symbol names from a single library file."""
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        # Track package nesting with brace depth
        package_stack: list[tuple[str, int]] = []  # (name, depth_at_open)
        brace_depth = 0

        for line in content.splitlines():
            # Strip comments
            stripped = line.strip()
            if stripped.startswith("doc") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            # Count braces in this line
            open_braces = stripped.count("{")
            close_braces = stripped.count("}")

            # Check for package opening (before updating depth)
            pkg_match = _PACKAGE_RE.search(stripped)
            if pkg_match:
                pkg_name = pkg_match.group(1)
                package_stack.append((pkg_name, brace_depth))
                # The package itself is a symbol
                if len(package_stack) > 1:
                    symbols.add("::".join(name for name, _ in package_stack))

            # Check for definitions (use current package context)
            def_match = _DEFINITION_RE.search(stripped)
            if def_match and package_stack:
                def_name = def_match.group(1).strip("'\"")
                qualified = "::".join(name for name, _ in package_stack) + "::" + def_name
                symbols.add(qualified)

            # Update brace depth
            brace_depth += open_braces - close_braces

            # Pop packages that have been closed
            while package_stack and package_stack[-1][1] >= brace_depth:
                package_stack.pop()

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the cached symbol index (useful for testing)."""
        cls._cache = None


# Backwards-compatible constant (populated lazily from library files)
_KNOWN_LIBRARY_SYMBOLS: frozenset[str] = frozenset({
    # Scalar values
    "ScalarValues::Boolean", "ScalarValues::Integer", "ScalarValues::Natural",
    "ScalarValues::Positive", "ScalarValues::Nonnegative",
    "ScalarValues::Rational", "ScalarValues::Real", "ScalarValues::String",
    "ScalarValues::Complex", "ScalarValues::UnlimitedNatural",
    "ScalarValues::Number", "ScalarValues::ScalarValue",
    # ISQ base quantities
    "ISQ::Length", "ISQ::Mass", "ISQ::Time", "ISQ::ElectricCurrent",
    "ISQ::ThermodynamicTemperature", "ISQ::AmountOfSubstance",
    "ISQ::LuminousIntensity", "ISQ::Angle", "ISQ::SolidAngle",
    "ISQ::Information",
    # ISQ value types
    "ISQ::LengthValue", "ISQ::MassValue", "ISQ::TimeValue",
    "ISQ::ElectricCurrentValue", "ISQ::ThermodynamicTemperatureValue",
    "ISQ::AmountOfSubstanceValue", "ISQ::LuminousIntensityValue",
    "ISQ::AngleValue", "ISQ::SolidAngleValue", "ISQ::InformationValue",
    # Common derived quantities
    "ISQ::Area", "ISQ::Volume", "ISQ::Velocity", "ISQ::Acceleration",
    "ISQ::Force", "ISQ::Pressure", "ISQ::Energy", "ISQ::Power",
    "ISQ::ElectricCharge", "ISQ::Voltage", "ISQ::Capacitance",
    "ISQ::Resistance", "ISQ::Conductance", "ISQ::MagneticFlux",
    "ISQ::MagneticFluxDensity", "ISQ::Inductance", "ISQ::Frequency",
    "ISQ::AreaValue", "ISQ::VolumeValue", "ISQ::VelocityValue",
    "ISQ::AccelerationValue", "ISQ::ForceValue", "ISQ::PressureValue",
    "ISQ::EnergyValue", "ISQ::PowerValue", "ISQ::ElectricChargeValue",
    "ISQ::VoltageValue", "ISQ::CapacitanceValue", "ISQ::ResistanceValue",
    "ISQ::ConductanceValue", "ISQ::MagneticFluxValue",
    "ISQ::MagneticFluxDensityValue", "ISQ::InductanceValue",
    "ISQ::FrequencyValue",
    # Base KerML/SysML types
    "KerML::Element", "KerML::Type", "KerML::Feature",
    "KerML::Namespace", "KerML::Relationship",
    "SysML::Occurrence", "SysML::Item", "SysML::Part",
    "SysML::Port", "SysML::Action", "SysML::State",
    "SysML::Requirement", "SysML::Connection",
    "SysML::Flow", "SysML::Interface",
    "SysML::Calculation", "SysML::Constraint",
    "SysML::Enumeration", "SysML::Case",
    "SysML::UseCase", "SysML::AnalysisCase",
    "SysML::VerificationCase", "SysML::View",
    "SysML::Viewpoint", "SysML::Concern",
    "SysML::Allocation", "SysML::Metadata",
    "SysML::Rendering", "SysML::Individual",
})


# ---------------------------------------------------------------------------
# Symbol Table
# ---------------------------------------------------------------------------

class SymbolTable:
    """Hierarchical symbol table for a parsed SysML model.

    Each scope maps simple names to model elements.  Parent scopes are
    consulted when a name is not found locally.  Imported symbols are
    merged into the scope based on import rules.
    """

    def __init__(self) -> None:
        self._symbols: dict[str, Any] = {}
        self._children: dict[str, SymbolTable] = {}
        self._parent: Optional[SymbolTable] = None
        self._imports: list[Any] = []  # Import grammar objects
        self._imported_symbols: dict[str, Any] = {}  # Resolved imported symbols
        self._definition_features: dict[str, dict[str, Any]] = {}  # definition_name -> {element, features, supertypes}

    # -- public API ----------------------------------------------------------

    def register(self, name: str, element: Any) -> None:
        """Register *element* under *name* in this scope."""
        self._symbols[name] = element

    def lookup(self, name: str) -> Optional[Any]:
        """Look up *name*, walking up parent scopes if not found locally."""
        if name in self._symbols:
            return self._symbols[name]
        if name in self._imported_symbols:
            return self._imported_symbols[name]
        if self._parent is not None:
            return self._parent.lookup(name)
        return None

    def build_from_model(self, model: Any) -> None:
        """Walk the model tree and populate the symbol table."""
        self._walk_element(model, self)
        self._resolve_imports(self)

    # -- internals -----------------------------------------------------------

    def _walk_element(self, element: Any, table: SymbolTable) -> None:
        if element is None:
            return

        name = getattr(element, "name", None)
        # Skip Model's UUID name (not a real SysML symbol)
        if name is not None and type(element).__name__ != "Model":
            table.register(name, element)

        # Track definitions and their features/supertypes for inheritance resolution
        elem_type = type(element).__name__
        if getattr(element, "is_definition", False) and name is not None:
            self._index_definition(element, name, table)

        # Create child scope for packages and definitions
        # Skip Model (it's just a root container, not a SysML namespace)
        child_table = table
        is_container = getattr(element, "is_definition", False) or elem_type == "Package"
        if is_container and name is not None and elem_type != "Model":
            child_table = table._children.setdefault(name, SymbolTable())
            child_table._parent = table

        # Collect imports from package grammar body
        if elem_type == "Package":
            self._collect_imports(element, child_table)

        # Walk children
        for child in getattr(element, "children", []):
            self._walk_element(child, child_table)

    def _collect_imports(self, package: Any, table: SymbolTable) -> None:
        """Collect Import objects from a package's grammar body."""
        grammar = getattr(package, "grammar", None)
        if grammar is None:
            return
        body = getattr(grammar, "body", None)
        if body is None:
            return
        for child in getattr(body, "children", []):
            child_type = type(child).__name__
            if child_type == "Import":
                table._imports.append(child)

    def _resolve_imports(self, table: SymbolTable) -> None:
        """Resolve all imports for this scope and its children."""
        for imp in table._imports:
            self._resolve_single_import(imp, table)

        # Recurse into children
        for child_table in table._children.values():
            self._resolve_imports(child_table)

    def _resolve_single_import(self, imp: Any, table: SymbolTable) -> None:
        """Resolve a single Import object into the symbol table."""
        if not imp.children:
            return

        import_child = imp.children[0]
        child_type = type(import_child).__name__

        if child_type == "MembershipImport":
            self._resolve_membership_import(import_child, table)
        elif child_type == "NamespaceImport":
            self._resolve_namespace_import(import_child, table)

    def _resolve_membership_import(self, mem_import: Any, table: SymbolTable) -> None:
        """Resolve a MembershipImport (import specific element)."""
        imported_mem = getattr(mem_import, "membership", None)
        if imported_mem is None:
            return

        qn = getattr(imported_mem, "name", None)
        if qn is None:
            return

        names = getattr(qn, "names", [])
        if not names:
            return

        ref_str = "::".join(names)
        element = self._resolve_qualified_name(ref_str, table)
        if element is not None:
            # Use the simple name (last part) as the imported name
            simple_name = names[-1]
            table._imported_symbols[simple_name] = element

    def _resolve_namespace_import(self, ns_import: Any, table: SymbolTable) -> None:
        """Resolve a NamespaceImport (import all from namespace)."""
        imported_ns = getattr(ns_import, "namespace", None)
        if imported_ns is None:
            return

        qn = getattr(imported_ns, "namespaces", None)
        if qn is None:
            return

        names = getattr(qn, "names", [])
        if not names:
            return

        is_recursive = getattr(imported_ns, "isRecursive", False)

        # Find the target namespace table
        ref_str = "::".join(names)
        target_table = self._find_namespace_table(ref_str, table)
        if target_table is None:
            return

        # Import all symbols from the target namespace
        for sym_name, element in target_table._symbols.items():
            table._imported_symbols[sym_name] = element

        # If recursive, also import from all child namespaces
        if is_recursive:
            self._recursive_import(target_table, table)

    def _recursive_import(self, source_table: SymbolTable, dest_table: SymbolTable) -> None:
        """Recursively import symbols from all child namespaces."""
        for child_name, child_table in source_table._children.items():
            for sym_name, element in child_table._symbols.items():
                if sym_name not in dest_table._imported_symbols:
                    dest_table._imported_symbols[sym_name] = element
            self._recursive_import(child_table, dest_table)

    def _resolve_qualified_name(self, ref_str: str, table: SymbolTable) -> Optional[Any]:
        """Resolve a qualified name reference from the given scope."""
        # Direct lookup
        if "::" not in ref_str:
            return table.lookup(ref_str)

        parts = ref_str.split("::")
        lookup_table = table
        last_found = None
        all_found = True
        for i, part in enumerate(parts):
            found = lookup_table.lookup(part)
            if found is None:
                all_found = False
                break
            last_found = found
            child_scope = lookup_table._children.get(part)
            if child_scope is None:
                owner = lookup_table._find_symbol_owner(part)
                if owner is not None:
                    child_scope = owner._children.get(part)
            if child_scope is not None:
                lookup_table = child_scope
            else:
                all_found = False
                break

        if all_found:
            return last_found

        # Fall back to simple name lookup
        return table.lookup(parts[-1])

    def _find_namespace_table(self, ref_str: str, from_table: SymbolTable) -> Optional[SymbolTable]:
        """Find the symbol table for a namespace path."""
        if "::" not in ref_str:
            # Simple name - try direct child first, then via parent lookup
            child = from_table._children.get(ref_str)
            if child is not None:
                return child
            # Try finding via parent chain
            owner = from_table._find_symbol_owner(ref_str)
            if owner is not None:
                return owner._children.get(ref_str)
            return None

        parts = ref_str.split("::")
        lookup_table = from_table
        for part in parts:
            child = lookup_table._children.get(part)
            if child is not None:
                lookup_table = child
            else:
                # Try from parent chain
                owner = lookup_table._find_symbol_owner(part)
                if owner is not None:
                    child = owner._children.get(part)
                    if child is not None:
                        lookup_table = child
                    else:
                        return None
                else:
                    return None
        return lookup_table

    def _find_symbol_owner(self, name: str) -> Optional[SymbolTable]:
        """Find the symbol table that directly contains *name* as a symbol."""
        if name in self._symbols:
            return self
        if self._parent is not None:
            return self._parent._find_symbol_owner(name)
        return None

    def _index_definition(self, element: Any, name: str, table: SymbolTable) -> None:
        """Index a definition's features and supertypes for inheritance resolution."""
        grammar = getattr(element, "grammar", None)
        if grammar is None:
            return

        # Extract supertype names from grammar
        supertypes = self._extract_supertypes(grammar)

        # Extract feature names defined directly in this definition
        features = self._extract_features(grammar)

        self._definition_features[name] = {
            "element": element,
            "features": features,
            "supertypes": supertypes,
            "scope": table,
        }

    def _extract_supertypes(self, grammar: Any) -> list[str]:
        """Extract supertype names from a definition's grammar."""
        supertypes = []

        # Navigate to subclassificationpart
        definition = getattr(grammar, "definition", None)
        if definition is None:
            return supertypes

        declaration = getattr(definition, "declaration", None)
        if declaration is None:
            return supertypes

        scp = getattr(declaration, "subclassificationpart", None)
        if scp is None:
            return supertypes

        for child in getattr(scp, "children", []):
            name_obj = getattr(child, "name", None)
            if name_obj is not None:
                names = getattr(name_obj, "names", [])
                if names:
                    supertypes.append(names[-1])  # Use simple name

        return supertypes

    def _extract_features(self, grammar: Any) -> set[str]:
        """Extract feature names defined directly in a definition's grammar."""
        features = set()

        definition = getattr(grammar, "definition", None)
        if definition is None:
            return features

        body = getattr(definition, "body", None)
        if body is None:
            return features

        for body_item in getattr(body, "children", []):
            for member in getattr(body_item, "children", []):
                for usage_elem in getattr(member, "children", []):
                    struct_elem = getattr(usage_elem, "children", None)
                    if struct_elem is None:
                        continue
                    # struct_elem can be either:
                    # 1. A Usage subclass directly (e.g., AttributeUsage)
                    # 2. A StructureUsageElement wrapper containing a Usage
                    feat_name = self._get_feature_name(struct_elem)
                    if feat_name:
                        features.add(feat_name)

        return features

    def _get_feature_name(self, usage: Any) -> Optional[str]:
        """Extract the declared name from a Usage object or wrapper."""
        try:
            # Case 1: Direct Usage subclass (e.g., AttributeUsage, PartUsage)
            # These have a 'usage' attribute
            usage_attr = getattr(usage, "usage", None)
            if usage_attr is not None:
                decl = getattr(usage_attr, "declaration", None)
                if decl is None:
                    return getattr(usage, "name", None)
                inner_decl = getattr(decl, "declaration", None)
                if inner_decl is None:
                    return None
                ident = getattr(inner_decl, "identification", None)
                if ident is None:
                    return None
                return getattr(ident, "declaredName", None)

            # Case 2: Wrapper with children containing Usage
            children = getattr(usage, "children", None)
            if children is not None:
                return self._get_feature_name(children)

            return getattr(usage, "name", None)
        except AttributeError:
            return None

    def resolve_inherited_feature(self, feature_name: str, defining_type: str, visited: Optional[set] = None) -> Optional[Any]:
        """Resolve a feature name by walking the supertype chain of *defining_type*.

        Returns the element that defines the feature, or None if not found.
        """
        if visited is None:
            visited = set()

        if defining_type in visited:
            return None
        visited.add(defining_type)

        if defining_type not in self._definition_features:
            return None

        def_info = self._definition_features[defining_type]

        # Check if feature is directly defined in this type
        if feature_name in def_info["features"]:
            return def_info["element"]

        # Recursively check supertypes
        for supertype in def_info["supertypes"]:
            result = self.resolve_inherited_feature(feature_name, supertype, visited)
            if result is not None:
                return result

        return None

    def find_defining_type_for_feature(self, feature_name: str, context_type: str) -> Optional[str]:
        """Find which type in the inheritance chain defines *feature_name*.

        Returns the type name that defines the feature, or None.
        """
        if context_type not in self._definition_features:
            return None

        def_info = self._definition_features[context_type]

        if feature_name in def_info["features"]:
            return context_type

        for supertype in def_info["supertypes"]:
            result = self.find_defining_type_for_feature(feature_name, supertype)
            if result is not None:
                return result

        return None


# ---------------------------------------------------------------------------
# Reference Collector
# ---------------------------------------------------------------------------

class ReferenceCollector:
    """Collect all qualified-name references from a model's grammar tree.

    Returns list of ``(qualified_name_str, element, scope_path)`` tuples where
    ``scope_path`` is the list of scope names from root to the element.
    """

    def collect(self, model: Any) -> list[tuple[str, Any, list[str]]]:
        results: list[tuple[str, Any, list[str]]] = []
        self._walk(model, results, [])
        return results

    def _walk(self, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]) -> None:
        if element is None:
            return

        # Compute child scope path
        name = getattr(element, "name", None)
        elem_type = type(element).__name__
        is_container = getattr(element, "is_definition", False) or elem_type == "Package"
        child_scope = scope_path
        if is_container and name is not None and elem_type != "Model":
            child_scope = scope_path + [name]

        grammar = getattr(element, "grammar", None)
        if grammar is not None:
            self._extract_from_grammar(grammar, element, results, scope_path)

        for child in getattr(element, "children", []):
            self._walk(child, results, child_scope)

    def _extract_from_grammar(
        self, grammar: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        usage = getattr(grammar, "usage", None)
        if usage is None:
            usage = grammar

        if usage is None:
            return

        decl = getattr(usage, "declaration", None)
        if decl is None:
            return

        inner_decl = getattr(decl, "declaration", None)
        if inner_decl is None:
            return

        spec = getattr(inner_decl, "specialization", None)
        if spec is None:
            return

        self._collect_specialization_part(spec, element, results, scope_path)

    def _collect_specialization_part(
        self, spec: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        if spec is None:
            return

        for fs in getattr(spec, "specializations", []):
            self._collect_feature_specialization(fs, element, results, scope_path)

        for fs in getattr(spec, "specializations2", []):
            self._collect_feature_specialization(fs, element, results, scope_path)

    def _collect_feature_specialization(
        self, fs: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        if fs is None:
            return

        rel = getattr(fs, "relationship", None)
        if rel is None:
            return

        rel_type = type(rel).__name__

        if rel_type == "Typings":
            self._collect_typings(rel, element, results, scope_path)
        elif rel_type == "Subsettings":
            self._collect_subsettings(rel, element, results, scope_path)
        elif rel_type == "Redefinitions":
            self._collect_redefinitions(rel, element, results, scope_path)
        elif rel_type == "SubclassificationPart":
            self._collect_subclassification(rel, element, results, scope_path)

    def _collect_typings(
        self, typings: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        tb = getattr(typings, "typing", None)
        if tb is not None:
            for ft in getattr(tb, "relationships", []):
                self._collect_feature_typing(ft, element, results, scope_path)

        for ft in getattr(typings, "relationships", []):
            self._collect_feature_typing(ft, element, results, scope_path)

    def _collect_feature_typing(
        self, ft: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        if ft is None:
            return

        rel = getattr(ft, "relationship", None)
        if rel is None:
            return

        rel_type = type(rel).__name__

        if rel_type == "OwnedFeatureTyping":
            ftype = getattr(rel, "type", None)
            if ftype is not None:
                qn = getattr(ftype, "type", None)
                if qn is not None:
                    names = getattr(qn, "names", [])
                    if names:
                        results.append(("::".join(names), element, scope_path))

        elif rel_type == "ConjugatedPortTyping":
            qn = getattr(rel, "name", None)
            if qn is not None:
                names = getattr(qn, "names", [])
                if names:
                    results.append(("::".join(names), element, scope_path))

    def _collect_subsettings(
        self, sub: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        for child in getattr(sub, "children", []):
            for el in getattr(child, "elements", []):
                names = getattr(el, "names", [])
                if names:
                    results.append(("::".join(names), element, scope_path))

    def _collect_redefinitions(
        self, red: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        for child in getattr(red, "children", []):
            rf = getattr(child, "redefinedFeature", None)
            if rf is not None:
                names = getattr(rf, "names", [])
                if names:
                    results.append(("::".join(names), element, scope_path))

    def _collect_subclassification(
        self, sc: Any, element: Any, results: list[tuple[str, Any, list[str]]], scope_path: list[str]
    ) -> None:
        for child in getattr(sc, "children", []):
            for el in getattr(child, "elements", []):
                names = getattr(el, "names", [])
                if names:
                    results.append(("::".join(names), element, scope_path))


# ---------------------------------------------------------------------------
# Semantic Analyzer
# ---------------------------------------------------------------------------

# Symbols that are always considered defined (standard library types).
_KNOWN_LIBRARY_SYMBOLS = frozenset({
    # Scalar values
    "ScalarValues::Boolean", "ScalarValues::Integer", "ScalarValues::Natural",
    "ScalarValues::Positive", "ScalarValues::Nonnegative",
    "ScalarValues::Rational", "ScalarValues::Real", "ScalarValues::String",
    "ScalarValues::Complex", "ScalarValues::UnlimitedNatural",
    "ScalarValues::Number", "ScalarValues::ScalarValue",
    # ISQ base quantities
    "ISQ::Length", "ISQ::Mass", "ISQ::Time", "ISQ::ElectricCurrent",
    "ISQ::ThermodynamicTemperature", "ISQ::AmountOfSubstance",
    "ISQ::LuminousIntensity", "ISQ::Angle", "ISQ::SolidAngle",
    "ISQ::Information",
    # ISQ value types
    "ISQ::LengthValue", "ISQ::MassValue", "ISQ::TimeValue",
    "ISQ::ElectricCurrentValue", "ISQ::ThermodynamicTemperatureValue",
    "ISQ::AmountOfSubstanceValue", "ISQ::LuminousIntensityValue",
    "ISQ::AngleValue", "ISQ::SolidAngleValue", "ISQ::InformationValue",
    # Common derived quantities
    "ISQ::Area", "ISQ::Volume", "ISQ::Velocity", "ISQ::Acceleration",
    "ISQ::Force", "ISQ::Pressure", "ISQ::Energy", "ISQ::Power",
    "ISQ::ElectricCharge", "ISQ::Voltage", "ISQ::Capacitance",
    "ISQ::Resistance", "ISQ::Conductance", "ISQ::MagneticFlux",
    "ISQ::MagneticFluxDensity", "ISQ::Inductance", "ISQ::Frequency",
    "ISQ::AreaValue", "ISQ::VolumeValue", "ISQ::VelocityValue",
    "ISQ::AccelerationValue", "ISQ::ForceValue", "ISQ::PressureValue",
    "ISQ::EnergyValue", "ISQ::PowerValue", "ISQ::ElectricChargeValue",
    "ISQ::VoltageValue", "ISQ::CapacitanceValue", "ISQ::ResistanceValue",
    "ISQ::ConductanceValue", "ISQ::MagneticFluxValue",
    "ISQ::MagneticFluxDensityValue", "ISQ::InductanceValue",
    "ISQ::FrequencyValue",
    # Base KerML/SysML types
    "KerML::Element", "KerML::Type", "KerML::Feature",
    "KerML::Namespace", "KerML::Relationship",
    "SysML::Occurrence", "SysML::Item", "SysML::Part",
    "SysML::Port", "SysML::Action", "SysML::State",
    "SysML::Requirement", "SysML::Connection",
    "SysML::Flow", "SysML::Interface",
    "SysML::Calculation", "SysML::Constraint",
    "SysML::Enumeration", "SysML::Case",
    "SysML::UseCase", "SysML::AnalysisCase",
    "SysML::VerificationCase", "SysML::View",
    "SysML::Viewpoint", "SysML::Concern",
    "SysML::Allocation", "SysML::Metadata",
    "SysML::Rendering", "SysML::Individual",
})


class SemanticAnalyzer:
    """Analyzes a parsed SysML model for semantic issues."""

    def analyze(self, model: Any) -> list[SemanticIssue]:
        """Run semantic analysis on *model* and return a list of issues."""
        issues: list[SemanticIssue] = []

        # Step 1: Build symbol table
        symtab = SymbolTable()
        symtab.build_from_model(model)

        # Step 2: Validate imports (check if import targets exist)
        issues.extend(self._validate_imports(symtab))

        # Step 3: Collect all references with scope paths
        collector = ReferenceCollector()
        references = collector.collect(model)

        # Step 4: Cross-reference using scope-aware lookup
        for ref_str, element, scope_path in references:
            if self._is_resolved(ref_str, symtab, scope_path):
                continue
            issues.append(SemanticIssue(
                severity="error",
                code="UNDEFINED_SYMBOL",
                message=f"Undefined symbol '{ref_str}' referenced in "
                        f"{type(element).__name__} '{getattr(element, 'name', '<anonymous>')}'",
                element=element,
                reference=ref_str,
            ))

        return issues

    def _validate_imports(self, symtab: SymbolTable) -> list[SemanticIssue]:
        """Validate that all import targets exist in the model."""
        issues: list[SemanticIssue] = []
        self._check_imports_in_scope(symtab, symtab, issues)
        return issues

    def _check_imports_in_scope(
        self, symtab: SymbolTable, table: SymbolTable, issues: list[SemanticIssue]
    ) -> None:
        """Check imports in this scope and recurse into children."""
        for imp in table._imports:
            self._validate_single_import(symtab, table, imp, issues)

        for child_table in table._children.values():
            self._check_imports_in_scope(symtab, child_table, issues)

    def _validate_single_import(
        self, symtab: SymbolTable, table: SymbolTable, imp: Any, issues: list[SemanticIssue]
    ) -> None:
        """Validate a single Import object."""
        if not imp.children:
            return

        import_child = imp.children[0]
        child_type = type(import_child).__name__

        if child_type == "MembershipImport":
            self._validate_membership_import(symtab, table, import_child, issues)
        elif child_type == "NamespaceImport":
            self._validate_namespace_import(symtab, table, import_child, issues)

    def _validate_membership_import(
        self, symtab: SymbolTable, table: SymbolTable, mem_import: Any, issues: list[SemanticIssue]
    ) -> None:
        """Validate a MembershipImport targets an existing element."""
        imported_mem = getattr(mem_import, "membership", None)
        if imported_mem is None:
            return

        qn = getattr(imported_mem, "name", None)
        if qn is None:
            return

        names = getattr(qn, "names", [])
        if not names:
            return

        ref_str = "::".join(names)
        element = symtab._resolve_qualified_name(ref_str, table)
        if element is None:
            issues.append(SemanticIssue(
                severity="error",
                code="UNRESOLVED_IMPORT",
                message=f"Import target '{ref_str}' does not exist",
                element=None,
                reference=ref_str,
            ))

    def _validate_namespace_import(
        self, symtab: SymbolTable, table: SymbolTable, ns_import: Any, issues: list[SemanticIssue]
    ) -> None:
        """Validate a NamespaceImport targets an existing namespace."""
        imported_ns = getattr(ns_import, "namespace", None)
        if imported_ns is None:
            return

        qn = getattr(imported_ns, "namespaces", None)
        if qn is None:
            return

        names = getattr(qn, "names", [])
        if not names:
            return

        ref_str = "::".join(names)
        target_table = symtab._find_namespace_table(ref_str, table)
        if target_table is None:
            issues.append(SemanticIssue(
                severity="error",
                code="UNRESOLVED_IMPORT",
                message=f"Import namespace '{ref_str}' does not exist",
                element=None,
                reference=ref_str,
            ))

    def _is_resolved(self, ref_str: str, symtab: SymbolTable, scope_path: list[str]) -> bool:
        """Check if a qualified name reference can be resolved from the given scope."""
        # Check known library symbols (loaded from .kerml/.sysml files)
        if ref_str in LibrarySymbolIndex.get_symbols():
            return True

        # Also check the hardcoded fallback for backwards compatibility
        if ref_str in _KNOWN_LIBRARY_SYMBOLS:
            return True

        # Get the symbol table for the scope where the reference is
        current = symtab
        for scope_name in scope_path:
            child = current._children.get(scope_name)
            if child is not None:
                current = child
            else:
                break

        # Direct lookup from current scope (walks up parent chain)
        if current.lookup(ref_str) is not None:
            return True

        # Check inherited features from supertypes
        if self._resolve_inherited(ref_str, symtab, scope_path):
            return True

        # Try as qualified name: resolve path P::A
        if "::" in ref_str:
            parts = ref_str.split("::")
            lookup_table = current
            all_found = True
            for i, part in enumerate(parts):
                # Find the element (may be in parent scope)
                found = lookup_table.lookup(part)
                if found is None:
                    all_found = False
                    break
                # Find the child scope for this part
                child_scope = lookup_table._children.get(part)
                if child_scope is None:
                    # The element was found via parent lookup.
                    # Find the table that actually contains this symbol.
                    owner = lookup_table._find_symbol_owner(part)
                    if owner is not None:
                        child_scope = owner._children.get(part)
                if child_scope is not None:
                    lookup_table = child_scope
                else:
                    all_found = False
                    break
            if all_found:
                return True

            # Fall back to simple name lookup for the last part
            return current.lookup(parts[-1]) is not None

        return False

    def _resolve_inherited(self, ref_str: str, symtab: SymbolTable, scope_path: list[str]) -> bool:
        """Check if *ref_str* is an inherited feature from a supertype in the scope chain."""
        # Walk scope_path to find the nearest definition that has supertypes
        for i in range(len(scope_path) - 1, -1, -1):
            context_type = scope_path[i]
            if context_type in symtab._definition_features:
                result = symtab.find_defining_type_for_feature(ref_str, context_type)
                if result is not None:
                    return True
        return False


    def _find_child_scope(self, root: SymbolTable, path: list[str]) -> Optional[SymbolTable]:
        """Find the symbol table scope for a qualified path from the root."""
        current = root
        for part in path:
            child = current._children.get(part)
            if child is None:
                return None
            current = child
        return current


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def analyze(model: Any) -> list[SemanticIssue]:
    """Run semantic analysis on *model* and return issues.

    Parameters
    ----------
    model : Model
        A parsed SysML model.

    Returns
    -------
    list[SemanticIssue]
        List of semantic issues found.
    """
    return SemanticAnalyzer().analyze(model)
