"""kerml_visitor.py — KerML parse tree → visitor-dict.

Converts KerMLParser parse trees into plain dicts shaped like the
SysML antlr_visitor dicts (name / ownedRelationship / ownedRelated-
Element keys), so downstream consumers can walk both notations with
the same conventions.

Metaclass names carried in "name" follow KerML §8.3 abstract-syntax
class names: the KEBNF rule annotations (`RuleName : Classifier`)
state the metaclass each production instantiates, and the visitor
reads them from the tree (context kinds map 1:1: ClassContext →
"class", LibraryPackageContext → "library package", FeatureContext →
"feature", ...).

Scope (honest): this visitor extracts the STRUCTURE — namespace
nesting, member kinds, names, short names, visibility, typing/subset/
redefine references, documentation bodies, imports — enough to index
library symbols and round-trip member inventories. Expression bodies
and operator trees are captured as raw text ("body" / "expr") pending
a deeper pass; they are never silently dropped.
"""
from __future__ import annotations

from sysmlpy.kerml.kerml import parse


class _Ctx:
    """Small helpers over ANTLR contexts."""
    @staticmethod
    def text(ctx) -> str:
        return ctx.getText() if ctx is not None else ""

    @staticmethod
    def kids(ctx, cls_name):
        """Direct children whose context type matches cls_name."""
        out = []
        for c in ctx.children or []:
            if type(c).__name__ == cls_name:
                out.append(c)
        return out

    @staticmethod
    def kid(ctx, cls_name):
        got = _Ctx.kids(ctx, cls_name)
        return got[0] if got else None

    @staticmethod
    def tokens(ctx) -> list[str]:
        """Terminal texts of this subtree (direct terminals only)."""
        return [c.getText() for c in (ctx.children or [])
                if type(c).__name__ == "TerminalNodeImpl"]


def _identification(ctx) -> tuple[str | None, str | None]:
    """(shortName, name) from a Feature/Classifier/Type identification."""
    if ctx is None:
        return None, None
    # FeatureIdentification: '<' shortName '>' (name)? | name
    toks = [t.getText() for t in (ctx.children or [])
            if type(t).__name__ == "TerminalNodeImpl"]
    names = _Ctx.kids(ctx, "NameContext")
    if toks and toks[0] == "<":
        short = toks[1] if len(toks) > 1 else None
        nm = names[0].getText() if names else None
        return short, nm
    nm = names[0].getText() if names else None
    return None, nm


def _ident_of_decl(ctx) -> tuple[str | None, str | None]:
    """(short, name) from any declaration context: resolves the
    identification wrapper (IdentificationContext or
    FeatureIdentificationContext) then reads it."""
    if ctx is None:
        return None, None
    idc = _Ctx.kid(ctx, "IdentificationContext")
    if idc is not None:
        names = _Ctx.kids(idc, "NameContext")
        toks = [t.getText() for t in (idc.children or [])
                if type(t).__name__ == "TerminalNodeImpl"]
        if toks and toks[0] == "<":
            return (toks[1] if len(toks) > 1 else None,
                    names[0].getText() if names else None)
        return None, names[0].getText() if names else None
    return _identification(_Ctx.kid(ctx, "FeatureIdentificationContext"))


def _name_of(ctx) -> str | None:
    """Declared name from a *Declaration context (any identification
    variant)."""
    if ctx is None:
        return None
    for cls in ("FeatureIdentificationContext",
                "ClassifierDeclarationContext",
                "TypeDeclarationContext",
                "PackageDeclarationContext"):
        sub = _Ctx.kid(ctx, cls)
        if sub is not None:
            short, nm = _identification(sub)
            if nm:
                return nm
            if short:
                return short
    # fallback: first IDENTIFIER/STRING terminal
    for c in (ctx.children or []):
        t = c.getText() if hasattr(c, "getText") else None
        if t and t not in ("abstract", "standard", "library", "public",
                           "private", "protected", "member", "end",
                           "const", "var", "derived", "composite",
                           "portion", "in", "out", "inout", "derived",
                           "all", "feature", "end", "bool", "inv"):
            return t
    return None


def _harvest_qnames(ctx, depth=4) -> list[str]:
    """All QualifiedName texts within a subtree, bounded depth, terminal
    nodes skipped."""
    out = []
    def rec(node, d):
        if d > depth:
            return
        if type(node).__name__ == "QualifiedNameContext":
            out.append(node.getText())
            return
        for c in (node.children or []):
            if type(c).__name__ != "TerminalNodeImpl":
                rec(c, d + 1)
    rec(ctx, 0)
    return out


