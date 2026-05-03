#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 30 23:23:31 2023

@author: christophercox
"""


# import os

# os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import uuid as uuidlib

import pint

ureg = pint.UnitRegistry()

from sysml2py.formatting import classtree

from sysml2py.grammar.classes import (
    Identification,
    DefinitionBody,
    DefinitionBodyItem,
    FeatureSpecializationPart,
    SubclassificationPart,
)

from sysml2py.grammar.classes import (
    AttributeUsage,
    AttributeDefinition,
    ValuePart,
    PartUsage,
    PartDefinition,
    ItemUsage,
    ItemDefinition,
    PortUsage,
    PortDefinition,
    DefaultReferenceUsage,
    RefPrefix,
    ActionUsage,
    ActionDefinition,
    RequirementDefinition,
    UseCaseDefinition,
    StateUsage,
    StateDefinition,
    ConstraintUsage,
    ConstraintDefinition,
    ConnectionUsage,
    ConnectionDefinition,
    FlowConnectionUsage,
    FlowConnectionDefinition,
    CalculationUsage,
    CalculationDefinition,
    EnumerationDefinition,
    AllocationDefinition,
    AllocationUsage,
    MetadataDefinition,
    MetadataUsage,
    RenderingDefinition,
    RenderingUsage,
    IndividualDefinition,
    IndividualUsageSimple,
    FlowDefinition,
    ViewDefinition,
    ViewUsage,
    ViewpointDefinition,
    ViewpointUsage,
    ConcernDefinition,
    ConcernUsage,
    CaseDefinition,
    CaseUsage,
    AnalysisCaseDefinition,
    AnalysisCaseUsage,
    VerificationCaseDefinition,
    VerificationCaseUsage,
)


class Usage:
    def __init__(self):
        self.name = str(uuidlib.uuid4())
        self.children = []
        self.typedby = None

    def _ensure_body(self, subgrammar="usage"):
        # Add children
        body = []
        for abc in self.children:
            body.append(
                DefinitionBodyItem(
                    abc._get_definition(child="DefinitionBody")
                ).get_definition()
            )

        if len(body) > 0:
            getattr(self.grammar, subgrammar).completion.body.body = DefinitionBody(
                {"name": "DefinitionBody", "ownedRelatedElement": body}
            )
        return self

    def usage_dump(self, child):
        # This is a usage.

        self._ensure_body("usage")

        # Add packaging
        package = {
            "name": "StructureUsageElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }
        package = {"name": "OccurrenceUsageElement", "ownedRelatedElement": package}

        if child == "DefinitionBody":
            package = {
                "name": "OccurrenceUsageMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }

            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        elif "PackageBody":
            package = {"name": "UsageElement", "ownedRelatedElement": package}
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }

        return package

    def definition_dump(self, child):
        # This is a definition.

        self._ensure_body("definition")

        package = {
            "name": "DefinitionElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }

        if child == "DefinitionBody":
            package = {
                "name": "DefinitionMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }

            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}

        elif child == "PackageBody" or child == None:
            # Add these packets to make this dump without parents

            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }

        return package

    def _get_definition(self, child=None):
        # Determine if this is a usage or definition based on grammar class name
        grammar_cls_name = type(self.grammar).__name__
        is_def = grammar_cls_name.endswith('Definition')
        
        if is_def:
            package = self.definition_dump(child)
        else:
            package = self.usage_dump(child)

        if child is None:
            package = {
                "name": "PackageBodyElement",
                "ownedRelationship": [package],
                "prefix": None,
            }

        # Add the typed by definition to the package output
        if self.typedby is not None:
            if child is None:
                package["ownedRelationship"].insert(
                    0, self.typedby._get_definition(child="PackageBody")
                )
            elif child == "PackageBody":
                package = [self.typedby._get_definition(child="PackageBody"), package]
            else:
                package["ownedRelationship"].insert(
                    0, self.typedby._get_definition(child=child)["ownedRelationship"][0]
                )

        return package

    def dump(self, child=None):
        return classtree(self._get_definition(child)).dump()

    def __repr__(self):
        # Safely get name
        try:
            name = getattr(self, 'name', None)
            if not name:
                id_obj = getattr(self.grammar, 'usage', None)
                if id_obj:
                    id_obj = getattr(id_obj.declaration, 'declaration', None)
                    if id_obj:
                        name = getattr(id_obj.identification, 'declaredName', None)
        except (AttributeError, TypeError):
            name = None
        
        # Safely get shortname
        try:
            shortname = None
            id_obj = getattr(self.grammar, 'usage', None)
            if id_obj:
                id_obj = getattr(id_obj.declaration, 'declaration', None)
                if id_obj:
                    shortname = getattr(id_obj.identification, 'declaredShortName', None)
            if shortname:
                shortname = shortname.strip('<').strip('>')
        except (AttributeError, TypeError):
            shortname = None
            
        is_def = hasattr(self.grammar, 'definition')
        cls_name = self.__class__.__name__
        
        if is_def:
            if name and shortname:
                return f"{cls_name}(definition=True, name={name!r}, shortname={shortname!r})"
            elif name:
                return f"{cls_name}(definition=True, name={name!r})"
            else:
                return f"{cls_name}(definition=True)"
        else:
            if name and shortname:
                return f"{cls_name}(name={name!r}, shortname={shortname!r})"
            elif name:
                return f"{cls_name}(name={name!r})"
            else:
                return f"{cls_name}()"

    def _set_name(self, name, short=False):
        if hasattr(self.grammar, "usage"):
            path = self.grammar.usage.declaration.declaration
        elif hasattr(self.grammar, "definition"):
            path = self.grammar.definition.declaration
        else:
            # Navigate recursively through .declaration chain to find identification
            path = self.grammar.declaration
            while hasattr(path, "declaration") and not hasattr(path, "identification"):
                path = path.declaration

        if path.identification is None:
            path.identification = Identification()

        if short:
            path.identification.declaredShortName = "<" + name + ">"
        else:
            self.name = name
            path.identification.declaredName = name

        return self

    def _get_name(self):
        return self.grammar.usage.declaration.declaration.identification.declaredName

    def _set_child(self, child):
        self.children.append(child)
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

    def _set_typed_by(self, typed):
        # Only set if the pointed object is a definition
        if "definition" in typed.grammar.__dict__:
            self.typedby = typed
            if "definition" in self.grammar.__dict__:
                raise ValueError("A definition element cannot be defined.")
            else:
                if self.grammar.usage.declaration.declaration.specialization is None:
                    package = {
                        "name": "QualifiedName",
                        "names": [typed.name],
                    }
                    package = {
                        "name": "FeatureType",
                        "type": package,
                        "ownedRelatedElement": [],
                    }
                    package = {"name": "OwnedFeatureTyping", "type": package}
                    package = {"name": "FeatureTyping", "ownedRelationship": package}
                    package = {"name": "TypedBy", "ownedRelationship": [package]}
                    package = {
                        "name": "Typings",
                        "typedby": package,
                        "ownedRelationship": [],
                    }
                    package = {
                        "name": "FeatureSpecialization",
                        "ownedRelationship": package,
                    }
                    package = {
                        "name": "FeatureSpecializationPart",
                        "specialization": [package],
                        "multiplicity": None,
                        "specialization2": [],
                        "multiplicity2": None,
                    }
                    self.grammar.usage.declaration.declaration.specialization = (
                        FeatureSpecializationPart(package)
                    )
        else:
            raise ValueError("Typed by element was not a definition.")
        return self

    def _set_specializes(self, *parents):
        """Set specialization (`:>`) for definitions.
        
        In SysML v2: `part def Car :> Vehicle;`
        
        Args:
            *parents: One or more definition elements to specialize.
        """
        if "definition" not in self.grammar.__dict__:
            raise ValueError(
                "Only definition elements can use specializes. "
                "Use _set_subsets() for usage elements."
            )
        
        names = [p.name for p in parents]
        relationships = []
        for name in names:
            relationships.append({
                "name": "OwnedSubclassification",
                "superclassifier": {
                    "name": "QualifiedName",
                    "names": [name],
                },
            })
        
        package = {
            "name": "SubclassificationPart",
            "ownedRelationship": relationships,
        }
        self.grammar.definition.declaration.subclassificationpart = (
            SubclassificationPart(package)
        )
        return self

    def _set_subsets(self, *parents):
        """Set subsetting (`:>`) for usage elements.
        
        In SysML v2: `part myEng :> eng;`
        
        Args:
            *parents: One or more elements to subset.
        """
        if "definition" in self.grammar.__dict__:
            raise ValueError(
                "Definition elements cannot use subsets. "
                "Use _set_specializes() for definitions."
            )
        
        names = [p.name if hasattr(p, 'name') else str(p) for p in parents]
        relationships = []
        for name in names:
            relationships.append({
                "name": "OwnedSubsetting",
                "subsettedFeature": {
                    "name": "QualifiedName",
                    "names": [name],
                },
                "ownedRelatedElement": [],
            })
        
        package = {
            "name": "Subsettings",
            "ownedRelationship": relationships,
        }
        package = {
            "name": "FeatureSpecialization",
            "ownedRelationship": package,
        }
        package = {
            "name": "FeatureSpecializationPart",
            "specialization": [package],
            "multiplicity": None,
            "specialization2": [],
            "multiplicity2": None,
        }
        self.grammar.usage.declaration.declaration.specialization = (
            FeatureSpecializationPart(package)
        )
        return self

    def _set_redefines(self, parent):
        """Set redefinition (`:>>`) for usage elements.
        
        In SysML v2: `attribute :>> mass = 100;`
        
        Args:
            parent: The element being redefined.
        """
        if "definition" in self.grammar.__dict__:
            raise ValueError("Definition elements cannot use redefines.")
        
        name = parent.name if hasattr(parent, 'name') else str(parent)
        
        package = {
            "name": "OwnedRedefinition",
            "redefinedFeature": {
                "name": "QualifiedName",
                "names": [name],
            },
            "ownedRelatedElement": [],
        }
        package = {
            "name": "Redefinitions",
            "ownedRelationship": [package],
        }
        package = {
            "name": "FeatureSpecialization",
            "ownedRelationship": package,
        }
        package = {
            "name": "FeatureSpecializationPart",
            "specialization": [package],
            "multiplicity": None,
            "specialization2": [],
            "multiplicity2": None,
        }
        self.grammar.usage.declaration.declaration.specialization = (
            FeatureSpecializationPart(package)
        )
        return self

    def _get_grammar(self):
        self._ensure_body()
        return self.grammar

    def load_from_grammar(self, grammar):
        #!TODO Typed By
        self.__init__()
        self.grammar = grammar
        children = []
        
        # Check if this is a definition or usage
        # Some definition types use 'definition' (PartDefinition, AttributeDefinition)
        # Others use 'declaration' directly (RequirementDefinition, UseCaseDefinition)
        # PartDefinition: has .definition which is a Definition object
        # Usage: has .declaration directly
        
        # First check if grammar has 'definition' (for definitions like PartDefinition)
        defn = getattr(grammar, 'definition', None)
        if defn:
            # This type uses 'definition' (PartDefinition, etc.)
            # Get name from definition.declaration.identification.declaredName
            u_name = defn.declaration.identification.declaredName
            
            # Get body from definition.body
            body = defn.body if hasattr(defn, 'body') else None
            
            # body is DefinitionBody with .children
            if body and hasattr(body, 'children') and body.children:
                children_list = []
                for body_item in body.children:
                    if hasattr(body_item, 'children') and body_item.children:
                        member = body_item.children[0]
                        if hasattr(member, 'children') and member.children:
                            inner = member.children[0]
                            # Handle DefinitionElement wrapping
                            if inner.__class__.__name__ == 'DefinitionElement' and hasattr(inner, 'children') and inner.children:
                                inner = inner.children[0]
                            if hasattr(inner, 'children'):
                                children_list.append(inner)
                            else:
                                children_list.append(inner)
                    elif hasattr(body_item, 'ownedRelatedElement'):
                        children_list.append(body_item)
                children = children_list
            else:
                children = []
        elif hasattr(grammar, 'usage'):
            # This is a usage (like PartUsage, ItemUsage)
            # Get name from grammar.usage.declaration.declaration.identification.declaredName
            usage = grammar.usage
            if hasattr(usage, 'declaration') and hasattr(usage.declaration, 'declaration'):
                decl = usage.declaration.declaration
                if hasattr(decl, 'identification') and decl.identification:
                    u_name = decl.identification.declaredName
                else:
                    u_name = None
            else:
                u_name = None
            children = []
        elif hasattr(grammar, 'declaration'):
            # This type uses 'declaration' directly (RequirementDefinition, UseCaseDefinition, some usages)
            decl = grammar.declaration
            u_name = None
            
            # Check nested declaration for Usage (UsageDeclaration -> FeatureDeclaration)
            nested_decl = getattr(decl, 'declaration', None)
            if nested_decl and hasattr(nested_decl, 'identification') and nested_decl.identification:
                u_name = nested_decl.identification.declaredName
            # Check direct identification (for RequirementDefinition, UseCaseDefinition)
            elif hasattr(decl, 'identification') and decl.identification:
                u_name = decl.identification.declaredName
            children = []
        else:
            u_name = None
            children = []

        if u_name is not None:
            self.name = u_name

        for child in children:
            # Handle different child types
            if hasattr(child, 'definition') and hasattr(child, 'body'):
                # It's a Definition (PartDefinition, ItemDefinition, etc.)
                sc = child
            elif hasattr(child, 'children'):
                # It's a StructureUsageElement or similar
                sc = child.children if hasattr(child, 'children') else child
            else:
                continue
                
            # Process the child
            class_name = sc.__class__.__name__ if not hasattr(sc, '__class__') else sc.__class__.__name__
            
            if class_name == "PartDefinition":
                self.children.append(Part(definition=True).load_from_grammar(sc))
            elif class_name == "ItemDefinition":
                self.children.append(Item(definition=True).load_from_grammar(sc))
            elif class_name == "PartUsage":
                self.children.append(Part().load_from_grammar(sc))
            elif class_name == "ItemUsage":
                self.children.append(Item().load_from_grammar(sc))
            elif class_name == "AttributeUsage":
                self.children.append(Attribute().load_from_grammar(sc))
            elif class_name == "AttributeDefinition":
                self.children.append(Attribute(definition=True).load_from_grammar(sc))
            elif class_name == "StructureUsageElement":
                if hasattr(sc, 'children'):
                    inner = sc.children
                    if inner.__class__.__name__ == "PartUsage":
                        self.children.append(Part().load_from_grammar(inner))
                    elif inner.__class__.__name__ == "ItemUsage":
                        self.children.append(Item().load_from_grammar(inner))
            elif class_name == "Definition":
                # Unwrap Definition to get the inner type
                if hasattr(sc, 'body') and hasattr(sc.body, 'children') and sc.body.children:
                    for body_item in sc.body.children:
                        if hasattr(body_item, 'children') and body_item.children:
                            inner = body_item.children[0]
                            if hasattr(inner, 'children'):
                                inner = inner.children
                            self.children.append(Part(definition=True).load_from_grammar(inner) if inner.__class__.__name__ == 'PartDefinition' else Item(definition=True).load_from_grammar(inner))

        return self

    def add_directed_feature(self, direction, name=str(uuidlib.uuid4())):
        self._set_child(DefaultReference()._set_name(name).set_direction(direction))
        return self

    # def modify_directed_feature(self, direction, name):
    #     child = self._get_child(name)
    #     if child is not None:
    #         pass
    #     else:
    #         raise AttributeError("Invalid Feature Name or Chain")


class Attribute(Usage):
    def __init__(self, definition=False, name=None):
        Usage.__init__(self)

        if definition:
            self.grammar = AttributeDefinition()
        else:
            self.grammar = AttributeUsage()

        if name is not None:
            self._set_name(name)

    def usage_dump(self, child):
        # Override - base output

        # Add children
        body = []
        for abc in self.children:
            body.append(DefinitionBodyItem(abc.dump(child=True)).get_definition())
        if len(body) > 0:
            self.grammar.usage.completion.body.body = DefinitionBody(
                {"name": "DefinitionBody", "ownedRelatedElement": body}
            )

        # Add packaging
        package = {
            "name": "NonOccurrenceUsageElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }

        if child:
            package = {
                "name": "NonOccurrenceUsageMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        else:
            # Add these packets to make this dump without parents
            package = {"name": "UsageElement", "ownedRelatedElement": package}
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }
        return package

    def set_value(self, value):
        if not isinstance(value, pint.Quantity):
            value = value * ureg.dimensionless
        if isinstance(value, pint.Quantity):
            # Only add units if not dimensionless
            if not value.units.dimensionless:
                package_units = {
                    "name": "QualifiedName",
                    "names": [str(value.units)],
                }
                package_units = {
                    "name": "FeatureReferenceMember",
                    "memberElement": package_units,
                }
                package_units = {
                    "name": "FeatureReferenceExpression",
                    "ownedRelationship": [package_units],
                }
                package_units = {
                    "name": "BaseExpression",
                    "ownedRelationship": package_units,
                }
                package_units = {
                    "name": "PrimaryExpression",
                    "operand": [],
                    "base": package_units,
                    "operator": [],
                    "ownedRelationship1": [],
                    "ownedRelationship2": [],
                }
                package_units = {
                    "name": "ExtentExpression",
                    "operator": "",
                    "ownedRelationship": [],
                    "primary": package_units,
                }
                package_units = {
                    "name": "UnaryExpression",
                    "operand": [],
                    "operator": None,
                    "extent": package_units,
                }
                package_units = {
                    "name": "ExponentiationExpression",
                    "operand": [],
                    "operator": [],
                    "unary": package_units,
                }
                package_units = {
                    "name": "MultiplicativeExpression",
                    "operation": [],
                    "exponential": package_units,
                }
                package_units = {
                    "name": "AdditiveExpression",
                    "operation": [],
                    "multiplicitive": package_units,
                }
                package_units = {
                    "name": "RangeExpression",
                    "operand": None,
                    "additive": package_units,
                }
                package_units = {
                    "name": "RelationalExpression",
                    "operation": [],
                    "range": package_units,
                }
                package_units = {
                    "name": "ClassificationExpression",
                    "operand": [],
                    "operator": None,
                    "ownedRelationship": [],
                    "relational": package_units,
                }
                package_units = {
                    "name": "EqualityExpression",
                    "operation": [],
                    "classification": package_units,
                }
                package_units = {
                    "name": "AndExpression",
                    "operation": [],
                    "equality": package_units,
                }
                package_units = {
                    "name": "XorExpression",
                    "operand": [],
                    "operator": [],
                    "and": package_units,
                }
                package_units = {
                    "name": "OrExpression",
                    "xor": package_units,
                    "operand": [],
                    "operator": [],
                }
                package_units = {
                    "name": "ImpliesExpression",
                    "operand": [],
                    "operator": [],
                    "or": package_units,
                }
                package_units = {
                    "name": "NullCoalescingExpression",
                    "implies": package_units,
                    "operator": [],
                    "operand": [],
                }
                package_units = {
                    "name": "ConditionalExpression",
                    "operator": None,
                    "operand": [package_units],
                }
                package_units = {"name": "OwnedExpression", "expression": package_units}
                package_units = {
                    "name": "SequenceExpression",
                    "operation": [],
                    "ownedRelationship": package_units,
                }
                package_units = [package_units]
                operator = ["["]
            else:
                package_units = []
                operator = []

            package = {
                "name": "BaseExpression",
                "ownedRelationship": {
                    "name": "LiteralInteger",
                    "value": str(value.magnitude),
                },
            }
            package = {
                "name": "PrimaryExpression",
                "operand": package_units,
                "base": package,
                "operator": operator,
                "ownedRelationship1": [],
                "ownedRelationship2": [],
            }
            package = {
                "name": "ExtentExpression",
                "operator": "",
                "ownedRelationship": [],
                "primary": package,
            }
            package = {
                "name": "UnaryExpression",
                "operand": [],
                "operator": None,
                "extent": package,
            }
            package = {
                "name": "ExponentiationExpression",
                "operand": [],
                "operator": [],
                "unary": package,
            }
            package = {
                "name": "MultiplicativeExpression",
                "operation": [],
                "exponential": package,
            }
            package = {
                "name": "AdditiveExpression",
                "operation": [],
                "multiplicitive": package,
            }
            package = {
                "name": "RangeExpression",
                "operand": None,
                "additive": package,
            }
            package = {
                "name": "RelationalExpression",
                "operation": [],
                "range": package,
            }
            package = {
                "name": "ClassificationExpression",
                "operand": [],
                "operator": None,
                "ownedRelationship": [],
                "relational": package,
            }
            package = {
                "name": "EqualityExpression",
                "operation": [],
                "classification": package,
            }
            package = {
                "name": "AndExpression",
                "operation": [],
                "equality": package,
            }
            package = {
                "name": "XorExpression",
                "operand": [],
                "operator": [],
                "and": package,
            }
            package = {
                "name": "OrExpression",
                "xor": package,
                "operand": [],
                "operator": [],
            }
            package = {
                "name": "ImpliesExpression",
                "operand": [],
                "operator": [],
                "or": package,
            }
            package = {
                "name": "NullCoalescingExpression",
                "implies": package,
                "operator": [],
                "operand": [],
            }
            package = {
                "name": "ConditionalExpression",
                "operator": None,
                "operand": [package],
            }
            package = {"name": "OwnedExpression", "expression": package}
            package = {
                "name": "FeatureValue",
                "isDefault": False,
                "isEqual": False,
                "isInitial": False,
                "ownedRelatedElement": package,
            }
            package = {"name": "ValuePart", "ownedRelationship": [package]}
            self.grammar.usage.completion.valuepart = ValuePart(package)
            # value.unit

        return self

    def get_value(self):
        realpart = (
            self.grammar.usage.completion.valuepart.relationships[0]
            .element.expression.operands[0]
            .implies.orexpression.xor.andexpression.equality.classification.relational.range.additive.left_hand.exponential.unary.extent.primary
        )
        real = float(realpart.base.relationship.dump())
        unit = (
            realpart.operand[0]
            .relationship.expression.operands[0]
            .implies.orexpression.xor.andexpression.equality.classification.relational.range.additive.left_hand.exponential.unary.extent.primary.base.relationship.children[
                0
            ]
            .memberElement.dump()
        )
        return real * ureg(unit)


class Part(Usage):
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = PartDefinition()
        else:
            self.grammar = PartUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Item(Usage):
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = ItemDefinition()
        else:
            self.grammar = ItemUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Port(Usage):
    def __init__(self, definition=False, name=None, shortname=None, conjugated=False):
        Usage.__init__(self)
        if definition:
            self.grammar = PortDefinition()
        else:
            self.grammar = PortUsage()

        self.is_definition = definition
        self.conjugated = conjugated
        self.port_attributes = []  # list of (name, type_name)
        self.port_in_items = []  # list of (name, type_name)
        self.port_out_items = []  # list of (name, type_name)
        self.port_inout_items = []  # list of (name, type_name)

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)

    def add_attribute(self, name, type_name=None):
        """Add an attribute to the port definition.

        Args:
            name: Attribute name
            type_name: Optional type
        """
        self.port_attributes.append((name, type_name))
        return self

    def add_in_item(self, name, type_name=None):
        """Add an input item to the port definition.

        Args:
            name: Item name
            type_name: Optional type
        """
        self.port_in_items.append((name, type_name))
        return self

    def add_out_item(self, name, type_name=None):
        """Add an output item to the port definition.

        Args:
            name: Item name
            type_name: Optional type
        """
        self.port_out_items.append((name, type_name))
        return self

    def add_inout_item(self, name, type_name=None):
        """Add an inout item to the port definition.

        Args:
            name: Item name
            type_name: Optional type
        """
        self.port_inout_items.append((name, type_name))
        return self

    def dump(self, child=None):
        # Check if we have enhanced features
        has_port_features = (
            self.port_attributes or self.port_in_items
            or self.port_out_items or self.port_inout_items
        )

        if not has_port_features:
            # Use standard grammar dump for basic ports
            return classtree(self._get_definition(child)).dump()

        # Enhanced dump with in/out items
        keyword = "port def" if self.is_definition else "port"
        name_str = getattr(self, 'name', "") or ""

        body_items = []
        for attr_name, attr_type in self.port_attributes:
            if attr_type:
                body_items.append(f"attribute {attr_name} : {attr_type}")
            else:
                body_items.append(f"attribute {attr_name}")

        for item_name, item_type in self.port_out_items:
            if item_type:
                body_items.append(f"out item {item_name} : {item_type}")
            else:
                body_items.append(f"out item {item_name}")

        for item_name, item_type in self.port_in_items:
            if item_type:
                body_items.append(f"in item {item_name} : {item_type}")
            else:
                body_items.append(f"in item {item_name}")

        for item_name, item_type in self.port_inout_items:
            if item_type:
                body_items.append(f"inout item {item_name} : {item_type}")
            else:
                body_items.append(f"inout item {item_name}")

        return f"{keyword} {name_str} {{\n   " + ";\n   ".join(body_items) + ";\n}"


class Interface(Usage):
    def __init__(self, definition=False, name=None, shortname=None):
        self.is_definition = definition
        self.name = name if name else str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.grammar = True
        self.iface_shortname = shortname
        self.ends = []  # list of (name, type_name, multiplicity, children)
        self.connections = []  # list of (from_path, to_path)

        if definition:
            self.keyword = "interface def"
        else:
            self.keyword = "interface"

    def add_end(self, name, type_name=None, multiplicity=None):
        """Add an end to the interface definition.

        Args:
            name: End name
            type_name: Optional type (e.g., 'FuelOutPort')
            multiplicity: Optional multiplicity (e.g., '1', '1..*')
        """
        self.ends.append((name, type_name, multiplicity))
        return self

    def add_connection(self, from_path, to_path):
        """Add a connection between ends.

        Args:
            from_path: Source path (e.g., 'suppliedBy.hot')
            to_path: Target path (e.g., 'deliveredTo.hot')
        """
        self.connections.append((from_path, to_path))
        return self

    def _set_typed_by(self, typed):
        """Set typing (`:`) for interface usage."""
        self._typed_by_name = typed.name if hasattr(typed, 'name') else str(typed)
        return self

    def _set_specializes(self, *parents):
        """Set specialization (`:>`) for interface definitions."""
        self._specializes_names = [
            p.name if hasattr(p, 'name') else str(p) for p in parents
        ]
        return self

    def dump(self):
        name_str = getattr(self, 'name', "") or ""
        keyword = getattr(self, 'keyword', 'interface')

        # Build type/specialization suffix
        type_suffix = ""
        if hasattr(self, '_typed_by_name') and self._typed_by_name:
            type_suffix = f" : {self._typed_by_name}"
        elif hasattr(self, '_specializes_names') and self._specializes_names:
            type_suffix = " :> " + ", ".join(self._specializes_names)

        body_items = []

        for end_name, end_type, end_mult in self.ends:
            mult_str = f"[{end_mult}]" if end_mult else ""
            if end_type:
                body_items.append(f"end {end_name} : {end_type}{mult_str};")
            else:
                body_items.append(f"end {end_name}{mult_str};")

        for from_path, to_path in self.connections:
            body_items.append(f"connect {from_path} to {to_path};")

        if body_items:
            body = " {\n   " + "\n   ".join(body_items) + "\n}"
            return f"{keyword} {name_str}{type_suffix}{body}"
        else:
            return f"{keyword} {name_str}{type_suffix};"


class Action(Usage):
    def __init__(self, definition=False, name=None, shortname=None, grammar=None):
        # If grammar is provided (from load_from_grammar), use it
        if grammar is not None:
            self.grammar = grammar
        else:
            # Initialize grammar properly (like Part does)
            if definition:
                self.grammar = ActionDefinition()
                self.grammar.declaration.identification.declaredName = name if name else None
            else:
                # Create ActionUsage with an empty dict to handle default initialization
                self.grammar = ActionUsage({} if name else None)
                if self.grammar.declaration and hasattr(self.grammar.declaration, 'identification'):
                    self.grammar.declaration.identification.declaredName = name if name else None
        
        self.is_definition = definition
        self.action_shortname = shortname
        self.name = name if name else str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.action_inputs = []  # List of (name, type_name)
        self.action_outputs = []
        
        if definition:
            self.keyword = "action def"
        else:
            self.keyword = "action"

    def add_input(self, name, type_name=None):
        """Add an input parameter (in) to the action.
        
        Args:
            name: Name of the input
            type_name: Optional type (e.g., 'Scene')
        """
        self.action_inputs.append((name, type_name))
        return self
    
    def add_output(self, name, type_name=None):
        """Add an output parameter (out) to the action.
        
        Args:
            name: Name of the output  
            type_name: Optional type (e.g., 'Image')
        """
        self.action_outputs.append((name, type_name))
        return self

    def _get_definition(self, child=None):
        if self.is_definition:
            keyword = "action def"
        else:
            keyword = "action"
        
        decl = {
            "name": "UsageDeclaration",
            "identification": {
                "name": "Identification",
                "declaredName": self.name if self.name else "",
                "declaredShortName": None
            }
        }
        
        # Build action body with in/out parameters
        body_items = []
        
        # Add inputs
        for inp_name, inp_type in self.action_inputs:
            if inp_type:
                item = f"in {inp_name} : {inp_type};"
            else:
                item = f"in {inp_name};"
            body_items.append(item)
        
        # Add outputs  
        for out_name, out_type in self.action_outputs:
            if out_type:
                item = f"out {out_name} : {out_type};"
            else:
                item = f"out {out_name};"
            body_items.append(item)
        
        body = {"name": "ActionBody", "items": body_items}
        
        if self.is_definition:
            grammar_type = "ActionDefinition"
        else:
            grammar_type = "ActionUsage"
        
        return {
            "name": grammar_type,
            "declaration": decl,
            "body": body
        }

    def load_from_grammar(self, grammar):
        self.is_definition = False
        self.action_inputs = []
        self.action_outputs = []
        
        # Check for 'declaration' directly (for definitions like ActionDefinition, RequirementDefinition)
        decl = getattr(grammar, 'declaration', None)
        if decl and hasattr(decl, 'identification') and decl.identification:
            self.name = decl.identification.declaredName
            self.is_definition = True
            self.keyword = "action def"
        elif hasattr(grammar, 'declaration') and grammar.declaration:
            # Handle nested declaration structure (ActionUsageDeclaration -> UsageDeclaration -> FeatureDeclaration)
            decl = getattr(grammar.declaration, 'declaration', None)
            if decl:
                # Try nested: declaration.declaration.declaration.identification (for ANTLR)
                nested_decl = getattr(decl, 'declaration', None)
                if nested_decl and hasattr(nested_decl, 'identification') and nested_decl.identification:
                    self.name = nested_decl.identification.declaredName
                    self.is_definition = False
                    self.keyword = "action"
                elif hasattr(decl, 'identification') and decl.identification:
                    self.name = decl.identification.declaredName
                    self.is_definition = False
                    self.keyword = "action"
        
        return self
    
    def _get_definition(self, child=None):
        # Sync self.name to grammar before getting definition
        if hasattr(self.grammar, 'declaration') and hasattr(self.grammar.declaration, 'identification'):
            self.grammar.declaration.identification.declaredName = self.name
        
        # Get the grammar's get_definition output
        if hasattr(self.grammar, 'get_definition'):
            grammar_def = self.grammar.get_definition()
        else:
            # Fallback - shouldn't happen now
            grammar_def = {"name": "ActionDefinition", "declaration": {}, "body": {}}
        
        package = {
            "name": "DefinitionElement",
            "ownedRelatedElement": grammar_def,
        }

        if child == "DefinitionBody":
            package = {
                "name": "DefinitionMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        elif child == "PackageBody" or child == None:
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }

        return package

    def dump(self):
        name_str = getattr(self, 'name', "") or ""
        keyword = getattr(self, 'keyword', 'action')
        
        # Build output with in/out parameters
        parts = [keyword, name_str]
        
        # Add in/out parameters
        params = []
        for inp_name, inp_type in self.action_inputs:
            if inp_type:
                params.append(f"in {inp_name} : {inp_type}")
            else:
                params.append(f"in {inp_name}")
        
        for out_name, out_type in self.action_outputs:
            if out_type:
                params.append(f"out {out_name} : {out_type}")
            else:
                params.append(f"out {out_name}")
        
        # Build type/specialization suffix
        type_suffix = ""
        if hasattr(self, '_typed_by_name') and self._typed_by_name:
            type_suffix = f" : {self._typed_by_name}"
        elif hasattr(self, '_specializes_names') and self._specializes_names:
            type_suffix = " :> " + ", ".join(self._specializes_names)
        
        if params:
            return f"{keyword} {name_str}{type_suffix} {{ " + "; ".join(params) + "; }"
        else:
            return f"{keyword} {name_str}{type_suffix};"

    def _set_typed_by(self, typed):
        """Set typing (`:`) for action usage typed by action definition."""
        self._typed_by_name = typed.name if hasattr(typed, 'name') else str(typed)
        return self

    def _set_specializes(self, *parents):
        """Set specialization (`:>`) for action definitions."""
        self._specializes_names = [
            p.name if hasattr(p, 'name') else str(p) for p in parents
        ]
        return self


class UseCase(Usage):
    def __init__(self, definition=False, name=None, shortname=None):
        if definition:
            self.grammar = UseCaseDefinition()
            self.grammar.declaration.identification.declaredName = name if name else None
        else:
            self.grammar = True
        
        self.is_definition = definition
        self.name = name if name else str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.subject = None  # (name, type_name)
        self.actors = []  # list of (name, type_name)
        self.includes = []  # list of use case names
        
        if definition:
            self.keyword = "use case def"
        else:
            self.keyword = "use case"

    def _get_definition(self, child=None):
        # Sync name to grammar
        if hasattr(self.grammar, 'declaration') and hasattr(self.grammar.declaration, 'identification'):
            self.grammar.declaration.identification.declaredName = self.name
        
        if hasattr(self.grammar, 'get_definition'):
            grammar_def = self.grammar.get_definition()
        else:
            grammar_def = {"name": "UseCaseDefinition", "declaration": {}, "body": {}}
        
        package = {
            "name": "DefinitionElement",
            "ownedRelatedElement": grammar_def,
        }

        if child == "DefinitionBody":
            package = {
                "name": "DefinitionMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        elif child == "PackageBody" or child == None:
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }

        return package

    def set_subject(self, name, type_name=None):
        """Set the subject of the use case.
        
        Args:
            name: Name of the subject
            type_name: Optional type (e.g., 'Vehicle')
        """
        self.subject = (name, type_name)
        return self

    def add_actor(self, name, type_name=None):
        """Add an actor to the use case.
        
        Args:
            name: Name of the actor
            type_name: Optional type (e.g., 'Driver')
        """
        self.actors.append((name, type_name))
        return self

    def add_include(self, use_case):
        """Add an included use case.
        
        Args:
            use_case: UseCase object or name string to include
        """
        name = use_case.name if hasattr(use_case, 'name') else str(use_case)
        self.includes.append(name)
        return self

    def _set_typed_by(self, typed):
        """Set typing (`:`) for use case usage."""
        self._typed_by_name = typed.name if hasattr(typed, 'name') else str(typed)
        return self

    def _set_specializes(self, *parents):
        """Set specialization (`:>`) for use case definitions."""
        self._specializes_names = [
            p.name if hasattr(p, 'name') else str(p) for p in parents
        ]
        return self

    def dump(self):
        name_str = getattr(self, 'name', "") or ""
        keyword = getattr(self, 'keyword', 'use case')
        
        # Build type/specialization suffix
        type_suffix = ""
        if hasattr(self, '_typed_by_name') and self._typed_by_name:
            type_suffix = f" : {self._typed_by_name}"
        elif hasattr(self, '_specializes_names') and self._specializes_names:
            type_suffix = " :> " + ", ".join(self._specializes_names)
        
        # Build body members
        body_items = []
        
        if self.subject:
            subj_name, subj_type = self.subject
            if subj_type:
                body_items.append(f"subject {subj_name} : {subj_type};")
            else:
                body_items.append(f"subject {subj_name};")
        
        for actor_name, actor_type in self.actors:
            if actor_type:
                body_items.append(f"actor {actor_name} : {actor_type};")
            else:
                body_items.append(f"actor {actor_name};")
        
        for inc in self.includes:
            body_items.append(f"include use case {inc};")
        
        if body_items:
            body = " {\n   " + "\n   ".join(body_items) + "\n}"
            return f"{keyword} {name_str}{type_suffix}{body}"
        else:
            return f"{keyword} {name_str}{type_suffix};"


class Requirement(Usage):
    def __init__(self, definition=False, name=None, shortname=None):
        if definition:
            self.grammar = RequirementDefinition(None)
            self.grammar.declaration.identification.declaredName = name if name else None
        else:
            self.grammar = True
        
        self.is_definition = definition
        self.name = name if name else str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.req_shortname = shortname
        self.subject = None
        self.actors = []
        self.doc = None
        self.attributes = []
        self.constraints = []
        self.assume_constraints = []

        if definition:
            self.keyword = "requirement def"
        else:
            self.keyword = "requirement"

    def _get_definition(self, child=None):
        # Sync name to grammar
        if hasattr(self.grammar, 'declaration') and hasattr(self.grammar.declaration, 'identification'):
            self.grammar.declaration.identification.declaredName = self.name
        
        if hasattr(self.grammar, 'get_definition'):
            grammar_def = self.grammar.get_definition()
        else:
            grammar_def = {"name": "RequirementDefinition", "declaration": {}, "body": {}}
        
        package = {
            "name": "DefinitionElement",
            "ownedRelatedElement": grammar_def,
        }

        if child == "DefinitionBody":
            package = {
                "name": "DefinitionMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        elif child == "PackageBody" or child == None:
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }

        return package

    def set_subject(self, name, type_name=None):
        """Set the subject of the requirement.

        Args:
            name: Name of the subject
            type_name: Optional type (e.g., 'Vehicle')
        """
        self.subject = (name, type_name)
        return self

    def add_actor(self, name, type_name=None):
        """Add an actor to the requirement.

        Args:
            name: Name of the actor
            type_name: Optional type
        """
        self.actors.append((name, type_name))
        return self

    def set_doc(self, text):
        """Set the documentation string.

        Args:
            text: Documentation text
        """
        self.doc = text
        return self

    def add_attribute(self, name, type_name=None):
        """Add an attribute to the requirement.

        Args:
            name: Attribute name
            type_name: Optional type
        """
        self.attributes.append((name, type_name))
        return self

    def add_constraint(self, expr):
        """Add a require constraint expression.

        Args:
            expr: Constraint expression string (e.g., 'massActual <= massReqd')
        """
        self.constraints.append(expr)
        return self

    def add_assume_constraint(self, expr):
        """Add an assume constraint expression.

        Args:
            expr: Assume constraint expression string
        """
        self.assume_constraints.append(expr)
        return self

    def _set_typed_by(self, typed):
        """Set typing (`:`) for requirement usage."""
        self._typed_by_name = typed.name if hasattr(typed, 'name') else str(typed)
        return self

    def _set_specializes(self, *parents):
        """Set specialization (`:>`) for requirement definitions."""
        self._specializes_names = [
            p.name if hasattr(p, 'name') else str(p) for p in parents
        ]
        return self

    def dump(self):
        name_str = getattr(self, 'name', "") or ""
        keyword = getattr(self, 'keyword', 'requirement')

        # Add shortname
        shortname_str = ""
        if self.req_shortname:
            shortname_str = f" <{self.req_shortname}>"

        # Build type/specialization suffix
        type_suffix = ""
        if hasattr(self, '_typed_by_name') and self._typed_by_name:
            type_suffix = f" : {self._typed_by_name}"
        elif hasattr(self, '_specializes_names') and self._specializes_names:
            type_suffix = " :> " + ", ".join(self._specializes_names)

        # Build body members
        body_items = []

        if self.doc:
            body_items.append(f"doc /* {self.doc} */")

        if self.subject:
            subj_name, subj_type = self.subject
            if subj_type:
                body_items.append(f"subject {subj_name} : {subj_type};")
            else:
                body_items.append(f"subject {subj_name};")

        for actor_name, actor_type in self.actors:
            if actor_type:
                body_items.append(f"actor {actor_name} : {actor_type};")
            else:
                body_items.append(f"actor {actor_name};")

        for attr_name, attr_type in self.attributes:
            if attr_type:
                body_items.append(f"attribute {attr_name} : {attr_type};")
            else:
                body_items.append(f"attribute {attr_name};")

        for expr in self.constraints:
            body_items.append(f"require constraint {{ {expr} }}")

        for expr in self.assume_constraints:
            body_items.append(f"assume constraint {{ {expr} }}")

        if body_items:
            body = " {\n   " + "\n   ".join(body_items) + "\n}"
            return f"{keyword}{shortname_str} {name_str}{type_suffix}{body}"
        else:
            return f"{keyword}{shortname_str} {name_str}{type_suffix};"


class Message(Usage):
    def __init__(self, name=None, from_port=None, to_port=None, of_type=None):
        """Create a message.

        Args:
            name: Optional message name
            from_port: Source port/part path (e.g., 'sensor')
            to_port: Target port/part path (e.g., 'controller')
            of_type: Optional item type (e.g., 'SensorData')
        """
        self.name = name if name else str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.grammar = True
        self.from_port = from_port
        self.to_port = to_port
        self.of_type = of_type

    def set_from(self, from_port):
        """Set the source of the message.

        Args:
            from_port: Source path string or element with .name
        """
        self.from_port = from_port.name if hasattr(from_port, 'name') else str(from_port)
        return self

    def set_to(self, to_port):
        """Set the target of the message.

        Args:
            to_port: Target path string or element with .name
        """
        self.to_port = to_port.name if hasattr(to_port, 'name') else str(to_port)
        return self

    def set_of(self, of_type):
        """Set the item type of the message.

        Args:
            of_type: Item type string or element with .name
        """
        self.of_type = of_type.name if hasattr(of_type, 'name') else str(of_type)
        return self

    def dump(self):
        parts = ["message"]

        # Name (if not a UUID)
        name_str = getattr(self, 'name', "") or ""
        try:
            import uuid as _uuid
            _uuid.UUID(name_str)
            # It's a UUID - anonymous message, skip name
        except ValueError:
            parts.append(name_str)

        if self.of_type:
            parts.append(f"of {self.of_type}")

        if self.from_port and self.to_port:
            parts.append(f"from {self.from_port} to {self.to_port}")
        elif self.to_port:
            parts.append(f"to {self.to_port}")

        return " ".join(parts) + ";"


class _BehaviorUsage(Usage):
    """Base class for behavior-style usages (state, action, etc.).
    
    These get wrapped in BehaviorUsageElement rather than StructureUsageElement.
    """
    # Subclasses should set _is_definition_grammar based on grammar class
    _is_definition_grammar = False
    
    def _get_definition(self, child=None):
        # Determine if this is a definition or usage based on grammar class name
        grammar_cls_name = type(self.grammar).__name__
        is_def = grammar_cls_name.endswith('Definition')
        
        if is_def:
            package = self.behavior_definition_dump(child)
        else:
            package = self.usage_dump(child)

        if child is None:
            package = {
                "name": "PackageBodyElement",
                "ownedRelationship": [package],
                "prefix": None,
            }
        return package
    
    def usage_dump(self, child):
        # This is a behavior usage, not a structure usage.
        package = {
            "name": "BehaviorUsageElement",
            "ownedRelationship": self.grammar.get_definition(),
        }
        package = {"name": "OccurrenceUsageElement", "ownedRelatedElement": package}

        if child == "DefinitionBody":
            package = {
                "name": "OccurrenceUsageMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        else:
            package = {"name": "UsageElement", "ownedRelatedElement": package}
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }
        return package

    def behavior_definition_dump(self, child):
        package = {
            "name": "DefinitionElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }

        if child == "DefinitionBody":
            package = {
                "name": "DefinitionMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        else:
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }
        return package


class _NonOccurrenceUsage(Usage):
    """Base class for non-occurrence usages (attribute, calculation, constraint, etc.).
    
    These get wrapped in NonOccurrenceUsageElement rather than StructureUsageElement.
    """
    def _get_definition(self, child=None):
        grammar_cls_name = type(self.grammar).__name__
        is_def = grammar_cls_name.endswith('Definition')
        
        if is_def:
            package = self.nonocc_definition_dump(child)
        else:
            package = self.usage_dump(child)

        if child is None:
            package = {
                "name": "PackageBodyElement",
                "ownedRelationship": [package],
                "prefix": None,
            }
        return package
    
    def usage_dump(self, child):
        # Add packaging for non-occurrence usage
        package = {
            "name": "NonOccurrenceUsageElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }

        if child == "DefinitionBody":
            package = {
                "name": "NonOccurrenceUsageMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        else:
            package = {"name": "UsageElement", "ownedRelatedElement": package}
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }
        return package

    def nonocc_definition_dump(self, child):
        package = {
            "name": "DefinitionElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }

        if child == "DefinitionBody":
            package = {
                "name": "DefinitionMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }
            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        else:
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }
        return package


class State(_BehaviorUsage):
    """SysML v2 State Machine state usage/definition.
    
    Usage:
        State()                              # state ;
        State(name='Idle')                   # state Idle;
        State(definition=True, name='Mode')  # state def Mode;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = StateDefinition()
        else:
            self.grammar = StateUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Constraint(_NonOccurrenceUsage):
    """SysML v2 Constraint usage/definition.
    
    Usage:
        Constraint()                              # constraint ;
        Constraint(name='PowerLimit')             # constraint PowerLimit;
        Constraint(definition=True, name='Limit') # constraint def Limit;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = ConstraintDefinition()
        else:
            self.grammar = ConstraintUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Connection(Usage):
    """SysML v2 Connection usage/definition.
    
    Usage:
        Connection()                                  # connection ;
        Connection(name='wire')                       # connection wire;
        Connection(definition=True, name='DataLink')  # connection def DataLink;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = ConnectionDefinition()
        else:
            self.grammar = ConnectionUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Flow(Usage):
    """SysML v2 Flow connection usage/definition.
    
    Usage:
        Flow()                                       # flow ;
        Flow(name='fuelFlow')                        # flow fuelFlow;
        Flow(definition=True, name='WaterFlow')      # flow def WaterFlow;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = FlowConnectionDefinition()
        else:
            self.grammar = FlowConnectionUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Calculation(_NonOccurrenceUsage):
    """SysML v2 Calculation usage/definition.
    
    Usage:
        Calculation()                                   # calc ;
        Calculation(name='computeArea')                 # calc computeArea;
        Calculation(definition=True, name='Distance')   # calc def Distance;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = CalculationDefinition()
        else:
            self.grammar = CalculationUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Enumeration(Usage):
    """SysML v2 Enumeration definition.
    
    Note: SysML v2 only has EnumerationDefinition, no EnumerationUsage.
    
    Usage:
        Enumeration(name='Color')  # enum def Color;
    """
    def __init__(self, definition=True, name=None, shortname=None):
        Usage.__init__(self)
        # EnumerationDefinition is the only form
        self.grammar = EnumerationDefinition()
        
        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Allocation(Usage):
    """SysML v2 Allocation usage/definition.
    
    Allocation represents mapping from one model element to another.
    
    Usage:
        Allocation()                                  # allocation ;
        Allocation(name='alloc1')                     # allocation alloc1;
        Allocation(definition=True, name='AllocSpec') # allocation def AllocSpec;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = AllocationDefinition()
        else:
            self.grammar = AllocationUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Metadata(_NonOccurrenceUsage):
    """SysML v2 Metadata usage/definition.
    
    Metadata attaches additional information to model elements.
    
    Usage:
        Metadata()                                       # metadata ;
        Metadata(name='tag1')                            # metadata tag1;
        Metadata(definition=True, name='AuthorMeta')     # metadata def AuthorMeta;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = MetadataDefinition()
        else:
            self.grammar = MetadataUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Rendering(Usage):
    """SysML v2 Rendering usage/definition.
    
    Rendering specifies how views should be rendered.
    
    Usage:
        Rendering()                                    # rendering ;
        Rendering(name='myRender')                     # rendering myRender;
        Rendering(definition=True, name='DefRender')   # rendering def DefRender;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = RenderingDefinition()
        else:
            self.grammar = RenderingUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Individual(Usage):
    """SysML v2 Individual usage/definition.
    
    Individual represents a specific instance or occurrence.
    
    Usage:
        Individual()                                     # individual ;
        Individual(name='instance1')                     # individual instance1;
        Individual(definition=True, name='DefIndiv')     # individual def DefIndiv;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = IndividualDefinition()
        else:
            self.grammar = IndividualUsageSimple()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class FlowDef(Usage):
    """SysML v2 FlowDefinition alternate form.
    
    Note: This is the simpler 'flow def' form (distinct from FlowConnectionDefinition).
    Usage already provides Flow class for flowConnectionUsage/Definition.
    
    Usage:
        FlowDef(name='DataStream')   # flow def DataStream;
    """
    def __init__(self, name=None, shortname=None):
        Usage.__init__(self)
        self.grammar = FlowDefinition()
        
        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class View(Usage):
    """SysML v2 View usage/definition.
    
    Views define how models are presented and filtered.
    
    Usage:
        View()                                  # view ;
        View(name='systemOverview')             # view systemOverview;
        View(definition=True, name='SysView')   # view def SysView;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = ViewDefinition()
        else:
            self.grammar = ViewUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Viewpoint(_BehaviorUsage):
    """SysML v2 Viewpoint usage/definition.
    
    Viewpoints specify viewing perspectives with stakeholder concerns.
    
    Usage:
        Viewpoint()                                   # viewpoint ;
        Viewpoint(name='stakeholderVP')               # viewpoint stakeholderVP;
        Viewpoint(definition=True, name='VPDef')      # viewpoint def VPDef;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = ViewpointDefinition()
        else:
            self.grammar = ViewpointUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Concern(_BehaviorUsage):
    """SysML v2 Concern usage/definition.
    
    Concerns represent stakeholder concerns for viewpoints.
    
    Usage:
        Concern()                                  # concern ;
        Concern(name='security')                   # concern security;
        Concern(definition=True, name='Safety')    # concern def Safety;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = ConcernDefinition()
        else:
            self.grammar = ConcernUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Case(_BehaviorUsage):
    """SysML v2 Case usage/definition.
    
    A case is a broad classifier for analysis, verification, and use cases.
    
    Usage:
        Case()                                  # case ;
        Case(name='scenario1')                  # case scenario1;
        Case(definition=True, name='CaseSpec')  # case def CaseSpec;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = CaseDefinition()
        else:
            self.grammar = CaseUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class AnalysisCase(_BehaviorUsage):
    """SysML v2 AnalysisCase usage/definition.
    
    Analysis cases represent analytical scenarios or studies.
    
    Usage:
        AnalysisCase()                                  # analysis ;
        AnalysisCase(name='thermal1')                   # analysis thermal1;
        AnalysisCase(definition=True, name='Thermal')   # analysis def Thermal;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = AnalysisCaseDefinition()
        else:
            self.grammar = AnalysisCaseUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class VerificationCase(_BehaviorUsage):
    """SysML v2 VerificationCase usage/definition.
    
    Verification cases represent verification scenarios or tests.
    
    Usage:
        VerificationCase()                                    # verification ;
        VerificationCase(name='test1')                        # verification test1;
        VerificationCase(definition=True, name='Verify1')     # verification case def Verify1;
    """
    def __init__(self, definition=False, name=None, shortname=None):
        Usage.__init__(self)
        if definition:
            self.grammar = VerificationCaseDefinition()
        else:
            self.grammar = VerificationCaseUsage()

        if name is not None:
            self._set_name(name)
        if shortname is not None:
            self._set_name(shortname, short=True)


class Reference(Usage):
    def __init__(self, name=None, shortname=None, redefines=None):
        self.name = name if name else str(uuidlib.uuid4())
        self.children = []
        self.typedby = None
        self.grammar = None
        self.shortname = shortname
        self.redefines = redefines  # for redefinition like ref :>> name :
        self.ref_type = None  # type reference

    def set_type(self, type_obj):
        """Set the type this reference points to.
        
        Args:
            type_obj: Another element (Item, Part, etc.) to reference
        """
        self.ref_type = type_obj
        return self

    def _set_typed_by(self, type_obj):
        """Alias for set_type for consistency with other classes."""
        return self.set_type(type_obj)

    def dump(self):
        name_str = getattr(self, 'name', "") or ""
        type_str = ""
        
        if self.ref_type:
            type_name = getattr(self.ref_type, 'name', str(self.ref_type))
            type_str = f" : {type_name}"
        
        if self.redefines:
            return f"ref :>> {name_str}{type_str};"
        
        return f"ref {name_str}{type_str};"


class DefaultReference(Usage):
    def __init__(self):
        Usage.__init__(self)
        self.grammar = DefaultReferenceUsage()

    def set_direction(self, direction):
        r = RefPrefix()
        if direction == "in":
            r.direction.isIn = True
        elif direction == "out":
            r.direction.isOut = True
        elif direction == "inout":
            r.direction.isInOut = True
        else:
            raise ValueError
        self.grammar.prefix = r
        return self

    def usage_dump(self, child):
        # This is a usage.

        self._ensure_body("definition")

        # Add packaging
        package = {
            "name": "NonOccurrenceUsageElement",
            "ownedRelatedElement": self.grammar.get_definition(),
        }

        if child == "DefinitionBody":
            package = {
                "name": "NonOccurrenceUsageMember",
                "prefix": None,
                "ownedRelatedElement": [package],
            }

            package = {"name": "DefinitionBodyItem", "ownedRelationship": [package]}
        elif "PackageBody":
            package = {"name": "UsageElement", "ownedRelatedElement": package}
            package = {
                "name": "PackageMember",
                "ownedRelatedElement": package,
                "prefix": None,
            }

        return package

    def _get_definition(self, child=None):
        package = self.usage_dump(child)

        if child is None:
            package = {
                "name": "PackageBodyElement",
                "ownedRelationship": [package],
                "prefix": None,
            }

        # Add the typed by definition to the package output
        if self.typedby is not None:
            if child is None:
                package["ownedRelationship"].insert(
                    0, self.typedby._get_definition(child="PackageBody")
                )
            elif child == "PackageBody":
                package = [self.typedby._get_definition(child="PackageBody"), package]
            else:
                package["ownedRelationship"].insert(
                    0, self.typedby._get_definition(child=child)["ownedRelationship"][0]
                )

        return package

    # def dump(self, child=None):
    #     package = self.usage_dump(child)

    #     if child is None:
    #         package = {
    #             "name": "PackageBodyElement",
    #             "ownedRelationship": [package],
    #             "prefix": None,
    #         }

    #     # Add the typed by definition to the package output
    #     if self.typedby is not None:
    #         if child is None:
    #             package["ownedRelationship"].insert(
    #                 0, self.typedby.dump(child="PackageBody")
    #             )
    #         elif child == "PackageBody":
    #             package = [self.typedby.dump(child="PackageBody"), package]
    #         else:
    #             package["ownedRelationship"].insert(
    #                 0, self.typedby.dump(child=child)["ownedRelationship"][0]
    #             )

    #     return package
