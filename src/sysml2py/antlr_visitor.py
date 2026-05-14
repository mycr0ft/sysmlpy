#!/usr/bin/env python3
"""
ANTLR4 to dictionary converter for SysML v2.0.

This module converts the ANTLR4 parse tree to a dictionary format
for use with the sysml2py class hierarchy.
"""
import uuid


def _extract_name_shortname(name_text):
    """Given a name text, return (name, shortname) tuple.
    
    This function is only called for single-name identifications without
    angle brackets. In that case the name is always a declaredName.
    Short names require explicit < > in source, handled at call sites.
    """
    return name_text, None


def _get_usage_identification(ctx):
    """Extract (name, shortname) from a usage context by navigating to usageDeclaration().identification().
    
    The ctx can be either a usage context (with usageDeclaration) or an occurrence usage element context (with usage() method).
    Returns (name, shortname) tuple.
    """
    name = None
    shortname = None
    if ctx is None:
        return name, shortname
    
    # Try to get usageDeclaration directly from ctx (if ctx is a usage context)
    usage_decl = None
    if hasattr(ctx, 'usageDeclaration') and ctx.usageDeclaration():
        usage_decl = ctx.usageDeclaration()
    else:
        # Try to get usage -> usageDeclaration
        usage = None
        if hasattr(ctx, 'usage') and ctx.usage():
            usage = ctx.usage()
            if usage and hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
                usage_decl = usage.usageDeclaration()
    
    if usage_decl and hasattr(usage_decl, 'identification') and usage_decl.identification():
        ident = usage_decl.identification()
        if hasattr(ident, 'name'):
            name_list = ident.name()
            if name_list and isinstance(name_list, list):
                if len(name_list) == 2:
                    # LT name GT name: first is short name, second is long name
                    shortname = name_list[0].getText()
                    name = name_list[1].getText()
                elif len(name_list) == 1:
                    name_text = name_list[0].getText()
                    if hasattr(ident, 'LT') and ident.LT() is not None:
                        shortname = name_text
                    else:
                        name = name_text
    
    return name, shortname


def _get_subclassification_part(ctx):
    """Extract SubclassificationPart dict from a definition context.
    
    Handles 'part def Foo :> Bar, Baz' — returns the :> clause as a dict,
    or None if there is no subclassification.
    """
    defn = None
    if hasattr(ctx, 'definition') and ctx.definition():
        defn = ctx.definition()
    if defn is None:
        return None
    
    dd = None
    if hasattr(defn, 'definitionDeclaration') and defn.definitionDeclaration():
        dd = defn.definitionDeclaration()
    elif hasattr(ctx, 'definitionDeclaration') and ctx.definitionDeclaration():
        dd = ctx.definitionDeclaration()
    if dd is None:
        return None
    
    if not (hasattr(dd, 'subclassificationPart') and dd.subclassificationPart()):
        return None
    
    sc = dd.subclassificationPart()
    owned = []
    if hasattr(sc, 'ownedSubclassification'):
        for osc in sc.ownedSubclassification():
            if hasattr(osc, 'qualifiedName') and osc.qualifiedName():
                qn_text = osc.qualifiedName().getText()
                qn_names = qn_text.split("::")
                owned.append({
                    "name": "OwnedSubclassification",
                    "superclassifier": {"name": "QualifiedName", "names": qn_names}
                })
    
    if not owned:
        return None
    
    return {
        "name": "SubclassificationPart",
        "ownedRelationship": owned
    }


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
                    name_text = name_list[0].getText()
                    if hasattr(ident, 'LT') and ident.LT() is not None:
                        shortname = name_text
                    else:
                        name = name_text
    
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
                # LT name GT name: first is short name, second is long name
                shortname = name_list[0].getText()
                name = name_list[1].getText()
            elif len(name_list) == 1:
                name_text = name_list[0].getText()
                # Check for explicit angle brackets: <name> → shortname only
                has_lt = hasattr(ident_ctx, 'LT') and ident_ctx.LT() is not None
                if has_lt:
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
                            name_text = name_list[0].getText()
                            # Check for explicit < > angle brackets
                            if hasattr(ident, 'LT') and ident.LT() is not None:
                                pkg_shortname = name_text
                            else:
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

    # Extract visibility from memberPrefix
    prefix = None
    if hasattr(alias_ctx, 'memberPrefix') and alias_ctx.memberPrefix():
        mp = alias_ctx.memberPrefix()
        if hasattr(mp, 'visibilityIndicator') and mp.visibilityIndicator():
            prefix = {
                "name": "MemberPrefix",
                "visibility": _visit_visibility_indicator_dict(mp.visibilityIndicator())
            }

    # Extract body annotations (e.g. block comments inside alias body)
    body_owned = []
    if hasattr(alias_ctx, 'relationshipBody') and alias_ctx.relationshipBody():
        rb = alias_ctx.relationshipBody()
        for child in rb.children:
            if type(child).__name__ == 'RelationshipOwnedElementContext':
                for c2 in child.children:
                    if type(c2).__name__ == 'OwnedAnnotationContext':
                        for c3 in c2.children:
                            if type(c3).__name__ == 'AnnotatingElementContext':
                                comment_text = c3.getText()
                                body_owned.append({
                                    "name": "OwnedAnnotation",
                                    "ownedRelatedElement": [
                                        {
                                            "name": "AnnotatingElement",
                                            "ownedRelatedElement": {
                                                "name": "CommentSysML",
                                                "body": comment_text,
                                                "identification": None,
                                                "ownedRelationship": []
                                            }
                                        }
                                    ]
                                })

    return {
        "name": "AliasMember",
        "prefix": prefix,
        "body": {"name": "RelationshipBody", "ownedRelationship": body_owned},
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
    
    # Get prefix if present (memberPrefix = (visibilityIndicator)?)
    prefix = None
    if hasattr(member, 'memberPrefix'):
        mp = member.memberPrefix()
        if mp and hasattr(mp, 'visibilityIndicator') and mp.visibilityIndicator():
            prefix = {
                "name": "MemberPrefix",
                "visibility": _visit_visibility_indicator_dict(mp.visibilityIndicator())
            }
    
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


def _make_item_definition_dict(ctx, member_prefix=None):
    """Create an ItemDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    
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
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ItemDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
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
                        # Explicit angle brackets <name> → shortname; bare name → declaredName
                        if hasattr(ident, 'LT') and ident.LT() is not None:
                            pkg_shortname = name_text
                        else:
                            pkg_name = name_text
    
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


def _get_occurrence_usage_prefix(ctx):
    """Extract OccurrenceUsagePrefix from a usage context (for 'ref', direction, etc.)."""
    is_reference = False
    direction_in = ""
    direction_out = ""
    direction_inout = ""
    is_end = False
    
    if hasattr(ctx, 'occurrenceUsagePrefix') and ctx.occurrenceUsagePrefix():
        oup = ctx.occurrenceUsagePrefix()
        if hasattr(oup, 'basicUsagePrefix') and oup.basicUsagePrefix():
            bup = oup.basicUsagePrefix()
            is_reference = hasattr(bup, 'REF') and bup.REF() is not None
            # Extract direction and end from refPrefix
            if hasattr(bup, 'refPrefix') and bup.refPrefix():
                rp = bup.refPrefix()
                if hasattr(rp, 'featureDirection') and rp.featureDirection():
                    fd = rp.featureDirection()
                    direction_in = "in " if fd.IN() is not None else ""
                    direction_out = "out" if fd.OUT() is not None else ""
                    direction_inout = "inout" if fd.INOUT() is not None else ""
                # Check for END keyword
                if hasattr(rp, 'END') and rp.END() is not None:
                    is_end = True
    
    has_direction = any([direction_in, direction_out, direction_inout])
    
    if not is_reference and not has_direction and not is_end:
        return None
    
    ref_prefix = None
    if has_direction or is_end:
        ref_prefix = {
            "name": "RefPrefix",
            "direction": {
                "name": "FeatureDirection",
                "in": direction_in,
                "out": direction_out,
                "inout": direction_inout
            },
            "isAbstract": None,
            "isVariation": None,
            "isReadOnly": None,
            "isDerived": None,
            "isEnd": "end" if is_end else None
        }
    
    return {
        "name": "OccurrenceUsagePrefix",
        "prefix": {
            "name": "BasicUsagePrefix",
            "prefix": ref_prefix,
            "isReference": is_reference
        },
        "isIndividual": None,
        "portionKind": None,
        "usageExtension": []
    }


def _get_occurrence_definition_prefix(ctx):
    """Extract OccurrenceDefinitionPrefix from a definition context (for 'abstract' etc.)."""
    is_abstract = False
    is_variation = False
    
    if hasattr(ctx, 'occurrenceDefinitionPrefix') and ctx.occurrenceDefinitionPrefix():
        odp = ctx.occurrenceDefinitionPrefix()
        if hasattr(odp, 'basicDefinitionPrefix') and odp.basicDefinitionPrefix():
            bdp = odp.basicDefinitionPrefix()
            is_abstract = hasattr(bdp, 'ABSTRACT') and bdp.ABSTRACT() is not None
            is_variation = hasattr(bdp, 'VARIATION') and bdp.VARIATION() is not None
    
    if not is_abstract and not is_variation:
        return None
    
    return {
        "name": "OccurrenceDefinitionPrefix",
        "prefix": {
            "name": "BasicDefinitionPrefix",
            "isAbstract": "abstract" if is_abstract else None,
            "isVariation": "variation" if is_variation else None,
        },
        "isIndividual": None,
        "ownedRelationship": [],
        "keyword": []
    }

def _make_part_definition_dict(ctx, member_prefix=None):
    """Create a PartDefinition dictionary.
    
    member_prefix: MemberPrefix dict (visibility) to place on PackageMember.prefix.
    The OccurrenceDefinitionPrefix (abstract) is extracted from the ANTLR context.
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    
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
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "PartDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
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


def _make_attribute_definition_dict(ctx, member_prefix=None):
    """Create an AttributeDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "AttributeDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_port_definition_dict(ctx, member_prefix=None):
    """Create a PortDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    
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
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "PortDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_requirement_definition_dict(ctx, member_prefix=None):
    """Create a RequirementDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    if not name and not shortname:
        name = "Requirement_" + str(uuid.uuid4())[:8]
    
    # Note: RequirementDefinition uses 'declaration' not 'definition'
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "RequirementDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "RequirementBody",
                    "item": []
                }
            }
        }
    }


def _make_use_case_definition_dict(ctx, member_prefix=None):
    """Create a UseCaseDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    if not name and not shortname:
        name = "UseCase_" + str(uuid.uuid4())[:8]
    
    # Note: UseCaseDefinition uses 'declaration' not 'definition'
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "UseCaseDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "CaseBody",
                    "item": [],
                    "ownedRelationship": None
                }
            }
        }
    }


