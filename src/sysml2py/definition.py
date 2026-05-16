#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 10:14:18 2023

@author: christophercox
"""

import uuid as uuidlib

from typing import TypeVar

from sysml2py.formatting import classtree
from sysml2py.navigate import Searchable
from sysml2py.grammar.classes import (
    Identification,
    PackageMember,
    PackageBody,
    RootNamespace,
)
from sysml2py.grammar.classes import Package as PackageGrammar

from sysml2py import Part, Item, Port, Requirement, UseCase, Attribute, Action, Case, AnalysisCase, VerificationCase
from sysml2py.usage import (
    State, Constraint, Connection, Flow, Calculation, Enumeration,
    Allocation, Metadata, Rendering, Individual, FlowDef,
    View, Viewpoint, Concern,
)

ModelType = TypeVar("Model", bound="Model")


class Model(Searchable):
    """Root model container.  Exposes typed accessors and ``find()`` / ``all()``
    across all child packages and their contents."""

    sysml_type = None  # Model is the root, not a SysML element itself

    def __init__(self):
        self.name = str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.grammar = None
        self.parent = None

    def __repr__(self):
        cls_name = self.__class__.__name__
        if self.children:
            children_repr = ', '.join(repr(c) for c in self.children)
            return f"{cls_name}(children=[{children_repr}])"
        return f"{cls_name}()"

    def load(self: type[ModelType], s: str, library=None) -> ModelType:
        """Load a SysML model from a string using ANTLR4 parser.
        
        Parameters
        ----------
        s : str
            The SysML source code to parse.
        library : str or Path, optional
            Path to SysML v2 library files for resolving imports.
        
        Returns
        -------
        Model
            The loaded model.
        """
        from sysml2py import load_grammar_antlr
        
        # Model requires the input to be a package declaration
        # Check if the string starts with a valid SysML keyword that's not 'package' or 'library'
        s_stripped = s.strip() if isinstance(s, str) else s
        if isinstance(s_stripped, str):
            # List of known SysML top-level keywords (definitions and usages that must be wrapped)
            invalid_starts = ['item', 'part', 'port', 'attribute', 'action', 'state',
                              'connection', 'interface', 'requirement', 'case', 'use',
                              'calc', 'constraint', 'concern', 'ref', 'flow', 'allocation',
                              'view', 'viewpoint', 'rendering', 'metadata', 'individual']
            first_word = s_stripped.split(None, 1)[0] if s_stripped.split() else ''
            if first_word in invalid_starts:
                raise ValueError("Base Model must be encapsulated by a package.")
        
        definition = load_grammar_antlr(s, library=library)["ownedRelationship"]

        member_grammar = []
        found_package = False
        for member in definition:
            if "ownedRelatedElement" not in member:
                if member.get("name") in ("Import", "AliasMember"):
                    member_grammar.append(member)
                continue
            if member["ownedRelatedElement"]["name"] == "DefinitionElement":
                de = member["ownedRelatedElement"]
                if de["ownedRelatedElement"]["name"] == "Package":
                    found_package = True
                    p = Package().load_from_grammar(
                        PackageGrammar(de["ownedRelatedElement"])
                    )
                    self.children.append(p)
                    member_grammar.append(p._get_definition(child="PackageBody"))

        if not found_package:
            # Wrap bare top-level definitions in a synthetic package
            synthetic_relationships = []
            for member in definition:
                if "ownedRelatedElement" not in member:
                    if member.get("name") in ("Import", "AliasMember"):
                        member_grammar.append(member)
                    continue
                if member["ownedRelatedElement"]["name"] == "DefinitionElement":
                    de = member["ownedRelatedElement"]
                    if de["ownedRelatedElement"]["name"] == "AnnotatingElement":
                        continue
                    synthetic_relationships.append({
                        "name": "PackageMember",
                        "prefix": None,
                        "ownedRelatedElement": de
                    })

            if synthetic_relationships:
                synthetic_definition = {
                    "name": "Package",
                    "declaration": {
                        "name": "PackageDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredName": None,
                            "declaredShortName": None,
                        }
                    },
                    "body": {
                        "name": "PackageBody",
                        "ownedRelationship": synthetic_relationships
                    },
                    "ownedRelationship": []
                }
                p = Package().load_from_grammar(
                    PackageGrammar(synthetic_definition)
                )
                self.children.append(p)
                member_grammar.append(p._get_definition(child="PackageBody"))
            else:
                raise ValueError("Base Model must be encapsulated by a package.")

        self.grammar = RootNamespace(
            {"name": "PackageBodyElement", "ownedRelationship": member_grammar}
        )

        return self

    def _ensure_body(self):
        body = []
        for abc in self.children:
            v = abc._get_definition(child="PackageBody")
            if isinstance(v, list):
                for subchild in v:
                    body.append(PackageMember(subchild).get_definition())
            else:
                body.append(PackageMember(v).get_definition())

        if hasattr(self, 'grammar') and self.grammar:
            for child in self.grammar.children:
                if child.__class__.__name__ in ('Import', 'AliasMember'):
                    body.append(child.get_definition())

        if len(body) > 0:
            self.grammar = RootNamespace(
                {"name": "PackageBodyElement", "ownedRelationship": body}
            )

        return self

    def _get_definition(self):
        return self.grammar.get_definition()

    def dump(self):
        if len(self.children) == 0:
            raise ValueError("Base Model has no elements to output.")

        self._ensure_body()
        return classtree(self._get_definition()).dump()

    def _set_child(self, child):
        self.children.append(child)
        child.parent = self
        return self

    def _get_child(self, featurechain):
        # 'x.y.z'
        if isinstance(featurechain, str):
            fc = featurechain.split(".")
        else:
            raise TypeError

        if fc[0] == self.name:
            # This first one must match self name, otherwise pass it all
            featurechain = ".".join(fc[1:])

        for child in self.children:
            fcs = featurechain.split(".")
            if child.name == fcs[0]:
                if len(fcs) == 1:
                    return child
                else:
                    return child._get_child(featurechain)


class Package(Searchable):
    """SysML v2 Package.  Exposes typed accessors and ``find()`` / ``all()``
    across its direct and nested children."""

    sysml_type = "package"

    def __init__(self, name=None, shortname=None):
        self.name = str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.grammar = PackageGrammar()
        self.parent = None

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)

    def __repr__(self):
        name = getattr(self, 'name', None)
        shortname = getattr(self.grammar.declaration.identification, 'declaredShortName', None)
        
        cls_name = self.__class__.__name__
        if name and shortname:
            return f"{cls_name}(name={name!r}, shortname={shortname!r})"
        elif name:
            return f"{cls_name}(name={name!r})"
        elif shortname:
            return f"{cls_name}(shortname={shortname!r})"
        else:
            return f"{cls_name}()"

    def _set_name(self, name, short=False):
        if short:
            if self.grammar.declaration.identification is None:
                self.grammar.declaration.identification = Identification()
            self.grammar.declaration.identification.declaredShortName = name
        else:
            self.name = name
            if self.grammar.declaration.identification is None:
                self.grammar.declaration.identification = Identification()
            self.grammar.declaration.identification.declaredName = name

        return self

    def _get_name(self):
        return self.grammar.declaration.identification.declaredName

    def _set_child(self, child):
        self.children.append(child)
        child.parent = self
        return self

    def _get_child(self, featurechain):
        # 'x.y.z'
        if isinstance(featurechain, str):
            fc = featurechain.split(".")
        else:
            raise TypeError

        if fc[0] == self.name:
            # This first one must match self name, otherwise pass it all
            featurechain = ".".join(fc[1:])

        for child in self.children:
            fcs = featurechain.split(".")
            if child.name == fcs[0]:
                if len(fcs) == 1:
                    return child
                else:
                    return child._get_child(featurechain)

    def _ensure_body(self):
        body = []
        for abc in self.children:
            v = abc._get_definition(child="PackageBody")
            if isinstance(v, list):
                for subchild in v:
                    body.append(PackageMember(subchild).get_definition())
            else:
                body.append(PackageMember(v).get_definition())

        if hasattr(self.grammar, 'body') and self.grammar.body:
            for child in self.grammar.body.children:
                if child.__class__.__name__ in ('Import', 'AliasMember'):
                    body.append(child.get_definition())

        if len(body) > 0:
            self.grammar.body = PackageBody(
                {"name": "PackageBody", "ownedRelationship": body}
            )

    def _get_definition(self, child=None):
        self._ensure_body()

        package = {
            "name": "DefinitionElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }
        package = {
            "name": "PackageMember",
            "ownedRelatedElement": package,
            "prefix": None,
        }
        if not child:
            package = {
                "name": "PackageBodyElement",
                "ownedRelationship": [package],
                "prefix": None,
            }

        # Add the typed by definition to the package output
        if self.typedby is not None:
            # Packages cannot be typed, they should import from other packages
            raise NotImplementedError

        return package

    def dump(self, child=None):
        return classtree(self._get_definition(child=False)).dump()

    def load_from_grammar(self, grammar):
        # Get the identification values
        declared_name = grammar.declaration.identification.declaredName
        declared_shortname = grammar.declaration.identification.declaredShortName if hasattr(grammar.declaration.identification, 'declaredShortName') else None
        
        # Handle the different cases:
        if declared_shortname and declared_name:
            # Both short and long name provided
            self.name = declared_name
            self._set_name(declared_shortname, short=True)
        elif declared_shortname and not declared_name:
            # Only short name is provided - use it as name
            self.name = declared_shortname
            self._set_name(declared_shortname, short=True)
        elif declared_name:
            # Only long name provided
            self.name = declared_name
        
        self.grammar = grammar
        for child in grammar.body.children:
            # Navigate the nested structure:
            # DefinitionBodyItem -> NonOccurrenceUsageMember -> NonOccurrenceUsageElement -> StructureUsageElement/BehaviorUsageElement
            # Or: DefinitionBodyItem -> PackageMember -> DefinitionElement -> ItemDefinition/PartDefinition
            # Or: DefinitionBodyItem -> PackageMember -> UsageElement -> OccurrenceUsageElement -> StructureUsageElement -> ItemUsage/PartUsage
            # Or: PackageBody -> UsageElement directly (for analysis cases in packages)
            if not hasattr(child, 'children') or not child.children:
                continue
            
            # Handle case where child.children is a single object (not a list)
            if isinstance(child.children, list):
                first_child = child.children[0]
            else:
                first_child = child.children
            
            # Handle NonOccurrenceUsageMember (for usages like item, attribute)
            if first_child.__class__.__name__ == 'NonOccurrenceUsageMember':
                if hasattr(first_child, 'children') and first_child.children:
                    second = first_child.children[0]
                    if hasattr(second, 'children'):
                        # NonOccurrenceUsageElement -> StructureUsageElement or BehaviorUsageElement
                        inner_element = second.children
                    else:
                        inner_element = second
                else:
                    continue
            # Handle DefinitionElement (for definitions like item def, part def)
            elif first_child.__class__.__name__ == 'DefinitionElement':
                if hasattr(first_child, 'children') and first_child.children:
                    inner_element = first_child.children[0]
                else:
                    continue
            # Handle UsageElement (for usages like item Hydrogen : Fuel, action Act1)
            elif first_child.__class__.__name__ == 'UsageElement':
                if hasattr(first_child, 'children') and first_child.children:
                    # Navigate: UsageElement -> OccurrenceUsageElement/NonOccurrenceUsageElement -> Usage
                    # first_child.children can be an object (not a list)
                    occ = first_child.children
                    
                    # Check if it's OccurrenceUsageElement (has children containing Structure/Behavior element)
                    if hasattr(occ, 'children') and occ.children:
                        inner = occ.children
                        # Check if it's StructureUsageElement or BehaviorUsageElement
                        if hasattr(inner, 'children'):
                            inner_element = inner.children
                        else:
                            inner_element = inner
                    # Check if it's NonOccurrenceUsageElement
                    elif hasattr(occ, 'ownedRelationship') or hasattr(occ, 'declaration'):
                        inner_element = occ
                    else:
                        continue
                else:
                    continue
            else:
                continue
            
            inner_class = inner_element.__class__.__name__
            
            if inner_class == "ItemUsage":
                child = Item().load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "PartUsage":
                child = Part().load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "PortUsage":
                child = Port().load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "Package":
                child = Package().load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "ItemDefinition":
                child = Item().load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "PartDefinition":
                child = Part(definition=True).load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "PortDefinition":
                child = Port(definition=True).load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "AttributeDefinition":
                child = Attribute(definition=True).load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "AttributeUsage":
                child = Attribute().load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "ActionDefinition":
                child = Action(definition=True).load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "RequirementDefinition":
                child = Requirement(definition=True).load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "UseCaseDefinition":
                child = UseCase(definition=True).load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "ActionUsage":
                child = Action(grammar=inner_element).load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "ActionUsage":
                child = Action().load_from_grammar(inner_element)
                child.parent = self
                self.children.append(child)
            elif inner_class == "ConstraintDefinition":
                c = Constraint(definition=True)
                c.grammar = inner_element
                # Extract the name from the grammar
                if hasattr(inner_element, 'declaration') and hasattr(inner_element.declaration, 'identification') and inner_element.declaration.identification:
                    c.name = inner_element.declaration.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "ConstraintUsage":
                c = Constraint()
                c.grammar = inner_element
                # Navigate to get name from nested declaration structure
                try:
                    if hasattr(inner_element, 'declaration') and inner_element.declaration:
                        decl = inner_element.declaration
                        if hasattr(decl, 'declaration') and decl.declaration:
                            inner_decl = decl.declaration
                            if hasattr(inner_decl, 'declaration') and inner_decl.declaration:
                                feat_decl = inner_decl.declaration
                                if hasattr(feat_decl, 'identification') and feat_decl.identification:
                                    c.name = feat_decl.identification.declaredName
                except AttributeError:
                    pass
                c.parent = self
                self.children.append(c)
            elif inner_class == "StateDefinition":
                s = State(definition=True).load_from_grammar(inner_element)
                s.parent = self
                self.children.append(s)
            elif inner_class == "StateUsage":
                s = State().load_from_grammar(inner_element)
                s.parent = self
                self.children.append(s)
            elif inner_class == "CalculationDefinition":
                c = Calculation(definition=True)
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and hasattr(inner_element.declaration, 'identification') and inner_element.declaration.identification:
                    c.name = inner_element.declaration.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "CalculationUsage":
                c = Calculation()
                c.grammar = inner_element
                try:
                    if hasattr(inner_element, 'declaration') and inner_element.declaration:
                        decl = inner_element.declaration
                        if hasattr(decl, 'declaration') and decl.declaration:
                            inner_decl = decl.declaration
                            if hasattr(inner_decl, 'declaration') and inner_decl.declaration:
                                feat_decl = inner_decl.declaration
                                if hasattr(feat_decl, 'identification') and feat_decl.identification:
                                    c.name = feat_decl.identification.declaredName
                except AttributeError:
                    pass
                c.parent = self
                self.children.append(c)
            elif inner_class == "ConnectionDefinition":
                c = Connection(definition=True)
                c.grammar = inner_element
                if hasattr(inner_element, 'definition') and hasattr(inner_element.definition, 'declaration') and inner_element.definition.declaration:
                    decl = inner_element.definition.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        c.name = decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "ConnectionUsage":
                c = Connection()
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            c.name = feat_decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "FlowConnectionDefinition":
                f = Flow(definition=True)
                f.grammar = inner_element
                if hasattr(inner_element, 'definition') and hasattr(inner_element.definition, 'declaration') and inner_element.definition.declaration:
                    decl = inner_element.definition.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        f.name = decl.identification.declaredName
                f.parent = self
                self.children.append(f)
            elif inner_class == "FlowConnectionUsage":
                f = Flow()
                f.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            f.name = feat_decl.identification.declaredName
                f.parent = self
                self.children.append(f)
            elif inner_class == "EnumerationDefinition":
                e = Enumeration(name=None)  # will set below
                e.grammar = inner_element
                if hasattr(inner_element, 'declaration') and hasattr(inner_element.declaration, 'identification') and inner_element.declaration.identification:
                    e.name = inner_element.declaration.identification.declaredName
                e.parent = self
                self.children.append(e)
            elif inner_class == "AllocationDefinition":
                a = Allocation(definition=True)
                a.grammar = inner_element
                # AllocationDefinition uses 'definition' -> Definition -> DefinitionDeclaration
                if hasattr(inner_element, 'definition') and inner_element.definition:
                    if hasattr(inner_element.definition, 'declaration') and inner_element.definition.declaration:
                        decl = inner_element.definition.declaration
                        if hasattr(decl, 'identification') and decl.identification:
                            a.name = decl.identification.declaredName
                a.parent = self
                self.children.append(a)
            elif inner_class == "AllocationUsage":
                a = Allocation()
                a.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            a.name = feat_decl.identification.declaredName
                a.parent = self
                self.children.append(a)
            elif inner_class == "MetadataDefinition":
                m = Metadata(definition=True)
                m.grammar = inner_element
                if hasattr(inner_element, 'definition') and inner_element.definition:
                    if hasattr(inner_element.definition, 'declaration') and inner_element.definition.declaration:
                        decl = inner_element.definition.declaration
                        if hasattr(decl, 'identification') and decl.identification:
                            m.name = decl.identification.declaredName
                m.parent = self
                self.children.append(m)
            elif inner_class == "MetadataUsage":
                m = Metadata()
                m.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            m.name = feat_decl.identification.declaredName
                m.parent = self
                self.children.append(m)
            elif inner_class == "RenderingDefinition":
                r = Rendering(definition=True)
                r.grammar = inner_element
                if hasattr(inner_element, 'definition') and inner_element.definition:
                    if hasattr(inner_element.definition, 'declaration') and inner_element.definition.declaration:
                        decl = inner_element.definition.declaration
                        if hasattr(decl, 'identification') and decl.identification:
                            r.name = decl.identification.declaredName
                r.parent = self
                self.children.append(r)
            elif inner_class == "RenderingUsage":
                r = Rendering()
                r.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            r.name = feat_decl.identification.declaredName
                r.parent = self
                self.children.append(r)
            elif inner_class == "IndividualDefinition":
                i = Individual(definition=True)
                i.grammar = inner_element
                if hasattr(inner_element, 'definition') and inner_element.definition:
                    if hasattr(inner_element.definition, 'declaration') and inner_element.definition.declaration:
                        decl = inner_element.definition.declaration
                        if hasattr(decl, 'identification') and decl.identification:
                            i.name = decl.identification.declaredName
                i.parent = self
                self.children.append(i)
            elif inner_class == "IndividualUsage" or inner_class == "IndividualUsageSimple":
                i = Individual()
                i.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            i.name = feat_decl.identification.declaredName
                i.parent = self
                self.children.append(i)
            elif inner_class == "FlowDefinition":
                f = FlowDef(name=None)
                f.grammar = inner_element
                if hasattr(inner_element, 'definition') and inner_element.definition:
                    if hasattr(inner_element.definition, 'declaration') and inner_element.definition.declaration:
                        decl = inner_element.definition.declaration
                        if hasattr(decl, 'identification') and decl.identification:
                            f.name = decl.identification.declaredName
                f.parent = self
                self.children.append(f)
            elif inner_class == "ViewDefinition":
                v = View(definition=True)
                v.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        v.name = decl.identification.declaredName
                v.parent = self
                self.children.append(v)
            elif inner_class == "ViewUsage":
                v = View()
                v.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            v.name = feat_decl.identification.declaredName
                v.parent = self
                self.children.append(v)
            elif inner_class == "ViewpointDefinition":
                vp = Viewpoint(definition=True)
                vp.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        vp.name = decl.identification.declaredName
                vp.parent = self
                self.children.append(vp)
            elif inner_class == "ViewpointUsage":
                vp = Viewpoint()
                vp.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            vp.name = feat_decl.identification.declaredName
                vp.parent = self
                self.children.append(vp)
            elif inner_class == "ConcernDefinition":
                c = Concern(definition=True)
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        c.name = decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "ConcernUsage":
                c = Concern()
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            c.name = feat_decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "CaseDefinition":
                c = Case(definition=True)
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        c.name = decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "AnalysisCaseDefinition":
                c = AnalysisCase(definition=True)
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        c.name = decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "VerificationCaseDefinition":
                c = VerificationCase(definition=True)
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'identification') and decl.identification:
                        c.name = decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "AnnotatingElement":
                wrapper = _GrammarAnnotationWrapper(inner_element)
                wrapper.parent = self
                self.children.append(wrapper)
            elif inner_class == "InterfaceDefinition":
                wrapper = _GrammarAnnotationWrapper(inner_element)
                wrapper.parent = self
                self.children.append(wrapper)
            elif inner_class == "InterfaceUsage":
                wrapper = _GrammarAnnotationWrapper(inner_element)
                wrapper.parent = self
                self.children.append(wrapper)
            elif inner_class == "AssertConstraintUsage":
                c = Constraint()
                c.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            c.name = feat_decl.identification.declaredName
                c.parent = self
                self.children.append(c)
            elif inner_class == "RequirementUsage":
                r = Requirement()
                r.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            r.name = feat_decl.identification.declaredName
                r.parent = self
                self.children.append(r)
            elif inner_class == "SatisfyRequirementUsage":
                r = Requirement()
                r.grammar = inner_element
                if hasattr(inner_element, 'declaration') and inner_element.declaration:
                    decl = inner_element.declaration
                    if hasattr(decl, 'declaration') and decl.declaration:
                        feat_decl = decl.declaration
                        if hasattr(feat_decl, 'identification') and feat_decl.identification:
                            r.name = feat_decl.identification.declaredName
                r.parent = self
                self.children.append(r)
            else:
                print(f"Unknown class: {inner_class}")
                raise NotImplementedError
        
        return self

    def _get_grammar(self):
        # Force updates to grammar if something has changed.
        self._ensure_body()
        return self.grammar


class _GrammarAnnotationWrapper:
    """Minimal wrapper for grammar-only elements (doc/comment) that need _get_definition."""
    def __init__(self, grammar_obj):
        self.grammar = grammar_obj
        self.name = None

    def _get_definition(self, child=None):
        if hasattr(self.grammar, 'get_definition'):
            inner = self.grammar.get_definition()
        else:
            inner = {"name": type(self.grammar).__name__}
        return {
            "name": "PackageMember",
            "prefix": None,
            "ownedRelatedElement": {
                "name": "DefinitionElement",
                "ownedRelatedElement": inner
            }
        }
