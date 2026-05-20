#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlantUML generator for SysML v2 models parsed by sysmlpy.

Follows the approach of the official SysML v2 Pilot Implementation:
maps SysML v2 relationships to PlantUML arrow approximations with
thickness/color differentiation and stereotype-based element styling.
"""

from sysmlpy.usage import Usage
from sysmlpy.definition import Model, Package


# ============================================================
# Relationship Arrow Mappings
# Based on the official org.omg.sysml.plantuml reference impl
# ============================================================

ARROW_STYLES = {
    # Containment / Membership
    "composite":      "*--",       # filled diamond (isComposite=True)
    "shared":         "o--",       # hollow diamond (isComposite=False)
    "owning":         "+--",       # plus sign (owning membership)
    "non_owning":     "+..",       # dotted plus (non-owning membership)

    # Typing / Specialization
    "typing":         "--:|>",     # colon + block arrow (feature typing)
    "specialization": "--|>",      # block arrow (general specialization)
    "redefinition":   "--||>",     # double bar + block arrow

    # Connections
    "binding":        "-[thickness=4,#E74C3C]-",   # thick red line, no arrowhead
    "connector":      "-[thickness=2,#3498DB]->",  # medium blue arrow
    "flow":           "-->",       # dotted arrow
    "succession":     "-->",       # dotted arrow
    "allocation":     "-[thickness=3,dotted,#9B59B6]->",  # thick dotted purple

    # Dependencies
    "dependency":     "..>>",      # dotted double-arrow
    "satisfy":        "-->",       # dotted arrow
    "verify":         "-->",       # dotted arrow
    "derive":         "*--",       # composite containment
    "refine":         "..>>",      # dotted double-arrow

    # Comments / Annotations
    "comment":        "..",        # dotted line, no arrowhead
    "import":         "..>",       # dotted arrow
}


# ============================================================
# Stereotype Mappings
# Maps sysml_type to PlantUML stereotype badges
# ============================================================

DEFINITION_STEREOTYPES = {
    "part":       "part def",
    "item":       "item def",
    "attribute":  "attribute def",
    "port":       "port def",
    "action":     "action def",
    "state":      "state def",
    "constraint": "constraint def",
    "requirement": "requirement def",
    "use_case":   "use case def",
    "case":       "case def",
    "analysis_case": "analysis case def",
    "verification_case": "verification case def",
    "connection": "connection def",
    "flow":       "flow def",
    "allocation": "allocation def",
    "metadata":   "metadata def",
    "view":       "view def",
    "viewpoint":  "viewpoint def",
    "concern":    "concern def",
    "interface":  "interface def",
    "enumeration": "enumeration def",
}

USAGE_STEREOTYPES = {
    "part":       "part",
    "item":       "item",
    "attribute":  "attribute",
    "port":       "port",
    "action":     "action",
    "state":      "state",
    "constraint": "constraint",
    "requirement": "requirement",
    "use_case":   "use case",
    "case":       "case",
    "analysis_case": "analysis case",
    "verification_case": "verification case",
    "connection": "connection",
    "flow":       "flow",
    "allocation": "allocation",
    "metadata":   "metadata",
    "view":       "view",
    "viewpoint":  "viewpoint",
    "concern":    "concern",
    "interface":  "interface",
    "enumeration": "enumeration",
}

# Color scheme for stereotypes (letter, color)
STEREOTYPE_COLORS = {
    "part":       ("P", "#32CD32"),
    "item":       ("I", "#32CD32"),
    "attribute":  ("A", "#32CD32"),
    "port":       ("P", "#4169E1"),
    "action":     ("A", "#F39C12"),
    "state":      ("S", "#9B59B6"),
    "constraint": ("C", "#E67E22"),
    "requirement": ("R", "#E74C3C"),
    "use_case":   ("UC", "#16A085"),
    "case":       ("C", "#16A085"),
    "analysis_case": ("AC", "#16A085"),
    "verification_case": ("VC", "#16A085"),
    "connection": ("C", "#3498DB"),
    "flow":       ("F", "#27AE60"),
    "allocation": ("A", "#9B59B6"),
    "metadata":   ("M", "#95A5A6"),
    "view":       ("V", "#8E44AD"),
    "viewpoint":  ("VP", "#8E44AD"),
    "concern":    ("CN", "#7F8C8D"),
    "interface":  ("IF", "#3498DB"),
    "enumeration": ("E", "#F1C40F"),
}


def _get_typedby_name(element):
    """Extract the typed-by type name from an element's grammar structure."""
    g = getattr(element, 'grammar', None)
    if g is None:
        return None

    # Navigate: PartUsage -> usage -> declaration -> declaration -> specialization
    # -> specializations[0] -> relationship -> typing -> relationships[0]
    # -> relationship -> type -> type -> names
    try:
        usage = getattr(g, 'usage', None)
        if usage is None:
            return None
        decl = getattr(usage, 'declaration', None)
        if decl is None:
            return None
        inner_decl = getattr(decl, 'declaration', None)
        if inner_decl is None:
            return None
        spec_part = getattr(inner_decl, 'specialization', None)
        if spec_part is None:
            return None
        specs = getattr(spec_part, 'specializations', None)
        if not specs:
            return None

        for spec in specs:
            rel = getattr(spec, 'relationship', None)
            if rel is None:
                continue
            typing = getattr(rel, 'typing', None)
            if typing is None:
                continue
            relationships = getattr(typing, 'relationships', None)
            if not relationships:
                continue

            for r in relationships:
                rr = getattr(r, 'relationship', None)
                if rr is None:
                    continue
                ft = getattr(rr, 'type', None)
                if ft is None:
                    continue
                qn = getattr(ft, 'type', None)
                if qn is None:
                    continue
                names = getattr(qn, 'names', None)
                if names:
                    return names[0]
    except (AttributeError, IndexError):
        pass

    return None