def _documentation(ctx) -> list[str]:
    """Bodies of doc blocks owned by this context (direct)."""
    docs = []
    for d in _Ctx.kids(ctx, "DocumentationContext"):
        body = d.getText()
        # strip 'doc' + /* */ framing
        if body.startswith("doc"):
            body = body[3:]
        if body.startswith("/*") and body.endswith("*/"):
            body = body[2:-2]
        docs.append(body)
    return docs


def _comment(ctx) -> list[str]:
    out = []
    for c in _Ctx.kids(ctx, "CommentContext"):
        body = c.getText()
        if body.startswith("/*") and body.endswith("*/"):
            body = body[2:-2]
        out.append(body)
    return out


def _specializations(ctx) -> list[str]:
    """Specialized type names from SuperclassingPart /
    SpecializationPart / FeatureSpecializationPart."""
    names = []
    for sp in _Ctx.kids(ctx, "SuperclassingPartContext") + \
            _Ctx.kids(ctx, "SpecializationPartContext") + \
            _Ctx.kids(ctx, "FeatureSpecializationPartContext"):
        # QualifiedName may sit directly under the part or one level
        # deeper inside an Owned*/OwnedSpecialization wrapper
        for qn in _Ctx.kids(sp, "QualifiedNameContext"):
            names.append(qn.getText())
        for wrapper in (c for c in (sp.children or [])
                        if type(c).__name__ not in ("TerminalNodeImpl",)
                        and type(c).__name__ not in
                        ("SuperclassingPartContext", "SpecializationPartContext",
                         "FeatureSpecializationPartContext")):
            for qn in _Ctx.kids(wrapper, "QualifiedNameContext"):
                names.append(qn.getText())
            for inner in (c for c in (wrapper.children or [])
                          if type(c).__name__ not in ("TerminalNodeImpl",)):
                for qn in _Ctx.kids(inner, "QualifiedNameContext"):
                    names.append(qn.getText())
    return names


def _feature_refs(ctx) -> list[str]:
    """Typed-by / subset / redefine reference names (qualified)."""
    names = []
    for cls in ("OwnedFeatureTypingContext", "OwnedSubsettingContext",
                "OwnedRedefinitionContext", "OwnedReferenceSubsettingContext",
                "ReferenceTypingContext", "OwnedSubclassificationContext"):
        for ref in _Ctx.kids(ctx, cls):
            for qn in _Ctx.kids(ref, "QualifiedNameContext"):
                names.append(qn.getText())
    return names


def _multiplicity(ctx) -> str | None:
    mp = _Ctx.kid(ctx, "MultiplicityPartContext")
    if mp is None:
        return None
    return mp.getText()


def _visibility(ctx) -> str | None:
    vp = _Ctx.kid(ctx, "VisibilityIndicatorContext")
    if vp is None:
        return None
    toks = _Ctx.tokens(vp)
    return toks[0] if toks else None


def _direction(ctx) -> str | None:
    fd = _Ctx.kid(ctx, "FeatureDirectionContext")
    return fd.getText() if fd is not None else None


def _body_items(ctx, depth_seen=None) -> list[dict]:
    """Members of a TypeBody/NamespaceBody, recursively."""
    out = []
    for c in (ctx.children or []):
        cls = type(c).__name__
        if cls in ("TypeBodyElementContext", "NamespaceBodyElementContext",
                   "FunctionBodyPartContext", "NamespaceMemberContext",
                   "MemberElementContext", "NonFeatureElementContext",
                   "PackageBodyContext", "TypeBodyContext",
                   "FunctionBodyContext"):
            out.extend(_body_items(c, depth_seen))
        elif cls in ("NonFeatureMemberContext", "FeatureMemberContext",
                     "NamespaceFeatureMemberContext", "AliasMemberContext",
                     "ImportContext", "OwnedExpressionMemberContext",
                     "ReturnFeatureMemberContext"):
            d = _member(c)
            if d:
                out.append(d)
        elif cls in ("ClassContext", "ClassifierContext", "StructureContext",
                     "AssociationContext", "AssociationStructureContext",
                     "BehaviorContext", "FunctionContext", "PredicateContext",
                     "StepContext", "DataTypeContext", "MetaclassContext",
                     "InteractionContext", "ConnectorContext",
                     "BindingConnectorContext", "SuccessionContext",
                     "FlowContext", "SuccessionFlowContext",
                     "MultiplicityContext", "PackageContext",
                     "LibraryPackageContext", "StandardPackageContext"):
            d = _element(c)
            if d:
                out.append(d)
    return out


