#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlantUML generator for SysML v2 models parsed by sysmlpy.

Follows the approach of the official SysML v2 Pilot Implementation:
maps SysML v2 relationships to PlantUML arrow approximations with
thickness/color differentiation and stereotype-based element styling.

Supports multiple rendering styles per SysML v2 View semantics:
- Graphical rendering (default): elements as shapes with relationship arrows
- Interconnection diagram: focus on connectors, bindings, and flows
- Tree diagram: hierarchical containment structure
- Element table: tabular listing of elements and properties
- Textual notation: structured text representation
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


def _get_stereotype(element, style="bw"):
    """Get the stereotype string for an element."""
    sysml_type = getattr(element, 'sysml_type', None)
    if sysml_type is None:
        return ""

    is_def = getattr(element, 'is_definition', False)
    stereotype_map = DEFINITION_STEREOTYPES if is_def else USAGE_STEREOTYPES
    label = stereotype_map.get(sysml_type, sysml_type)

    if style == "bw":
        # Simple label without colors for journal rendering
        return f"<<{label}>>"

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


def _arrow_to_rel_type(arrow):
    """Map a PlantUML arrow string back to a relationship type name."""
    for rel_type, pattern in ARROW_STYLES.items():
        if pattern in arrow or arrow in pattern:
            return rel_type
    return None


def _extract_flow_endpoints(flow_element):
    """Extract (from_names, to_names) from a flow element's grammar.

    Navigates the FlowConnectionDeclaration structure to recover
    the source and target qualified name references.

    Returns:
        (from_names, to_names) where each is a list of name strings
        (e.g. ["actionName", "portName"]) or None if not available.
    """
    g = getattr(flow_element, 'grammar', None)
    if g is None:
        return None, None

    declaration = getattr(g, 'declaration', None)
    if declaration is None:
        return None, None

    children = getattr(declaration, 'children', None)
    if not children or len(children) < 3:
        return None, None

    from_names = None
    to_names = None

    for end_idx, result in [(1, 'from'), (2, 'to')]:
        end_member = children[end_idx]
        if end_member is None:
            continue
        if not hasattr(end_member, 'children'):
            continue

        flow_end = end_member.children
        if flow_end is None:
            continue
        if not hasattr(flow_end, 'children'):
            continue

        for child in flow_end.children:
            if hasattr(child, 'children') and hasattr(child.children, 'names'):
                names = child.children.names
                if result == 'from':
                    from_names = names
                else:
                    to_names = names

    return from_names, to_names


def _find_element_by_qualified_name(model, names):
    """Resolve a qualified name (e.g. ['a', 'q']) to a model element.

    First tries dot-separated model.find(), then falls back to
    searching by individual segments (action name -> child feature name).
    """
    if not names:
        return None

    # Try full dot-separated name first
    dot_name = '.'.join(names)
    found = model.find(dot_name)
    if found:
        return found[0] if isinstance(found, list) else found

    # Try segment by segment: model -> action -> feature
    for i in range(len(names), 0, -1):
        segment = '.'.join(names[:i])
        found = model.find(segment)
        if found:
            elem = found[0] if isinstance(found, list) else found
            # Walk remaining segments
            remaining = names[i:]
            current = elem
            for part in remaining:
                child = getattr(current, 'children', None)
                if child:
                    match = None
                    for c in child:
                        if getattr(c, 'name', None) == part:
                            match = c
                            break
                    if match:
                        current = match
                    else:
                        break
                else:
                    break
            return current

    return None


