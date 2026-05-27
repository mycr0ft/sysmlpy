#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for __repr__ methods across the public API.

Verifies that repr outputs are:
  1. Constructor-mirroring — i.e. clearly show how to recreate an equivalent
     instance using the public constructor.
  2. UUID-free — auto-generated UUID names are suppressed so repr is readable.
  3. Correct for every definition/usage variant, including types that
     previously had a broken ``definition=True`` flag (13 of 24 types).
"""

import pytest

import sysmlpy
from sysmlpy.definition import Model, Package
from sysmlpy.usage import Part, Item, Attribute, Port, Action, State, Constraint, Requirement
from sysmlpy.store import InMemoryStore
from sysmlpy.semantic import SymbolTable, SemanticAnalyzer, SemanticIssue


# ---------------------------------------------------------------------------
# _is_uuid helper
# ---------------------------------------------------------------------------

def test_is_uuid_detects_uuid4():
    from sysmlpy.usage import _is_uuid
    import uuid
    assert _is_uuid(str(uuid.uuid4())) is True


def test_is_uuid_rejects_normal_name():
    from sysmlpy.usage import _is_uuid
    assert _is_uuid("engine") is False
    assert _is_uuid("Engine") is False
    assert _is_uuid("my-part") is False


def test_is_uuid_rejects_empty_string():
    from sysmlpy.usage import _is_uuid
    assert _is_uuid("") is False


def test_is_uuid_rejects_none():
    from sysmlpy.usage import _is_uuid
    assert _is_uuid(None) is False


# ---------------------------------------------------------------------------
# Model / Package repr
# ---------------------------------------------------------------------------

def test_model_empty_repr():
    m = Model()
    assert repr(m) == "Model()"


def test_model_with_children_repr():
    model = sysmlpy.loads("package P;")
    r = repr(model)
    assert r.startswith("Model(children=[")
    assert "Package(name='P')" in r


def test_model_repr_no_uuid():
    """Model.name is a UUID internally but repr must not expose it."""
    m = Model()
    assert "uuid" not in repr(m).lower()
    # No raw UUID pattern (36 chars with 4 dashes)
    assert len([c for c in repr(m) if c == '-']) < 4


def test_package_named_repr():
    assert repr(Package(name="Vehicles")) == "Package(name='Vehicles')"


def test_package_anonymous_repr():
    assert repr(Package()) == "Package()"


def test_package_repr_from_loaded_model():
    model = sysmlpy.loads("package SystemDesign;")
    assert repr(model.children[0]) == "Package(name='SystemDesign')"


# ---------------------------------------------------------------------------
# Usage repr — definition=True detection (previously broken for 13 types)
# ---------------------------------------------------------------------------

def test_part_def_repr():
    model = sysmlpy.loads("package P { part def Engine; }")
    child = model.children[0].children[0]
    assert repr(child) == "Part(definition=True, name='Engine')"


def test_part_usage_repr():
    model = sysmlpy.loads("package P { part def E; part e : E; }")
    usage = model.children[0].children[1]
    assert repr(usage) == "Part(name='e')"


def test_action_def_repr_shows_definition_true():
    """Previously broken — action defs silently dropped definition=True."""
    model = sysmlpy.loads("package P { action def Drive; }")
    child = model.children[0].children[0]
    assert repr(child) == "Action(definition=True, name='Drive')"


def test_action_usage_repr():
    model = sysmlpy.loads("package P { action def D; action drive : D; }")
    usage = model.children[0].children[1]
    assert repr(usage) == "Action(name='drive')"


def test_state_def_repr_shows_definition_true():
    """Previously broken."""
    model = sysmlpy.loads("package P { state def Running; }")
    child = model.children[0].children[0]
    assert repr(child) == "State(definition=True, name='Running')"


def test_constraint_def_repr_shows_definition_true():
    """Previously broken."""
    model = sysmlpy.loads("package P { constraint def C { attribute x : Real; } }")
    child = model.children[0].children[0]
    assert repr(child) == "Constraint(definition=True, name='C')"


def test_requirement_def_repr_shows_definition_true():
    """Previously broken."""
    model = sysmlpy.loads("package P { requirement def R { text = \"t\"; } }")
    child = model.children[0].children[0]
    assert repr(child) == "Requirement(definition=True, name='R')"


def test_item_def_repr_shows_definition_true():
    model = sysmlpy.loads("package P { item def Signal; }")
    child = model.children[0].children[0]
    assert repr(child) == "Item(definition=True, name='Signal')"


def test_attribute_def_repr_shows_definition_true():
    model = sysmlpy.loads("package P { attribute def Mass; }")
    child = model.children[0].children[0]
    assert repr(child) == "Attribute(definition=True, name='Mass')"


# ---------------------------------------------------------------------------
# Usage repr — UUID suppression
# ---------------------------------------------------------------------------

def test_anonymous_part_repr_no_uuid():
    p = Part()
    assert repr(p) == "Part()"


def test_anonymous_action_repr_no_uuid():
    a = Action()
    assert repr(a) == "Action()"


def test_anonymous_state_repr_no_uuid():
    s = State()
    assert repr(s) == "State()"


def test_named_part_shows_name():
    p = Part(name="wheel")
    assert repr(p) == "Part(name='wheel')"


def test_definition_part_named():
    p = Part(definition=True, name="Wheel")
    assert repr(p) == "Part(definition=True, name='Wheel')"


# ---------------------------------------------------------------------------
# Usage repr — shortname
# ---------------------------------------------------------------------------

def test_part_with_shortname_repr():
    p = Part(name="engine", shortname="e")
    assert repr(p) == "Part(name='engine', shortname='e')"


def test_definition_part_with_shortname_repr():
    p = Part(definition=True, name="Engine", shortname="E")
    assert repr(p) == "Part(definition=True, name='Engine', shortname='E')"


# ---------------------------------------------------------------------------
# repr does not crash on any loaded model element
# ---------------------------------------------------------------------------

def test_repr_does_not_crash_on_complex_model():
    model = sysmlpy.loads("""
    package VehicleSystem {
        part def Engine {
            attribute horsepower : Real;
            port powerOut;
        }
        part def Vehicle {
            part engine : Engine;
        }
        action def Drive;
        state def Operational {
            state Idle;
            state Running;
        }
        item def Signal;
        constraint def PowerConstraint {
            attribute maxPower : Real;
        }
    }
    """)

    def _repr_all(elem):
        repr(elem)
        for child in getattr(elem, 'children', []):
            _repr_all(child)

    _repr_all(model)  # must not raise


# ---------------------------------------------------------------------------
# InMemoryStore repr
# ---------------------------------------------------------------------------

def test_in_memory_store_empty_repr():
    s = InMemoryStore()
    assert repr(s) == "InMemoryStore(elements=0, edges=0)"


def test_in_memory_store_repr_mirrors_constructor():
    s = InMemoryStore()
    assert repr(s).startswith("InMemoryStore(")


# ---------------------------------------------------------------------------
# SymbolTable / SemanticAnalyzer repr
# ---------------------------------------------------------------------------

def test_symbol_table_empty_repr():
    st = SymbolTable()
    assert repr(st) == "SymbolTable(symbols=0, children=0)"


def test_symbol_table_repr_after_registration():
    st = SymbolTable()
    st.register("Engine", object())
    assert repr(st) == "SymbolTable(symbols=1, children=0)"


def test_semantic_analyzer_repr():
    sa = SemanticAnalyzer()
    assert repr(sa) == "SemanticAnalyzer()"


def test_semantic_issue_repr_is_dataclass():
    """SemanticIssue is a dataclass — repr already mirrors the constructor."""
    issue = SemanticIssue(
        severity="error", code="UNDEF",
        message="undefined symbol", element=None, reference=""
    )
    r = repr(issue)
    assert "SemanticIssue(" in r
    assert "severity='error'" in r
    assert "code='UNDEF'" in r
    assert "message='undefined symbol'" in r
