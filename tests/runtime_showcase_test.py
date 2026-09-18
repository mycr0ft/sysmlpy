#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenSysML runtime-showcase fixtures in sysmlpy.

The five models come from Open-MBEE/OpenSysML's examples/runtime-showcase/
(Apache-2.0; see tests/fixtures/runtime_showcase/README.md). They are the
same inputs the OpenSysML runtime showcase runs, used here as comparison
fixtures.

This file pins sysmlpy's behavior on them:
- every fixture parses cleanly,
- the key elements surface in the public tree (including ``exhibit state``
  and ``perform action`` members, which the visitor/grammar layers
  previously dropped silently),
- Model.dump() re-parses with an identical element tree,
- the two state machines build and drive with the simulator.
"""

import pytest

from sysmlpy import loads
from sysmlpy.sim import StateSimulator


ALL = ["delta-v-budget.sysml", "mass-rollup.sysml", "mission-sequence.sysml",
       "reliability.sysml", "spacecraft-comms.sysml"]


@pytest.mark.parametrize("name", ALL)
def test_fixture_parses(name):
    src = (_fixture_dir() / name).read_text()
    model = loads(src)
    assert model.children, f"{name}: no top-level elements"


def _fixture_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures" / "runtime_showcase"


def _collect(node):
    out = []
    for ch in getattr(node, "children", []) or []:
        name = getattr(ch, "name", None)
        # Anonymous elements carry a fresh uuid4 per parse; normalize so
        # the round-trip comparison tests the tree, not name generation.
        if isinstance(name, str) and _UUID_RE.match(name):
            name = None
        out.append((ch.__class__.__name__, name))
        out.extend(_collect(ch))
    return out


_UUID_RE = __import__("re").compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


@pytest.mark.parametrize("name", ALL)
def test_fixture_dump_round_trips(name):
    src = (_fixture_dir() / name).read_text()
    model = loads(src)
    text = model.dump()
    assert text.strip()
    model2 = loads(text)
    # The re-parsed model must expose the same public element tree in
    # declaration order (the tree, not the text, is the contract).
    assert _collect(model2.children[0]) == _collect(model.children[0])


def test_delta_v_budget_elements():
    model = loads((_fixture_dir() / "delta-v-budget.sysml").read_text())
    pkg = model.children[0]
    names = {getattr(c, "name", None) for c in pkg.children}
    assert {"RocketEquation", "StageDeltaV", "InjectionDeltaV"} <= names
    assert "AscentBudget" in names
    assert "saturnIB" in names
    assert "OrbitWithMargin" in names


def test_delta_v_budget_rocket_equation_evaluates():
    # The showcase's stage numbers through the evaluator with pint
    # quantities (positional arg binding): Isp*g0*ln(m0/mf).
    # These reproduce OpenSysML's published runtime-showcase output
    # (3037.6966629706967 / 6432.955324716369 m/s, margin 70.65...),
    # computed here by sysmlpy's evaluator.
    from sysmlpy.evaluator import evaluate_calculation, evaluate_expression
    from sysmlpy.usage import ureg

    model = loads((_fixture_dir() / "delta-v-budget.sysml").read_text())
    g0 = 9.80665 * ureg("m/s^2")

    # Stage 1 lifts the stack above it: m0 = 45000+400000 + (10000+105000+18000),
    # mf = 45000 + (10000+105000+18000).
    stage1 = evaluate_calculation(
        model, "RocketEquation",
        args=[263 * ureg.s, g0, 578000 * ureg.kg, 178000 * ureg.kg])
    assert stage1.magnitude == pytest.approx(3037.6966629706967, rel=1e-9)

    # Stage 2: m0 = 10000+105000+18000, mf = 10000+18000.
    stage2 = evaluate_calculation(
        model, "RocketEquation",
        args=[421 * ureg.s, g0, 133000 * ureg.kg, 28000 * ureg.kg])
    assert stage2.magnitude == pytest.approx(6432.955324716369, rel=1e-9)

    # The budget: total minus required, with units carried.
    total = stage1 + stage2
    assert total.magnitude == pytest.approx(9470.651987687066, rel=1e-9)
    margin = total - 9400 * ureg("m/s")
    assert margin.magnitude == pytest.approx(70.65198768706614, rel=1e-9)
    assert str(margin.units) == "meter / second"


def test_mass_rollup_structure():
    model = loads((_fixture_dir() / "mass-rollup.sysml").read_text())
    text = model.dump()
    assert "totalMass" in text


def test_mission_sequence_perform_and_exhibit_surface():
    model = loads((_fixture_dir() / "mission-sequence.sysml").read_text())
    pkg = model.children[0]
    found = []

    def walk(node):
        for ch in getattr(node, "children", []) or []:
            found.append((ch.__class__.__name__, getattr(ch, "name", None)))
            walk(ch)

    walk(pkg)
    # perform action mission (in part def Flight) — previously dropped.
    assert ("Action", "mission") in found
    # exhibit state phases (in part mission) — previously dropped.
    assert ("State", "phases") in found
    # the machine itself with all six phases
    states = [n for tn, n in found if tn == "State"]
    for phase in ("MissionPhases", "prelaunch", "translunarCoast",
                  "lunarOrbit", "onSurface", "transEarthCoast", "recovered"):
        assert phase in states


def test_mission_sequence_state_machine_drives():
    from sysmlpy.sim import StateSimulator

    model = loads((_fixture_dir() / "mission-sequence.sysml").read_text())
    sim = StateSimulator(model, focus="MissionPhases")
    hist = [sim.state]
    for _ in range(10):
        sim.step()
        if sim.state == hist[-1]:
            break
        hist.append(sim.state)
    assert hist == ["prelaunch", "translunarCoast", "lunarOrbit",
                    "onSurface", "transEarthCoast", "recovered"]


def test_spacecraft_comms_exhibit_state_surfaces_and_drives():
    model = loads((_fixture_dir() / "spacecraft-comms.sysml").read_text())
    # The GroundStation's exhibit-state machine is discoverable...
    sim = StateSimulator(model, focus="modes")
    assert sim.state == "idle"
    # ...and drivable (time-triggered ping fires idle -> operation).
    sim.step()
    assert sim.state == "operation"


def test_reliability_requirements_surface():
    model = loads((_fixture_dir() / "reliability.sysml").read_text())
    pkg = model.children[0]
    names = {getattr(c, "name", None) for c in pkg.children}
    assert "CrewSafetyReliability" in names
    assert "SurvivalProbability" in names


def test_spacecraft_comms_missions_parallel_machine_builds():
    from sysmlpy.sim import build_state_machine

    model = loads((_fixture_dir() / "spacecraft-comms.sysml").read_text())
    # The SpacecraftVehicle exhibit-state machine is a parallel
    # composite (dataTransit | charging); the collector exposes it
    # under the focus name of the exhibiting usage.
    machines = build_state_machine(model, focus="modes")
    assert machines is not None