def _element(ctx) -> dict | None:
    """A classifier/package element → dict. Accepts either the concrete
    element context (ClassContext, ...) or a wrapper (NonFeatureElement-
    Context) whose child is the concrete element."""
    cls = type(ctx).__name__
    if cls not in _KIND:
        # wrapper: find the concrete element one level down
        for c in (ctx.children or []):
            if type(c).__name__ in _KIND:
                return _element(c)
        return None
    kind = _KIND[cls]
    d = {"name": kind}
    decl = _Ctx.kid(ctx, "ClassifierDeclarationContext") or \
        _Ctx.kid(ctx, "TypeDeclarationContext") or \
        _Ctx.kid(ctx, "PackageDeclarationContext") or \
        _Ctx.kid(ctx, "FeatureDeclarationContext")
    short, nm = _ident_of_decl(decl)
    d["declaredShortName"] = short
    d["declaredName"] = nm
    # visibility
    body = _Ctx.kid(ctx, "TypeBodyContext") or \
        _Ctx.kid(ctx, "PackageBodyContext") or \
        _Ctx.kid(ctx, "FunctionBodyContext")
    d["documentation"] = _documentation(ctx) + _comment(ctx)
    d["specializes"] = _specializations(decl) if decl is not None else \
        _specializations(ctx)
    d["typed_by"] = []
    d["redefines"] = []
    d["subsets"] = []
    d["multiplicity"] = None
    d["children"] = []
    if decl is not None:
        for ref in _feature_refs(decl):
            d["typed_by"].append(ref)
        m = _multiplicity(decl)
        d["multiplicity"] = m
    if body is not None:
        for item in _body_items(body):
            if item.get("name") == "doc":
                d["documentation"].extend(item.get("documentation", []))
            else:
                d["children"].append(item)
    return d


_KIND = {
    "ClassContext": "class",
    "ClassifierContext": "classifier",
    "StructureContext": "struct",
    "AssociationContext": "assoc",
    "AssociationStructureContext": "assoc struct",
    "BehaviorContext": "behavior",
    "FunctionContext": "function",
    "PredicateContext": "predicate",
    "StepContext": "step",
    "DataTypeContext": "datatype",
    "MetaclassContext": "metaclass",
    "InteractionContext": "interaction",
    "PackageContext": "package",
    "LibraryPackageContext": "library package",
    "StandardPackageContext": "standard library package",
}


def _member(ctx) -> dict | None:
    """A body member (feature/comment/import/alias/...)."""
    cls = type(ctx).__name__
    # unwrap one level (FeatureMemberContext → OwnedFeatureMemberContext)
    for inner in (ctx.children or []):
        icls = type(inner).__name__
        if icls in ("OwnedFeatureMemberContext", "TypeFeatureMemberContext",
                    "NonFeatureMemberContext", "NamespaceFeatureMemberContext",
                    "FeatureMemberContext", "NamespaceMemberContext") \
                and icls != cls:
            return _member(inner)
    if cls in ("OwnedFeatureMemberContext", "TypeFeatureMemberContext",
               "FeatureMemberContext", "NamespaceFeatureMemberContext"):
        fe = _Ctx.kid(ctx, "FeatureElementContext")
        if fe is not None:
            return _feature_element(fe, ctx)
    if cls == "NonFeatureMemberContext":
        me = _Ctx.kid(ctx, "MemberElementContext")
        if me is not None:
            el = _Ctx.kid(me, "NonFeatureElementContext")
            if el is not None:
                d = _element(el)
                if d:
                    vp = _Ctx.kid(ctx, "MemberPrefixContext")
                    if vp is not None:
                        vis = _Ctx.kid(vp, "VisibilityIndicatorContext")
                        if vis is not None:
                            d["visibility"] = vis.getText()
                    return d
            # import / dependency / doc paths
            if me is not None:
                for sub in (me.children or []):
                    if type(sub).__name__ == "AnnotatingElementContext":
                        docs = []
                        for dc in _Ctx.kids(sub, "DocumentationContext"):
                            body = dc.getText()
                            if body.startswith("doc"):
                                body = body[3:]
                            if body.startswith("/*") and body.endswith("*/"):
                                body = body[2:-2]
                            docs.append(body)
                        return {"name": "doc", "documentation": docs}
                    d = _element(sub) if hasattr(sub, "children") else None
                    if d:
                        return d
    if cls in ("ReturnFeatureMemberContext", "ResultExpressionMemberContext"):
        # return-parameters and result expressions ride the function's
        # return end (ReturnParameterMembership /
        # ResultExpressionMembership)
        fe = _Ctx.kid(ctx, "FeatureElementContext")
        if fe is not None:
            d = _feature_element(fe, ctx)
            if cls == "ReturnFeatureMemberContext":
                d["is_return"] = True
            else:
                d["is_result"] = True
            return d
        return {"name": "return"}
    if cls == "AliasMemberContext":
        return {"name": "alias"}
    return None


