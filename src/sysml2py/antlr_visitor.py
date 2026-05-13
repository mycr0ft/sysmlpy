#!/usr/bin/env python3
"""
ANTLR4 to dictionary converter for SysML v2.0.

This module converts the ANTLR4 parse tree to a dictionary format
for use with the sysml2py class hierarchy.
"""
import uuid


def _extract_name_shortname(name_text):
    """Given a name text, determine if it's a short name (quoted) or regular name.
    
    Returns (name, shortname) tuple.
    """
    if name_text and (name_text.startswith("'") or name_text.startswith('"')):
        return None, name_text
    return name_text, None


def _get_usage_identification(ctx):
    """Extract (name, shortname) from a usage context by navigating usage().usageDeclaration().identification().
    
    Returns (name, shortname) tuple.
    """
    name = None
    shortname = None
    if ctx is None:
        return name, shortname
    
    # Try to get usage -> usageDeclaration -> identification
    usage = None
    if hasattr(ctx, 'usage') and ctx.usage():
        usage = ctx.usage()
    
    ud = None
    if usage and hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
        ud = usage.usageDeclaration()
    elif hasattr(ctx, 'usageDeclaration') and ctx.usageDeclaration():
        ud = ctx.usageDeclaration()
    
    if ud and hasattr(ud, 'identification') and ud.identification():
        ident = ud.identification()
        if hasattr(ident, 'name'):
            name_list = ident.name()
            if name_list and isinstance(name_list, list):
                if len(name_list) == 2:
                    # LT name GT name: first is short name, second is long name
                    shortname = name_list[0].getText()
                    name = name_list[1].getText()
                elif len(name_list) == 1:
                    # Single name: could be short or long depending on token type
                    name_text = name_list[0].getText()
                    name, shortname = _extract_name_shortname(name_text)
    
    return name, shortname


def _get_definition_identification(ctx):
    """Extract (name, shortname) from a definition context by navigating definition().definitionDeclaration().identification().
    
    Returns (name, shortname) tuple.
    """
    name = None
    shortname = None
    if ctx is None:
        return name, shortname
    
    # Try different paths to find definitionDeclaration
    defn = None
    if hasattr(ctx, 'definition') and ctx.definition():
        defn = ctx.definition()
    
    dd = None
    if defn and hasattr(defn, 'definitionDeclaration') and defn.definitionDeclaration():
        dd = defn.definitionDeclaration()
    elif hasattr(ctx, 'definitionDeclaration') and ctx.definitionDeclaration():
        dd = ctx.definitionDeclaration()
    
    if dd and hasattr(dd, 'identification') and dd.identification():
        ident = dd.identification()
        if hasattr(ident, 'name'):
            name_list = ident.name()
            if name_list and isinstance(name_list, list):
                if len(name_list) == 2:
                    # LT name GT name: first is short name, second is long name
                    shortname = name_list[0].getText()
                    name = name_list[1].getText()
                elif len(name_list) == 1:
                    # Single name: could be short or long depending on token type
                    name_text = name_list[0].getText()
                    name, shortname = _extract_name_shortname(name_text)
    
    return name, shortname


def _build_identification_dict(ident_ctx):
    """Build an identification dictionary from an ANTLR IdentificationContext.
    
    Returns a dict like {"name": "Identification", "declaredName": ..., "declaredShortName": ...}
    or None if there is no identification.
    """
    if ident_ctx is None:
        return None
    
    name = None
    shortname = None
    
    if hasattr(ident_ctx, 'name'):
        name_list = ident_ctx.name()
        if name_list and isinstance(name_list, list):
            if len(name_list) == 2:
                shortname = name_list[0].getText()
                name = name_list[1].getText()
            elif len(name_list) == 1:
                name_text = name_list[0].getText()
                if name_text.startswith("'") or name_text.startswith('"'):
                    shortname = name_text
                else:
                    name = name_text
    
    if name is None and shortname is None:
        return None
    
    return {
        "name": "Identification",
        "declaredShortName": shortname,
        "declaredName": name
    }


def _visit_documentation_dict(ctx):
    """Visit a documentation context and return a Documentation dictionary.
    
    Grammar: DOC identification? (LOCALE DOUBLE_STRING)? REGULAR_COMMENT
    """
    body = None
    if ctx.REGULAR_COMMENT():
        body = ctx.REGULAR_COMMENT().getText()
    
    identification = None
    if ctx.identification():
        identification = _build_identification_dict(ctx.identification())
    
    return {
        "name": "Documentation",
        "body": body,
        "identification": identification,
        "ownedRelationship": []
    }


def _visit_comment_dict(ctx):
    """Visit a comment context and return a CommentSysML dictionary.
    
    Grammar: (COMMENT identification? ( ABOUT annotation ( COMMA annotation)*)?)? (LOCALE DOUBLE_STRING)? REGULAR_COMMENT
    """
    body = None
    if ctx.REGULAR_COMMENT():
        body = ctx.REGULAR_COMMENT().getText()
    
    identification = None
    if ctx.identification():
        identification = _build_identification_dict(ctx.identification())
    
    annotations = []
    if ctx.ABOUT():
        for i in range(ctx.getChildCount()):
            ann_ctx = ctx.annotation(i) if i < len(ctx.annotation()) else None
            # annotation(i) returns None for out-of-range; iterate properly
        for ann_idx in range(len(ctx.annotation())):
            ann_ctx = ctx.annotation(ann_idx)
            if ann_ctx and ann_ctx.qualifiedName():
                qn_text = ann_ctx.qualifiedName().getText()
                annotations.append({
                    "name": "Annotation",
                    "annotatedElement": {
                        "name": "QualifiedName",
                        "names": qn_text.split("::")
                    }
                })
    
    return {
        "name": "CommentSysML",
        "body": body,
        "identification": identification,
        "ownedRelationship": annotations
    }


def _visit_annotating_element_dict(annot_elem_ctx):
    """Visit an annotating element context and return an AnnotatingElement dictionary.
    
    Dispatches to documentation or comment based on the context.
    """
    if annot_elem_ctx is None:
        return None
    
    inner = None
    if hasattr(annot_elem_ctx, 'documentation') and annot_elem_ctx.documentation():
        inner = _visit_documentation_dict(annot_elem_ctx.documentation())
    elif hasattr(annot_elem_ctx, 'comment') and annot_elem_ctx.comment():
        inner = _visit_comment_dict(annot_elem_ctx.comment())
    
    if inner is None:
        return None
    
    return {
        "name": "AnnotatingElement",
        "ownedRelatedElement": inner
    }


def parse_to_dict(source, library=None):
    """Parse SysML source and return a dictionary.
    
    Parameters
    ----------
    source : str or file-like
        Either a string containing SysML v2.0 code, or a file object.
    library : str or Path, optional
        Path to SysML v2 library files for resolving imports.
    
    Returns
    -------
    dict
        A dictionary representation of the SysML model.
    """
    from sysml2py import antlr_parser
    
    tree = antlr_parser.parse(source, library=library)
    return _visit_root_namespace_dict(tree)


def _visit_root_namespace_dict(tree):
    """Visit the root namespace (top-level) which can have multiple packageBodyElements."""
    body_elements = []
    
    if hasattr(tree, 'packageBodyElement'):
        elements = tree.packageBodyElement()
        if elements:
            for elem_ctx in elements:
                elem_dict = _visit_package_body_element_dict(elem_ctx)
                if elem_dict:
                    body_elements.append(elem_dict)
    
    return {
        "name": "PackageBodyElement",
        "ownedRelationship": body_elements
    }


def _visit_package_dict(tree):
    """Visit a package context and return a dictionary."""
    # Get package name from identification
    pkg_name = None
    pkg_shortname = None
    if tree.packageDeclaration():
        decl = tree.packageDeclaration()
        if hasattr(decl, 'identification'):
            ident = decl.identification()
            if ident:
                # Handle identification: LT name GT name | LT name GT | name
                if hasattr(ident, 'name'):
                    name_list = ident.name()
                    if name_list and isinstance(name_list, list):
                        if len(name_list) == 2:
                            # LT name GT name: first is short name, second is long name
                            pkg_shortname = name_list[0].getText()
                            pkg_name = name_list[1].getText()
                        elif len(name_list) == 1:
                            # Single name - need to tell if it's a short or long name
                            # Check the actual token text - if it starts with quote, it's a short name
                            name_text = name_list[0].getText()
                            if name_text.startswith("'") or name_text.startswith('"'):
                                # Short name (<name>)
                                pkg_shortname = name_text
                            else:
                                # Regular identifier (name)
                                pkg_name = name_text
                        # If len(name_list) == 0, leave both as None

    # Build package body elements
    body_elements = []
    if tree.packageBody():
        body = tree.packageBody()
        if hasattr(body, 'packageBodyElement'):
            elements = body.packageBodyElement()
            for elem_ctx in elements:
                elem_dict = _visit_package_body_element_dict(elem_ctx)
                if elem_dict:
                    body_elements.append(elem_dict)

    # Build the complete package dictionary
    result = {
        "name": "PackageBodyElement",
        "ownedRelationship": [
            {
                "name": "PackageMember",
                "prefix": None,
                "ownedRelatedElement": {
                    "name": "DefinitionElement",
                    "ownedRelatedElement": {
                        "name": "Package",
                        "ownedRelationship": [],
                        "declaration": {
                            "name": "PackageDeclaration",
                            "identification": {
                                "name": "Identification",
                                "declaredShortName": pkg_shortname,
                                "declaredName": pkg_name
                            }
                        },
                        "body": {
                            "name": "PackageBody",
                            "ownedRelationship": body_elements
                        }
                    }
                }
            }
        ]
    }

    return result


def _visit_visibility_indicator_dict(vis_ctx):
    """Build a VisibilityIndicator dict from ANTLR context."""
    return {
        "name": "VisibilityIndicator",
        "private": "private" if vis_ctx.PRIVATE() else "",
        "protected": "protected" if vis_ctx.PROTECTED() else "",
        "public": "public" if vis_ctx.PUBLIC() else ""
    }