def _make_interface_definition_dict(ctx, member_prefix=None):
    """Create an InterfaceDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from interface body
    body_items = []
    if hasattr(ctx, "interfaceBody") and ctx.interfaceBody():
        body_ctx = ctx.interfaceBody()
        if hasattr(body_ctx, 'interfaceBodyItem') and body_ctx.interfaceBodyItem():
            for item_ctx in body_ctx.interfaceBodyItem():
                item_dict = _visit_definition_body_item_dict(item_ctx, is_interface=True)
                if item_dict:
                    body_items.append(item_dict)
    if not name and not shortname:
        name = "Interface_" + str(uuid.uuid4())[:8]
    
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "InterfaceDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_action_definition_dict(ctx, member_prefix=None):
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
                        if hasattr(ident, 'LT') and ident.LT() is not None:
                            shortname = name_text
                        else:
                            name = name_text
    
    # Extract action body items
    action_items = _visit_action_body_items(ctx)
    
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ActionDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "ActionBody",
                    "items": action_items
                }
            }
        }
    }


def _visit_action_body_items(ctx):
    """Extract ActionBodyItem dicts from an actionDefinition or actionUsage context.
    
    Processes actionBody().actionBodyItem() items, handling nonBehaviorBodyItem
    (in/out parameters, attributes) and actionBehaviorMember (nested actions).
    """
    if ctx is None:
        return []
    
    action_body = None
    if hasattr(ctx, 'actionBody') and ctx.actionBody():
        action_body = ctx.actionBody()
    
    if action_body is None:
        return []
    
    items = []
    if not (hasattr(action_body, 'actionBodyItem') and action_body.actionBodyItem()):
        return []
    
    for abi_ctx in action_body.actionBodyItem():
        item_dict = _visit_action_body_item(abi_ctx)
        if item_dict:
            items.append(item_dict)
    
    return items


def _visit_action_body_item(abi_ctx):
    """Visit a single actionBodyItem and return an ActionBodyItem dict."""
    if abi_ctx is None:
        return None
    
    # Handle nonBehaviorBodyItem (in/out params, attributes, imports)
    if hasattr(abi_ctx, 'nonBehaviorBodyItem') and abi_ctx.nonBehaviorBodyItem():
        nbi = abi_ctx.nonBehaviorBodyItem()
        inner = _visit_non_behavior_body_item(nbi)
        if inner:
            return {
                "name": "ActionBodyItem",
                "ownedRelationship": [inner]
            }
    
    return None


def _visit_non_behavior_body_item(nbi_ctx):
    """Visit a nonBehaviorBodyItem - similar to definitionBodyItem but inside action body."""
    if nbi_ctx is None:
        return None
    
    # Handle nonOccurrenceUsageMember (in/out params, attributes)
    for child in nbi_ctx.children:
        cname = type(child).__name__
        
        if cname == 'NonOccurrenceUsageMemberContext':
            # Navigate: NonOccurrenceUsageMember -> NonOccurrenceUsageElement -> usage
            for c2 in child.children:
                if type(c2).__name__ == 'NonOccurrenceUsageElementContext':
                    inner = _visit_nested_non_occurrence_usage(c2)
                    if inner:
                        if inner.get("name") == "NonOccurrenceUsageElement":
                            owned = [inner]
                        else:
                            owned = [inner]
                        return {
                            "name": "NonOccurrenceUsageMember",
                            "prefix": None,
                            "ownedRelatedElement": owned
                        }
        
        elif cname == 'StructureUsageMemberContext':
            # Handle occurrence usages (parts, items, ports)
            for c2 in child.children:
                if type(c2).__name__ == 'OccurrenceUsageElementContext':
                    inner = _visit_nested_occurrence_usage(c2)
                    if inner:
                        if inner.get("name") == "UsageElement":
                            occ_elem = inner.get("ownedRelatedElement", {})
                            if occ_elem.get("name") == "OccurrenceUsageElement":
                                owned = [occ_elem]
                            else:
                                owned = [inner]
                        else:
                            owned = [inner]
                        return {
                            "name": "OccurrenceUsageMember",
                            "prefix": None,
                            "ownedRelatedElement": owned
                        }
    
    return None


def _make_state_definition_dict(ctx, member_prefix=None):
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
    
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "StateDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "StateDefBody",
                    "part": None,
                    "isParallel": None
                }
            }
        }
    }


def _make_constraint_definition_dict(ctx, member_prefix=None):
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
    
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ConstraintDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "CalculationBody",
                    "part": []
                }
            }
        }
    }


def _make_calculation_definition_dict(ctx, member_prefix=None):
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
    
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "CalculationDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "CalculationBody",
                    "part": []
                }
            }
        }
    }


def _make_connection_definition_dict(ctx, member_prefix=None):
    """Create a ConnectionDefinition dictionary.
    
    ConnectionDefinition uses 'definition' wrapper pattern (like part, item, port).
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "ConnectionDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_flow_connection_definition_dict(ctx, member_prefix=None):
    """Create a FlowConnectionDefinition dictionary.
    
    FlowConnectionDefinition uses 'definition' wrapper pattern.
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "FlowConnectionDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
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


def _make_interface_usage_dict(ctx, prefix=None):
    """Create an InterfaceUsage dictionary.
    
    interfaceUsage: occurrenceUsagePrefix INTERFACE interfaceUsageDeclaration interfaceBody
    interfaceUsageDeclaration: usageDeclaration? valuePart? (CONNECT interfacePart)?
    
    interfacePart: binaryInterfacePart | naryInterfacePart
    binaryInterfacePart: interfaceEndMember TO interfaceEndMember
    naryInterfacePart: LPAREN interfaceEndMember COMMA interfaceEndMember (COMMA interfaceEndMember)* RPAREN
    
    interfaceEndMember: interfaceEnd
    interfaceEnd: (ownedCrossMultiplicityMember)? (name (COLON_COLON_GT | REFERENCES))? ownedReferenceSubsetting
    """
    name = None
    shortname = None
    typed_by = None
    if ctx is not None:
        aud = None
        if hasattr(ctx, 'interfaceUsageDeclaration') and ctx.interfaceUsageDeclaration():
            aud = ctx.interfaceUsageDeclaration()
            if isinstance(aud, list):
                aud = aud[0] if aud else None
        
        ud = None
        if aud and hasattr(aud, 'usageDeclaration') and aud.usageDeclaration():
            ud = aud.usageDeclaration()
            if isinstance(ud, list):
                ud = ud[0] if ud else None
        
        if ud and hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            if isinstance(ident, list):
                ident = ident[0] if ident else None
            if hasattr(ident, 'name'):
                name_list = ident.name()
                if name_list and isinstance(name_list, list):
                    if len(name_list) == 2:
                        shortname = name_list[0].getText()
                        name = name_list[1].getText()
                    elif len(name_list) == 1:
                        name_text = name_list[0].getText()
                        name, shortname = _extract_name_shortname(name_text)
        
        if ud and hasattr(ud, 'featureSpecializationPart') and ud.featureSpecializationPart():
            fsp = ud.featureSpecializationPart()
            if isinstance(fsp, list):
                fsp = fsp[0] if fsp else None
            if fsp and hasattr(fsp, 'featureSpecialization') and fsp.featureSpecialization():
                specs = fsp.featureSpecialization()
                if not isinstance(specs, list):
                    specs = [specs]
                for spec in specs:
                    if hasattr(spec, 'typings') and spec.typings():
                        typings = spec.typings()
                        if isinstance(typings, list):
                            typings = typings[0] if typings else None
                        if typings and hasattr(typings, 'getText'):
                            text = typings.getText()
                            if text.startswith(':'):
                                typed_by = text[1:].strip()
                                break
        
        if aud and hasattr(aud, 'interfacePart') and aud.interfacePart():
            interface_part = aud.interfacePart()
            if isinstance(interface_part, list):
                interface_part = interface_part[0] if interface_part else None
    
    occ_prefix = _get_occurrence_usage_prefix(ctx)
    
    body_items = []
    if hasattr(ctx, 'interfaceBody') and ctx.interfaceBody():
        body_ctx = ctx.interfaceBody()
        if hasattr(body_ctx, 'interfaceBodyItem') and body_ctx.interfaceBodyItem():
            for item_ctx in body_ctx.interfaceBodyItem():
                item_dict = _visit_definition_body_item_dict(item_ctx, is_interface=True)
                if item_dict:
                    body_items.append(item_dict)
    
    specialization = _build_specialization(typed_by) if typed_by else None
    
    interface_end_members = []
    if interface_part:
        if hasattr(interface_part, 'binaryInterfacePart') and interface_part.binaryInterfacePart():
            bip = interface_part.binaryInterfacePart()
            if isinstance(bip, list):
                bip = bip[0] if bip else None
            if bip:
                end_members_list = bip.interfaceEndMember() if hasattr(bip, 'interfaceEndMember') else []
                if isinstance(end_members_list, list) and len(end_members_list) >= 1:
                    end1 = _visit_interface_end_member(end_members_list[0])
                    if end1:
                        interface_end_members.append(end1)
                if isinstance(end_members_list, list) and len(end_members_list) >= 2:
                    end2 = _visit_interface_end_member(end_members_list[1])
                    if end2:
                        interface_end_members.append(end2)
        elif hasattr(interface_part, 'naryInterfacePart') and interface_part.naryInterfacePart():
            nip = interface_part.naryInterfacePart()
            if isinstance(nip, list):
                nip = nip[0] if nip else None
            if nip and hasattr(nip, 'interfaceEndMember') and nip.interfaceEndMember():
                end_members = nip.interfaceEndMember()
                if isinstance(end_members, list):
                    for em in end_members:
                        end = _visit_interface_end_member(em)
                        if end:
                            interface_end_members.append(end)
    
    decl_dict = {
        "name": "InterfaceUsageDeclaration",
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
        "part1": {
            "name": "InterfacePart",
            "binarypart": {
                "name": "BinaryInterfacePart",
                "ownedRelationship": [
                    {"name": "InterfaceEndMember", "ownedRelatedElement": end}
                    for end in interface_end_members
                ]
            }
        },
        "part2": None
    }
    
    if interface_end_members:
        interface_body = {
            "name": "InterfaceBody",
            "item": body_items
        }
    else:
        interface_body = None if not body_items else {
            "name": "InterfaceBody",
            "item": body_items
        }
    
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
                        "name": "InterfaceUsage",
                        "prefix": occ_prefix or prefix,
                        "declaration": decl_dict,
                        "body": interface_body
                    }
                }
            }
        }
    }


def _visit_interface_end_member(em_ctx):
    """Visit an interface end member and return an InterfaceEnd dict.
    
    interfaceEnd: (ownedCrossMultiplicityMember)? (name (COLON_COLON_GT | REFERENCES))? ownedReferenceSubsetting
    """
    end_dict = {
        "name": "InterfaceEnd",
        "declaredName": None,
        "ownedRelationship": []
    }
    
    if em_ctx is None:
        return end_dict
    
    if hasattr(em_ctx, 'interfaceEnd') and em_ctx.interfaceEnd():
        iface_end = em_ctx.interfaceEnd()
        if isinstance(iface_end, list):
            iface_end = iface_end[0] if iface_end else None
        
        if iface_end:
            end_dict = {
                "name": "InterfaceEnd",
                "declaredName": None,
                "ownedRelationship": []
            }
            
            if hasattr(iface_end, 'name') and iface_end.name():
                names = iface_end.name()
                if isinstance(names, list):
                    end_dict["declaredName"] = names[0].getText() if names else None
                else:
                    end_dict["declaredName"] = names.getText() if hasattr(names, 'getText') else None
            
            if hasattr(iface_end, 'ownedReferenceSubsetting') and iface_end.ownedReferenceSubsetting():
                ref = iface_end.ownedReferenceSubsetting()
                if isinstance(ref, list):
                    ref = ref[0] if ref else None
                if ref:
                    ref_subset = _visit_reference_subsetting(ref)
                    if ref_subset:
                        end_dict["ownedRelationship"].append(ref_subset)
            
            if hasattr(iface_end, 'ownedCrossMultiplicityMember') and iface_end.ownedCrossMultiplicityMember():
                mult = iface_end.ownedCrossMultiplicityMember()
                if isinstance(mult, list):
                    mult = mult[0] if mult else None
                if mult:
                    mult_dict = _visit_multiplicity(mult)
                    if mult_dict:
                        end_dict["ownedRelationship"].append(mult_dict)
    
    return end_dict


def _visit_reference_subsetting(ref_ctx):
    """Visit an owned reference subsetting and return a dict.
    
    ownedReferenceSubsetting: qualifiedName (DOT qualifiedName)*
    """
    result = {
        "name": "OwnedReferenceSubsetting",
        "referencedFeature": None,
        "ownedRelatedElement": []
    }
    
    if ref_ctx is None:
        return result
    
    chaining_items = []
    current_name = []
    
    def process_qname(qn_ctx):
        if hasattr(qn_ctx, 'name') and qn_ctx.name():
            name_list = qn_ctx.name()
            if isinstance(name_list, list):
                return [n.getText() for n in name_list]
            elif hasattr(name_list, 'getText'):
                return [name_list.getText()]
        return []
    
    if hasattr(ref_ctx, 'qualifiedName') and ref_ctx.qualifiedName():
        qn_list = ref_ctx.qualifiedName()
        if not isinstance(qn_list, list):
            qn_list = [qn_list]
        
        first = True
        for qn in qn_list:
            names = process_qname(qn)
            if names:
                if first and not chaining_items:
                    current_name.extend(names)
                    first = False
                else:
                    if current_name:
                        chaining_items.append({
                            "name": "OwnedFeatureChaining",
                            "chainingFeature": {"name": "QualifiedName", "names": current_name}
                        })
                    current_name = names
    
    if current_name:
        chaining_items.append({
            "name": "OwnedFeatureChaining",
            "chainingFeature": {"name": "QualifiedName", "names": current_name}
        })
    
    if chaining_items:
        result["ownedRelatedElement"].append({
            "name": "OwnedFeatureChain",
            "feature": {
                "name": "FeatureChain",
                "ownedRelationship": chaining_items
            }
        })
    
    return result


def _build_reference_subsetting_from_ctx(rs_ctx):
    """Build an OwnedReferenceSubsetting dict from a referenceSubsetting context."""
    result = {
        "name": "OwnedReferenceSubsetting",
        "referencedFeature": None,
        "ownedRelatedElement": []
    }
    
    if rs_ctx is None:
        return result
    
    if hasattr(rs_ctx, 'ownedRelatedElement') and rs_ctx.ownedRelatedElement():
        ore_list = rs_ctx.ownedRelatedElement()
        if not isinstance(ore_list, list):
            ore_list = [ore_list]
        
        for ore in ore_list:
            if hasattr(ore, 'featureReference') and ore.featureReference():
                fr = ore.featureReference()
                if isinstance(fr, list):
                    fr = fr[0] if fr else None
                if fr:
                    ref_dict = _build_feature_reference_from_ctx(fr)
                    if ref_dict:
                        result["ownedRelatedElement"].append(ref_dict)
            elif hasattr(ore, 'referenceSubsetting') and ore.referenceSubsetting():
                sub_rs = ore.referenceSubsetting()
                if isinstance(sub_rs, list):
                    sub_rs = sub_rs[0] if sub_rs else None
                if sub_rs:
                    sub_result = _build_reference_subsetting_from_ctx(sub_rs)
                    result["ownedRelatedElement"].append(sub_result)
            elif hasattr(ore, 'ownedFeatureChain') and ore.ownedFeatureChain():
                fc = ore.ownedFeatureChain()
                if isinstance(fc, list):
                    fc = fc[0] if fc else None
                if fc:
                    fc_dict = _build_feature_chain_from_ctx(fc)
                    if fc_dict:
                        result["ownedRelatedElement"].append(fc_dict)
    
    if hasattr(rs_ctx, 'referencedFeature') and rs_ctx.referencedFeature():
        rf = rs_ctx.referencedFeature()
        if isinstance(rf, list):
            rf = rf[0] if rf else None
        if rf and hasattr(rf, 'qualifiedName') and rf.qualifiedName():
            qn = rf.qualifiedName()
            if isinstance(qn, list):
                qn = qn[0] if qn else None
            if qn and hasattr(qn, 'name'):
                names_list = qn.name()
                if isinstance(names_list, list):
                    names = [n.getText() for n in names_list]
                elif hasattr(names_list, 'getText'):
                    names = [names_list.getText()]
                else:
                    names = []
                result["referencedFeature"] = {
                    "name": "QualifiedName",
                    "names": names
                }
    
    return result


def _build_feature_chain_from_ctx(fc_ctx):
    """Build a FeatureChain dict from a featureChain context."""
    result = {
        "name": "OwnedFeatureChain",
        "feature": {
            "name": "FeatureChain",
            "ownedRelationship": []
        }
    }
    
    if fc_ctx is None:
        return result
    
    if hasattr(fc_ctx, 'ownedRelatedElement') and fc_ctx.ownedRelatedElement():
        ore_list = fc_ctx.ownedRelatedElement()
        if not isinstance(ore_list, list):
            ore_list = [ore_list]
        
        for ore in ore_list:
            chaining_dict = _build_feature_chaining_from_ctx(ore)
            if chaining_dict:
                result["feature"]["ownedRelationship"].append(chaining_dict)
    
    return result


def _build_feature_chaining_from_ctx(ch_ctx):
    """Build an OwnedFeatureChaining dict from a context."""
    result = {
        "name": "OwnedFeatureChaining",
        "chainingFeature": {
            "name": "QualifiedName",
            "names": []
        }
    }
    
    if ch_ctx is None:
        return result
    
    if hasattr(ch_ctx, 'qualifiedName') and ch_ctx.qualifiedName():
        qn = ch_ctx.qualifiedName()
        if isinstance(qn, list):
            qn = qn[0] if qn else None
        if qn and hasattr(qn, 'name'):
            names_list = qn.name()
            if isinstance(names_list, list):
                names = [n.getText() for n in names_list]
            elif hasattr(names_list, 'getText'):
                names = [names_list.getText()]
            else:
                names = []
            result["chainingFeature"]["names"] = names
    
    return result


def _build_feature_reference_from_ctx(fr_ctx):
    """Build a FeatureReference dict from a featureReference context."""
    result = {
        "name": "FeatureReference",
        "ownedRelatedElement": []
    }
    
    if fr_ctx is None:
        return result
    
    if hasattr(fr_ctx, 'ownedRelatedElement') and fr_ctx.ownedRelatedElement():
        ore_list = fr_ctx.ownedRelatedElement()
        if not isinstance(ore_list, list):
            ore_list = [ore_list]
        
        for ore in ore_list:
            chaining_dict = _build_feature_chaining_from_ctx(ore)
            if chaining_dict:
                result["ownedRelatedElement"].append(chaining_dict)
    
    return result


def _visit_multiplicity(mult_ctx):
    """Visit a multiplicity and return a dict."""
    result = {"name": "OwnedMultiplicity"}
    
    if mult_ctx is None:
        return result
    
    if hasattr(mult_ctx, 'ownedRelatedElement') and mult_ctx.ownedRelatedElement():
        related = mult_ctx.ownedRelatedElement()
        if isinstance(related, list):
            related = related[0] if related else None
        if related and hasattr(related, 'multiplicity') and related.multiplicity():
            mult = related.multiplicity()
            if isinstance(mult, list):
                mult = mult[0] if mult else None
            if mult:
                result = _build_multiplicity_from_ctx(mult)
    
    return result


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
                        if hasattr(ident, 'LT') and ident.LT() is not None:
                            shortname = name_text
                        else:
                            name = name_text
        
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


def _make_view_definition_dict(ctx, member_prefix=None):
    """Create a ViewDefinition dictionary.
    
    viewDefinition: occurrenceDefinitionPrefix VIEW DEF definitionDeclaration viewDefinitionBody
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    # ViewDefinition uses _DeclaredDefinitionBase pattern: prefix + keyword + declaration + body
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
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
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "DefinitionBody",
                    "ownedRelatedElement": body_items
                }
            }
        }
    }


