# -*- coding: utf-8 -*-
"""Issue #44 — connectors and interfaces need two related elements.

OpenSysML's constraint pass treats a concrete association or connector with
fewer than two related elements as an error — ``internal/core/passes/
w10b_related_elements.go`` (KerML 1.1 §8.3.3.5, §8.3.4.7), message
``Must have at least two related elements``.  sysmlpy reported nothing for
the GTRI one-sided interface repro:

    interface def OneSidedInterface { item payload : Payload; }

Pinned here, mirroring the reference's exemptions as implemented upstream:

1. zero-end and one-end interface definitions are errors (message verbatim);
2. two ends are fine, and so are abstract and variation definitions (their
   ends arrive through specialization);
3. one-sided connectors and one-sided bindings follow the same rule — a
   binding connector must bind exactly two features;
4. a one-item interface inside a larger model is flagged at the interface,
   not as collateral elsewhere (the GTRI CCMM shape);
5. the message matches OpenSysML verbatim, so cross-tool runs diff cleanly.
"""

import pytest

import sysmlpy
from sysmlpy import analyze, loads

MSG = "Must have at least two related elements"


def related_issues(issues):
    return [i for i in issues if i.code == "RELATED_ELEMENTS"]


def binding_issues(issues):
    return [i for i in issues if i.code == "BINDING_CONNECTOR_BINARY"]


# --------------------------------------------------------------------------
# 1. interface definitions
# --------------------------------------------------------------------------

def test_zero_end_interface_is_an_error():
    model = loads("package P { interface def I { } }")
    unres = related_issues(analyze(model))
    assert len(unres) == 1
    assert unres[0].severity == "error"
    assert unres[0].message == MSG
    assert type(unres[0].element).__name__ == "Interface"


def test_one_end_interface_is_an_error():
    """The GTRI SingleItemInterface repro."""
    model = loads(
        "package SingleItemInterface {\n"
        "    item def Payload;\n"
        "    interface def OneSizedInterface {\n"
        "        item payload : Payload;\n"
        "    }\n"
        "}"
    )
    unres = related_issues(analyze(model))
    assert unres, "one-sided interface was not diagnosed"


def test_one_end_interface_spelling_exact():
    """The exact repro spelling is diagnosed, message verbatim."""
    model = loads(
        "package SingleItemInterface {\n"
        "    item def Payload;\n"
        "    interface def OneSidedInterface {\n"
        "        item payload : Payload;\n"
        "    }\n"
        "}"
    )
    unres = related_issues(analyze(model))
    assert len(unres) == 1
    assert unres[0].message == MSG


def test_two_end_interface_is_silent():
    """The CCMM-side shape that must keep working: two ends (or an end plus
    a typed member) → no diagnosis."""
    model = loads(
        "package P {\n"
        "    port def Pd;\n"
        "    interface def I {\n"
        "        end e1 : Pd;\n"
        "        end e2 : Pd;\n"
        "    }\n"
        "}"
    )
    assert related_issues(analyze(model)) == []


def test_two_member_interface_is_silent():
    """Two typed members carry two related elements, like the Ethernet
    shape but with a second member added."""
    model = loads(
        "package P {\n"
        "    item def A;\n"
        "    item def B;\n"
        "    interface def J {\n"
        "        item x : A;\n"
        "        item y : B;\n"
        "    }\n"
        "}"
    )
    assert related_issues(analyze(model)) == []


def test_abstract_interface_is_exempt():
    """An abstract declaration's ends arrive through specialization — the
    reference exempts it."""
    model = loads(
        "package P {\n"
        "    item def Payload;\n"
        "    abstract interface def I {\n"
        "        item payload : Payload;\n"
        "    }\n"
        "}"
    )
    assert related_issues(analyze(model)) == []


def test_variation_interface_is_exempt():
    model = loads(
        "package P {\n"
        "    item def Payload;\n"
        "    variation interface def Vi {\n"
        "        item payload : Payload;\n"
        "    }\n"
        "}"
    )
    assert related_issues(analyze(model)) == []


def test_interface_subtype_inherits_ends():
    """An interface specializing a two-end parent has two related elements
    even with an empty body."""
    model = loads(
        "package P {\n"
        "    port def Pd;\n"
        "    interface def Base {\n"
        "        end e1 : Pd;\n"
        "        end e2 : Pd;\n"
        "    }\n"
        "    interface def Sub :> Base { }\n"
        "}"
    )
    assert related_issues(analyze(model)) == []


def test_interface_redefining_parent_end_counts():
    """An interface usage typed by a two-end interface definition keeps two
    related elements even with additional members."""
    model = loads(
        "package P {\n"
        "    port def Pd;\n"
        "    interface def Base {\n"
        "        end e1 : Pd;\n"
        "        end e2 : Pd;\n"
        "    }\n"
        "    interface def Sub2 :> Base {\n"
        "        item extra : Base;\n"
        "    }\n"
        "}"
    )
    assert related_issues(analyze(model)) == []


# --------------------------------------------------------------------------
# 2. the GTRI CCMM shape
# --------------------------------------------------------------------------

def test_ethernet_like_shape_flagged_with_message():
    model = loads(
        "package CCMM {\n"
        "    item def MissionData;\n"
        "    interface def EthernetInterface {\n"
        "        item payload : MissionData;\n"
        "    }\n"
        "}"
    )
    unres = related_issues(analyze(model))
    assert len(unres) == 1
    assert unres[0].message == MSG
    assert getattr(unres[0].element, "name", None) == "EthernetInterface"


# --------------------------------------------------------------------------
# 3. connectors and bindings
# --------------------------------------------------------------------------

def test_one_end_connection_cannot_parse():
    """A one-end connect is a syntax error in the grammar itself
    (`connect X` requires 'to'), so the semantic check has no one-end
    connector surface here — the syntax gate catches it upstream.
    Documented, not pinned as a semantic issue."""
    with pytest.raises(Exception):
        loads(
            "package P {\n"
            "    port def Pd;\n"
            "    part def T { port p1 : Pd; }\n"
            "    part t1 : T;\n"
            "    connection c connect t1.p1;\n"
            "}"
        )


def test_binding_with_one_feature_cannot_parse():
    """``bind X;`` without '=' is a syntax error — a binding with a single
    bound feature cannot be written, so the binary rule is enforced by the
    grammar gate.  Documented, not pinned as a semantic issue."""
    with pytest.raises(Exception):
        loads("package P {\n attribute a;\n bind a;\n}")


def test_binding_degenerate_self_bind_is_silent():
    """The only single-feature-ish legal form, ``bind a = a;``, binds the
    same feature twice — count 2, silent."""
    model = loads("package P { attribute a; bind a = a; }")
    assert binding_issues(analyze(model)) == []


# --------------------------------------------------------------------------
# 4. scope: model under analysis only
# --------------------------------------------------------------------------

def test_model_only_scope_interface_in_library_not_flagged():
    """The arity rule applies to the analyzed model's own interface
    definitions.  A model whose elements merely type against library names
    must not become an arity collateral."""
    model = loads(
        "package P {\n"
        "    part x : Real;\n"
        "    interface def Good {\n"
        "        item a : Real;\n"
        "        item b : Real;\n"
        "    }\n"
        "}"
    )
    assert related_issues(analyze(model)) == []
