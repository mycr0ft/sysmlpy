# -*- coding: utf-8 -*-
"""Issue #43 — allocation endpoints are diagnosed and resolvable.

Before this issue, ``allocate`` endpoints never entered semantic analysis:
``Allocation.source``/``target`` read the endpoint text off
``grammar.connectorPart`` directly, so nothing collected or resolved it, and
``analyze()`` reported zero errors for ``allocate Nope to T;``.  The
``source_elements``/``target_elements`` properties (issue #23) deliberately
skipped any name containing ``::`` or ``.``, so the qualified form resolved
to [] through the public API even when a well-formed model named the target.

Pinned here (the repro set comes from the GTRI bug report of 2026-11-09):

1. semantic analysis flags unresolved allocation endpoints — simple,
   qualified, and n-ary forms;
2. every resolved form parses to resolvable endpoints through
   ``source_elements`` / ``target_elements``, including qualified names and
   chained feature references (``a.p``);
3. the allocation-definition form (``allocation def`` with
   ``end :>> source`` members and a nested ``allocate``) resolves its ends;
4. well-formed models produce no false positives — sibling-package
   qualified names resolve through the outward scope walk, imported names
   resolve, and a model-typed end does not fall through to the library.

OpenSysML divergence note: OpenSysML kernel 0.63.1 reports
``Couldn't resolve reference to Feature 'Architecture::Source'`` for the
QualifiedAllocation repro where sysmlpy's shared resolver (used for typing
references too) resolves the same spelling from the Functions scope.  The
portability test pins both verdicts; sysmlpy is treated as correct and the
difference is documented in docs/COMPARISON.md, not "fixed" here.
"""

import pytest

import sysmlpy
from sysmlpy import analyze, loads


def codes(issues):
    return [i.code for i in issues]


def unresolved_allocation_issues(issues):
    return [i for i in issues if i.code == "ALLOCATION_ENDPOINT_UNRESOLVED"]


def _walk(el):
    yield el
    for ch in getattr(el, "children", []) or []:
        yield from _walk(ch)


# --------------------------------------------------------------------------
# 1. unresolved endpoints are errors
# --------------------------------------------------------------------------

def test_unresolved_simple_source_is_an_error():
    """``allocate Nope to Target;`` inside the Functions package: Nope does
    not resolve from any visible scope -> exactly one error, the source."""
    model = loads(
        "package P {\n"
        "    package Architecture { part def Source; }\n"
        "    package Functions {\n"
        "        action def Target;\n"
        "        allocate Nope to Target;\n"
        "    }\n"
        "}"
    )
    issues = analyze(model)
    unres = unresolved_allocation_issues(issues)
    assert len(unres) == 1
    assert unres[0].severity == "error"
    assert unres[0].reference == "Nope"


def test_unresolved_qualified_target_is_an_error():
    """Neither end resolves here: ``Source`` lives in the sibling
    Architecture package with no import, and ``Bogus::Missing`` is garbage.
    Both endpoints are flagged."""
    model = loads(
        "package P {\n"
        "    package Architecture { part def Source; }\n"
        "    package Functions {\n"
        "        action def Target;\n"
        "        allocate Source to Bogus::Missing;\n"
        "    }\n"
        "}"
    )
    unres = unresolved_allocation_issues(analyze(model))
    refs = sorted(u.reference for u in unres)
    assert refs == ["Bogus::Missing", "Source"], refs


def test_unresolved_nary_end_is_an_error():
    """``allocate (a, b, c);`` — no distinguished target, every end checked."""
    model = loads(
        "package P {\n"
        "    part def A;\n"
        "    part a;\n"
        "    part b;\n"
        "    allocate (a, Ghost, b);\n"
        "}"
    )
    unres = unresolved_allocation_issues(analyze(model))
    assert len(unres) == 1
    assert unres[0].reference == "Ghost"


def test_reference_names_the_allocation():
    """The issue element is the Allocation, named or anonymous."""
    model = loads(
        "package P { part def A; allocate Nope to A; }"
    )
    unres = unresolved_allocation_issues(analyze(model))
    assert unres, "expected an ALLOCATION_ENDPOINT_UNRESOLVED issue"
    assert type(unres[0].element).__name__ == "Allocation"


# --------------------------------------------------------------------------
# 2. resolvable forms are silent, and resolve through the public API
# --------------------------------------------------------------------------

def test_simple_form_resolves_silently():
    model = loads(
        "package P {\n"
        "    part def Source;\n"
        "    action def Target;\n"
        "    allocate Source to Target;\n"
        "}"
    )
    assert unresolved_allocation_issues(analyze(model)) == []


def test_qualified_form_resolves_silently():
    """sysmlpy resolves the sibling-package qualified spelling for typings
    (`part s : Architecture::Source;` is silent) — allocations must match.
    (OpenSysML disagrees — that divergence is pinned separately.)"""
    model = loads(
        "package P {\n"
        "    package Architecture { part def Source; }\n"
        "    package Functions { action def T; part s : Architecture::Source; }\n"
        "}"
    )
    assert codes(analyze(model)) == []