def _make_viewpoint_definition_dict(ctx, member_prefix=None):
    """Create a ViewpointDefinition dictionary.
    
    viewpointDefinition: occurrenceDefinitionPrefix VIEWPOINT DEF definitionDeclaration requirementBody
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
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
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "RequirementBody",
                    "ownedRelationship": []
                }
            }
        }
    }


def _make_concern_definition_dict(ctx, member_prefix=None):
    """Create a ConcernDefinition dictionary.
    
    concernDefinition: occurrenceDefinitionPrefix CONCERN DEF definitionDeclaration requirementBody
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
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
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "RequirementBody",
                    "ownedRelationship": []
                }
            }
        }
    }


def _make_case_definition_dict(ctx, member_prefix=None):
    """Create a CaseDefinition dictionary.
    
    caseDefinition: occurrenceDefinitionPrefix CASE DEF definitionDeclaration caseBody
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    if not name and not shortname:
        name = "Case_" + str(uuid.uuid4())[:8]
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "CaseDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "CaseBody",
                    "item": [],
                    "ownedRelationship": None
                }
            }
        }
    }


def _make_analysis_case_definition_dict(ctx, member_prefix=None):
    """Create an AnalysisCaseDefinition dictionary.
    
    analysisCaseDefinition: occurrenceDefinitionPrefix ANALYSIS DEF definitionDeclaration caseBody
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    if not name and not shortname:
        name = "AnalysisCase_" + str(uuid.uuid4())[:8]
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "AnalysisCaseDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "CaseBody",
                    "item": [],
                    "ownedRelationship": None
                }
            }
        }
    }