def _get_specializes_names(element):
    """Extract specialization (superclass) names from a definition's grammar."""
    g = getattr(element, 'grammar', None)
    if g is None:
        return []

    names = []
    try:
        # For definitions: get_definition -> definition -> declaration -> subclassificationpart
        defn_method = getattr(g, 'get_definition', None)
        if defn_method is None:
            return []

        d = defn_method() if callable(defn_method) else defn_method
        if not isinstance(d, dict):
            return []

        definition = d.get('definition') or d.get('usage')
        if not definition:
            return []

        declaration = definition.get('declaration')
        if not declaration:
            return []

        # The subclassificationpart is directly under declaration for definitions
        subclass_part = declaration.get('subclassificationpart')
        if not subclass_part:
            return []

        owned_rel = subclass_part.get('ownedRelationship', [])
        for rel in owned_rel:
            if rel.get('name') == 'OwnedSubclassification':
                sc = rel.get('superclassifier')
                if sc and sc.get('names'):
                    names.extend(sc['names'])
    except (AttributeError, TypeError):
        pass

    return names


def _get_redefines_names(element):
    """Extract redefinition names from an element's grammar."""
    g = getattr(element, 'grammar', None)
    if g is None:
        return []

    names = []
    try:
        usage = getattr(g, 'usage', None)
        if usage is None:
            return []
        decl = getattr(usage, 'declaration', None)
        if decl is None:
            return []
        inner_decl = getattr(decl, 'declaration', None)
        if inner_decl is None:
            return []
        spec_part = getattr(inner_decl, 'specialization', None)
        if spec_part is None:
            return []
        specs = getattr(spec_part, 'specializations', None)
        if not specs:
            return []

        for spec in specs:
            rel = getattr(spec, 'relationship', None)
            if rel is None:
                continue
            # Check for Redefinitions
            if hasattr(rel, 'children'):
                for child in rel.children:
                    if hasattr(child, 'redefinedFeature'):
                        rf = child.redefinedFeature
                        if hasattr(rf, 'names'):
                            names.extend(rf.names)
    except (AttributeError, IndexError):
        pass

    return names