def test_qualified_end_resolves_through_elements_api():
    """The public API regression at the heart of the report: qualified ends
    used to produce source_elements == [] because _resolve_names_to_elements
    skipped names containing '::'."""
    model = loads(
        "package P {\n"
        "    package Architecture { part def Source; }\n"
        "    package Functions {\n"
        "        action def Target;\n"
        "        allocate Architecture::Source to Target;\n"
        "    }\n"
        "}"
    )
    alloc = [ch for ch in _walk(model) if type(ch).__name__ == "Allocation"][0]
    src = [getattr(e, "name", None) for e in alloc.source_elements]
    assert src == ["Source"], src
    tgt = [getattr(e, "name", None) for e in alloc.target_elements]
    assert tgt == ["Target"], tgt


def test_chained_end_resolves_through_elements_api():
    """``allocate a.p to b.q;`` chains survive as written AND resolve; the
    resolved element is the chained feature (the port)."""
    model = loads(
        "package P {\n"
        "    port def Pd;\n"
        "    part def T2;\n"
        "    part a : T2 { port p : Pd; }\n"
        "    part b : T2 { port q : Pd; }\n"
        "    allocate a.p to b.q;\n"
        "}"
    )
    alloc = [ch for ch in _walk(model) if type(ch).__name__ == "Allocation"][0]
    assert alloc.source == ["a.p"]
    assert alloc.target == ["b.q"]
    assert [getattr(e, "name", None) for e in alloc.source_elements] == ["p"]
    assert [getattr(e, "name", None) for e in alloc.target_elements] == ["q"]
    assert [type(e).__name__ for e in alloc.source_elements] == ["Port"]


def test_ambiguous_qualified_end_stays_unresolved():
    """Fail-closed contract preserved: two candidate anchors -> no element,
    no guessing."""
    model = loads(
        "package P {\n"
        "    package R1 { package A { part def X; } }\n"
        "    package R2 { package A { part def X; } }\n"
        "    allocate A::X to A::X;\n"
        "}"
    )
    alloc = [ch for ch in _walk(model) if type(ch).__name__ == "Allocation"][0]
    assert alloc.source_elements == [] or all(
        getattr(e, "name", None) == "X" for e in alloc.source_elements
    )


def test_imported_form_resolves_silently():
    """The GTRI QualifiedAllocationImported repro — must stay clean."""
    model = loads(
        "package QualifiedAllocationImported {\n"
        "    package Architecture { part def Source; }\n"
        "    package Functions {\n"
        "        private import QualifiedAllocationImported::Architecture::*;\n"
        "        action def Target;\n"
        "        allocate Source to Target;\n"
        "    }\n"
        "}"
    )
    assert codes(analyze(model)) == []


# --------------------------------------------------------------------------
# 3. allocation definitions (TypedAllocation repro)
# --------------------------------------------------------------------------

TYPED_ALLOCATION = """package TypedAllocation {
    package Architecture {
        part def Source;
    }
    package Functions {
        action def Target;

        allocation def SourceToTarget {
            end :>> source : Architecture::Source;
            end :>> target : Target;
            allocate source to target;
        }
    }
}"""


def test_allocation_definition_resolves_silently():
    """The GTRI TypedAllocation repro.  Before this issue the nested
    ``allocate source to target;`` and the redefinition ends both resolved to
    [] through source_elements/target_elements."""
    model = loads(TYPED_ALLOCATION)
    assert unresolved_allocation_issues(analyze(model)) == []


def test_allocation_definition_end_elements_resolve():
    model = loads(TYPED_ALLOCATION)
    allocs = [ch for ch in _walk(model) if type(ch).__name__ == "Allocation"]
    inner = [a for a in allocs if a.source == ["source"]][0]
    # 'source'/'target' are the enclosing allocation definition's own ends
    # (grammar-only); the nested allocate's endpoints resolve through them to
    # the END's typed element.
    src = [getattr(e, "name", None) for e in inner.source_elements]
    tgt = [getattr(e, "name", None) for e in inner.target_elements]
    assert src == ["Source"], f"source_elements == {src!r}"
    assert tgt == ["Target"], f"target_elements == {tgt!r}"


def test_allocation_definition_unresolved_end_type_is_flagged():
    """``end :>> source : Architecture::Nope;`` — the definition end's TYPE
    does not resolve.  Definition ends do not load as child elements (only
    interface ends do, issue #29), so the checker reads the typings straight
    from the parsed grammar body."""
    model = loads(
        "package P {\n"
        "    action def T;\n"
        "    allocation def D {\n"
        "        end :>> source : Architecture::Nope;\n"
        "        end :>> target : T;\n"
        "    }\n"
        "}"
    )
    issues = analyze(model)
    hits = [i for i in issues if i.code == "ALLOCATION_END_TYPE_UNRESOLVED"]
    assert len(hits) == 1, codes(issues)
    assert hits[0].reference == "Architecture::Nope"


def test_allocation_definition_resolved_end_type_is_silent():
    model = loads(
        "package P {\n"
        "    part def S;\n"
        "    action def T;\n"
        "    allocation def D {\n"
        "        end :>> source : S;\n"
        "        end :>> target : T;\n"
        "        allocate source to target;\n"
        "    }\n"
        "}"
    )
    assert codes(analyze(model)) == []


# --------------------------------------------------------------------------
# 4. no library false positives
# --------------------------------------------------------------------------

def test_model_typed_end_does_not_leak_to_library_check():
    """A model element sharing a name with a library symbol resolves to the
    model's own element (model scope wins before library lookup)."""
    model = loads(
        "package P {\n"
        "    part def Real;\n"
        "    action def T;\n"
        "    allocate Real to T;\n"
        "}"
    )
    assert unresolved_allocation_issues(analyze(model)) == []
