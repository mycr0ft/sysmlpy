#!/usr/bin/env python3
"""KerML v1.0 parser module — ANTLR4-based, sibling of antlr_parser.py.

Parses KerML textual notation (the Kernel Modeling Language, OMG KerML
v1.0) into ANTLR parse trees. The grammar was generated from the OMG
KerML KEBNF (bnf/KerML-textual-bnf.kebnf in Systems-Modeling/
SysML-v2-Release, 2026-08 checkout) with the daltskin sysml-v2-grammar
generator in KerML-only mode.

Corpus corrections applied after generation (each follows OMG's own
published examples over the KEBNF text — the same KEBNF-vs-example
inconsistency class OMG tracks as issue SYSML21-669; all verified
against the OMG corpus: kerml/src/examples 58/58, kernel libraries
36/36, sysmlpy bundled kernel 36/36):

1. Fix 52 of the upstream generator drops rules it deems unreachable in
   the merged SysML grammar; six are still reachable in pure KerML and
   were re-added: featureReferenceMember, ownedFeatureChainMember,
   flowFeatureMember, featureReference, ownedFeatureChain, flowFeature.
2. `definitionBodyItem` (a sysml-side alias) → TypeBodyElement.
3. FeaturePrefix: the OwnedCrossFeatureMember after an EndFeaturePrefix
   is OPTIONAL in the KEBNF — restored (`end feature X;` without a
   cross member is used by TransitionPerformances.kerml).
4. Invariant / BooleanExpression: FeatureDeclaration made OPTIONAL
   (`inv { ... }`, `end bool X;` — used by the OMG Individuals and
   TransitionPerformances examples).
5. FlowFeature: accepts a bare qualifiedName (`flow a.y to b.x1;`).
6. FunctionOperationExpression (ARROW): the trailing reference after
   the function name is a FeatureReference by qualified name
   (`->reduce '+'`), and the body/argument part is mandatory.
7. CollectExpression shorthand: `x.{in xx; xx+1}` — DOT (not just
   DOT_QUESTION) may be followed by a bodyExpression.

Public API:
    parse(source)             → KerMLParser.rootNamespaceContext tree
    parse_file(path)          → parse a .kerml file
    parse_to_dict(source)     → visitor-dict (name-keyed, SysML-shaped)
"""
from __future__ import annotations

import os
import sys

from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from sysmlpy.kerml.KerMLLexer import KerMLLexer
from sysmlpy.kerml.KerMLParser import KerMLParser


class KerMLSyntaxError(Exception):
    """Exception raised for KerML syntax errors."""


class _ErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"Syntax error at {line}:{column}: {msg}")

    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex,
                        exact, ambigAlts, configs):
        pass

    def reportAttemptingFullContext(self, recognizer, dfa, startIndex,
                                    stopIndex, conflictingAlts, configs):
        pass

    def reportContextSensitivity(self, recognizer, dfa, startIndex,
                                 stopIndex, prediction, configs):
        pass


def _make_parser(content):
    lexer = KerMLLexer(InputStream(content))
    stream = CommonTokenStream(lexer)
    return KerMLParser(stream)


def parse(source, prediction_mode="sll"):
    """Parse KerML source text, returning the rootNamespace parse tree.

    Raises KerMLSyntaxError on syntax errors (message carries all
    listener errors, one per line).
    """
    lexer = KerMLLexer(InputStream(source))
    stream = CommonTokenStream(lexer)
    parser = KerMLParser(stream)
    listener = _ErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    if prediction_mode == "sll":
        parser._interp.predictionMode = 1  # PredictionMode.SLL
    tree = parser.rootNamespace()
    if listener.errors:
        raise KerMLSyntaxError("\n".join(listener.errors))
    return tree


def parse_file(filepath):
    """Parse a .kerml file, returning the rootNamespace parse tree."""
    with open(filepath, encoding="utf-8") as fh:
        return parse(fh.read())


def parse_to_dict(source):
    """Parse KerML source into a visitor-dict tree (SysML-shaped).

    The dict mirrors the shapes antlr_visitor.parse_to_dict produces for
    SysML so downstream consumers can treat both notations uniformly:
    packages nest via "ownedRelationship"/"ownedRelatedElement" and
    classifiers/features carry their KerML metaclass names as "name".
    """
    from sysmlpy.kerml.kerml_visitor import parse_to_dict as _to_dict
    return _to_dict(source)