def _make_verification_case_definition_dict(ctx, member_prefix=None):
    """Create a VerificationCaseDefinition dictionary.
    
    verificationCaseDefinition: occurrenceDefinitionPrefix VERIFICATION DEF definitionDeclaration caseBody
    """
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    if not name and not shortname:
        name = "VerificationCase_" + str(uuid.uuid4())[:8]
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "VerificationCaseDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
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


def _make_enumeration_definition_dict(ctx, member_prefix=None):
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
                        if hasattr(ident, 'LT') and ident.LT() is not None:
                            shortname = name_text
                        else:
                            name = name_text
    
    # Extract enum body members
    enum_members = []
    if ctx is not None and hasattr(ctx, 'enumerationBody') and ctx.enumerationBody():
        body_ctx = ctx.enumerationBody()
        if hasattr(body_ctx, 'enumerationUsageMember'):
            for member_ctx in body_ctx.enumerationUsageMember():
                member_dict = _visit_enumeration_usage_member(member_ctx)
                if member_dict:
                    enum_members.append(member_dict)
    
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "EnumerationDefinition",
                "prefix": occ_prefix,
                "declaration": {
                    "name": "DefinitionDeclaration",
                    "identification": {
                        "name": "Identification",
                        "declaredShortName": shortname,
                        "declaredName": name
                    },
                    "subclassificationpart": _get_subclassification_part(ctx)
                },
                "body": {
                    "name": "EnumerationBody",
                    "ownedRelationship": enum_members
                }
            }
        }
    }