def _visit_import_rule_dict(import_ctx):
    """Visit an import rule context and return an Import dictionary."""
    visibility_dict = None
    if import_ctx.visibilityIndicator():
        visibility_dict = _visit_visibility_indicator_dict(import_ctx.visibilityIndicator())

    is_import_all = import_ctx.ALL() is not None

    imp_dec = import_ctx.importDeclaration()

    qn_text = None
    is_recursive = False
    has_namespace = False

    if imp_dec.membershipImport():
        mem = imp_dec.membershipImport()
        qn_text = mem.qualifiedName().getText()
        is_recursive = mem.STAR_STAR() is not None
        qn_names = qn_text.split("::")
        return {
            "name": "Import",
            "body": {"name": "RelationshipBody", "ownedRelationship": []},
            "ownedRelationship": {
                "name": "MembershipImport",
                "prefix": {
                    "name": "ImportPrefix",
                    "visibility": visibility_dict,
                    "isImportAll": is_import_all
                },
                "membership": {
                    "name": "ImportedMembership",
                    "importedMembership": {"name": "QualifiedName", "names": qn_names},
                    "isRecursive": is_recursive
                }
            }
        }

    elif imp_dec.namespaceImport():
        ns = imp_dec.namespaceImport()
        qn_text = ns.qualifiedName().getText()
        qn_names = qn_text.split("::")
        has_colon_colon = ns.COLON_COLON() is not None
        has_star_star = ns.STAR_STAR() is not None

        if has_colon_colon:
            return {
                "name": "Import",
                "body": {"name": "RelationshipBody", "ownedRelationship": []},
                "ownedRelationship": {
                    "name": "NamespaceImport",
                    "prefix": {
                        "name": "ImportPrefix",
                        "visibility": visibility_dict,
                        "isImportAll": is_import_all
                    },
                    "ownedRelatedElement": [],
                    "namespace": {
                        "name": "ImportedNamespace",
                        "namespace": {"name": "QualifiedName", "names": qn_names},
                        "isRecursive": has_star_star
                    }
                }
            }
        else:
            return {
                "name": "Import",
                "body": {"name": "RelationshipBody", "ownedRelationship": []},
                "ownedRelationship": {
                    "name": "MembershipImport",
                    "prefix": {
                        "name": "ImportPrefix",
                        "visibility": visibility_dict,
                        "isImportAll": is_import_all
                    },
                    "membership": {
                        "name": "ImportedMembership",
                        "importedMembership": {"name": "QualifiedName", "names": qn_names},
                        "isRecursive": False
                    }
                }
            }

    return None


def _visit_alias_member_dict(alias_ctx):
    """Visit an alias member context and return an AliasMember dictionary."""
    short_name = None
    name = None
    has_short_name = alias_ctx.LT() is not None

    name_list = alias_ctx.name() if hasattr(alias_ctx, 'name') else None
    if name_list and isinstance(name_list, list):
        if len(name_list) >= 2:
            short_name = name_list[0].getText() if name_list[0] else None
            name = name_list[1].getText() if name_list[1] else None
        elif len(name_list) == 1:
            if has_short_name:
                short_name = name_list[0].getText()
            else:
                name = name_list[0].getText()

    qn_text = alias_ctx.qualifiedName().getText()

    return {
        "name": "AliasMember",
        "prefix": None,
        "body": {"name": "RelationshipBody", "ownedRelationship": []},
        "memberShortName": short_name,
        "memberName": name,
        "memberElement": {"name": "QualifiedName", "names": qn_text.split("::")}
    }


def _visit_package_body_element_dict(elem_ctx):
    """Visit a package body element and return a dictionary."""
    # Check for importRule first
    if hasattr(elem_ctx, 'importRule') and elem_ctx.importRule():
        return _visit_import_rule_dict(elem_ctx.importRule())

    # Check for aliasMember
    if hasattr(elem_ctx, 'aliasMember') and elem_ctx.aliasMember():
        return _visit_alias_member_dict(elem_ctx.aliasMember())

    if not hasattr(elem_ctx, 'packageMember'):
        return None
    
    member = elem_ctx.packageMember()
    if not member:
        return None
    
    # Get prefix if present
    prefix = None
    if hasattr(member, 'memberPrefix'):
        mp = member.memberPrefix()
        if mp:
            if hasattr(mp, 'redefines'):
                prefix = 'redefines'
            elif hasattr(mp, 'conjugated'):
                prefix = 'conjugated'
    
    # Check if it's a definition or usage element
    if hasattr(member, 'definitionElement'):
        def_elem = member.definitionElement()
        if def_elem:
            return _visit_definition_element_dict(def_elem, prefix)
    
    # Check usage element (only if definition was falsy or absent)
    if hasattr(member, 'usageElement'):
        usage_elem = member.usageElement()
        if usage_elem:
            return _visit_usage_element_dict(usage_elem, prefix)
    
    return None


def _visit_definition_element_dict(def_elem_ctx, prefix=None):
    """Visit a definition element context and return a dictionary."""
    # Try different definition types
    # Check package first (nested packages)
    if hasattr(def_elem_ctx, 'package') and def_elem_ctx.package():
        ctx = def_elem_ctx.package()
        return _make_nested_package_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'itemDefinition') and def_elem_ctx.itemDefinition():
        ctx = def_elem_ctx.itemDefinition()
        return _make_item_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'partDefinition') and def_elem_ctx.partDefinition():
        ctx = def_elem_ctx.partDefinition()
        return _make_part_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'attributeDefinition') and def_elem_ctx.attributeDefinition():
        ctx = def_elem_ctx.attributeDefinition()
        return _make_attribute_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'portDefinition') and def_elem_ctx.portDefinition():
        ctx = def_elem_ctx.portDefinition()
        return _make_port_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'requirementDefinition') and def_elem_ctx.requirementDefinition():
        ctx = def_elem_ctx.requirementDefinition()
        return _make_requirement_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'useCaseDefinition') and def_elem_ctx.useCaseDefinition():
        ctx = def_elem_ctx.useCaseDefinition()
        return _make_use_case_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'actionDefinition') and def_elem_ctx.actionDefinition():
        ctx = def_elem_ctx.actionDefinition()
        return _make_action_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'stateDefinition') and def_elem_ctx.stateDefinition():
        ctx = def_elem_ctx.stateDefinition()
        return _make_state_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'flowConnectionDefinition') and def_elem_ctx.flowConnectionDefinition():
        ctx = def_elem_ctx.flowConnectionDefinition()
        return _make_flow_connection_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'flowDefinition') and def_elem_ctx.flowDefinition():
        ctx = def_elem_ctx.flowDefinition()
        return _make_flow_connection_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'calculationDefinition') and def_elem_ctx.calculationDefinition():
        ctx = def_elem_ctx.calculationDefinition()
        return _make_calculation_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'interfaceDefinition') and def_elem_ctx.interfaceDefinition():
        ctx = def_elem_ctx.interfaceDefinition()
        return _make_interface_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'connectionDefinition') and def_elem_ctx.connectionDefinition():
        ctx = def_elem_ctx.connectionDefinition()
        return _make_connection_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'constraintDefinition') and def_elem_ctx.constraintDefinition():
        ctx = def_elem_ctx.constraintDefinition()
        return _make_constraint_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'enumerationDefinition') and def_elem_ctx.enumerationDefinition():
        ctx = def_elem_ctx.enumerationDefinition()
        return _make_enumeration_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'allocationDefinition') and def_elem_ctx.allocationDefinition():
        ctx = def_elem_ctx.allocationDefinition()
        return _make_allocation_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'metadataDefinition') and def_elem_ctx.metadataDefinition():
        ctx = def_elem_ctx.metadataDefinition()
        return _make_metadata_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'renderingDefinition') and def_elem_ctx.renderingDefinition():
        ctx = def_elem_ctx.renderingDefinition()
        return _make_rendering_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'individualDefinition') and def_elem_ctx.individualDefinition():
        ctx = def_elem_ctx.individualDefinition()
        return _make_individual_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'viewDefinition') and def_elem_ctx.viewDefinition():
        ctx = def_elem_ctx.viewDefinition()
        return _make_view_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'viewpointDefinition') and def_elem_ctx.viewpointDefinition():
        ctx = def_elem_ctx.viewpointDefinition()
        return _make_viewpoint_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'concernDefinition') and def_elem_ctx.concernDefinition():
        ctx = def_elem_ctx.concernDefinition()
        return _make_concern_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'caseDefinition') and def_elem_ctx.caseDefinition():
        ctx = def_elem_ctx.caseDefinition()
        return _make_case_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'analysisCaseDefinition') and def_elem_ctx.analysisCaseDefinition():
        ctx = def_elem_ctx.analysisCaseDefinition()
        return _make_analysis_case_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'verificationCaseDefinition') and def_elem_ctx.verificationCaseDefinition():
        ctx = def_elem_ctx.verificationCaseDefinition()
        return _make_verification_case_definition_dict(ctx, prefix)
    elif hasattr(def_elem_ctx, 'annotatingElement') and def_elem_ctx.annotatingElement():
        ann_ctx = def_elem_ctx.annotatingElement()
        ann_dict = _visit_annotating_element_dict(ann_ctx)
        if ann_dict is None:
            return None
        return {
            "name": "PackageMember",
            "prefix": prefix,
            "ownedRelatedElement": {
                "name": "DefinitionElement",
                "ownedRelatedElement": ann_dict
            }
        }
    
    return None


def _make_item_definition_dict(ctx, prefix=None):
    """Create an ItemDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    
    # Get body items
    body_items = []
    if hasattr(ctx, 'definition'):
        defn = ctx.definition()
        if defn and hasattr(defn, 'definitionBody'):
            body_ctx = defn.definitionBody()
            if body_ctx:
                body_items = _visit_definition_body_dict(body_ctx)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ItemDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_nested_package_dict(ctx, prefix=None):
    """Create a Package dictionary for a nested package.
    
    Similar to _visit_package_dict but returns a PackageMember wrapped result.
    """
    pkg_name = None
    pkg_shortname = None
    if hasattr(ctx, 'packageDeclaration') and ctx.packageDeclaration():
        decl = ctx.packageDeclaration()
        if hasattr(decl, 'identification'):
            ident = decl.identification()
            if ident and hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        pkg_shortname = name_list[0].getText()
                        pkg_name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        pkg_name, pkg_shortname = _extract_name_shortname(name_text)
    
    # Process body elements
    body_elements = []
    if hasattr(ctx, 'packageBody') and ctx.packageBody():
        body = ctx.packageBody()
        if hasattr(body, 'packageBodyElement'):
            elements = body.packageBodyElement()
            for elem_ctx in elements:
                elem_dict = _visit_package_body_element_dict(elem_ctx)
                if elem_dict:
                    body_elements.append(elem_dict)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "Package",
                "ownedRelationship": [],
                "declaration": {
                    "name": "PackageDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": pkg_shortname,
                        "declaredName": pkg_name
                    }
                },
                "body": {
                    "name": "PackageBody",
                    "ownedRelationship": body_elements
                }
            }
        }
    }


def _make_part_definition_dict(ctx, prefix=None):
    """Create a PartDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    
    # Get body items
    body_items = []
    if hasattr(ctx, 'definition'):
        defn = ctx.definition()
        if defn and hasattr(defn, 'definitionBody'):
            body_ctx = defn.definitionBody()
            if body_ctx:
                body_items = _visit_definition_body_dict(body_ctx)
    
    result = {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "PartDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }
    
    return result


def _make_attribute_definition_dict(ctx, prefix=None):
    """Create an AttributeDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "AttributeDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _make_port_definition_dict(ctx, prefix=None):
    """Create a PortDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    
    # Get body items
    body_items = []
    if hasattr(ctx, 'definition'):
        defn = ctx.definition()
        if defn and hasattr(defn, 'definitionBody'):
            body_ctx = defn.definitionBody()
            if body_ctx:
                body_items = _visit_definition_body_dict(body_ctx)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "PortDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_requirement_definition_dict(ctx, prefix=None):
    """Create a RequirementDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    if not name and not shortname:
        name = "Requirement_" + str(uuid.uuid4())[:8]
    
    # Note: RequirementDefinition uses 'declaration' not 'definition'
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "RequirementDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "RequirementBody",
                    "item": []
                }
            }
        }
    }


def _make_use_case_definition_dict(ctx, prefix=None):
    """Create a UseCaseDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    if not name and not shortname:
        name = "UseCase_" + str(uuid.uuid4())[:8]
    
    # Note: UseCaseDefinition uses 'declaration' not 'definition'
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "UseCaseDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "CaseBody",
                    "item": [],
                    "ownedRelationship": None
                }
            }
        }
    }


