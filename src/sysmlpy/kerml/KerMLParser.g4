/*
 * KerML v1.0 ANTLR4 grammar (parser).
 *
 * Generated from the OMG KerML textual-notation KEBNF
 * (Systems-Modeling/SysML-v2-Release, bnf/KerML-textual-bnf.kebnf,
 * 2026-08 checkout / Release 2026-07 edition) using the daltskin
 * sysml-v2-grammar generator in KerML-only mode, plus 7 documented
 * corrections applied during corpus bring-up (see kerml.py module
 * docstring). MIT license, same as the generator upstream.
 */

parser grammar KerMLParser;

options {
    tokenVocab = KerMLLexer;
}