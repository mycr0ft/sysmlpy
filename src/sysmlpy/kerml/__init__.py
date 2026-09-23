"""KerML parsing package: ANTLR4 grammar + parser + visitor-dict.

Generated from the OMG KerML textual-notation KEBNF; see kerml.py for
provenance and the corpus-correction notes.
"""
from sysmlpy.kerml.kerml import (
    KerMLSyntaxError,
    parse,
    parse_file,
    parse_to_dict,
)

__all__ = [
    "KerMLSyntaxError",
    "parse",
    "parse_file",
    "parse_to_dict",
]