def _make_interface_definition_dict(ctx, prefix=None):
    """Create an InterfaceDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    if not name and not shortname:
        name = "Interface_" + str(uuid.uuid4())[:8]
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "InterfaceDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _make_action_definition_dict(ctx, prefix=None):
    """Create an ActionDefinition dictionary.
    
    ActionDefinition uses 'declaration' directly (not wrapped in 'definition').
    """
    # ActionDefinition's identification is at ctx.definitionDeclaration().identification()
    name = None
    shortname = None
    if ctx is not None:
        dd = None
        if hasattr(ctx, 'definitionDeclaration') and ctx.definitionDeclaration():
            dd = ctx.definitionDeclaration()
        
        if dd and hasattr(dd, 'identification') and dd.identification():
            ident = dd.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ActionDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "ActionBody",
                    "items": []
                }
            }
        }
    }


def _make_state_definition_dict(ctx, prefix=None):
    """Create a StateDefinition dictionary.
    
    StateDefinition has the pattern:
    state def Name { body }
    
    Uses 'declaration' directly (DefinitionDeclaration) and 'body' (StateDefBody).
    """
    # StateDefinition's declaration is at ctx.definitionDeclaration()
    name = None
    shortname = None
    if ctx is not None:
        dd = None
        if hasattr(ctx, 'definitionDeclaration') and ctx.definitionDeclaration():
            dd = ctx.definitionDeclaration()
        
        if dd and hasattr(dd, 'identification') and dd.identification():
            ident = dd.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "StateDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "StateDefBody",
                    "part": None,
                    "isParallel": None
                }
            }
        }
    }


def _make_constraint_definition_dict(ctx, prefix=None):
    """Create a ConstraintDefinition dictionary."""
    name = None
    shortname = None
    if ctx is not None:
        dd = None
        if hasattr(ctx, 'definitionDeclaration') and ctx.definitionDeclaration():
            dd = ctx.definitionDeclaration()
        
        if dd and hasattr(dd, 'identification') and dd.identification():
            ident = dd.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ConstraintDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "CalculationBody",
                    "part": []
                }
            }
        }
    }


def _make_calculation_definition_dict(ctx, prefix=None):
    """Create a CalculationDefinition dictionary."""
    name = None
    shortname = None
    if ctx is not None:
        dd = None
        if hasattr(ctx, 'definitionDeclaration') and ctx.definitionDeclaration():
            dd = ctx.definitionDeclaration()
        
        if dd and hasattr(dd, 'identification') and dd.identification():
            ident = dd.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "CalculationDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "CalculationBody",
                    "part": []
                }
            }
        }
    }


def _make_connection_definition_dict(ctx, prefix=None):
    """Create a ConnectionDefinition dictionary.
    
    ConnectionDefinition uses 'definition' wrapper pattern (like part, item, port).
    """
    name, shortname = _get_definition_identification(ctx)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ConnectionDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _make_flow_connection_definition_dict(ctx, prefix=None):
    """Create a FlowConnectionDefinition dictionary.
    
    FlowConnectionDefinition uses 'definition' wrapper pattern.
    """
    name, shortname = _get_definition_identification(ctx)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "FlowConnectionDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _make_state_usage_dict(ctx, prefix=None):
    """Create a StateUsage dictionary.
    
    State usage: state Name ;
    Wrapped: PackageMember -> UsageElement -> OccurrenceUsageElement -> BehaviorUsageElement -> StateUsage
    """
    # StateUsage has actionUsageDeclaration (like ActionUsage does)
    name = None
    shortname = None
    if ctx is not None:
        aud = None
        if hasattr(ctx, 'actionUsageDeclaration') and ctx.actionUsageDeclaration():
            aud = ctx.actionUsageDeclaration()
        
        ud = None
        if aud and hasattr(aud, 'usageDeclaration') and aud.usageDeclaration():
            ud = aud.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "BehaviorUsageElement",
                    "ownedRelationship": {
                        "name": "StateUsage",
                        "prefix": prefix,
                        "declaration": {
                            "name": "ActionUsageDeclaration",
                            "declaration": {
                                "name": "UsageDeclaration",
                                "declaration": {
                                    "name": "FeatureDeclaration",
                                    "identification": {
                                        "name": "Identification",
                                        "declaredShortName": shortname,
                                        "declaredName": name
                                    },
                                    "specialization": None
                                }
                            },
                            "valuepart": None
                        },
                        "body": {
                            "name": "StateUsageBody",
                            "body": {
                                "name": "StateDefBody",
                                "part": None,
                                "isParallel": None
                            }
                        }
                    }
                }
            }
        }
    }


def _make_calculation_usage_dict(ctx, prefix=None):
    """Create a CalculationUsage dictionary.
    
    calc Name ;
    Wrapped: ... -> BehaviorUsageElement -> CalculationUsage
    
    Per grammar, CalculationUsage uses actionUsageDeclaration (not calculationUsageDeclaration).
    """
    name = None
    shortname = None
    if ctx is not None:
        cud = None
        # Try both actionUsageDeclaration and calculationUsageDeclaration
        if hasattr(ctx, 'actionUsageDeclaration') and ctx.actionUsageDeclaration():
            cud = ctx.actionUsageDeclaration()
        elif hasattr(ctx, 'calculationUsageDeclaration') and ctx.calculationUsageDeclaration():
            cud = ctx.calculationUsageDeclaration()
        
        ud = None
        if cud and hasattr(cud, 'usageDeclaration') and cud.usageDeclaration():
            ud = cud.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "BehaviorUsageElement",
                    "ownedRelationship": {
                        "name": "CalculationUsage",
                        "prefix": prefix,
                        "declaration": {
                            "name": "CalculationUsageDeclaration",
                            "declaration": {
                                "name": "UsageDeclaration",
                                "declaration": {
                                    "name": "FeatureDeclaration",
                                    "identification": {
                                        "name": "Identification",
                                        "declaredShortName": shortname,
                                        "declaredName": name
                                    },
                                    "specialization": None
                                }
                            },
                            "valuepart": None
                        },
                        "body": {
                            "name": "CalculationBody",
                            "part": []
                        }
                    }
                }
            }
        }
    }


def _make_constraint_usage_dict(ctx, prefix=None):
    """Create a ConstraintUsage dictionary.
    
    constraint Name ;
    """
    name = None
    shortname = None
    if ctx is not None:
        cud = None
        # Try several possibilities
        if hasattr(ctx, 'constraintUsageDeclaration') and ctx.constraintUsageDeclaration():
            cud = ctx.constraintUsageDeclaration()
        elif hasattr(ctx, 'actionUsageDeclaration') and ctx.actionUsageDeclaration():
            cud = ctx.actionUsageDeclaration()
        elif hasattr(ctx, 'calculationUsageDeclaration') and ctx.calculationUsageDeclaration():
            cud = ctx.calculationUsageDeclaration()
        
        ud = None
        if cud and hasattr(cud, 'usageDeclaration') and cud.usageDeclaration():
            ud = cud.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    # ConstraintUsage is handled as NonOccurrenceUsageElement per grammar class structure
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "NonOccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "ConstraintUsage",
                    "prefix": prefix,
                    "declaration": {
                        "name": "CalculationUsageDeclaration",
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "valuepart": None
                    },
                    "body": {
                        "name": "CalculationBody",
                        "part": []
                    }
                }
            }
        }
    }


def _make_connection_usage_dict(ctx, prefix=None):
    """Create a ConnectionUsage dictionary."""
    name, shortname = _get_usage_identification(ctx)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "StructureUsageElement",
                    "ownedRelatedElement": {
                        "name": "ConnectionUsage",
                        "prefix": prefix,
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "part": None,
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    }


def _make_flow_connection_usage_dict(ctx, prefix=None):
    """Create a FlowConnectionUsage dictionary.
    
    FlowUsage has `flowDeclaration` with `featureDeclaration` (not usageDeclaration).
    """
    name = None
    shortname = None
    if ctx is not None:
        fd = None
        if hasattr(ctx, 'flowDeclaration') and ctx.flowDeclaration():
            fd = ctx.flowDeclaration()
        elif hasattr(ctx, 'flowConnectionDeclaration') and ctx.flowConnectionDeclaration():
            fd = ctx.flowConnectionDeclaration()
        
        # Try to get via featureDeclaration -> featureIdentification (used by flowUsage)
        if fd and hasattr(fd, 'featureDeclaration') and fd.featureDeclaration():
            featd = fd.featureDeclaration()
            if hasattr(featd, 'featureIdentification') and featd.featureIdentification():
                fi = featd.featureIdentification()
                # Get the name from the children
                if hasattr(fi, 'name') and fi.name():
                    name_res = fi.name()
                    # name() may return a list or a single object
                    if isinstance(name_res, list):
                        if len(name_res) == 2:
                            shortname = name_res[0].getText()
                            name = name_res[1].getText()
                        elif len(name_res) == 1:
                            name_text = name_res[0].getText()
                            name, shortname = _extract_name_shortname(name_text)
                    elif name_res:
                        name_text = name_res.getText()
                        name, shortname = _extract_name_shortname(name_text)
                else:
                    # Fall back to text
                    text = fi.getText()
                    if text:
                        name, shortname = _extract_name_shortname(text)
        # Alternative: usageDeclaration (for flowConnectionUsage)
        elif fd and hasattr(fd, 'usageDeclaration') and fd.usageDeclaration():
            ud = fd.usageDeclaration()
            if ud and hasattr(ud, 'identification') and ud.identification():
                ident = ud.identification()
                if hasattr(ident, 'name'):
                    name_list = ident.name()
                    if name_list and isinstance(name_list, list):
                        if len(name_list) == 2:
                            shortname = name_list[0].getText()
                            name = name_list[1].getText()
                        elif len(name_list) == 1:
                            name_text = name_list[0].getText()
                            name, shortname = _extract_name_shortname(name_text)
        
        # If still no name, fall back to _get_usage_identification
        if not name and not shortname:
            name, shortname = _get_usage_identification(ctx)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "StructureUsageElement",
                    "ownedRelatedElement": {
                        "name": "FlowConnectionUsage",
                        "prefix": prefix,
                        "declaration": {
                            "name": "FlowConnectionDeclaration",
                            "declaration": {
                                "name": "UsageDeclaration",
                                "declaration": {
                                    "name": "FeatureDeclaration",
                                    "identification": {
                                        "name": "Identification",
                                        "declaredShortName": shortname,
                                        "declaredName": name
                                    },
                                    "specialization": None
                                }
                            },
                            "valuepart": None,
                            "ownedRelationship_of": None,
                            "ownedRelationship_from": None,
                            "ownedRelationship_to": None
                        },
                        "body": {
                            "name": "DefinitionBody",
                            "ownedRelatedElement": []
                        }
                    }
                }
            }
        }
    }


def _make_view_definition_dict(ctx, prefix=None):
    """Create a ViewDefinition dictionary.
    
    viewDefinition: occurrenceDefinitionPrefix VIEW DEF definitionDeclaration viewDefinitionBody
    """
    name, shortname = _get_definition_identification(ctx)
    # ViewDefinition uses _DeclaredDefinitionBase pattern: prefix + keyword + declaration + body
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ViewDefinition",
                "prefix": None,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "DefinitionBody",
                    "ownedRelatedElement": []
                }
            }
        }
    }


def _make_viewpoint_definition_dict(ctx, prefix=None):
    """Create a ViewpointDefinition dictionary.
    
    viewpointDefinition: occurrenceDefinitionPrefix VIEWPOINT DEF definitionDeclaration requirementBody
    """
    name, shortname = _get_definition_identification(ctx)
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ViewpointDefinition",
                "prefix": None,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "RequirementBody",
                    "ownedRelationship": []
                }
            }
        }
    }


def _make_concern_definition_dict(ctx, prefix=None):
    """Create a ConcernDefinition dictionary.
    
    concernDefinition: occurrenceDefinitionPrefix CONCERN DEF definitionDeclaration requirementBody
    """
    name, shortname = _get_definition_identification(ctx)
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ConcernDefinition",
                "prefix": None,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "RequirementBody",
                    "ownedRelationship": []
                }
            }
        }
    }


def _make_case_definition_dict(ctx, prefix=None):
    """Create a CaseDefinition dictionary.
    
    caseDefinition: occurrenceDefinitionPrefix CASE DEF definitionDeclaration caseBody
    """
    name, shortname = _get_definition_identification(ctx)
    if not name and not shortname:
        name = "Case_" + str(uuid.uuid4())[:8]
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "CaseDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "CaseBody",
                    "item": [],
                    "ownedRelationship": None
                }
            }
        }
    }


def _make_analysis_case_definition_dict(ctx, prefix=None):
    """Create an AnalysisCaseDefinition dictionary.
    
    analysisCaseDefinition: occurrenceDefinitionPrefix ANALYSIS DEF definitionDeclaration caseBody
    """
    name, shortname = _get_definition_identification(ctx)
    if not name and not shortname:
        name = "AnalysisCase_" + str(uuid.uuid4())[:8]
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "AnalysisCaseDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "CaseBody",
                    "item": [],
                    "ownedRelationship": None
                }
            }
        }
    }


def _make_verification_case_definition_dict(ctx, prefix=None):
    """Create a VerificationCaseDefinition dictionary.
    
    verificationCaseDefinition: occurrenceDefinitionPrefix VERIFICATION DEF definitionDeclaration caseBody
    """
    name, shortname = _get_definition_identification(ctx)
    if not name and not shortname:
        name = "VerificationCase_" + str(uuid.uuid4())[:8]
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "VerificationCaseDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "CaseBody",
                    "item": [],
                    "ownedRelationship": None
                }
            }
        }
    }


def _make_view_usage_dict(ctx, prefix=None):
    """Create a ViewUsage dictionary.
    
    viewUsage: occurrenceUsagePrefix VIEW usageDeclaration? valuePart? viewBody
    """
    name, shortname = _get_usage_identification(ctx)
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "StructureUsageElement",
                    "ownedRelatedElement": {
                        "name": "ViewUsage",
                        "prefix": None,
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    }


def _make_viewpoint_usage_dict(ctx, prefix=None):
    """Create a ViewpointUsage dictionary.
    
    viewpointUsage: occurrenceUsagePrefix VIEWPOINT constraintUsageDeclaration requirementBody
    """
    name = None
    shortname = None
    if ctx is not None:
        cud = None
        if hasattr(ctx, 'constraintUsageDeclaration') and ctx.constraintUsageDeclaration():
            cud = ctx.constraintUsageDeclaration()
        
        ud = None
        if cud and hasattr(cud, 'usageDeclaration') and cud.usageDeclaration():
            ud = cud.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "BehaviorUsageElement",
                    "ownedRelationship": {
                        "name": "ViewpointUsage",
                        "prefix": None,
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    }


def _make_concern_usage_dict(ctx, prefix=None):
    """Create a ConcernUsage dictionary.
    
    concernUsage: occurrenceUsagePrefix CONCERN constraintUsageDeclaration requirementBody
    """
    name = None
    shortname = None
    if ctx is not None:
        cud = None
        if hasattr(ctx, 'constraintUsageDeclaration') and ctx.constraintUsageDeclaration():
            cud = ctx.constraintUsageDeclaration()
        
        ud = None
        if cud and hasattr(cud, 'usageDeclaration') and cud.usageDeclaration():
            ud = cud.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "BehaviorUsageElement",
                    "ownedRelationship": {
                        "name": "ConcernUsage",
                        "prefix": None,
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    }


def _make_allocation_usage_dict(ctx, prefix=None):
    """Create an AllocationUsage dictionary.
    
    allocationUsage: occurrenceUsagePrefix allocationUsageDeclaration usageBody
    """
    name = None
    shortname = None
    if ctx is not None:
        aud = None
        if hasattr(ctx, 'allocationUsageDeclaration') and ctx.allocationUsageDeclaration():
            aud = ctx.allocationUsageDeclaration()
        
        ud = None
        if aud and hasattr(aud, 'usageDeclaration') and aud.usageDeclaration():
            ud = aud.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "StructureUsageElement",
                    "ownedRelatedElement": {
                        "name": "AllocationUsage",
                        "prefix": None,
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    }


def _make_rendering_usage_dict(ctx, prefix=None):
    """Create a RenderingUsage dictionary.
    
    renderingUsage: occurrenceUsagePrefix RENDERING usage
    """
    name = None
    shortname = None
    if ctx is not None:
        # RenderingUsage uses just `usage` (not usageDeclaration)
        usage = None
        if hasattr(ctx, 'usage') and ctx.usage():
            usage = ctx.usage()
        
        ud = None
        if usage and hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
            ud = usage.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "StructureUsageElement",
                    "ownedRelatedElement": {
                        "name": "RenderingUsage",
                        "prefix": None,
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    }


def _make_individual_usage_dict(ctx, prefix=None):
    """Create an IndividualUsage dictionary.
    
    individualUsage: basicUsagePrefix INDIVIDUAL usageExtensionKeyword* usage
    """
    name = None
    shortname = None
    if ctx is not None:
        # individualUsage has `usage` at the end
        usage = None
        if hasattr(ctx, 'usage') and ctx.usage():
            usage = ctx.usage()
        
        ud = None
        if usage and hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
            ud = usage.usageDeclaration()
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    # Use IndividualUsageSimple per our simplified model
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "UsageElement",
            "ownedRelatedElement": {
                "name": "OccurrenceUsageElement",
                "ownedRelatedElement": {
                    "name": "StructureUsageElement",
                    "ownedRelatedElement": {
                        "name": "IndividualUsageSimple",
                        "prefix": None,
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    }


def _make_enumeration_definition_dict(ctx, prefix=None):
    """Create an EnumerationDefinition dictionary.
    
    EnumerationDefinition has 'declaration' and 'body' (EnumerationBody).
    """
    name = None
    shortname = None
    if ctx is not None:
        dd = None
        if hasattr(ctx, 'definitionDeclaration') and ctx.definitionDeclaration():
            dd = ctx.definitionDeclaration()
        
        if dd and hasattr(dd, 'identification') and dd.identification():
            ident = dd.identification()
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "EnumerationDefinition",
                "prefix": prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": None
                },
                "body": {
                    "name": "EnumerationBody",
                    "ownedRelationship": []
                }
            }
        }
    }


def _make_allocation_definition_dict(ctx, prefix=None):
    """Create an AllocationDefinition dictionary (uses Definition body)."""
    name, shortname = _get_definition_identification(ctx)
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "AllocationDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _make_metadata_definition_dict(ctx, prefix=None):
    """Create a MetadataDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "MetadataDefinition",
                "isAbstract": False,
                "keyword": [],
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _make_rendering_definition_dict(ctx, prefix=None):
    """Create a RenderingDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "RenderingDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _make_individual_definition_dict(ctx, prefix=None):
    """Create an IndividualDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    return {
        "name": "PackageMember",
        "prefix": None,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "IndividualDefinition",
                "prefix": prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": None
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": []
                    }
                }
            }
        }
    }