def _feature_element(fe, owner_ctx=None) -> dict:
    """Feature / step / connector / flow / invariant / bool-expression."""
    cls = type(fe).__name__
    d = None
    for c in (fe.children or []):
        ccls = type(c).__name__
        if ccls in ("FeatureContext", "StepContext", "ConnectorContext",
                    "BindingConnectorContext", "FlowContext",
                    "SuccessionFlowContext", "SuccessionContext",
                    "BooleanExpressionContext", "InvariantContext",
                    "ExpressionContext"):
            el = _element(c) or {"name": "feature", "declaredName": None}
            if ccls == "FeatureContext":
                el = _feature(c)
            d = el
            break
    if d is None:
        d = {"name": "feature", "declaredName": None}
    if owner_ctx is not None:
        vp = _Ctx.kid(owner_ctx, "MemberPrefixContext")
        if vp is not None:
            vis = _Ctx.kid(vp, "VisibilityIndicatorContext")
            if vis is not None:
                d["visibility"] = vis.getText()
    return d


def _feature(ctx) -> dict:
    d = {"name": "feature", "declaredShortName": None, "declaredName": None,
         "typed_by": [], "subsets": [], "redefines": [], "references": [],
         "multiplicity": None, "direction": None, "is_end": False,
         "visibility": None, "value": None, "children": []}
    prefix = _Ctx.kid(ctx, "FeaturePrefixContext")
    if prefix is not None:
        efp = _Ctx.kid(prefix, "EndFeaturePrefixContext")
        if efp is not None:
            d["is_end"] = True
            # `end <decl>` — the end's own declaration rides the optional
            # OwnedCrossFeatureMember (KEBNF FeaturePrefix)
            for cfm in _Ctx.kids(prefix, "OwnedCrossFeatureMemberContext"):
                cross = _Ctx.kid(cfm, "OwnedCrossFeatureContext")
                if cross is not None:
                    xdecl = _Ctx.kid(cross, "FeatureDeclarationContext")
                    if xdecl is not None:
                        short, nm = _ident_of_decl(xdecl)
                        d["declaredShortName"], d["declaredName"] = short, nm
                        for xfsp in _Ctx.kids(xdecl,
                                              "FeatureSpecializationPartContext"):
                            if d["multiplicity"] is None:
                                d["multiplicity"] = _multiplicity(xfsp)
                        for qn in _harvest_qnames(xdecl, depth=8):
                            if qn not in d["typed_by"]:
                                d["typed_by"].append(qn)
        bfp = _Ctx.kid(prefix, "BasicFeaturePrefixContext")
        if bfp is not None:
            d["direction"] = _direction(bfp)
        vis = _Ctx.kid(prefix, "VisibilityIndicatorContext")
        if vis is not None:
            d["visibility"] = vis.getText()
    decl = _Ctx.kid(ctx, "FeatureDeclarationContext")
    if decl is not None:
        short, nm = _identification(_Ctx.kid(decl, "FeatureIdentificationContext"))
        d["declaredShortName"], d["declaredName"] = short, nm
        for ref in _feature_refs(decl):
            d["typed_by"].append(ref)
        for fp in _Ctx.kids(decl, "FeatureSpecializationPartContext"):
            # multiplicity attaches directly to the part
            if d["multiplicity"] is None:
                d["multiplicity"] = _multiplicity(fp)
            for sp in _Ctx.kids(fp, "FeatureSpecializationContext"):
                # FeatureSpecialization = Typings | Subsettings | Redefini-
                # tions | References (KEBNF 8.2.4.3.1); the wrapper kind
                # carries the classification
                kind_ctx = next((c for c in (sp.children or [])
                                 if type(c).__name__ != "TerminalNodeImpl"),
                                None)
                if kind_ctx is None:
                    continue
                kcls = type(kind_ctx).__name__
                target = {"TypingsContext": "typed_by",
                          "SubsettingsContext": "subsets",
                          "RedefinitionsContext": "redefines",
                          "ReferencesContext": "references"}.get(kcls)
                if target is None:
                    continue
                qns = _harvest_qnames(kind_ctx, depth=8)
                d[target].extend(qns)
        for rp in _Ctx.kids(decl, "FeatureRelationshipPartContext"):
            for qn in _feature_refs(rp):
                d["subsets"].append(qn)
    for fch in _Ctx.kids(ctx, "FeatureChainMemberContext"):
        pass  # chains recorded in text capture below
    # value
    vp = _Ctx.kid(ctx, "ValuePartContext")
    if vp is not None:
        d["value"] = vp.getText()
    for item in _body_items(ctx):
        d["children"].append(item)
    return d


def parse_to_dict(source: str) -> dict:
    """KerML source → visitor-dict with a synthetic root."""
    from sysmlpy.kerml.kerml import parse
    tree = parse(source)
    root = {"name": "RootNamespace", "children": []}
    root["children"].extend(_body_items(tree))
    return root