def _visit_enumeration_usage_member(member_ctx):
    """Build an EnumerationUsageMember dict from ANTLR context."""
    # member_ctx children: MemberPrefixContext, EnumeratedValueContext
    prefix = None
    if hasattr(member_ctx, 'memberPrefix') and member_ctx.memberPrefix():
        mp = member_ctx.memberPrefix()
        if hasattr(mp, 'visibilityIndicator') and mp.visibilityIndicator():
            prefix = {
                "name": "MemberPrefix",
                "visibility": _visit_visibility_indicator_dict(mp.visibilityIndicator())
            }
    
    # Find EnumeratedValueContext
    ev_ctx = None
    for child in member_ctx.children:
        if type(child).__name__ == 'EnumeratedValueContext':
            ev_ctx = child
            break
    
    if ev_ctx is None:
        return None
    
    # EnumeratedValue children: TerminalNodeImpl("enum"), UsageContext
    keyword = None
    usage_ctx = None
    for child in ev_ctx.children:
        cname = type(child).__name__
        if cname == 'TerminalNodeImpl':
            keyword = child.getText()  # "enum"
        elif cname == 'UsageContext':
            usage_ctx = child
    
    if usage_ctx is None:
        return None
    
    # Extract name from UsageContext -> UsageDeclarationContext -> IdentificationContext
    ev_name = None
    ev_shortname = None
    if hasattr(usage_ctx, 'usageDeclaration') and usage_ctx.usageDeclaration():
        ud = usage_ctx.usageDeclaration()
        if hasattr(ud, 'identification') and ud.identification():
            ident = ud.identification()
            name_list = ident.name() if hasattr(ident, 'name') else []
            if name_list and isinstance(name_list, list):
                if len(name_list) == 2:
                    ev_shortname = name_list[0].getText()
                    ev_name = name_list[1].getText()
                elif len(name_list) == 1:
                    ev_name_text = name_list[0].getText()
                    if hasattr(ident, 'LT') and ident.LT() is not None:
                        ev_shortname = ev_name_text
                    else:
                        ev_name = ev_name_text
    
    return {
        "name": "EnumerationUsageMember",
        "prefix": prefix,
        "ownedRelatedElement": [
            {
                "name": "EnumeratedValue",
                "keyword": keyword,
                "usage": {
                    "name": "Usage",
                    "declaration": {
                        "name": "UsageDeclaration",
                        "declaration": {
                            "name": "FeatureDeclaration",
                            "identification": {
                                "name": "Identification",
                                "declaredShortName": ev_shortname,
                                "declaredName": ev_name
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
        ]
    }


def _make_allocation_definition_dict(ctx, member_prefix=None):
    """Create an AllocationDefinition dictionary (uses Definition body)."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "AllocationDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_metadata_definition_dict(ctx, member_prefix=None):
    """Create a MetadataDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
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
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_rendering_definition_dict(ctx, member_prefix=None):
    """Create a RenderingDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    # Get body items from definition body
    body_items = []
    if hasattr(ctx, "definition") and ctx.definition():
        defn = ctx.definition()
        if hasattr(defn, "definitionBody") and defn.definitionBody():
            body_items = _visit_definition_body_dict(defn.definitionBody())
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "RenderingDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
                    },
                    "body": {
                        "name": "DefinitionBody",
                        "ownedRelatedElement": body_items
                    }
                }
            }
        }
    }


def _make_individual_definition_dict(ctx, member_prefix=None):
    """Create an IndividualDefinition dictionary."""
    name, shortname = _get_definition_identification(ctx)
    occ_prefix = _get_occurrence_definition_prefix(ctx)
    return {
        "name": "PackageMember",
        "prefix": member_prefix,
        "ownedRelatedElement": {
            "name": "DefinitionElement",
            "ownedRelatedElement": {
                "name": "IndividualDefinition",
                "prefix": occ_prefix,
                "definition": {
                    "name": "Definition",
                    "declaration": {
                        "name": "DefinitionDeclaration",
                        "identification": {
                            "name": "Identification",
                            "declaredShortName": shortname,
                            "declaredName": name
                        },
                        "subclassificationpart": _get_subclassification_part(ctx)
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
    """Visit a definition body and return a list of DefinitionBodyItem dicts."""
    # Debug print
    # print(f"_visit_definition_body_dict called with body_ctx: {body_ctx}")
    if body_ctx is None:
        # print("  body_ctx is None")
        return []
    
    items = []
    if hasattr(body_ctx, 'definitionBodyItem') and body_ctx.definitionBodyItem():
        items_list = body_ctx.definitionBodyItem()
        # print(f"  Found {len(items_list)} definitionBodyItem(s)")
        for i, item_ctx in enumerate(items_list):
            # print(f"    Item {i}: {item_ctx}")
            item_dict = _visit_definition_body_item_dict(item_ctx)
            if item_dict:
                # print(f"      -> item_dict: {item_dict}")
                items.append(item_dict)
            else:
                # print(f"      -> item_dict is None")
                pass
    else:
        # print("  No definitionBodyItem found")
        pass
    # print(f"  Returning {len(items)} items")
    return items


def _visit_definition_body_item_dict(item_ctx, is_interface=False):
    """Visit a definition body item and return a dictionary.
    
    Per grammar:
    definitionBodyItem
        : importRule
        | memberPrefix definitionBodyItemContent
        | ( sourceSuccessionMember)? memberPrefix endOccurrenceUsageElement
        | ( sourceSuccessionMember)? memberPrefix occurrenceUsageElement
        | ( sourceSuccessionMember)? memberPrefix interfaceOccurrenceUsageElement
        | ( sourceSuccessionMember)? interfaceNonOccurrenceUsageMember
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
    
    # print(f"DEBUG _visit_definition_body_item_dict: {item_ctx}")
    
    inner_element = None
    wrapper = None
    
    # Check for occurrenceUsageElement (part, item, port, action, etc.)
    if hasattr(item_ctx, 'occurrenceUsageElement') and item_ctx.occurrenceUsageElement():
        occ_elem = item_ctx.occurrenceUsageElement()
        # print(f"DEBUG: Found occurrenceUsageElement: {occ_elem}")
        inner_element = _visit_nested_occurrence_usage(occ_elem)
        wrapper = "OccurrenceUsageMember"
    # Check for interfaceOccurrenceUsageMember (for interface ends, etc.)
    elif hasattr(item_ctx, 'interfaceOccurrenceUsageMember') and item_ctx.interfaceOccurrenceUsageMember():
        memb = item_ctx.interfaceOccurrenceUsageMember()
        # print(f"DEBUG: Found interfaceOccurrenceUsageMember: {memb}")
        if memb and hasattr(memb, 'interfaceOccurrenceUsageElement') and memb.interfaceOccurrenceUsageElement():
            occ_elem = memb.interfaceOccurrenceUsageElement()
            # print(f"DEBUG: Found interfaceOccurrenceUsageElement: {occ_elem}")
            inner_element = _visit_nested_occurrence_usage(occ_elem)
            wrapper = "InterfaceOccurrenceUsageMember"
    # Check for endOccurrenceUsageElement (for regular definition body)
    elif hasattr(item_ctx, 'endOccurrenceUsageElement') and item_ctx.endOccurrenceUsageElement():
        occ_elem = item_ctx.endOccurrenceUsageElement()
        # print(f"DEBUG: Found endOccurrenceUsageElement: {occ_elem}")
        inner_element = _visit_nested_occurrence_usage(occ_elem)
        wrapper = "OccurrenceUsageMember"
    # Check for interfaceNonOccurrenceUsageMember
    elif hasattr(item_ctx, 'interfaceNonOccurrenceUsageMember') and item_ctx.interfaceNonOccurrenceUsageMember():
        memb = item_ctx.interfaceNonOccurrenceUsageMember()
        # print(f"DEBUG: Found interfaceNonOccurrenceUsageMember: {memb}")
        if memb and hasattr(memb, 'interfaceNonOccurrenceUsageElement') and memb.interfaceNonOccurrenceUsageElement():
            non_occ = memb.interfaceNonOccurrenceUsageElement()
            # print(f"DEBUG: Found interfaceNonOccurrenceUsageElement: {non_occ}")
            inner_element = _visit_nested_non_occurrence_usage(non_occ)
            wrapper = "NonOccurrenceUsageMember"
    
    # Check for definitionBodyItemContent
    if not inner_element and hasattr(item_ctx, 'definitionBodyItemContent') and item_ctx.definitionBodyItemContent():
        content = item_ctx.definitionBodyItemContent()
        # print(f"DEBUG: Found definitionBodyItemContent: {content}")
        # Check nested definition
        if hasattr(content, 'definitionElement') and content.definitionElement():
            def_elem = content.definitionElement()
            # print(f"DEBUG: Found definitionElement: {def_elem}")
            inner_element = _visit_nested_definition_element(def_elem)
            wrapper = "DefinitionMember"
        # Check nonOccurrenceUsageElement
        elif hasattr(content, 'nonOccurrenceUsageElement') and content.nonOccurrenceUsageElement():
            non_occ = content.nonOccurrenceUsageElement()
            # print(f"DEBUG: Found nonOccurrenceUsageElement: {non_occ}")
            inner_element = _visit_nested_non_occurrence_usage(non_occ)
            wrapper = "NonOccurrenceUsageMember"
    
    # print(f"DEBUG: inner_element={inner_element}, wrapper={wrapper}")
    if not inner_element or not wrapper:
        # print(f"DEBUG: Returning None")
        return None
    
    # For OccurrenceUsageMember and InterfaceOccurrenceUsageMember, the ownedRelatedElement should be a LIST of OccurrenceUsageElement
    if wrapper == "OccurrenceUsageMember":
        # inner_element is currently UsageElement wrapping OccurrenceUsageElement
        # We need to extract just the OccurrenceUsageElement and put it in a list
        if inner_element.get("name") == "UsageElement":
            occ_elem = inner_element.get("ownedRelatedElement", {})
            if occ_elem.get("name") == "OccurrenceUsageElement":
                # Check if it's a StructureUsageElement with InterfaceUsage
                inner2 = occ_elem.get("ownedRelatedElement", {})
                if inner2.get("name") == "StructureUsageElement":
                    inner3 = inner2.get("ownedRelatedElement", {})
                    if inner3.get("name") == "InterfaceUsage":
                        # For InterfaceUsage, keep the full UsageElement structure
                        # but we need to create a wrapper that doesn't break the class hierarchy
                        owned = [{
                            "name": "OccurrenceUsageElement",
                            "ownedRelatedElement": inner3  # InterfaceUsage directly, not wrapped in StructureUsageElement
                        }]
                    else:
                        owned = [occ_elem]
                else:
                    owned = [occ_elem]
            else:
                owned = [inner_element]
        else:
            owned = [inner_element]
    elif wrapper == "InterfaceOccurrenceUsageMember":
        # InterfaceOccurrenceUsageMember expects ownedRelatedElement as a list of InterfaceOccurrenceUsageElement dicts
        # Each InterfaceOccurrenceUsageElement has: element (DefaultInterfaceEnd dict), isAbstract, isVariation, isEnd
        if inner_element.get("name") == "UsageElement":
            occ_elem_dict = inner_element.get("ownedRelatedElement", {})
            if occ_elem_dict.get("name") == "OccurrenceUsageElement":
                struct_usage_elem = occ_elem_dict.get("ownedRelatedElement", {})
                # Navigate: struct_usage_elem -> ownedRelatedElement (PartUsage) -> prefix
                inner_usage = struct_usage_elem.get("ownedRelatedElement", {})
                part_usage_prefix = inner_usage.get("prefix", {}) if isinstance(inner_usage, dict) else {}
                # Navigate: part_usage_prefix -> prefix (BasicUsagePrefix) -> prefix (RefPrefix)
                occ_prefix = part_usage_prefix.get("prefix", {}) if isinstance(part_usage_prefix, dict) else {}
                ref_prefix = occ_prefix.get("prefix", {}) if isinstance(occ_prefix, dict) else {}
                is_abstract = ref_prefix.get("isAbstract") if isinstance(ref_prefix, dict) else None
                is_variation = ref_prefix.get("isVariation") if isinstance(ref_prefix, dict) else None
                is_end = ref_prefix.get("isEnd") if isinstance(ref_prefix, dict) else None
                # Build DefaultInterfaceEnd element (not StructureUsageElement with PartUsage)
                usage_dict = inner_usage.get("usage", {})
                # Build direction from ref_prefix
                direction = None
                if isinstance(ref_prefix, dict) and "direction" in ref_prefix:
                    dir_dict = ref_prefix["direction"]
                    if dir_dict and isinstance(dir_dict, dict) and len(dir_dict) > 0:
                        direction = dir_dict
                default_interface_end = {
                    "name": "DefaultInterfaceEnd",
                    "direction": direction,
                    "isAbstract": is_abstract,
                    "isVariation": is_variation,
                    "isEnd": is_end,
                    "usage": usage_dict
                }
                # Build the interface occurrence usage element
                iface_elem = {
                    "name": "InterfaceOccurrenceUsageElement",
                    "element": default_interface_end
                }
                owned = [iface_elem]
            else:
                # Fallback: wrap the whole thing as DefaultInterfaceEnd
                default_interface_end = {
                    "name": "DefaultInterfaceEnd",
                    "direction": None,
                    "isAbstract": None,
                    "isVariation": None,
                    "isEnd": "end",
                    "usage": None
                }
                iface_elem = {
                    "name": "InterfaceOccurrenceUsageElement",
                    "element": default_interface_end
                }
                owned = [iface_elem]
        else:
            # Already some other structure
            default_interface_end = {
                "name": "DefaultInterfaceEnd",
                "direction": None,
                "isAbstract": None,
                "isVariation": None,
                "isEnd": "end",
                "usage": None
            }
            iface_elem = {
                "name": "InterfaceOccurrenceUsageElement",
                "element": default_interface_end
            }
            owned = [iface_elem]
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
    
    # print(f"DEBUG: Returning DefinitionBodyItem with wrapper={wrapper}, owned={owned}")
    return {
        "name": "InterfaceBodyItem" if is_interface else "DefinitionBodyItem",
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
    
    # print(f"DEBUG _visit_nested_occurrence_usage: {type(occ_elem).__name__}")
    
    # Check structure usage elements (part, item, port)
    if hasattr(occ_elem, 'structureUsageElement') and occ_elem.structureUsageElement():
        struct_elem = occ_elem.structureUsageElement()
        # print(f"DEBUG: Has structureUsageElement: {struct_elem}")
        
        if hasattr(struct_elem, 'partUsage') and struct_elem.partUsage():
            ctx = struct_elem.partUsage()
            # print(f"DEBUG: Found partUsage: {ctx}")
            name, shortname = _get_usage_identification(ctx)
            # print(f"DEBUG: partUsage name: {name}, shortname: {shortname}")
            body_items = _get_usage_body_items(ctx)
            occ_prefix = _get_occurrence_usage_prefix(ctx)
            specialization = _build_full_specialization_from_ctx(ctx)
            return _make_nested_usage_element("PartUsage", name, shortname, occ_prefix, body_items, specialization)
        elif hasattr(struct_elem, 'itemUsage') and struct_elem.itemUsage():
            ctx = struct_elem.itemUsage()
            # print(f"DEBUG: Found itemUsage: {ctx}")
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            occ_prefix = _get_occurrence_usage_prefix(ctx)
            specialization = _build_full_specialization_from_ctx(ctx)
            return _make_nested_usage_element("ItemUsage", name, shortname, occ_prefix, body_items, specialization)
        elif hasattr(struct_elem, 'portUsage') and struct_elem.portUsage():
            ctx = struct_elem.portUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            occ_prefix = _get_occurrence_usage_prefix(ctx)
            specialization = _build_full_specialization_from_ctx(ctx)
            return _make_nested_usage_element("PortUsage", name, shortname, occ_prefix, body_items, specialization)
        elif hasattr(struct_elem, 'interfaceUsage') and struct_elem.interfaceUsage():
            ctx = struct_elem.interfaceUsage()
            result = _make_interface_usage_dict(ctx, None)
            if result and result.get("name") == "PackageMember":
                inner = result.get("ownedRelatedElement", {})
                return inner  # Extract the inner UsageElement for nested usage
            return result
    
    # Check for interface occurrence usage element (has defaultInterfaceEnd keyword)
    if hasattr(occ_elem, 'defaultInterfaceEnd') and occ_elem.defaultInterfaceEnd() is not None:
        default_interface_end_ctx = occ_elem.defaultInterfaceEnd()
        # print(f"DEBUG: Found defaultInterfaceEnd: {default_interface_end_ctx}")
        if default_interface_end_ctx and hasattr(default_interface_end_ctx, 'usage') and default_interface_end_ctx.usage():
            ctx = default_interface_end_ctx.usage()
            # print(f"DEBUG: Usage context: {ctx}")
            name, shortname = _get_usage_identification(ctx)
            # print(f"DEBUG: Name: {name}, Shortname: {shortname}")
            body_items = _get_usage_body_items(ctx)
            # print(f"DEBUG: Body items: {body_items}")
            occ_prefix = _get_occurrence_usage_prefix(ctx)
            # print(f"DEBUG: Occ prefix: {occ_prefix}")
            # If we have a defaultInterfaceEnd, we need to set the is_end flag in the occurrence usage prefix
            if hasattr(default_interface_end_ctx, 'END') and default_interface_end_ctx.END() is not None:
                if occ_prefix is None:
                    # Create a ref_prefix with just the end flag
                    ref_prefix = {
                        "name": "RefPrefix",
                        "direction": {
                            "name": "FeatureDirection",
                            "in": "",
                            "out": "",
                            "inout": ""
                        },
                        "isAbstract": None,
                        "isVariation": None,
                        "isReadOnly": None,
                        "isDerived": None,
                        "isEnd": "end"
                    }
                    occ_prefix = {
                        "name": "OccurrenceUsagePrefix",
                        "prefix": {
                            "name": "BasicUsagePrefix",
                            "prefix": ref_prefix,
                            "isReference": False
                        },
                        "isIndividual": None,
                        "portionKind": None,
                        "usageExtension": []
                    }
                else:
                    # Update the existing occ_prefix to set isEnd
                    # The occ_prefix structure: {name: "OccurrenceUsagePrefix", prefix: {name: "BasicUsagePrefix", prefix: ref_prefix, isReference: bool}, ...}
                    basic_prefix = occ_prefix["prefix"]["prefix"]
                    if basic_prefix and basic_prefix["name"] == "RefPrefix":
                        basic_prefix["direction"]["isEnd"] = "end"
                    else:
                        # This should not happen if occ_prefix is not None, but just in case
                        # We'll create a new RefPrefix with the end flag and keep the existing direction if possible?
                        # For simplicity, we'll assume the direction is empty and just set the end flag.
                        ref_prefix = {
                            "name": "RefPrefix",
                            "direction": {
                                "name": "FeatureDirection",
                                "in": "",
                                "out": "",
                                "inout": "",
                                "isEnd": "end"
                            },
                            "isAbstract": None,
                            "isVariation": None,
                            "isReadOnly": None,
                            "isDerived": None
                        }
                        occ_prefix["prefix"]["prefix"] = ref_prefix
            specialization = _build_full_specialization_from_ctx(default_interface_end_ctx)
            return _make_nested_usage_element("PartUsage", name, shortname, occ_prefix, body_items, specialization)
    if hasattr(occ_elem, 'behaviorUsageElement') and occ_elem.behaviorUsageElement():
        behav_elem = occ_elem.behaviorUsageElement()
        # print(f"DEBUG: Found behaviorUsageElement: {behav_elem}")
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
    
    # print(f"DEBUG: No match found in _visit_nested_occurrence_usage")
    # Fall through to check structure usage elements
    
    # Check structure usage elements (part, item, port, interface, connection, etc.)
    if hasattr(occ_elem, 'structureUsageElement') and occ_elem.structureUsageElement():
        struct_elem = occ_elem.structureUsageElement()
        
        if hasattr(struct_elem, 'partUsage') and struct_elem.partUsage():
            ctx = struct_elem.partUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            occ_prefix = _get_occurrence_usage_prefix(ctx)
            specialization = _build_full_specialization_from_ctx(ctx)
            return _make_nested_usage_element("PartUsage", name, shortname, occ_prefix, body_items, specialization)
        elif hasattr(struct_elem, 'itemUsage') and struct_elem.itemUsage():
            ctx = struct_elem.itemUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            occ_prefix = _get_occurrence_usage_prefix(ctx)
            specialization = _build_full_specialization_from_ctx(ctx)
            return _make_nested_usage_element("ItemUsage", name, shortname, occ_prefix, body_items, specialization)
        elif hasattr(struct_elem, 'portUsage') and struct_elem.portUsage():
            ctx = struct_elem.portUsage()
            name, shortname = _get_usage_identification(ctx)
            body_items = _get_usage_body_items(ctx)
            occ_prefix = _get_occurrence_usage_prefix(ctx)
            specialization = _build_full_specialization_from_ctx(ctx)
            return _make_nested_usage_element("PortUsage", name, shortname, occ_prefix, body_items, specialization)
    
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
        specialization = _build_full_specialization_from_ctx(ctx)
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
    
    # Extract name and typed_by from usage -> usageDeclaration -> identification
    name = None
    shortname = None
    typed_by = None
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
                            has_lt = hasattr(ident, 'LT') and ident.LT() is not None
                            if has_lt:
                                shortname = name_text
                            else:
                                name = name_text
        # Extract typed_by from the usage context itself
        typed_by = _get_usage_typed_by(ctx)
    
    specialization = _build_specialization(typed_by)
    
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
                    "specialization": specialization
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
    elif hasattr(def_elem, 'interfaceDefinition') and def_elem.interfaceDefinition():
        return _make_interface_definition_dict(def_elem.interfaceDefinition(), None)
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


def _make_nested_usage_element(usage_type, name, shortname, prefix, body_items=None, specialization=None):
    """Build a nested usage element (not wrapped in PackageMember).
    
    Parameters
    ----------
    specialization : dict or None
        Pre-built FeatureSpecializationPart dict, or None.
    """
    if body_items is None:
        body_items = []
    
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
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                occ_prefix = _get_occurrence_usage_prefix(ctx)
                return _make_nested_usage_element("PartUsage", name, shortname, occ_prefix, body_items=body_items)
            elif hasattr(struct_elem, 'itemUsage') and struct_elem.itemUsage():
                ctx = struct_elem.itemUsage()
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                occ_prefix = _get_occurrence_usage_prefix(ctx)
                return _make_nested_usage_element("ItemUsage", name, shortname, occ_prefix, body_items=body_items)
            elif hasattr(struct_elem, 'portUsage') and struct_elem.portUsage():
                ctx = struct_elem.portUsage()
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                occ_prefix = _get_occurrence_usage_prefix(ctx)
                return _make_nested_usage_element("PortUsage", name, shortname, occ_prefix, body_items=body_items)
        
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
                occ_prefix = _get_occurrence_usage_prefix(ctx)
                return _make_usage_dict("PartUsage", name, shortname, occ_prefix or prefix, structure=True, wrapped=True, body_items=body_items, typed_by=typed_by)
            elif hasattr(struct_elem, 'itemUsage') and struct_elem.itemUsage():
                ctx = struct_elem.itemUsage()
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                typed_by = _get_usage_typed_by(ctx)
                occ_prefix = _get_occurrence_usage_prefix(ctx)
                return _make_usage_dict("ItemUsage", name, shortname, occ_prefix or prefix, structure=True, wrapped=True, body_items=body_items, typed_by=typed_by)
            elif hasattr(struct_elem, 'portUsage') and struct_elem.portUsage():
                ctx = struct_elem.portUsage()
                name, shortname = _get_usage_identification(ctx)
                body_items = _get_usage_body_items(ctx)
                typed_by = _get_usage_typed_by(ctx)
                occ_prefix = _get_occurrence_usage_prefix(ctx)
                return _make_usage_dict("PortUsage", name, shortname, occ_prefix or prefix, structure=True, wrapped=True, body_items=body_items, typed_by=typed_by)
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
            elif hasattr(struct_elem, 'interfaceUsage') and struct_elem.interfaceUsage():
                ctx = struct_elem.interfaceUsage()
                return _make_interface_usage_dict(ctx, prefix)
        
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
    
    qn_names = typed_by.split("::")
    
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
                                            "names": qn_names
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


def _get_multiplicity_part(fsp_ctx):
    """Extract MultiplicityPart dict from featureSpecializationPart context.
    
    Handles [N], [N..M], [*] forms. Returns None if no multiplicity.
    """
    if fsp_ctx is None:
        return None
    
    for child in fsp_ctx.children:
        if type(child).__name__ == 'MultiplicityPartContext':
            mp_ctx = child
            break
    else:
        return None
    
    try:
        omc = mp_ctx.children[0]       # OwnedMultiplicityContext
        omrc = omc.children[0]          # OwnedMultiplicityRangeContext
        bounds = omrc.children[0]       # MultiplicityBoundsContext
        members = [c for c in bounds.children if 'ExpressionMember' in type(c).__name__]
        
        def _make_bound(value_text):
            if value_text == '*':
                return {
                    "name": "MultiplicityExpressionMember",
                    "ownedRelatedElement": [
                        {"name": "MultiplicityRelatedElement", "ownedRelatedElement":
                            {"name": "LiteralInfinity", "value": "*"}
                        }
                    ]
                }
            else:
                return {
                    "name": "MultiplicityExpressionMember",
                    "ownedRelatedElement": [
                        {"name": "MultiplicityRelatedElement", "ownedRelatedElement":
                            {"name": "LiteralInteger", "value": int(value_text)}
                        }
                    ]
                }
        
        if len(members) == 1:
            # [N] or [*]
            bound_dicts = [_make_bound(members[0].getText())]
        elif len(members) == 2:
            # [N..M]
            bound_dicts = [_make_bound(members[0].getText()), _make_bound(members[1].getText())]
        else:
            return None
        
        return {
            "name": "MultiplicityPart",
            "isOrdered": False,
            "isNonunique": False,
            "ownedRelationship": [
                {
                    "name": "OwnedMultiplicity",
                    "ownedRelatedElement": [
                        {
                            "name": "MultiplicityRange",
                            "ownedRelationship": bound_dicts
                        }
                    ]
                }
            ]
        }
    except (IndexError, AttributeError):
        return None


def _build_full_specialization_from_ctx(ctx):
    """Build a full FeatureSpecializationPart dict from a usage ANTLR context.
    
    Extracts all specializations (typings, redefinitions, subsets) from the
    featureSpecializationPart of the usage declaration.
    Returns None if there are no specializations.
    """
    if ctx is None:
        return None
    
    usage = None
    if hasattr(ctx, 'usage') and ctx.usage():
        usage = ctx.usage()
    
    ud = None
    if usage and hasattr(usage, 'usageDeclaration') and usage.usageDeclaration():
        ud = usage.usageDeclaration()
    
    if ud is None:
        return None
    
    fsp = None
    if hasattr(ud, 'featureSpecializationPart') and ud.featureSpecializationPart():
        fsp = ud.featureSpecializationPart()
    
    if fsp is None:
        return None
    
    specs = fsp.featureSpecialization() if hasattr(fsp, 'featureSpecialization') else []
    if not specs:
        return None
    
    if not isinstance(specs, list):
        specs = [specs]
    
    specialization_list = []
    
    for spec in specs:
        # Typings: ': TypeName'
        if hasattr(spec, 'typings') and spec.typings():
            typings = spec.typings()
            # Navigate to the type qualified name
            typed_by = None
            if hasattr(typings, 'typedby') and typings.typedby():
                tb = typings.typedby()
                if hasattr(tb, 'featureType'):
                    for ft in (tb.featureType() if isinstance(tb.featureType(), list) else [tb.featureType()]):
                        if hasattr(ft, 'qualifiedName') and ft.qualifiedName():
                            typed_by = ft.qualifiedName().getText()
                            break
            if typed_by is None:
                # Fallback: extract from typings getText
                t_text = typings.getText()
                if t_text.startswith(':'):
                    typed_by = t_text[1:].strip()
            if typed_by:
                qn_names = typed_by.split("::")
                specialization_list.append({
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
                                            "type": {"name": "QualifiedName", "names": qn_names},
                                            "ownedRelatedElement": []
                                        }
                                    }
                                }
                            ]
                        },
                        "ownedRelationship": []
                    }
                })
        
        # Redefinitions: ':>> name' or 'redefines name'
        elif hasattr(spec, 'redefinitions') and spec.redefinitions():
            redef_ctx = spec.redefinitions()
            redef_names = []
            # RedefinitionsContext → [RedefinesContext, ...] → [OwnedRedefinitionContext, ...] → QualifiedNameContext
            for child in redef_ctx.children:
                child_name = type(child).__name__
                if child_name == 'OwnedRedefinitionContext':
                    for c2 in child.children:
                        if type(c2).__name__ == 'QualifiedNameContext':
                            redef_names.append(c2.getText())
                elif child_name == 'RedefinesContext':
                    for c2 in child.children:
                        if type(c2).__name__ == 'OwnedRedefinitionContext':
                            for c3 in c2.children:
                                if type(c3).__name__ == 'QualifiedNameContext':
                                    redef_names.append(c3.getText())
            if redef_names:
                owned = [
                    {
                        "name": "OwnedRedefinition",
                        "redefinedFeature": {"name": "QualifiedName", "names": n.split("::")},
                        "ownedRelatedElement": []
                    }
                    for n in redef_names
                ]
                specialization_list.append({
                    "name": "FeatureSpecialization",
                    "ownedRelationship": {
                        "name": "Redefinitions",
                        "ownedRelationship": owned
                    }
                })
        
        # Subsettings: ':> name' or 'subsets name'
        elif hasattr(spec, 'subsettings') and spec.subsettings():
            sub_ctx = spec.subsettings()
            sub_names = []
            # SubsettingsContext → [SubsetsContext, ...] → [OwnedSubsettingContext] → QualifiedNameContext
            for child in sub_ctx.children:
                child_name = type(child).__name__
                if child_name == 'OwnedSubsettingContext':
                    for c2 in child.children:
                        if type(c2).__name__ == 'QualifiedNameContext':
                            sub_names.append(c2.getText())
                elif child_name == 'SubsetsContext':
                    for c2 in child.children:
                        if type(c2).__name__ == 'OwnedSubsettingContext':
                            for c3 in c2.children:
                                if type(c3).__name__ == 'QualifiedNameContext':
                                    sub_names.append(c3.getText())
                elif child_name == 'SpecializesContext':
                    for c2 in child.children:
                        if type(c2).__name__ == 'OwnedSubsettingContext':
                            for c3 in c2.children:
                                if type(c3).__name__ == 'QualifiedNameContext':
                                    sub_names.append(c3.getText())
            if sub_names:
                owned = [
                    {
                        "name": "OwnedSubsetting",
                        "subsettedFeature": {"name": "QualifiedName", "names": n.split("::")},
                        "ownedRelatedElement": []
                    }
                    for n in sub_names
                ]
                specialization_list.append({
                    "name": "FeatureSpecialization",
                    "ownedRelationship": {
                        "name": "Subsettings",
                        "ownedRelationship": owned
                    }
                })
    
    if not specialization_list and fsp is None:
        return None
    
    multiplicity = _get_multiplicity_part(fsp)
    
    if not specialization_list and multiplicity is None:
        return None
    
    return {
        "name": "FeatureSpecializationPart",
        "specialization": specialization_list,
        "multiplicity": multiplicity,
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
        # Only look for Typings (': TypeName'), not subsets/redefines/specializes
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
        # NOTE: Do NOT fall back to fsp.getText() — that would return
        # 'redefines X', 'subsets X', or ':> X' which are NOT types.
    
    return None


__all__ = ['parse_to_dict']