def _expand_with_connected_flows(model, included_ids, show_external=False):
    """Expand an inclusion set to include flows connected to selected elements.

    Scans all flow connections in the model (both Usage-level and grammar-level).
    For each flow connected to an already-included element (via its from/to
    endpoints or parent container), adds the flow and its endpoint elements
    to the set.

    Args:
        model: A sysmlpy Model instance
        included_ids: Mutable set of element IDs to expand
        show_external: If True, include all referenced endpoints even
                      if they are outside the original selection
    """
    # Get all flow connections (Usage and grammar level)
    flow_connections = _extract_flow_connections(model)

    for from_names, to_names, flow_name, is_grammar_obj in flow_connections:
        referenced_elements = []

        for names in [from_names, to_names]:
            if not names:
                continue
            elem = _find_element_by_qualified_name(model, names)
            if elem:
                referenced_elements.append(elem)

        # Check if any referenced element is in the inclusion set
        connected = False
        all_endpoint_elements = []

        for ref in referenced_elements:
            all_endpoint_elements.append(ref)
            if id(ref) in included_ids:
                connected = True
            # Also check parent of resolved element
            elem_parent = getattr(ref, 'parent', None)
            if elem_parent:
                all_endpoint_elements.append(elem_parent)
                if id(elem_parent) in included_ids:
                    connected = True

        if connected:
            if show_external:
                for ref in all_endpoint_elements:
                    included_ids.add(id(ref))


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

    def __init__(self, model, style="bw", direction="TB", include_legend=True,
                 focus=None, elements=None, max_depth=None, show_external=False,
                 custom_style=None):
        """
        Args:
            model: A sysmlpy Model instance
            style: "bw" for black-and-white (default, journal-ready),
                   "color" for colored stereotypes
            direction: "TB" for top-to-bottom, "LR" for left-to-right
            include_legend: Whether to include a relationship legend
            focus: A single element to focus on (renders it and its subtree)
            elements: A list of specific elements to include (ignores focus if set)
            max_depth: Maximum depth to traverse from focus element (None = unlimited)
            show_external: If True, show relationships to elements outside the selection
                          as dashed/ghosted lines. If False, hide them entirely.
            custom_style: Optional list of PlantUML style lines to append to the
                         default style. Useful for custom formatting while keeping
                         the base style consistent.
        """
        self.model = model
        self.style = style
        self.direction = direction
        self.include_legend = include_legend
        self.focus = focus
        self.elements_filter = elements
        self.max_depth = max_depth
        self.show_external = show_external
        self.custom_style = custom_style or []
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
            lines = [
                "skinparam monochrome true",
                "skinparam wrapWidth 300",
                "skinparam defaultFontSize 12",
                "skinparam defaultFontName Helvetica",
                "",
                "# Definitions: sharp corners, hatched background",
                "skinparam rectangle<<part def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "    StereotypeFontSize 11",
                "}",
                "skinparam rectangle<<item def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<attribute def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<port def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<action def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<state def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<requirement def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<view def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<viewpoint def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<enumeration def>> {",
                "    RoundCorner 0",
                "    BackgroundColor white",
                "}",
                "",
                "# Usages: rounded corners, plain background",
                "skinparam rectangle<<part>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<item>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<attribute>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<port>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<action>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<state>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<requirement>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<view>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<viewpoint>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "skinparam rectangle<<enumeration>> {",
                "    RoundCorner 15",
                "    BackgroundColor white",
                "}",
                "",
                "# Views as folders",
                "skinparam folder<<view def>> {",
                "    BackgroundColor white",
                "}",
                "skinparam folder<<view>> {",
                "    BackgroundColor white",
                "}",
            ]
        else:
            lines = [
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
                "skinparam folder<<view def>> {",
                "    BackgroundColor #F5E6FF",
                "    BorderColor #8E44AD",
                "}",
                "skinparam folder<<view>> {",
                "    BackgroundColor #F5E6FF",
                "    BorderColor #8E44AD",
                "}",
            ]

        # Append custom style overrides
        if self.custom_style:
            lines.append("")
            lines.extend(self.custom_style)

        return lines

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
            stereotype = _get_stereotype(element, style=self.style)
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
        elif sysml_type == 'view':
            keyword = "folder"
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


def to_plantuml(model, style="bw", direction="TB", include_legend=True,
                focus=None, elements=None, max_depth=None, show_external=False,
                custom_style=None):
    """
    Convenience function to generate PlantUML text from a sysmlpy Model.

    Args:
        model: A sysmlpy Model instance (from sysmlpy.loads())
        style: "bw" for black-and-white (default, journal-ready),
               "color" for colored stereotypes
        direction: "TB" or "LR"
        include_legend: bool
        focus: A single element to focus on (renders it and its subtree)
        elements: A list of specific elements to include
        max_depth: Maximum depth to traverse from focus (None = unlimited)
        show_external: If True, show relationships to elements outside selection
        custom_style: Optional list of PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    gen = PlantUMLGenerator(model, style=style, direction=direction,
                            include_legend=include_legend, focus=focus,
                            elements=elements, max_depth=max_depth,
                            show_external=show_external,
                            custom_style=custom_style)
    return gen.generate()


# ============================================================
# View Rendering Convenience Functions
# Per SysML v2 View semantics, views can be rendered in multiple ways.
# These functions provide ready-made configurations for common patterns.
# ============================================================


def as_graphical_rendering(model, focus=None, style="bw", direction="TB",
                           include_legend=True, max_depth=None,
                           show_external=False, custom_style=None):
    """Generate a graphical rendering of a model or view.

    This is the default rendering: elements as shapes (rectangles, folders)
    with relationship arrows (typing, specialization, containment, etc.).

    Corresponds to SysML v2 ``GraphicalRendering``.

    Args:
        model: A sysmlpy Model instance
        focus: Optional element to focus on (renders subtree)
        style: "bw" (default) or "color"
        direction: "TB" or "LR"
        include_legend: Whether to include relationship legend
        max_depth: Maximum depth to traverse from focus
        show_external: Show relationships to elements outside selection
        custom_style: Optional PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    gen = PlantUMLGenerator(model, style=style, direction=direction,
                            include_legend=include_legend, focus=focus,
                            max_depth=max_depth, show_external=show_external,
                            custom_style=custom_style)
    return gen.generate()


def as_interconnection_diagram(model, focus=None, elements=None, style="bw",
                                direction="TB", include_legend=True,
                                max_depth=None, show_external=False,
                                auto_include_connections=True,
                                custom_style=None):
    """Generate an Interconnection View (IV) diagram.

    Corresponds to SysML v2 ``InterconnectionView``. Presents exposed
    features as nodes, nested features as nested nodes, and connections
    between features as edges. Nested nodes may present boundary features
    (e.g., ports, parameters).

    When ``auto_include_connections=True`` (default), selecting features
    via ``focus`` or ``elements`` automatically discovers and includes all
    binding, connector, and flow connections involving those features.

    Args:
        model: A sysmlpy Model instance
        focus: Optional element to focus on (renders subtree)
        elements: Optional list of specific elements to include
        style: "bw" (default) or "color"
        direction: "TB" or "LR"
        include_legend: Whether to include relationship legend
        max_depth: Maximum depth to traverse from focus
        show_external: Show relationships to elements outside selection
        auto_include_connections: Auto-discover connections for selected
                                  features (bindings, connectors, flows)
        custom_style: Optional PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    lines = []
    lines.append("@startuml")
    lines.append("")

    # Style
    if style == "bw":
        lines.extend([
            "skinparam monochrome true",
            "skinparam wrapWidth 300",
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Helvetica",
            "",
            "skinparam rectangle<<part def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<part>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<port def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<port>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<interface def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<interface>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<item def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<item>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<attribute def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<attribute>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<connection def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<connection>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<flow def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<flow>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
        ])
    else:
        lines.extend([
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
            "</style>",
            "",
            "skinparam wrapWidth 400",
            "",
            "skinparam rectangle<<part def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<part>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<port def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<port>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<interface def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<interface>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<item def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<item>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<attribute>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<connection>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<flow>> {",
            "    RoundCorner 15",
            "}",
        ])

    if custom_style:
        lines.append("")
        lines.extend(custom_style)

    lines.append("")

    if direction == "LR":
        lines.append("left to right direction")
    else:
        lines.append("top to bottom direction")
    lines.append("")

    title = "Interconnection View"
    if focus is not None:
        focus_name = getattr(focus, 'name', None) or "Focus"
        title = f"Interconnection — {focus_name}"
    elif elements is not None:
        title = f"Interconnection — Selected Elements ({len(elements)})"
    lines.append(f'title {title}')
    lines.append("")
    lines.append("hide circle")
    lines.append("")

    # Build inclusion set
    gen = PlantUMLGenerator(model, style=style, focus=focus,
                            elements=elements, max_depth=max_depth,
                            include_legend=False,
                            show_external=show_external)
    gen._build_inclusion_set()

    # Auto-expand with connected flows (grammar-level scanning)
    if auto_include_connections:
        _expand_with_connected_flows(model, gen._included_ids,
                                     show_external=show_external)

    # Collect all flow connections for arrow rendering
    flow_connections = _extract_flow_connections(model)

    # Traverse
    gen._traverse(gen.model)

    id_map = gen.id_map
    elements_list = gen.elements
    relationships = gen.relationships

    # Filter to show interconnection-relevant elements
    iv_types = {"part", "port", "interface", "item", "attribute",
                "connection", "flow", "allocation"}

    for alias, name, stereotype, elem, is_included in elements_list:
        sysml_type = getattr(elem, 'sysml_type', '')
        if sysml_type in iv_types:
            keyword = "rectangle"
            if sysml_type == 'state':
                keyword = "state"
            elif sysml_type == 'view':
                keyword = "folder"
            lines.append(f'{keyword} "{name}" as {alias} {stereotype}')

    lines.append("")

    # Render containment, typing, and specialization relationships
    for src, arrow, dst, label, is_external in relationships:
        if is_external and not show_external:
            continue
        if is_external:
            arrow = f"-[dotted,thickness=1,#999999]{arrow.lstrip('-')}"
        if label:
            lines.append(f'{src} {arrow} {dst} : {label}')
        else:
            lines.append(f'{src} {arrow} {dst}')

    lines.append("")

    # Render flow connection arrows (from grammar-level scanning)
    for from_names, to_names, flow_name, is_grammar_obj in flow_connections:
        from_elem = _find_element_by_qualified_name(model, from_names) if from_names else None
        to_elem = _find_element_by_qualified_name(model, to_names) if to_names else None

        if from_elem is None or to_elem is None:
            continue

        from_id = id(from_elem)
        to_id = id(to_elem)

        from_included = from_id in gen._included_ids
        to_included = to_id in gen._included_ids
        if not (from_included or to_included):
            continue

        from_alias = id_map.get(from_id)
        to_alias = id_map.get(to_id)
        if from_alias and to_alias:
            label_text = flow_name if flow_name else "flow"
            lines.append(f'{from_alias} {ARROW_STYLES["flow"]} {to_alias} : {label_text}')

    lines.append("")

    if include_legend:
        lines.extend([
            "legend right",
            "  <b>Interconnection Legend</b>",
            "  |= Relationship |= Notation |",
            "  | Binding | -[thickness=4]- |",
            "  | Connector | -[thickness=2]-> |",
            "  | Flow Transfer | --> |",
            "  | Allocation | -[dotted]-> |",
            "  | Feature Typing | --:|> |",
            "  | Composite (owns) | *-- |",
            "  | Specialization | --|> |",
            "endlegend",
        ])
        lines.append("")

    lines.append("@enduml")
    return "\n".join(lines)


def as_interconnection_view(model, focus=None, elements=None, style="bw",
                             direction="TB", include_legend=True,
                             max_depth=None, show_external=False,
                             auto_include_connections=True,
                             custom_style=None):
    """Alias for :func:`as_interconnection_diagram`.

    Corresponds to SysML v2 ``InterconnectionView`` (short name ``iv``).
    """
    return as_interconnection_diagram(
        model, focus=focus, elements=elements, style=style,
        direction=direction, include_legend=include_legend,
        max_depth=max_depth, show_external=show_external,
        auto_include_connections=auto_include_connections,
        custom_style=custom_style,
    )


def as_action_flow_view(model, focus=None, elements=None, style="bw", direction="TB",
                        include_legend=True, max_depth=None, show_external=False,
                        auto_include_flows=True, custom_style=None):
    """Generate an Action Flow View (AFV) diagram.

    Corresponds to SysML v2 ``ActionFlowView``, which specializes
    ``InterconnectionView``. Presents connections between actions,
    including:
    - Actions with nested actions
    - Parameters with direction
    - Flow connection usages (transfers from output to input)
    - Binding connections between parameters

    When ``auto_include_flows=True`` (default), selecting actions via
    ``focus`` or ``elements`` automatically discovers and includes all
    flow connections and binding connections that involve those actions.

    Args:
        model: A sysmlpy Model instance
        focus: Optional element to focus on (renders its subtree)
        elements: Optional list of specific elements to include
        style: "bw" (default) or "color"
        direction: "TB" or "LR"
        include_legend: Whether to include relationship legend
        max_depth: Maximum depth to traverse from focus
        show_external: Show relationships to elements outside selection
        auto_include_flows: Auto-discover flows connected to selected actions
        custom_style: Optional PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    lines = []
    lines.append("@startuml")
    lines.append("")

    # Style block
    if style == "bw":
        lines.extend([
            "skinparam monochrome true",
            "skinparam wrapWidth 300",
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Helvetica",
            "",
            "skinparam rectangle<<action def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<action>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<flow def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<flow>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<attribute def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<attribute>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<port def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<port>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<part def>> {",
            "    RoundCorner 0",
            "    BackgroundColor white",
            "}",
            "skinparam rectangle<<part>> {",
            "    RoundCorner 15",
            "    BackgroundColor white",
            "}",
            "",
            "# Swim lane styling for actions",
            "skinparam rectangle<<action def>> {",
            "    StereotypeFontSize 11",
            "}",
            "skinparam rectangle<<action>> {",
            "    StereotypeFontSize 11",
            "}",
        ])
    else:
        lines.extend([
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
            "</style>",
            "",
            "skinparam wrapWidth 400",
            "",
            "skinparam rectangle<<action def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<action>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<flow def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<flow>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<attribute>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<port>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<part>> {",
            "    RoundCorner 15",
            "}",
        ])

    if custom_style:
        lines.append("")
        lines.extend(custom_style)

    lines.append("")

    if direction == "LR":
        lines.append("left to right direction")
    else:
        lines.append("top to bottom direction")
    lines.append("")

    title = "Action Flow View"
    if focus is not None:
        focus_name = getattr(focus, 'name', None) or "Focus"
        title = f"Action Flow — {focus_name}"
    lines.append(f'title {title}')
    lines.append("")
    lines.append("hide circle")
    lines.append("")

    # Build inclusion set
    gen = PlantUMLGenerator(model, style=style, focus=focus,
                            elements=elements, max_depth=max_depth,
                            include_legend=False,
                            show_external=show_external)
    gen._build_inclusion_set()

    # Auto-expand with connected flows
    if auto_include_flows:
        _expand_with_connected_flows(model, gen._included_ids,
                                     show_external=show_external)

    # Collect all flow connections for arrow rendering
    flow_connections = _extract_flow_connections(model)

    # Traverse the model
    gen._traverse(gen.model)

    id_map = gen.id_map
    elements_list = gen.elements
    relationships = gen.relationships

    # Filter for action-flow relevant element types
    afv_types = {"action", "flow", "attribute", "port", "part"}

    for alias, name, stereotype, elem, is_included in elements_list:
        sysml_type = getattr(elem, 'sysml_type', '')
        if sysml_type in afv_types:
            keyword = "rectangle"
            if sysml_type == 'state':
                keyword = "state"
            elif sysml_type == 'view':
                keyword = "folder"
            lines.append(f'{keyword} "{name}" as {alias} {stereotype}')

    lines.append("")

    # Render containment and typing relationships
    for src, arrow, dst, label, is_external in relationships:
        if is_external and not show_external:
            continue
        if is_external:
            arrow = f"-[dotted,thickness=1,#999999]{arrow.lstrip('-')}"
        if label:
            lines.append(f'{src} {arrow} {dst} : {label}')
        else:
            lines.append(f'{src} {arrow} {dst}')

    lines.append("")

    # Render flow connection arrows
    # Grammar-level flows won't have entries in the id_map, so we check
    # if their resolved source/target elements are in the inclusion set.
    for from_names, to_names, flow_name, is_grammar_obj in flow_connections:
        from_elem = _find_element_by_qualified_name(model, from_names) if from_names else None
        to_elem = _find_element_by_qualified_name(model, to_names) if to_names else None

        if from_elem is None or to_elem is None:
            continue

        from_id = id(from_elem)
        to_id = id(to_elem)

        # Only render if at least one endpoint is in the inclusion set
        # (or if auto_include_flows expanded the set to include both)
        from_included = from_id in gen._included_ids
        to_included = to_id in gen._included_ids
        if not (from_included or to_included):
            continue

        from_alias = id_map.get(from_id)
        to_alias = id_map.get(to_id)
        if from_alias and to_alias:
            label_text = flow_name if flow_name else "flow"
            lines.append(f'{from_alias} {ARROW_STYLES["flow"]} {to_alias} : {label_text}')

    lines.append("")

    if include_legend:
        lines.extend([
            "legend right",
            "  <b>Action Flow Legend</b>",
            "  |= Relationship |= Notation |",
            "  | Flow Transfer | --> |",
            "  | Binding | -[thickness=4]- |",
            "  | Composite (owns) | *-- |",
            "  | Feature Typing | --:|> |",
            "endlegend",
        ])
        lines.append("")

    lines.append("@enduml")
    return "\n".join(lines)


def _scan_grammar_body_for_flows(grammar_obj, result_list):
    """Recursively scan a grammar object's body for FlowConnectionUsage/FlowConnectionDefinition.

    Flows inside action bodies are raw grammar objects, not Usage wrappers.
    This function finds them and extracts their from/to endpoint names.

    Appends (from_names, to_names, flow_name) tuples to result_list.
    """
    body = getattr(grammar_obj, 'body', None)
    if body is None:
        return
    children = getattr(body, 'children', None)
    if children is None:
        return
    if not isinstance(children, list):
        children = [children]

    for body_item in children:
        _scan_body_tree(body_item, result_list)


def _scan_body_tree(node, result_list):
    """Recursively walk grammar body tree nodes looking for flow grammar objects."""
    if node is None:
        return

    class_name = node.__class__.__name__
    if class_name in ('FlowConnectionUsage', 'FlowConnectionDefinition'):
        from_names, to_names = _extract_flow_endpoints_from_grammar(node)
        # Extract name from declaration
        flow_name = None
        decl = getattr(node, 'declaration', None)
        if decl:
            inner_decl = getattr(decl, 'declaration', None)
            if inner_decl and hasattr(inner_decl, 'identification') and inner_decl.identification:
                flow_name = inner_decl.identification.declaredName
        # Also try usage-level declaration
        if flow_name is None and hasattr(node, 'declaration'):
            d = node.declaration
            if hasattr(d, 'identification') and d.identification:
                flow_name = d.identification.declaredName
        result_list.append((from_names, to_names, flow_name, node))
        return

    children = getattr(node, 'children', None)
    if children is None:
        return
    if not isinstance(children, list):
        children = [children]
    for child in children:
        _scan_body_tree(child, result_list)


def _extract_flow_endpoints_from_grammar(flow_grammar):
    """Extract from/to names from a FlowConnectionUsage/FlowConnectionDefinition grammar object."""
    declaration = getattr(flow_grammar, 'declaration', None)
    if declaration is None:
        return None, None

    children = getattr(declaration, 'children', None)
    if not children or len(children) < 3:
        return None, None

    from_names = None
    to_names = None

    for end_idx, result in [(1, 'from'), (2, 'to')]:
        end_member = children[end_idx]
        if end_member is None:
            continue
        if not hasattr(end_member, 'children'):
            continue
        flow_end = end_member.children
        if flow_end is None:
            continue
        if not hasattr(flow_end, 'children'):
            continue
        for child in flow_end.children:
            if hasattr(child, 'children') and hasattr(child.children, 'names'):
                names = child.children.names
                if result == 'from':
                    from_names = names
                else:
                    to_names = names

    return from_names, to_names


def _extract_flow_connections(model):
    """Scan the model for all flow connections (Usage-level and grammar-level).

    Returns:
        list of (from_names, to_names, flow_name, is_grammar_obj) tuples.
        is_grammar_obj is True for flows found inside grammar bodies
        (e.g., flows inside action definitions).
    """
    connections = []
    visited = set()

    def _scan_element(element):
        elem_id = id(element)
        if elem_id in visited:
            return
        visited.add(elem_id)

        if isinstance(element, (Model, Package)):
            for child in getattr(element, 'children', []):
                _scan_element(child)
            return

        # Check for Usage-level flow
        if getattr(element, 'sysml_type', '') == 'flow':
            from_names, to_names = _extract_flow_endpoints(element)
            flow_name = getattr(element, 'name', None)
            connections.append((from_names, to_names, flow_name, False))

        # Scan every element's grammar body for embedded flows
        grammar = getattr(element, 'grammar', None)
        if grammar:
            _scan_grammar_body_for_flows(grammar, connections)

        # Recurse into children
        for child in getattr(element, 'children', []):
            _scan_element(child)

    for child in getattr(model, 'children', []):
        _scan_element(child)

    return connections


def _find_state_in_children(element, state_name):
    """Find a child state element by name within a parent's children tree."""
    if state_name is None:
        return None
    children = getattr(element, 'children', None)
    if not children:
        return None
    for child in children:
        if getattr(child, 'sysml_type', '') == 'state' and getattr(child, 'name', None) == state_name:
            return child
        # Recurse into nested states
        found = _find_state_in_children(child, state_name)
        if found:
            return found
    return None


def _extract_state_transitions(model):
    """Scan the model for all state transitions with resolved source/target elements.

    Returns:
        list of (from_state_elem, to_state_elem, transition_obj) tuples
        where from/to are resolved State elements, or None if unresolvable.
    """
    transitions = []
    visited = set()

    def _scan(element):
        elem_id = id(element)
        if elem_id in visited:
            return
        visited.add(elem_id)

        if isinstance(element, (Model, Package)):
            for child in getattr(element, 'children', []):
                _scan(child)
            return

        if getattr(element, 'sysml_type', '') == 'state':
            # Extract transitions from this state
            state_transitions = getattr(element, 'transitions', [])
            for trans in state_transitions:
                source_name = getattr(trans, 'source', None)
                target_name = getattr(trans, 'target', None)

                from_elem = None
                to_elem = None

                # Resolve source: look in same parent scope first
                parent = getattr(element, 'parent', None)
                if source_name and parent:
                    from_elem = _find_state_in_children(parent, source_name)
                # Fall back to model-wide search
                if from_elem is None and source_name:
                    found = model.find(source_name)
                    if found:
                        from_elem = found[0] if isinstance(found, list) else found

                # Resolve target: same approach
                if target_name and parent:
                    to_elem = _find_state_in_children(parent, target_name)
                if to_elem is None and target_name:
                    found = model.find(target_name)
                    if found:
                        to_elem = found[0] if isinstance(found, list) else found

                transitions.append((from_elem, to_elem, trans))

            # Recurse into nested states
            for child in getattr(element, 'children', []):
                _scan(child)

        # Also recurse into non-state children (for states inside parts, etc.)
        for child in getattr(element, 'children', []):
            _scan(child)

    for child in getattr(model, 'children', []):
        _scan(child)

    return transitions


def _format_transition_label(transition):
    """Format a transition's trigger, guard, and effect into a PlantUML label."""
    parts = []
    trigger = getattr(transition, 'trigger', None)
    guard = getattr(transition, 'guard', None)
    effect = getattr(transition, 'effect', None)
    name = getattr(transition, 'name', None)

    if trigger:
        parts.append(trigger)
    if guard:
        parts.append(f"[{guard}]")
    if effect:
        parts.append(f"/ {effect}")
    if not parts and name:
        return name
    return " ".join(parts) if parts else "transition"


def _expand_with_state_transitions(model, included_ids):
    """Expand inclusion set to include states connected by transitions."""
    state_transitions = _extract_state_transitions(model)
    for from_elem, to_elem, trans in state_transitions:
        for elem in [from_elem, to_elem]:
            if elem and id(elem) in included_ids:
                # Add the other endpoint too
                other = to_elem if elem is from_elem else from_elem
                if other:
                    included_ids.add(id(other))
                # Also add the parent state that owns this transition
                parent = getattr(trans, 'parent', None)
                if parent:
                    included_ids.add(id(parent))


def as_state_transition_view(model, focus=None, elements=None, style="bw",
                              direction="TB", include_legend=True,
                              max_depth=None, show_external=False,
                              auto_include_transitions=True,
                              custom_style=None):
    """Generate a State Transition View (STV) diagram.

    Corresponds to SysML v2 ``StateTransitionView``, which specializes
    ``InterconnectionView``. Presents states and their transitions,
    including:
    - States with nested states
    - Entry, do, and exit actions
    - Transition usages with triggers, guards, and actions
    - Compartments on states

    When ``auto_include_transitions=True`` (default), selecting states
    via ``focus`` or ``elements`` automatically discovers and includes
    all transitions involving those states.

    Args:
        model: A sysmlpy Model instance
        focus: Optional element to focus on (renders subtree)
        elements: Optional list of specific elements to include
        style: "bw" (default) or "color"
        direction: "TB" or "LR"
        include_legend: Whether to include relationship legend
        max_depth: Maximum depth to traverse from focus
        show_external: Show relationships to elements outside selection
        auto_include_transitions: Auto-discover transitions for selected states
        custom_style: Optional PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    lines = []
    lines.append("@startuml")
    lines.append("")

    # Style
    if style == "bw":
        lines.extend([
            "skinparam monochrome true",
            "skinparam wrapWidth 300",
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Helvetica",
            "",
            "skinparam state<<state def>> {",
            "    BackgroundColor white",
            "    BorderColor black",
            "}",
            "skinparam state<<state>> {",
            "    BackgroundColor white",
            "    BorderColor black",
            "}",
        ])
    else:
        lines.extend([
            "<style>",
            "root {",
            "    BackGroundColor white",
            "    FontName Helvetica",
            "    FontSize 13",
            "}",
            "state {",
            "    LineColor #444444",
            "    LineThickness 1.5",
            "    BackgroundColor white",
            "    Padding 10",
            "}",
            "arrow {",
            "    LineColor #555555",
            "    LineThickness 1.5",
            "}",
            "</style>",
            "",
            "skinparam wrapWidth 400",
        ])

    if custom_style:
        lines.append("")
        lines.extend(custom_style)

    lines.append("")

    if direction == "LR":
        lines.append("left to right direction")
    else:
        lines.append("top to bottom direction")
    lines.append("")

    title = "State Transition View"
    if focus is not None:
        focus_name = getattr(focus, 'name', None) or "Focus"
        title = f"State Transition — {focus_name}"
    elif elements is not None:
        title = f"State Transition — Selected Elements ({len(elements)})"
    lines.append(f'title {title}')
    lines.append("")
    lines.append("hide circle")
    lines.append("")

    # Build inclusion set
    gen = PlantUMLGenerator(model, style=style, focus=focus,
                            elements=elements, max_depth=max_depth,
                            include_legend=False,
                            show_external=show_external)
    gen._build_inclusion_set()

    # Auto-expand with state transitions
    if auto_include_transitions:
        _expand_with_state_transitions(model, gen._included_ids)

    # Extract all state transitions for arrow rendering
    state_transitions = _extract_state_transitions(model)

    # Traverse
    gen._traverse(gen.model)

    id_map = gen.id_map
    elements_list = gen.elements
    relationships = gen.relationships

    # Filter for state-relevant elements
    stv_types = {"state", "action", "attribute"}

    # Render state elements with PlantUML's state keyword
    for alias, name, stereotype, elem, is_included in elements_list:
        sysml_type = getattr(elem, 'sysml_type', '')
        if sysml_type == 'state':
            keyword = "state"
        elif sysml_type in stv_types:
            keyword = "rectangle"
        else:
            continue
        lines.append(f'{keyword} "{name}" as {alias} {stereotype}')

    lines.append("")

    # Render containment and typing relationships
    for src, arrow, dst, label, is_external in relationships:
        if is_external and not show_external:
            continue
        if is_external:
            arrow = f"-[dotted,thickness=1,#999999]{arrow.lstrip('-')}"
        if label:
            lines.append(f'{src} {arrow} {dst} : {label}')
        else:
            lines.append(f'{src} {arrow} {dst}')

    lines.append("")

    # Render transition arrows
    for from_elem, to_elem, trans in state_transitions:
        if from_elem is None or to_elem is None:
            continue
        from_id = id(from_elem)
        to_id = id(to_elem)

        from_included = from_id in gen._included_ids
        to_included = to_id in gen._included_ids
        if not (from_included or to_included):
            continue

        from_alias = id_map.get(from_id)
        to_alias = id_map.get(to_id)
        if from_alias and to_alias:
            label_text = _format_transition_label(trans)
            lines.append(f'{from_alias} {ARROW_STYLES["succession"]} {to_alias} : {label_text}')

    lines.append("")

    if include_legend:
        lines.extend([
            "legend right",
            "  <b>State Transition Legend</b>",
            "  |= Relationship |= Notation |",
            "  | Transition | --> |",
            "  | Composite (owns) | *-- |",
            "  | Feature Typing | --:|> |",
            "endlegend",
        ])
        lines.append("")

    lines.append("@enduml")
    return "\n".join(lines)


def as_tree_diagram(model, focus=None, style="bw", direction="TB",
                    max_depth=None, custom_style=None):
    """Generate a tree diagram showing hierarchical containment.

    Uses nested PlantUML containers to show the ownership hierarchy
    of the model. Definitions have sharp corners, usages have rounded corners.

    Corresponds to SysML v2 tree/structure views.

    Args:
        model: A sysmlpy Model instance
        focus: Optional element to focus on (renders subtree)
        style: "bw" (default) or "color"
        direction: "TB" or "LR"
        max_depth: Maximum depth to traverse from focus
        custom_style: Optional PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    lines = []
    lines.append("@startuml")
    lines.append("")

    if style == "bw":
        lines.extend([
            "skinparam monochrome true",
            "skinparam wrapWidth 300",
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Helvetica",
            "",
            "skinparam rectangle<<part def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<part>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<item def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<item>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<action def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<action>> {",
            "    RoundCorner 15",
            "}",
            "skinparam rectangle<<view def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<view>> {",
            "    RoundCorner 15",
            "}",
        ])
    else:
        lines.extend([
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
            "</style>",
            "",
            "skinparam wrapWidth 400",
            "",
            "skinparam rectangle<<part def>> {",
            "    RoundCorner 0",
            "}",
            "skinparam rectangle<<part>> {",
            "    RoundCorner 15",
            "}",
        ])

    if custom_style:
        lines.append("")
        lines.extend(custom_style)

    lines.append("")

    if direction == "LR":
        lines.append("left to right direction")
    else:
        lines.append("top to bottom direction")
    lines.append("")

    title = "Tree Diagram"
    if focus is not None:
        focus_name = getattr(focus, 'name', None) or "Focus"
        title = f"Tree — {focus_name}"
    lines.append(f'title {title}')
    lines.append("")
    lines.append("hide circle")
    lines.append("")

    # Build tree structure
    id_map = {}
    visited = set()

    def render_tree(element, depth=0):
        elem_id = id(element)
        if elem_id in visited:
            return []
        visited.add(elem_id)

        if max_depth is not None and depth >= max_depth:
            return []

        result = []
        sysml_type = getattr(element, 'sysml_type', '')
        is_def = getattr(element, 'is_definition', False)

        # Skip Model and Package containers
        if isinstance(element, (Model, Package)):
            children = getattr(element, 'children', [])
            for child in children:
                result.extend(render_tree(child, depth))
            return result

        name = getattr(element, 'name', None) or "unnamed"
        name = name.replace('"', "''")

        stereotype_map = DEFINITION_STEREOTYPES if is_def else USAGE_STEREOTYPES
        label = stereotype_map.get(sysml_type, sysml_type)
        stereotype = f"<<{label}>>"

        keyword = "rectangle"
        if sysml_type == 'state':
            keyword = "state"
        elif sysml_type == 'view':
            keyword = "folder"

        alias = _get_element_id(element, id_map)

        children = getattr(element, 'children', [])
        if children:
            result.append(f'{keyword} "{name}" as {alias} {stereotype} {{')
            for child in children:
                child_lines = render_tree(child, depth + 1)
                for cl in child_lines:
                    result.append(f"    {cl}")
            result.append("}")
        else:
            result.append(f'{keyword} "{name}" as {alias} {stereotype}')

        return result

    # Start from focus or model children
    if focus is not None:
        tree_lines = render_tree(focus)
    else:
        tree_lines = []
        for child in model.children:
            tree_lines.extend(render_tree(child))

    lines.extend(tree_lines)
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def as_element_table(model, focus=None, style="bw", custom_style=None):
    """Generate a tabular element listing.

    Produces a PlantUML table showing elements with their name, type,
    definition/usage status, and parent container.

    Corresponds to SysML v2 ``TabularRendering`` / ``asElementTable``.

    Args:
        model: A sysmlpy Model instance
        focus: Optional element to focus on (lists its subtree)
        style: "bw" (default) or "color" (affects header shading)
        custom_style: Optional PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    lines = []
    lines.append("@startuml")
    lines.append("")

    if style == "bw":
        lines.extend([
            "skinparam monochrome true",
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Helvetica",
        ])
    else:
        lines.extend([
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Helvetica",
        ])

    if custom_style:
        lines.append("")
        lines.extend(custom_style)

    lines.append("")

    title = "Element Table"
    if focus is not None:
        focus_name = getattr(focus, 'name', None) or "Focus"
        title = f"Element Table — {focus_name}"
    lines.append(f'title {title}')
    lines.append("")

    # Collect elements
    elements = []
    visited = set()

    def collect(element, parent_name=None):
        elem_id = id(element)
        if elem_id in visited:
            return
        visited.add(elem_id)

        if isinstance(element, Model):
            for child in element.children:
                collect(child, parent_name=None)
            return

        if isinstance(element, Package):
            for child in element.children:
                collect(child, parent_name=parent_name)
            return

        name = getattr(element, 'name', None) or "unnamed"
        sysml_type = getattr(element, 'sysml_type', '') or ""
        is_def = getattr(element, 'is_definition', False)
        kind = "def" if is_def else "usage"
        stereotype_map = DEFINITION_STEREOTYPES if is_def else USAGE_STEREOTYPES
        label = stereotype_map.get(sysml_type, sysml_type)

        elements.append((name, label, kind, parent_name or "(root)"))

        children = getattr(element, 'children', [])
        for child in children:
            collect(child, parent_name=name)

    if focus is not None:
        collect(focus)
    else:
        for child in model.children:
            collect(child)

    # Generate table
    lines.append("|= Name |= Type |= Kind |= Parent |")
    for name, label, kind, parent in elements:
        safe_name = name.replace("|", "\\|").replace('"', "''")
        safe_parent = parent.replace("|", "\\|")
        lines.append(f"| {safe_name} | {label} | {kind} | {safe_parent} |")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def as_textual_notation(model, focus=None, style="bw", custom_style=None):
    """Generate a textual notation rendering.

    Uses PlantUML notes to display the hierarchical structure as
    indented text, similar to the SysML v2 textual concrete syntax.

    Corresponds to SysML v2 ``TextualRendering`` / ``asTextualNotation``.

    Args:
        model: A sysmlpy Model instance
        focus: Optional element to focus on (renders its subtree)
        style: "bw" (default) or "color"
        custom_style: Optional PlantUML style lines to append

    Returns:
        str: PlantUML text
    """
    lines = []
    lines.append("@startuml")
    lines.append("")

    if style == "bw":
        lines.extend([
            "skinparam monochrome true",
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Helvetica",
            "skinparam defaultFontName Monospaced",
        ])
    else:
        lines.extend([
            "skinparam defaultFontSize 12",
            "skinparam defaultFontName Monospaced",
        ])

    if custom_style:
        lines.append("")
        lines.extend(custom_style)

    lines.append("")

    title = "Textual Notation"
    if focus is not None:
        focus_name = getattr(focus, 'name', None) or "Focus"
        title = f"Textual — {focus_name}"
    lines.append(f'title {title}')
    lines.append("")

    # Build textual representation
    text_lines = []
    visited = set()

    def build_text(element, indent=0):
        elem_id = id(element)
        if elem_id in visited:
            return
        visited.add(elem_id)

        if isinstance(element, Model):
            for child in element.children:
                build_text(child, indent)
            return

        if isinstance(element, Package):
            for child in element.children:
                build_text(child, indent)
            return

        name = getattr(element, 'name', None) or "unnamed"
        sysml_type = getattr(element, 'sysml_type', '') or ""
        is_def = getattr(element, 'is_definition', False)
        stereotype_map = DEFINITION_STEREOTYPES if is_def else USAGE_STEREOTYPES
        label = stereotype_map.get(sysml_type, sysml_type)

        prefix = "  " * indent
        text_lines.append(f"{prefix}{label} {name}")

        children = getattr(element, 'children', [])
        for child in children:
            build_text(child, indent + 1)

    if focus is not None:
        build_text(focus)
    else:
        for child in model.children:
            build_text(child)

    # Output as a single note
    lines.append("note as TextualNotation")
    for tl in text_lines:
        lines.append(tl)
    lines.append("end note")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)