def _visit_definition_body_dict(body_ctx):
    """Visit a definition body and return list of body items."""
    if not body_ctx:
        return []
    
    items = []
    
    if hasattr(body_ctx, 'definitionBodyItem'):
        body_items = body_ctx.definitionBodyItem()
        if body_items:
            for item in body_items:
                item_dict = _visit_definition_body_item_dict(item)
                if item_dict:
                    items.append(item_dict)
    
    return items


def _visit_definition_body_item_dict(item_ctx):
    """Visit a definition body item and return a dictionary.
    
    Per grammar:
    definitionBodyItem
        : importRule
        | memberPrefix definitionBodyItemContent
        | ( sourceSuccessionMember)? memberPrefix endOccurrenceUsageElement
        | ( sourceSuccessionMember)? memberPrefix occurrenceUsageElement
        ;
    
    definitionBodyItemContent
        : ALIAS (LT name GT)? (name)? FOR qualifiedName relationshipBody
        | VARIANT variantUsageElement
        | definitionElement
        | nonOccurrenceUsageElement
        ;
    """
    if item_ctx is None:
        return None
    
    inner_element = None
    wrapper = None
    
    # Check for occurrenceUsageElement (part, item, port, action, etc.)
    if hasattr(item_ctx, 'occurrenceUsageElement') and item_ctx.occurrenceUsageElement():
        occ_elem = item_ctx.occurrenceUsageElement()
        inner_element = _visit_nested_occurrence_usage(occ_elem)
        wrapper = "OccurrenceUsageMember"
    
    # Check for definitionBodyItemContent
    if not inner_element and hasattr(item_ctx, 'definitionBodyItemContent') and item_ctx.definitionBodyItemContent():
        content = item_ctx.definitionBodyItemContent()
        # Check nested definition
        if hasattr(content, 'definitionElement') and content.definitionElement():
            def_elem = content.definitionElement()
            inner_element = _visit_nested_definition_element(def_elem)
            wrapper = "DefinitionMember"
        # Check nonOccurrenceUsageElement
        elif hasattr(content, 'nonOccurrenceUsageElement') and content.nonOccurrenceUsageElement():
            non_occ = content.nonOccurrenceUsageElement()
            inner_element = _visit_nested_non_occurrence_usage(non_occ)
            wrapper = "NonOccurrenceUsageMember"
    
    if not inner_element or not wrapper:
        return None
    
    # For OccurrenceUsageMember, the ownedRelatedElement should be a LIST of OccurrenceUsageElement
    if wrapper == "OccurrenceUsageMember":
        # inner_element is currently UsageElement wrapping OccurrenceUsageElement
        # We need to extract just the OccurrenceUsageElement and put it in a list
        if inner_element.get("name") == "UsageElement":
            occ_elem = inner_element.get("ownedRelatedElement", {})
            if occ_elem.get("name") == "OccurrenceUsageElement":
                owned = [occ_elem]
            else:
                owned = [inner_element]
        else:
            owned = [inner_element]
    elif wrapper == "NonOccurrenceUsageMember":
        # NonOccurrenceUsageMember expects ownedRelatedElement to be a list
        if inner_element.get("name") == "NonOccurrenceUsageElement":
            owned = [inner_element]
        else:
            owned = [inner_element]
    else:
        # DefinitionMember - expects ownedRelatedElement to be a list of DefinitionElements
        # inner_element from _visit_nested_definition_element is a PackageMember containing DefinitionElement
        # We need to extract the DefinitionElement
        if inner_element.get("name") == "PackageMember":
            de = inner_element.get("ownedRelatedElement", {})
            if de.get("name") == "DefinitionElement":
                owned = [de]
            else:
                owned = [inner_element]
        elif inner_element.get("name") == "DefinitionElement":
            owned = [inner_element]
        else:
            owned = [inner_element]
    
    return {
        "name": "DefinitionBodyItem",
        "ownedRelationship": [
            {
                "name": wrapper,
                "prefix": None,
                "ownedRelatedElement": owned
            }
        ]
    }


