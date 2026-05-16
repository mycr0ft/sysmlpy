#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SysML v2 Python Library

A pure Python implementation for parsing SysML v2.0 models.
Uses the ANTLR4 parser for full SysML v2 grammar support.
"""

__all__ = [
    "load", "loads", "load_grammar", "load_antlr", "load_grammar_antlr",
    "Searchable",
]
__author__ = "Jon Fox"
__version__ = "0.10.0"

from sysml2py.usage import (
    Item, Attribute, Part, Port, Action, Reference, UseCase, Requirement, Interface, Message,
    State, Constraint, Connection, Flow, Calculation, Enumeration,
    Allocation, Metadata, Rendering, Individual, FlowDef,
    View, Viewpoint, Concern,
    Case, AnalysisCase, VerificationCase,
)

from sysml2py.definition import Model, Package
from sysml2py.navigate import Searchable

from sysml2py.usage import ureg


def load_grammar(s, debug=False):
    """SysML load from string to dictionary

    Deserialize a string containing a SysML v2.0 document to a Python dictionary.

    Parameters
    ----------
    s : str or _io.TextIOWrapper
        String instance of SysML v2.0 document or file pointer

    Returns
    -------
    dict
        Dictionary version structured utilizing SysML v2.0 grammar

    Raises
    ------
    TypeError
        Input was not str or file
    """
    import sysml2py.antlr_visitor as antlr_visitor
    import sysml2py.antlr_parser as antlr_parser
    import io

    # Handle file pointer or string
    if isinstance(s, io.TextIOWrapper):
        s = s.read()
    elif not isinstance(s, str):
        raise TypeError(
            f"the SysML object must be str or file, not {s.__class__.__name__}"
        )

    # Wrap in package if not starting with 'package' for parsing
    s_stripped = s.strip()
    needs_unwrap = not s_stripped.startswith('package')
    if needs_unwrap:
        s = f'package __implicit__ {{ {s_stripped} }}'

    try:
        result = antlr_visitor.parse_to_dict(s)
        
        # If we wrapped, we need to return a format compatible with what the tests expect
        # The grammar classes expect "PackageBodyElement" as the top-level name
        if needs_unwrap:
            # Navigate to Package body ownedRelationship
            pkg_member = result['ownedRelationship'][0]
            pkg_elem = pkg_member['ownedRelatedElement']
            pkg = pkg_elem['ownedRelatedElement']
            body = pkg['body']
            
            # Return in PackageBodyElement format (no Package wrapper)
            return {
                "name": "PackageBodyElement",
                "ownedRelationship": body['ownedRelationship']
            }
        
        return result
    except antlr_parser.SysMLSyntaxError as e:
        print("ANTLR4 returned the following error: {}".format(e))
        raise


def load(fp):
    """SysML load from file pointer

    Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a SysML v2.0 document) to a Python dictionary object.

    Parameters
    ----------
    fp : _io.TextIOWrapper
        File pointer to SysML v2.0 document

    Returns
    -------
    dict
        Dictionary version structured utilizing SysML v2.0 grammar

    Raises
    ------
    TypeError
        Input was not _io.TextIOWrapper
    """
    import io

    if not isinstance(fp, io.TextIOWrapper):
        raise TypeError(
            f"the SysML object must be _io.TextIOWrapper, "
            f"not {fp.__class__.__name__}"
        )

    return loads(fp.read())


def loads(s: str, library=None):
    """Loads a model from string.

    This shortcut function allows a user to build a model from a string by
    first instantiating a base model class which builds out a default namespace
    and then that model loads all elements underneath.

    Uses the ANTLR4 parser.

    Parameters
    ----------
    s : str
        The SysML v2 source code to parse.
    library : str or Path, optional
        Path to SysML v2 library files for resolving imports.
    """
    return Model().load(s, library=library)


def load_grammar_antlr(fp, debug=False, library=None):
    """SysML load from file pointer using ANTLR4 parser.

    Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a SysML v2.0 document) or ``s`` (a ``str`` instance containing a SysML
    v2.0 document) to a Python dictionary object using the ANTLR4 parser.

    Parameters
    ----------
    fp : _io.TextIOWrapper or str
        File pointer to SysML v2.0 document or string instance of SysML v2.0
        document
    debug : bool
        Enable debug output.
    library : str or Path, optional
        Path to SysML v2 library files for resolving imports.

    Returns
    -------
    dict
        Dictionary version structured utilizing SysML v2.0 grammar

    Raises
    ------
    TypeError
        Input was not _io.TextIOWrapper or str

    """
    import io
    import sysml2py.antlr_visitor as antlr_visitor
    import sysml2py.antlr_parser as antlr_parser

    if isinstance(fp, io.TextIOWrapper):
        s = fp.read()
    elif isinstance(fp, str):
        s = fp
    else:
        raise TypeError(
            f"the SysML object must be _io.TextIOWrapper or str "
            f"not {fp.__class__.__name__}"
        )

    try:
        return antlr_visitor.parse_to_dict(s, library=library)
    except antlr_parser.SysMLSyntaxError as e:
        print("ANTLR4 returned the following error: {}".format(e))
        raise


def load_antlr(fp):
    """SysML load from file pointer using ANTLR4 parser.

    Deserialize ``fp`` (a ``.read()``-supporting file-like object containing
    a SysML v2.0 document) to a Python dictionary object.

    Parameters
    ----------
    fp : _io.TextIOWrapper
        File pointer to SysML v2.0 document

    Returns
    -------
    dict
        Dictionary version structured utilizing SysML v2.0 grammar

    Raises
    ------
    TypeError
        Input was not _io.TextIOWrapper
    """
    import io

    if not isinstance(fp, io.TextIOWrapper):
        raise TypeError(
            f"the SysML object must be _io.TextIOWrapper, "
            f"not {fp.__class__.__name__}"
        )

    return loads(fp.read())


