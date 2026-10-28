#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interaction definition/usage + message parsing (the 0.98.0 grammar fix).

The generated `interaction` rule originally rejected every
`interaction def X { ... }` form (and even a bare `interaction T;`).
These tests pin the fixed forms end-to-end: parse -> dict -> model.
"""
import pytest

import sysmlpy


SRC = """package P {
  item def SensorData;
  interaction def Talk {
    part cli;
    part srv;
    message m1 of SensorData from cli to srv;
  }
}"""

SRC_USAGE = "package P { interaction Talk; }"

SRC_MSG_ANYWHERE = (
    "package P { part def H { message m2 of Data from here to there; } }"
)


def find(model, cls_name, name=None):
    out = []

    def walk(el):
        if type(el).__name__ == cls_name and (
            name is None or getattr(el, "name", None) == name
        ):
            out.append(el)
        for c in getattr(el, "children", ()) or ():
            walk(c)

    walk(model)
    return out


def test_interaction_def_builds():
    model = sysmlpy.parse(SRC)[0]
    ix = find(model, "Interaction", "Talk")
    assert len(ix) == 1
    assert {c.name for c in ix[0].children} >= {"cli", "srv", "m1"}


def test_message_carries_ends_and_payload():
    model = sysmlpy.parse(SRC)[0]
    (msg,) = find(model, "Message", "m1")
    assert msg.from_port == "cli"
    assert msg.to_port == "srv"
    assert msg.of_type == "SensorData"


def test_message_in_any_body_carries_ends():
    model = sysmlpy.parse(SRC_MSG_ANYWHERE)[0]
    (msg,) = find(model, "Message", "m2")
    assert msg.from_port == "here"
    assert msg.to_port == "there"
    assert msg.of_type == "Data"


def test_interaction_usage_builds():
    model = sysmlpy.parse(SRC_USAGE)[0]
    (ix,) = find(model, "Interaction", "Talk")
    assert type(ix).__name__ == "Interaction"


def test_interaction_keyword_no_longer_rescues():
    # the strict parse must accept the def form without the
    # constraint-body rescue path firing
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model = sysmlpy.parse(SRC)[0]
    assert model is not None