def _visit_nested_occurrence_usage(occ_elem):
    """Visit an occurrence usage element for nested body items."""
    if occ_elem is None:
        return None
    
    # Check structure usage elements (part, item, port)
    if hasattr(occ_elem, 'structureUsageElement') and occ_elem.structureUsageElement():
        struct_elem = occ_elem.structureUsageElement()
        
        if hasattr(struct_elem, 'partUsage') and struct_elem.partUsage():
            ctx = struct_elem.partUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            typed_by = _get_usage_typed_by(ctx)
            return _make_nested_usage_element("PartUsage", name, shortname, None, body_items, typed_by)
        elif hasattr(struct_elem, 'itemUsage') and struct_elem.itemUsage():
            ctx = struct_elem.itemUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            typed_by = _get_usage_typed_by(ctx)
            return _make_nested_usage_element("ItemUsage", name, shortname, None, body_items, typed_by)
        elif hasattr(struct_elem, 'portUsage') and struct_elem.portUsage():
            ctx = struct_elem.portUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            typed_by = _get_usage_typed_by(ctx)
            return _make_nested_usage_element("PortUsage", name, shortname, None, body_items, typed_by)
    
    # Check behavior usage elements (action)
    if hasattr(occ_elem, 'behaviorUsageElement') and occ_elem.behaviorUsageElement():
        behav_elem = occ_elem.behaviorUsageElement()
        if hasattr(behav_elem, 'actionUsage') and behav_elem.actionUsage():
            ctx = behav_elem.actionUsage()
            # Use action usage navigation
            name = None
            shortname = None
            if ctx.actionUsageDeclaration():
                aud = ctx.actionUsageDeclaration()
                if hasattr(aud, 'usageDeclaration') and aud.usageDeclaration():
                    ud = aud.usageDeclaration()
                    if ud and hasattr(ud, 'identification') and ud.identification():
                        ident = ud.identification()
                        if hasattr(ident, 'name'):
                            name_list = ident.name()
                            if name_list and isinstance(name_list, list):
                                if len(name_list) == 2:
                                    shortname = name_list[0].getText()
                                    name = name_list[1].getText()
                                elif len(name_list) == 1:
                                    name_text = name_list[0].getText()
                                    name, shortname = _extract_name_shortname(name_text)
            return {
                "name": "UsageElement",
                "ownedRelatedElement": {
                    "name": "OccurrenceUsageElement",
                    "ownedRelatedElement": {
                        "name": "BehaviorUsageElement",
                        "ownedRelationship": {
                            "name": "ActionUsage",
                            "prefix": None,
                            "declaration": {
                                "name": "ActionUsageDeclaration",
                                "declaration": {
                                    "name": "UsageDeclaration",
                                    "declaration": {
                                        "name": "FeatureDeclaration",
                                        "identification": {
                                            "name": "Identification",
                                            "declaredShortName": shortname,
                                            "declaredName": name
                                        },
                                        "specialization": None
                                    }
                                },
                                "valuepart": None
                            },
                            "body": {
                                "name": "ActionBody",
                                "items": []
                            }
                        }
                    }
                }
            }
    
    return None


def _visit_nested_non_occurrence_usage(non_occ):
    """Visit a non-occurrence usage element for nested body items."""
    if non_occ is None:
        return None
    
    if hasattr(non_occ, 'attributeUsage') and non_occ.attributeUsage():
        ctx = non_occ.attributeUsage()
        name, shortname = _get_usage_identification(ctx)
        typed_by = _get_usage_typed_by(ctx)
        specialization = _build_specialization(typed_by)
        valuepart = _get_usage_value_part(ctx)
        return {
            "name": "NonOccurrenceUsageElement",
            "ownedRelatedElement": {
                "name": "AttributeUsage",
                "prefix": None,
                "usage": {
                    "name": "Usage",
                    "declaration": {
                        "name": "UsageDeclaration",
                        "declaration": {
                            "name": "FeatureDeclaration",
                            "identification": {
                                "name": "Identification",
                                "declaredShortName": shortname,
                                "declaredName": name
                            },
                            "specialization": specialization
                        }
                    },
                    "completion": {
                        "name": "UsageCompletion",
                        "valuepart": valuepart,
                        "body": {
                            "name": "UsageBody",
                            "body": {
                                "name": "DefinitionBody",
                                "ownedRelatedElement": []
                            }
                        }
                    }
                }
            }
        }
    
    # Handle defaultReferenceUsage (directed features like "in Fuel;", "out Fuel;")
    if hasattr(non_occ, 'defaultReferenceUsage') and non_occ.defaultReferenceUsage():
        ctx = non_occ.defaultReferenceUsage()
        return _make_default_reference_usage_dict(ctx)
    
    return None


