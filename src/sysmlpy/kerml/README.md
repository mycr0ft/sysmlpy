# KerML grammar — provenance and corpus corrections

Source grammar: OMG KerML textual-notation KEBNF
(`bnf/KerML-textual-bnf.kebnf` from
[Systems-Modeling/SysML-v2-Release](https://github.com/Systems-Modeling/SysML-v2-Release),
2026-08 checkout / Release 2026-07 edition, commit `fb97b75`).

Generation: the [daltskin/sysml-v2-grammar](https://github.com/daltskin/sysml-v2-grammar)
generator (`scripts/generate_grammar.py`, MIT) run in **KerML-only mode**
(KerML KEBNF only; no SysML merge), producing `KerMLLexer.g4` and
`KerMLParser.g4` (929 parser rules-worth of productions; 80 KEBNF
productions, 44 KerML-only keywords).

## Corpus corrections (each verified against the OMG .kerml corpus:
kerml/src/examples 58/58, sysml.library/Kernel Libraries 36/36,
sysmlpy bundled kernel 36/36 — 130/130)

Each follows OMG's own published examples over the BNF text — the same
KEBNF-vs-example inconsistency class OMG tracks as issue SYSML21-669:

1. **Generator Fix 52 reverts** — the upstream dead-rule list drops six
   rules that are still reachable in pure KerML and were re-added:
   `featureReferenceMember`, `ownedFeatureChainMember`,
   `flowFeatureMember`, `featureReference`, `ownedFeatureChain`,
   `flowFeature`.
2. `definitionBodyItem` → `TypeBodyElement` (sysml-side alias name).
3. `featurePrefix`: the `OwnedCrossFeatureMember` after an
   `EndFeaturePrefix` is OPTIONAL per the KEBNF — restored (`end
   feature X;` without a cross member, used by
   `TransitionPerformances.kerml`).
4. `invariant` / `booleanExpression`: `featureDeclaration` made OPTIONAL
   (`inv { ... }`, `end bool X;` — OMG Individuals examples).
5. `flowFeature`: accepts a bare qualifiedName (`flow a.y to b.x1;`).
6. ARROW (FunctionOperationExpression): the trailing reference after the
   function name is a FeatureReference by qualified name
   (`->reduce '+'`), and body/argument is mandatory.
7. CollectExpression shorthand: `x.{in xx; xx+1}` — DOT (not just
   DOT_QUESTION) may be followed by a bodyExpression.

## Regeneration

Re-run the daltskin generator with `bnf_files: {kerml: ...}` only, then
re-apply items 1–7 above. The generated Python files
(`KerMLLexer.py`, `KerMLParser.py`) are ANTLR 4.13.1,
`-Dlanguage=Python3 -no-listener -visitor`.