def _get_stereotype(element):
    """Get the stereotype string for an element."""
    sysml_type = getattr(element, 'sysml_type', None)
    if sysml_type is None:
        return ""

    is_def = getattr(element, 'is_definition', False)
    stereotype_map = DEFINITION_STEREOTYPES if is_def else USAGE_STEREOTYPES
    label = stereotype_map.get(sysml_type, sysml_type)

    color_info = STEREOTYPE_COLORS.get(sysml_type, ("T", "#3498DB"))
    letter, color = color_info

    return f"<<({letter},{color}) {label}>>"


def _get_element_name(element):
    """Get a safe PlantUML name for an element."""
    name = getattr(element, 'name', None)

    # If no declared name, check for redefinition target
    if name is None or len(name) > 30:  # UUID heuristic
        redefines = _get_redefines_names(element)
        if redefines:
            return f":>> {redefines[0]}"

    if name is None:
        return "unnamed"

    # Escape quotes and special chars
    name = name.replace('"', "''").replace("\n", "\\n")
    return name


def _get_element_id(element, id_map):
    """Get or create a unique PlantUML alias for an element."""
    elem_id = id(element)
    if elem_id not in id_map:
        alias = f"E{len(id_map) + 1}"
        id_map[elem_id] = alias
    return id_map[elem_id]