def _wrap_expression_layers(primary_expression):
    """Wrap a primary expression in all the intermediate expression layers.
    
    The SysML v2 grammar has deep nesting for expressions. This helper builds
    the full chain: OwnedExpression -> ConditionalExpression -> ... -> PrimaryExpression.
    """
    return {
        "name": "OwnedExpression",
        "expression": {
            "name": "ConditionalExpression",
            "operator": [],
            "operand": [
                {
                    "name": "NullCoalescingExpression",
                    "operator": [],
                    "operand": [],
                    "implies": {
                        "name": "ImpliesExpression",
                        "operator": [],
                        "operand": [],
                        "or": {
                            "name": "OrExpression",
                            "operator": [],
                            "operand": [],
                            "xor": {
                                "name": "XorExpression",
                                "operator": [],
                                "operand": [],
                                "and": {
                                    "name": "AndExpression",
                                    "operation": [],
                                    "equality": {
                                        "name": "EqualityExpression",
                                        "operation": [],
                                        "classification": {
                                            "name": "ClassificationExpression",
                                            "operator": None,
                                            "operand": [],
                                            "relational": {
                                                "name": "RelationalExpression",
                                                "operation": [],
                                                "range": {
                                                    "name": "RangeExpression",
                                                    "operand": None,
                                                    "additive": {
                                                        "name": "AdditiveExpression",
                                                        "multiplicitive": {
                                                            "name": "MultiplicativeExpression",
                                                            "operation": [],
                                                            "exponential": {
                                                                "name": "ExponentiationExpression",
                                                                "operator": [],
                                                                "operand": [],
                                                                "unary": {
                                                                    "name": "UnaryExpression",
                                                                    "operator": None,
                                                                    "operand": [],
                                                                    "extent": {
                                                                        "name": "ExtentExpression",
                                                                        "operator": "",
                                                                        "operand": [],
                                                                        "primary": primary_expression
                                                                    }
                                                                }
                                                            }
                                                        },
                                                        "operation": []
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        }
    }


def _make_literal_integer_primary(value):
    """Build a PrimaryExpression containing a LiteralInteger."""
    return {
        "name": "PrimaryExpression",
        "operator": [],
        "operand": [],
        "base": {
            "name": "BaseExpression",
            "ownedRelationship": {
                "name": "LiteralInteger",
                "value": str(value)
            }
        },
        "ownedRelationship1": [],
        "ownedRelationship2": []
    }


def _make_literal_real_primary(value):
    """Build a PrimaryExpression containing a LiteralReal."""
    return {
        "name": "PrimaryExpression",
        "operator": [],
        "operand": [],
        "base": {
            "name": "BaseExpression",
            "ownedRelationship": {
                "name": "LiteralReal",
                "value": str(value)
            }
        },
        "ownedRelationship1": [],
        "ownedRelationship2": []
    }


def _make_literal_string_primary(value):
    """Build a PrimaryExpression containing a LiteralString."""
    return {
        "name": "PrimaryExpression",
        "operator": [],
        "operand": [],
        "base": {
            "name": "BaseExpression",
            "ownedRelationship": {
                "name": "LiteralString",
                "value": value
            }
        },
        "ownedRelationship1": [],
        "ownedRelationship2": []
    }


def _make_feature_reference_primary(qualified_name):
    """Build a PrimaryExpression containing a FeatureReferenceExpression (for unit names, variable refs)."""
    return {
        "name": "PrimaryExpression",
        "operator": [],
        "operand": [],
        "base": {
            "name": "BaseExpression",
            "ownedRelationship": {
                "name": "FeatureReferenceExpression",
                "ownedRelationship": [
                    {
                        "name": "FeatureReferenceMember",
                        "memberElement": {
                            "name": "QualifiedName",
                            "names": [qualified_name]
                        }
                    }
                ]
            }
        },
        "ownedRelationship1": [],
        "ownedRelationship2": []
    }


def _make_primary_with_unit(literal_primary, unit_name):
    """Build a PrimaryExpression with a unit operator (e.g., "100 [kilogram]").
    
    This modifies the literal's primary to include the unit as an operator/operand.
    """
    # The unit is wrapped in SequenceExpression -> OwnedExpression -> ... -> PrimaryExpression
    unit_primary = _make_feature_reference_primary(unit_name)
    unit_expr = _wrap_expression_layers(unit_primary)
    
    sequence_expr = {
        "name": "SequenceExpression",
        "operation": [],
        "ownedRelationship": unit_expr
    }
    
    # Return a new primary that has the literal as base and unit as operand
    literal_primary_with_unit = dict(literal_primary)
    literal_primary_with_unit["operator"] = ["["]
    literal_primary_with_unit["operand"] = [sequence_expr]
    
    return literal_primary_with_unit


def _extract_number_value(text):
    """Try to parse text as an integer or float.
    
    Returns (value, is_integer) tuple. If text isn't numeric, returns (None, False).
    """
    if text is None:
        return None, False
    text = text.strip()
    # Try integer first
    try:
        return int(text), True
    except ValueError:
        pass
    try:
        return float(text), False
    except ValueError:
        pass
    return None, False


def _visit_owned_expression(oe_ctx):
    """Visit an ownedExpression context and return the OwnedExpression dict.
    
    This handles literals (int, real, string) and unit expressions like "100 [kilogram]".
    For complex expressions, it falls back to a best-effort interpretation.
    """
    if oe_ctx is None:
        return None
    
    text = oe_ctx.getText().strip() if hasattr(oe_ctx, 'getText') else ''
    
    # Check for unit expression pattern: "value[unit]"
    if '[' in text and text.endswith(']'):
        # Split at '['
        idx = text.index('[')
        value_part = text[:idx].strip()
        unit_part = text[idx+1:-1].strip()
        
        # Try to get literal primary for value
        value, is_int = _extract_number_value(value_part)
        if value is not None:
            if is_int:
                literal_primary = _make_literal_integer_primary(value)
            else:
                literal_primary = _make_literal_real_primary(value)
            primary_with_unit = _make_primary_with_unit(literal_primary, unit_part)
            return _wrap_expression_layers(primary_with_unit)
    
    # Simple literal
    value, is_int = _extract_number_value(text)
    if value is not None:
        if is_int:
            primary = _make_literal_integer_primary(value)
        else:
            primary = _make_literal_real_primary(value)
        return _wrap_expression_layers(primary)
    
    # String literal
    if text.startswith('"') and text.endswith('"'):
        primary = _make_literal_string_primary(text)
        return _wrap_expression_layers(primary)
    
    # Feature reference (identifier)
    if text and text[0].isalpha():
        primary = _make_feature_reference_primary(text)
        return _wrap_expression_layers(primary)
    
    return None


def _visit_value_part(vp_ctx):
    """Visit a valuePart context and return the ValuePart dict.
    
    valuePart : featureValue ;
    featureValue : (EQ | COLON_EQ | DEFAULT ( EQ | COLON_EQ)?) ownedExpression ;
    """
    if vp_ctx is None:
        return None
    
    if not hasattr(vp_ctx, 'featureValue') or not vp_ctx.featureValue():
        return None
    
    fv = vp_ctx.featureValue()
    
    # Determine the equality flags based on the tokens
    is_default = False
    is_equal = False
    is_initial = False
    
    # Check if DEFAULT token is present
    if hasattr(fv, 'DEFAULT') and fv.DEFAULT():
        is_default = True
    
    # Check if COLON_EQ token is present (initial assignment)
    if hasattr(fv, 'COLON_EQ') and fv.COLON_EQ():
        is_initial = True
    
    # Check EQ token (though default is usually that it's equal if not default/initial)
    if hasattr(fv, 'EQ') and fv.EQ():
        is_equal = True
    
    # If neither default nor initial, reset is_equal to False to match the original pint-based structure
    # (which sets isEqual: false when value is just "= 100")
    if not is_default and not is_initial:
        is_equal = False
    
    # Get the ownedExpression
    oe = None
    if hasattr(fv, 'ownedExpression') and fv.ownedExpression():
        oe = fv.ownedExpression()
    
    owned_expr_dict = _visit_owned_expression(oe)
    if owned_expr_dict is None:
        return None
    
    return {
        "name": "ValuePart",
        "ownedRelationship": [
            {
                "name": "FeatureValue",
                "ownedRelatedElement": owned_expr_dict,
                "isEqual": is_equal,
                "isInitial": is_initial,
                "isDefault": is_default
            }
        ]
    }


def _get_usage_value_part(ctx):
    """Extract the valuePart from a usage context.
    
    Navigates usage().usageCompletion().valuePart().
    """
    if ctx is None:
        return None
    
    usage = None
    if hasattr(ctx, 'usage') and ctx.usage():
        usage = ctx.usage()
    
    if usage and hasattr(usage, 'usageCompletion') and usage.usageCompletion():
        uc = usage.usageCompletion()
        if hasattr(uc, 'valuePart') and uc.valuePart():
            vp_ctx = uc.valuePart()
            return _visit_value_part(vp_ctx)
    
    return None


def _make_default_reference_usage_dict(ctx):
    """Create a DefaultReferenceUsage dictionary (for directed features like 'in Fuel;').
    
    The grammar rule is: defaultReferenceUsage : refPrefix usage ;
    refPrefix can contain featureDirection (in, out, inout).
    """
    # Extract direction from refPrefix
    direction_in = ""
    direction_out = ""
    direction_inout = ""
    is_abstract = False
    is_variation = False
    is_readonly = False
    is_derived = False
    is_end = False
    
    if hasattr(ctx, 'refPrefix') and ctx.refPrefix():
        rp = ctx.refPrefix()
        if hasattr(rp, 'featureDirection') and rp.featureDirection():
            fd = rp.featureDirection()
            direction_text = fd.getText()
            if direction_text == 'in':
                direction_in = "in "
            elif direction_text == 'out':
                direction_out = "out"
            elif direction_text == 'inout':
                direction_inout = "inout"
    
    # Extract name from usage -> usageDeclaration -> identification
    name = None
    shortname = None
    if hasattr(ctx, 'usage') and ctx.usage():
        usage = ctx.usage()
        if hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
            ud = usage.usageDeclaration()
            if hasattr(ud, 'identification') and ud.identification():
                ident = ud.identification()
                if hasattr(ident, 'name'):
                    name_list = ident.name()
                    if name_list and isinstance(name_list, list):
                        if len(name_list) == 2:
                            shortname = name_list[0].getText()
                            name = name_list[1].getText()
                        elif len(name_list) == 1:
                            name_text = name_list[0].getText()
                            name, shortname = _extract_name_shortname(name_text)
    
    return {
        "name": "NonOccurrenceUsageElement",
        "ownedRelatedElement": {
            "name": "DefaultReferenceUsage",
            "prefix": {
                "name": "RefPrefix",
                "isAbstract": is_abstract,
                "isVariation": is_variation,
                "isReadOnly": is_readonly,
                "isDerived": is_derived,
                "isEnd": is_end,
                "direction": {
                    "name": "FeatureDirection",
                    "in": direction_in,
                    "out": direction_out,
                    "inout": direction_inout
                }
            },
            "valuepart": None,
            "declaration": {
                "name": "UsageDeclaration",
                "declaration": {
                    "name": "FeatureDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "specialization": None
                }
            },
            "body": {
                "name": "UsageBody",
                "body": {
                    "name": "DefinitionBody",
                    "ownedRelatedElement": []
                }
            }
        }
    }


def _visit_nested_definition_element(def_elem):
    """Visit a nested definition element for body items."""
    if def_elem is None:
        return None
    
    # Handle various definition types
    if hasattr(def_elem, 'itemDefinition') and def_elem.itemDefinition():
        return _make_item_definition_dict(def_elem.itemDefinition(), None)
    elif hasattr(def_elem, 'partDefinition') and def_elem.partDefinition():
        return _make_part_definition_dict(def_elem.partDefinition(), None)
    elif hasattr(def_elem, 'attributeDefinition') and def_elem.attributeDefinition():
        return _make_attribute_definition_dict(def_elem.attributeDefinition(), None)
    elif hasattr(def_elem, 'portDefinition') and def_elem.portDefinition():
        return _make_port_definition_dict(def_elem.portDefinition(), None)
    elif hasattr(def_elem, 'annotatingElement') and def_elem.annotatingElement():
        ann_ctx = def_elem.annotatingElement()
        ann_dict = _visit_annotating_element_dict(ann_ctx)
        if ann_dict is None:
            return None
        return {
            "name": "PackageMember",
            "prefix": None,
            "ownedRelatedElement": {
                "name": "DefinitionElement",
                "ownedRelatedElement": ann_dict
            }
        }
    
    return None


def _make_nested_usage_element(usage_type, name, shortname, prefix, body_items=None, typed_by=None):
    """Build a nested usage element (not wrapped in PackageMember)."""
    if body_items is None:
        body_items = []
    
    specialization = _build_specialization(typed_by)
    
    return {
        "name": "UsageElement",
        "ownedRelatedElement": {
            "name": "OccurrenceUsageElement",
            "ownedRelatedElement": {
                "name": "StructureUsageElement",
                "ownedRelatedElement": {
                    "name": usage_type,
                    "prefix": prefix,
                    "usage": {
                        "name": "Usage",
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": shortname,
                                    "declaredName": name
                                },
                                "specialization": specialization
                            }
                        },
                        "completion": {
                            "name": "UsageCompletion",
                            "valuepart": None,
                            "body": {
                                "name": "UsageBody",
                                "body": {
                                    "name": "DefinitionBody",
                                    "ownedRelatedElement": body_items
                                }
                            }
                        }
                    }
                }
            }
        }
    }


def _visit_nested_definition(def_elem_ctx):
    """Visit a nested definition within a body."""
    if hasattr(def_elem_ctx, 'partDefinition') and def_elem_ctx.partDefinition():
        ctx = def_elem_ctx.partDefinition()
        return _make_part_definition_dict(ctx)
    elif hasattr(def_elem_ctx, 'attributeDefinition') and def_elem_ctx.attributeDefinition():
        ctx = def_elem_ctx.attributeDefinition()
        return _make_attribute_definition_dict(ctx)
    elif hasattr(def_elem_ctx, 'portDefinition') and def_elem_ctx.portDefinition():
        ctx = def_elem_ctx.portDefinition()
        return _make_port_definition_dict(ctx)
    # Add more types as needed
    
    return None


def _visit_nested_usage(usage_elem_ctx):
    """Visit a nested usage within a body."""
    # Check for occurrence usage (part, item, port)
    if hasattr(usage_elem_ctx, 'occurrenceUsageElement') and usage_elem_ctx.occurrenceUsageElement():
        occ_elem = usage_elem_ctx.occurrenceUsageElement()
        
        # Check structure usage elements
        if hasattr(occ_elem, 'structureUsageElement') and occ_elem.structureUsageElement():
            struct_elem = occ_elem.structureUsageElement()
            
            if hasattr(struct_elem, 'partUsage') and struct_elem.partUsage():
                ctx = struct_elem.partUsage()
                name = None
                if hasattr(ctx, 'identifier'):
                    ids = ctx.identifier()
                    if isinstance(ids, list) and ids:
                        name = ids[0].getText()
                return {
                    "name": "UsageElement",
                    "ownedRelatedElement": {
                        "name": "PartUsage",
                        "prefix": None,
                        "usage": {
                            "name": "Usage",
                            "declaration": {
                                "name": "UsageDeclaration",
                                "declaration": {
                                    "name": "FeatureDeclaration",
                                    "identification": {
                                        "name": "Identification",
                                        "declaredShortName": None,
                                        "declaredName": name
                                    },
                                    "specialization": None
                                }
                            },
                            "completion": {
                                "name": "UsageCompletion",
                                "valuepart": None,
                                "body": {
                                    "name": "UsageBody",
                                    "body": {
                                        "name": "DefinitionBody",
                                        "ownedRelatedElement": []
                                    }
                                }
                            }
                        }
                    }
                }
            elif hasattr(struct_elem, 'itemUsage') and struct_elem.itemUsage():
                ctx = struct_elem.itemUsage()
                name = None
                shortname = None
                # Get name from usage().usageDeclaration().identification()
                if hasattr(ctx, 'usage') and ctx.usage():
                    usage = ctx.usage()
                    if usage and hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
                        ud = usage.usageDeclaration()
                        if ud and hasattr(ud, 'identification') and ud.identification():
                            ident = ud.identification()
                            if hasattr(ident, 'name') and ident.name():
                                name_list = ident.name()
                                if name_list and isinstance(name_list, list):
                                    name_text = name_list[0].getText()
                                    # Check if it's a short name (quoted)
                                    if name_text.startswith("'") or name_text.startswith('"'):
                                        shortname = name_text
                                    else:
                                        name = name_text
                return {
                    "name": "UsageElement",
                    "ownedRelatedElement": {
                        "name": "ItemUsage",
                        "prefix": None,
                        "usage": {
                            "name": "Usage",
                            "declaration": {
                                "name": "UsageDeclaration",
                                "declaration": {
                                    "name": "FeatureDeclaration",
                                    "identification": {
                                        "name": "Identification",
                                        "declaredShortName": shortname,
                                        "declaredName": name
                                    },
                                    "specialization": None
                                }
                            },
                            "completion": {
                                "name": "UsageCompletion",
                                "valuepart": None,
                                "body": {
                                    "name": "UsageBody",
                                    "body": {
                                        "name": "DefinitionBody",
                                        "ownedRelatedElement": []
                                    }
                                }
                            }
                        }
                    }
                }
            elif hasattr(struct_elem, 'portUsage') and struct_elem.portUsage():
                ctx = struct_elem.portUsage()
                name = None
                if hasattr(ctx, 'identifier'):
                    ids = ctx.identifier()
                    if isinstance(ids, list) and ids:
                        name = ids[0].getText()
                return {
                    "name": "UsageElement",
                    "ownedRelatedElement": {
                        "name": "PortUsage",
                        "prefix": None,
                        "usage": {
                            "name": "Usage",
                            "declaration": {
                                "name": "UsageDeclaration",
                                "declaration": {
                                    "name": "FeatureDeclaration",
                                    "identification": {
                                        "name": "Identification",
                                        "declaredShortName": None,
                                        "declaredName": name
                                    },
                                    "specialization": None
                                }
                            },
                            "completion": {
                                "name": "UsageCompletion",
                                "valuepart": None,
                                "body": {
                                    "name": "UsageBody",
                                    "body": {
                                        "name": "DefinitionBody",
                                        "ownedRelatedElement": []
                                    }
                                }
                            }
                        }
                    }
                }
        
        # Check behavior usage elements (action)
        if hasattr(occ_elem, 'behaviorUsageElement') and occ_elem.behaviorUsageElement():
            behav_elem = occ_elem.behaviorUsageElement()
            
            if hasattr(behav_elem, 'actionUsage') and behav_elem.actionUsage():
                ctx = behav_elem.actionUsage()
                name = None
                if ctx.actionUsageDeclaration():
                    aud = ctx.actionUsageDeclaration()
                    if hasattr(aud, 'usageDeclaration') and aud.usageDeclaration():
                        ud = aud.usageDeclaration()
                        if hasattr(ud, 'getText'):
                            text = ud.getText().strip()
                            if text and text != 'ACTION':
                                name = text
                return {
                    "name": "UsageElement",
                    "ownedRelatedElement": {
                        "name": "OccurrenceUsageElement",
                        "ownedRelatedElement": {
                            "name": "BehaviorUsageElement",
                            "ownedRelationship": {
                                "name": "ActionUsage",
                                "prefix": None,
                                "declaration": {
                                    "name": "ActionUsageDeclaration",
                                    "declaration": {
                                        "name": "UsageDeclaration",
                                        "declaration": {
                                            "name": "FeatureDeclaration",
                                            "identification": {
                                                "name": "Identification",
                                                "declaredShortName": None,
                                                "declaredName": name
                                            },
                                            "specialization": None
                                        }
                                    },
                                    "valuepart": None
                                },
                                "body": {
                                    "name": "ActionBody",
                                    "items": []
                                }
                            }
                        }
                    }
                }
    
    # Check for non-occurrence usage (attribute, calculation)
    if hasattr(usage_elem_ctx, 'nonOccurrenceUsageElement') and usage_elem_ctx.nonOccurrenceUsageElement():
        non_occ = usage_elem_ctx.nonOccurrenceUsageElement()
        
        if hasattr(non_occ, 'attributeUsage') and non_occ.attributeUsage():
            ctx = non_occ.attributeUsage()
            name = None
            if hasattr(ctx, 'identifier'):
                ids = ctx.identifier()
                if isinstance(ids, list) and ids:
                    name = ids[0].getText()
            return {
                "name": "UsageElement",
                "ownedRelatedElement": {
                    "name": "AttributeUsage",
                    "prefix": None,
                    "usage": {
                        "name": "Usage",
                        "declaration": {
                            "name": "UsageDeclaration",
                            "declaration": {
                                "name": "FeatureDeclaration",
                                "identification": {
                                    "name": "Identification",
                                    "declaredShortName": None,
                                    "declaredName": name
                                },
                                "specialization": None
                            }
                        },
                        "completion": {
                            "name": "UsageCompletion",
                            "valuepart": None,
                            "body": {
                                "name": "UsageBody",
                                "body": {
                                    "name": "DefinitionBody",
                                    "ownedRelatedElement": []
                                }
                            }
                        }
                    }
                }
            }
    
    return None


def _visit_usage_element_dict(usage_elem_ctx, prefix=None):
    """Visit a usage element context and return a dictionary."""
    # The usage element can be either:
    # 1. NonOccurrenceUsageElement (attribute, calculation, etc.)
    # 2. OccurrenceUsageElement -> StructureUsageElement or BehaviorUsageElement
    
    # First check for occurrence usage (part, item, port)
    if hasattr(usage_elem_ctx, 'occurrenceUsageElement') and usage_elem_ctx.occurrenceUsageElement():
        occ_elem = usage_elem_ctx.occurrenceUsageElement()
        
        # Check structure usage elements (part, item, port)
        if hasattr(occ_elem, 'structureUsageElement') and occ_elem.structureUsageElement():
            struct_elem = occ_elem.structureUsageElement()
            
            if hasattr(struct_elem, 'partUsage') and struct_elem.partUsage():
                ctx = struct_elem.partUsage()
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                typed_by = _get_usage_typed_by(ctx)
                return _make_usage_dict("PartUsage", name, shortname, prefix, structure=True, wrapped=True, body_items=body_items, typed_by=typed_by)
            elif hasattr(struct_elem, 'itemUsage') and struct_elem.itemUsage():
                ctx = struct_elem.itemUsage()
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                typed_by = _get_usage_typed_by(ctx)
                return _make_usage_dict("ItemUsage", name, shortname, prefix, structure=True, wrapped=True, body_items=body_items, typed_by=typed_by)
            elif hasattr(struct_elem, 'portUsage') and struct_elem.portUsage():
                ctx = struct_elem.portUsage()
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                typed_by = _get_usage_typed_by(ctx)
                return _make_usage_dict("PortUsage", name, shortname, prefix, structure=True, wrapped=True, body_items=body_items, typed_by=typed_by)
            elif hasattr(struct_elem, 'connectionUsage') and struct_elem.connectionUsage():
                ctx = struct_elem.connectionUsage()
                return _make_connection_usage_dict(ctx, prefix)
            elif hasattr(struct_elem, 'flowConnectionUsage') and struct_elem.flowConnectionUsage():
                ctx = struct_elem.flowConnectionUsage()
                return _make_flow_connection_usage_dict(ctx, prefix)
            elif hasattr(struct_elem, 'flowUsage') and struct_elem.flowUsage():
                ctx = struct_elem.flowUsage()
                return _make_flow_connection_usage_dict(ctx, prefix)
            elif hasattr(struct_elem, 'allocationUsage') and struct_elem.allocationUsage():
                ctx = struct_elem.allocationUsage()
                return _make_allocation_usage_dict(ctx, prefix)
            elif hasattr(struct_elem, 'renderingUsage') and struct_elem.renderingUsage():
                ctx = struct_elem.renderingUsage()
                return _make_rendering_usage_dict(ctx, prefix)
            elif hasattr(struct_elem, 'individualUsage') and struct_elem.individualUsage():
                ctx = struct_elem.individualUsage()
                return _make_individual_usage_dict(ctx, prefix)
            elif hasattr(struct_elem, 'viewUsage') and struct_elem.viewUsage():
                ctx = struct_elem.viewUsage()
                return _make_view_usage_dict(ctx, prefix)
        
        # Check behavior usage elements (action, state, etc.)
        if hasattr(occ_elem, 'behaviorUsageElement') and occ_elem.behaviorUsageElement():
            behav_elem = occ_elem.behaviorUsageElement()
            
            if hasattr(behav_elem, 'stateUsage') and behav_elem.stateUsage():
                ctx = behav_elem.stateUsage()
                return _make_state_usage_dict(ctx, prefix)
            elif hasattr(behav_elem, 'calculationUsage') and behav_elem.calculationUsage():
                ctx = behav_elem.calculationUsage()
                return _make_calculation_usage_dict(ctx, prefix)
            elif hasattr(behav_elem, 'constraintUsage') and behav_elem.constraintUsage():
                ctx = behav_elem.constraintUsage()
                return _make_constraint_usage_dict(ctx, prefix)
            elif hasattr(behav_elem, 'viewpointUsage') and behav_elem.viewpointUsage():
                ctx = behav_elem.viewpointUsage()
                return _make_viewpoint_usage_dict(ctx, prefix)
            elif hasattr(behav_elem, 'concernUsage') and behav_elem.concernUsage():
                ctx = behav_elem.concernUsage()
                return _make_concern_usage_dict(ctx, prefix)
            elif hasattr(behav_elem, 'actionUsage') and behav_elem.actionUsage():
                ctx = behav_elem.actionUsage()
                name = None
                shortname = None
                # Get name from actionUsageDeclaration -> usageDeclaration -> identification
                if ctx.actionUsageDeclaration():
                    aud = ctx.actionUsageDeclaration()
                    if hasattr(aud, 'usageDeclaration') and aud.usageDeclaration():
                        ud = aud.usageDeclaration()
                        if ud and hasattr(ud, 'identification') and ud.identification():
                            ident = ud.identification()
                            if hasattr(ident, 'name'):
                                name_list = ident.name()
                                if name_list and isinstance(name_list, list):
                                    if len(name_list) == 2:
                                        shortname = name_list[0].getText()
                                        name = name_list[1].getText()
                                    elif len(name_list) == 1:
                                        name_text = name_list[0].getText()
                                        name, shortname = _extract_name_shortname(name_text)
                        # If no identification, fall back to text extraction
                        elif hasattr(ud, 'getText'):
                            text = ud.getText().strip()
                            if text and text != 'ACTION':
                                name = text
                return {
                    "name": "PackageMember",
                    "prefix": None,
                    "ownedRelatedElement": {
                        "name": "UsageElement",
                        "ownedRelatedElement": {
                            "name": "OccurrenceUsageElement",
                            "ownedRelatedElement": {
                                "name": "BehaviorUsageElement",
                                "ownedRelationship": {
                                    "name": "ActionUsage",
                                    "prefix": prefix,
                                    "declaration": {
                                        "name": "ActionUsageDeclaration",
                                        "declaration": {
                                            "name": "UsageDeclaration",
                                            "declaration": {
                                                "name": "FeatureDeclaration",
                                                "identification": {
                                                    "name": "Identification",
                                                    "declaredShortName": shortname,
                                                    "declaredName": name
                                                },
                                                "specialization": None
                                            }
                                        },
                                        "valuepart": None
                                    },
                                    "body": {
                                        "name": "ActionBody",
                                        "items": []
                                    }
                                }
                            }
                        }
                    }
                }
    
    # Fall back to checking non-occurrence usage types
    if hasattr(usage_elem_ctx, 'nonOccurrenceUsageElement') and usage_elem_ctx.nonOccurrenceUsageElement():
        non_occ = usage_elem_ctx.nonOccurrenceUsageElement()
        
        if hasattr(non_occ, 'attributeUsage') and non_occ.attributeUsage():
            ctx = non_occ.attributeUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            typed_by = _get_usage_typed_by(ctx)
            specialization = _build_specialization(typed_by)
            valuepart = _get_usage_value_part(ctx)
            return {
                "name": "PackageMember",
                "prefix": None,
                "ownedRelatedElement": {
                    "name": "UsageElement",
                    "ownedRelatedElement": {
                        "name": "NonOccurrenceUsageElement",
                        "ownedRelatedElement": {
                            "name": "AttributeUsage",
                            "prefix": prefix,
                            "usage": {
                                "name": "Usage",
                                "declaration": {
                                    "name": "UsageDeclaration",
                                    "declaration": {
                                        "name": "FeatureDeclaration",
                                        "identification": {
                                            "name": "Identification",
                                            "declaredShortName": shortname,
                                            "declaredName": name
                                        },
                                        "specialization": specialization
                                    }
                                },
                                "completion": {
                                    "name": "UsageCompletion",
                                    "valuepart": valuepart,
                                    "body": {
                                        "name": "UsageBody",
                                        "body": {
                                            "name": "DefinitionBody",
                                            "ownedRelatedElement": body_items
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
    
    return None


def _make_usage_dict(usage_type, name, shortname, prefix, structure=True, wrapped=True, body_items=None, typed_by=None):
    """Build a usage dictionary for PartUsage/ItemUsage/PortUsage.
    
    Parameters
    ----------
    usage_type : str
        'PartUsage', 'ItemUsage', or 'PortUsage'
    name : str or None
        The long name
    shortname : str or None
        The short name
    prefix : str or None
        Prefix (redefines, conjugated, etc.)
    structure : bool
        True for StructureUsageElement wrapping
    wrapped : bool
        True if this should be wrapped in PackageMember (top-level),
        False for nested usages
    body_items : list
        List of nested body items
    typed_by : str
        Name of the type this usage is typed by (e.g., "Fuel" in "item Hydrogen : Fuel")
    
    Returns
    -------
    dict
        The usage dictionary
    """
    if body_items is None:
        body_items = []
    
    # Build specialization if typed_by is present
    specialization = _build_specialization(typed_by)
    
    inner_usage = {
        "name": usage_type,
        "prefix": prefix,
        "usage": {
            "name": "Usage",
            "declaration": {
                "name": "UsageDeclaration",
                "declaration": {
                    "name": "FeatureDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "specialization": specialization
                }
            },
            "completion": {
                "name": "UsageCompletion",
                "valuepart": None,
                "body": {
                    "name": "UsageBody",
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }
    
    if wrapped:
        return {
            "name": "PackageMember",
            "prefix": None,
            "ownedRelatedElement": {
                "name": "UsageElement",
                "ownedRelatedElement": {
                    "name": "OccurrenceUsageElement",
                    "ownedRelatedElement": {
                        "name": "StructureUsageElement",
                        "ownedRelatedElement": inner_usage
                    }
                }
            }
        }
    else:
        return {
            "name": "UsageElement",
            "ownedRelatedElement": inner_usage
        }


def _build_specialization(typed_by):
    """Build the specialization dictionary structure for a typed-by reference."""
    if not typed_by:
        return None
    
    return {
        "name": "FeatureSpecializationPart",
        "specialization": [
            {
                "name": "FeatureSpecialization",
                "ownedRelationship": {
                    "name": "Typings",
                    "typedby": {
                        "name": "TypedBy",
                        "ownedRelationship": [
                            {
                                "name": "FeatureTyping",
                                "ownedRelationship": {
                                    "name": "OwnedFeatureTyping",
                                    "type": {
                                        "name": "FeatureType",
                                        "type": {
                                            "name": "QualifiedName",
                                            "names": [typed_by]
                                        },
                                        "ownedRelatedElement": []
                                    }
                                }
                            }
                        ]
                    },
                    "ownedRelationship": []
                }
            }
        ],
        "multiplicity": None,
        "specialization2": [],
        "multiplicity2": None,
    }


def _get_usage_body_items(ctx):
    """Extract body items from a usage context via usage().usageCompletion().usageBody().definitionBody().
    
    Returns a list of body items or empty list.
    """
    body_items = []
    if ctx is None:
        return body_items
    
    # Get usage -> usageCompletion -> usageBody -> definitionBody
    usage = None
    if hasattr(ctx, 'usage') and ctx.usage():
        usage = ctx.usage()
    
    if usage and hasattr(usage, 'usageCompletion') and usage.usageCompletion():
        uc = usage.usageCompletion()
        if hasattr(uc, 'usageBody') and uc.usageBody():
            ub = uc.usageBody()
            if hasattr(ub, 'definitionBody') and ub.definitionBody():
                db = ub.definitionBody()
                body_items = _visit_definition_body_dict(db)
    
    return body_items


def _get_usage_typed_by(ctx):
    """Extract the typed-by reference from a usage context.
    
    Returns the qualified name of the type, or None.
    """
    if ctx is None:
        return None
    
    # Get usage -> usageDeclaration -> featureSpecializationPart
    usage = None
    if hasattr(ctx, 'usage') and ctx.usage():
        usage = ctx.usage()
    
    ud = None
    if usage and hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
        ud = usage.usageDeclaration()
    
    if ud and hasattr(ud, 'featureSpecializationPart') and ud.featureSpecializationPart():
        fsp = ud.featureSpecializationPart()
        # Get the typing
        if hasattr(fsp, 'featureSpecialization') and fsp.featureSpecialization():
            specs = fsp.featureSpecialization()
            if not isinstance(specs, list):
                specs = [specs]
            for spec in specs:
                if hasattr(spec, 'typings') and spec.typings():
                    typings = spec.typings()
                    if hasattr(typings, 'getText'):
                        text = typings.getText()
                        if text.startswith(':'):
                            text = text[1:].strip()
                        return text
        # Try direct feature specialization access
        if hasattr(fsp, 'getText'):
            text = fsp.getText()
            # Remove leading ':' or ':>' etc
            if text.startswith(':'):
                text = text[1:].strip()
            return text
    
    return None


__all__ = ['parse_to_dict']