class PlantUMLGenerator:
    """
    Generates PlantUML text from a sysmlpy Model.

    Usage:
        # Full model
        model = sysmlpy.loads('package P { part def Car { part engine; } }')
        puml = PlantUMLGenerator(model).generate()

        # Focus on a specific element and its subtree
        car = model.find('Car')[0]
        puml = PlantUMLGenerator(model, focus=car).generate()

        # Select specific elements
        wheel = model.find('Wheel')[0]
        axle = model.find('Axle')[0]
        puml = PlantUMLGenerator(model, elements=[wheel, axle]).generate()
    """

    def __init__(self, model, style="color", direction="TB", include_legend=True,
                 focus=None, elements=None, max_depth=None, show_external=False):
        """
        Args:
            model: A sysmlpy Model instance
            style: "color" for colored stereotypes, "bw" for monochrome
            direction: "TB" for top-to-bottom, "LR" for left-to-right
            include_legend: Whether to include a relationship legend
            focus: A single element to focus on (renders it and its subtree)
            elements: A list of specific elements to include (ignores focus if set)
            max_depth: Maximum depth to traverse from focus element (None = unlimited)
            show_external: If True, show relationships to elements outside the selection
                          as dashed/ghosted lines. If False, hide them entirely.
        """
        self.model = model
        self.style = style
        self.direction = direction
        self.include_legend = include_legend
        self.focus = focus
        self.elements_filter = elements
        self.max_depth = max_depth
        self.show_external = show_external
        self.id_map = {}
        self.elements = []
        self.relationships = []
        self._visited = set()
        self._included_ids = set()  # Elements that are in the selection

    def _build_inclusion_set(self):
        """Build the set of element IDs that should be included in the diagram."""
        if self.elements_filter is not None:
            # Explicit element list
            for elem in self.elements_filter:
                self._included_ids.add(id(elem))
        elif self.focus is not None:
            # Focus on a single element and its subtree
            self._collect_subtree(self.focus, depth=0)
        else:
            # Include everything
            self._included_ids.add(id(self.model))
            for child in self.model.children:
                self._collect_subtree(child, depth=0)

    def _collect_subtree(self, element, depth):
        """Recursively collect all elements in a subtree up to max_depth."""
        elem_id = id(element)
        if elem_id in self._included_ids:
            return
        self._included_ids.add(elem_id)

        if self.max_depth is not None and depth >= self.max_depth:
            return

        children = getattr(element, 'children', None)
        if children:
            for child in children:
                self._collect_subtree(child, depth + 1)

    def _is_included(self, element):
        """Check if an element is in the inclusion set."""
        return id(element) in self._included_ids

    def generate(self):
        """Generate complete PlantUML text."""
        lines = []

        # Build inclusion set
        self._build_inclusion_set()

        # Header
        lines.append("@startuml")
        lines.append("")

        # Style block
        lines.extend(self._generate_style())
        lines.append("")

        # Direction
        if self.direction == "LR":
            lines.append("left to right direction")
        else:
            lines.append("top to bottom direction")
        lines.append("")

        # Title
        if self.focus is not None:
            focus_name = getattr(self.focus, 'name', None) or "Focus"
            title = f"SysML v2 — {focus_name}"
        elif self.elements_filter is not None:
            title = f"SysML v2 — Selected Elements ({len(self.elements_filter)})"
        else:
            title = getattr(self.model, 'name', None) or "SysML v2 Diagram"
        lines.append(f'title {title}')
        lines.append("")

        # Hide default circle on state diagrams
        lines.append("hide circle")
        lines.append("")

        # Traverse model and collect elements + relationships
        self._traverse(self.model)

        # Output elements
        for alias, name, stereotype, elem, is_included in self.elements:
            lines.append(self._render_element(alias, name, stereotype, elem, is_included))

        lines.append("")

        # Output relationships
        for src, arrow, dst, label, is_external in self.relationships:
            if is_external and not self.show_external:
                continue

            # Style external relationships differently
            if is_external:
                arrow = f"-[dotted,thickness=1,#999999]{arrow.lstrip('-')}"

            if label:
                lines.append(f'{src} {arrow} {dst} : {label}')
            else:
                lines.append(f'{src} {arrow} {dst}')

        lines.append("")

        # Legend
        if self.include_legend:
            lines.extend(self._generate_legend())
            lines.append("")

        lines.append("@enduml")
        return "\n".join(lines)

    def _generate_style(self):
        """Generate CSS style block."""
        if self.style == "bw":
            return [
                "skinparam monochrome true",
                "skinparam wrapWidth 300",
                "skinparam roundcorner 20",
            ]

        return [
            "<style>",
            "root {",
            "    BackGroundColor white",
            "    FontName Helvetica",
            "    FontSize 13",
            "}",
            "rectangle {",
            "    LineColor #444444",
            "    LineThickness 1.5",
            "    BackgroundColor white",
            "    Padding 10",
            "}",
            "arrow {",
            "    LineColor #555555",
            "    LineThickness 1.5",
            "    FontSize 11",
            "}",
            "</style>",
            "",
            "skinparam wrapWidth 400",
            "",
            "skinparam rectangle<<part def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<item def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<attribute def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<port def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<action def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<state def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<requirement def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<part>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<item>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<attribute>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<port>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<action>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<state>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<requirement>> {",
            "    RoundCorner 15",
            "}",
        ]

    def _traverse(self, element, parent=None):
        """Recursively traverse the model tree, collecting elements and relationships."""
        elem_id = id(element)
        if elem_id in self._visited:
            return
        self._visited.add(elem_id)

        # Skip the root Model itself (start from its children)
        if isinstance(element, Model):
            for child in element.children:
                self._traverse(child, parent=None)
            return

        # Skip Package containers (we flatten the structure, don't render packages)
        if isinstance(element, Package):
            for child in element.children:
                self._traverse(child, parent=None)
            return

        # Check if this element is in the inclusion set
        is_included = self._is_included(element)

        # Register this element if included, or if show_external and it's referenced
        if is_included or self.show_external:
            alias = _get_element_id(element, self.id_map)
            name = _get_element_name(element)
            stereotype = _get_stereotype(element)
            self.elements.append((alias, name, stereotype, element, is_included))

        # Containment relationship (parent -> child)
        # Only add if parent is a renderable element (not Model or Package)
        if parent is not None and not isinstance(parent, (Model, Package)):
            parent_included = self._is_included(parent)
            # Only show containment if both parent and child are included
            if is_included and parent_included:
                parent_alias = _get_element_id(parent, self.id_map)
                arrow = ARROW_STYLES["composite"]
                self.relationships.append((parent_alias, arrow, alias, None, False))

        # Typing relationship (element -> typedby)
        # First try the typedby attribute, then extract from grammar
        typedby = getattr(element, 'typedby', None)
        if typedby is None:
            typedby_name = _get_typedby_name(element)
            if typedby_name:
                typedby = self.model.find(typedby_name)
                if typedby:
                    typedby = typedby[0] if isinstance(typedby, list) else typedby

        if typedby is not None:
            typedby_id = id(typedby)
            if typedby_id not in self._visited:
                self._traverse(typedby, parent=None)
            typedby_included = self._is_included(typedby)
            # Show typing if source is included; mark as external if target is not
            if is_included:
                typedby_alias = _get_element_id(typedby, self.id_map)
                arrow = ARROW_STYLES["typing"]
                is_external = not typedby_included
                self.relationships.append((alias, arrow, typedby_alias, "types", is_external))

        # Specialization relationship (definition -> superclass)
        if getattr(element, 'is_definition', False):
            specializes_names = _get_specializes_names(element)
            for super_name in specializes_names:
                super_elem = self.model.find(super_name)
                if super_elem:
                    super_elem = super_elem[0] if isinstance(super_elem, list) else super_elem
                    super_id = id(super_elem)
                    if super_id not in self._visited:
                        self._traverse(super_elem, parent=None)
                    super_included = self._is_included(super_elem)
                    if is_included:
                        super_alias = _get_element_id(super_elem, self.id_map)
                        arrow = ARROW_STYLES["specialization"]
                        is_external = not super_included
                        self.relationships.append((alias, arrow, super_alias, "specializes", is_external))

        # Redefinition relationship (usage -> redefined feature)
        redefines_names = _get_redefines_names(element)
        for redef_name in redefines_names:
            redef_elem = self.model.find(redef_name)
            if redef_elem:
                redef_elem = redef_elem[0] if isinstance(redef_elem, list) else redef_elem
                redef_id = id(redef_elem)
                if redef_id not in self._visited:
                    self._traverse(redef_elem, parent=None)
                redef_included = self._is_included(redef_elem)
                if is_included:
                    redef_alias = _get_element_id(redef_elem, self.id_map)
                    arrow = ARROW_STYLES["redefinition"]
                    is_external = not redef_included
                    self.relationships.append((alias, arrow, redef_alias, "redefines", is_external))

        # Traverse children
        children = getattr(element, 'children', None)
        if children:
            for child in children:
                self._traverse(child, parent=element)

    def _render_element(self, alias, name, stereotype, element, is_included=True):
        """Render a single element as PlantUML text."""
        sysml_type = getattr(element, 'sysml_type', '')

        if sysml_type == 'state':
            keyword = "state"
        elif sysml_type == 'action':
            keyword = "rectangle"
        else:
            keyword = "rectangle"

        safe_name = name.replace('"', "''")

        if stereotype:
            return f'{keyword} "{safe_name}" as {alias} {stereotype}'
        else:
            return f'{keyword} "{safe_name}" as {alias}'

    def _generate_legend(self):
        """Generate a relationship legend table."""
        legend = [
            "legend right",
            "  <b>SysML v2 Relationship Legend</b>",
            "  |= Relationship |= Notation |",
        ]

        legend_items = [
            ("Feature Typing", "--:|>", "types"),
            ("Specialization", "--|>", "specializes"),
            ("Redefinition", "--||>", "redefines"),
            ("Composite (owns)", "*--", "owns"),
            ("Shared", "o--", "shares"),
            ("Binding", "-[thickness=4]-", "binds"),
            ("Connector", "-[thickness=2]->", "connects"),
            ("Flow", "-->", "flows"),
            ("Dependency", "..>>", "depends"),
        ]

        for rel_name, notation, _ in legend_items:
            legend.append(f"  | {rel_name} | {notation} |")

        legend.append("endlegend")
        return legend


def to_plantuml(model, style="color", direction="TB", include_legend=True,
                focus=None, elements=None, max_depth=None, show_external=False):
    """
    Convenience function to generate PlantUML text from a sysmlpy Model.

    Args:
        model: A sysmlpy Model instance (from sysmlpy.loads())
        style: "color" or "bw"
        direction: "TB" or "LR"
        include_legend: bool
        focus: A single element to focus on (renders it and its subtree)
        elements: A list of specific elements to include
        max_depth: Maximum depth to traverse from focus (None = unlimited)
        show_external: If True, show relationships to elements outside selection

    Returns:
        str: PlantUML text
    """
    gen = PlantUMLGenerator(model, style=style, direction=direction,
                            include_legend=include_legend, focus=focus,
                            elements=elements, max_depth=max_depth,
                            show_external=show_external)
    return gen.generate()
