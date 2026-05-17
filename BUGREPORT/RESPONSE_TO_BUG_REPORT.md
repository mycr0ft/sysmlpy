# Response to BUG_REPORT_FOR_SYSML2PY.md

**Date:** 2026-05-16  
**Version:** sysmlpy 0.8.0 (commit ee195a4)

---

## Thank You

Thank you for the detailed bug report and for being a production user of sysmlpy! We appreciate the feedback and the willingness to help. The report was well-structured and made it easy to identify and fix the issues.

---

## Issue 1: State Machine Parsing Crashes — ✅ FIXED

**Status:** Resolved in v0.8.0

The `BehaviorUsageMember`, `EntryActionMember`, `DoActionMember`, `ExitActionMember`, `TargetTransitionUsageMember`, `EntryTransitionMember`, and related grammar classes now have `get_definition()` methods. State machines with transitions parse and round-trip correctly.

### What's New

The `State` class now exposes a full Python API for state machine elements:

```python
from sysmlpy import loads

text = """package 'VehicleStates' {
    attribute def VehicleStartSignal;
    state vehicleStates {
        entry; then off;
        state off;
        accept VehicleStartSignal then starting;
        state starting;
        state on {
            entry performSelfTest;
            do action providePower;
            exit action applyParkingBrake;
        }
    }
}"""

model = loads(text)
state = model.children[0].children[0]  # vehicleStates

# Transitions
for t in state.transitions:
    print(f"Transition: trigger={t.trigger}, target={t.target}, entry={t.is_entry}")
# Output:
# Transition: trigger=None, target=off, entry=True
# Transition: trigger=VehicleStartSignal, target=starting, entry=False

# Actions
print(f"Entry actions: {state.entry_actions}")
print(f"Do actions: {state.do_actions}")
print(f"Exit actions: {state.exit_actions}")

# Nested states
for s in state.children:
    print(f"Nested state: {s.name}")
```

The new `Transition` class provides:
- `.trigger` — trigger event name (from `accept` statements)
- `.guard` — guard condition expression
- `.target` — target state name
- `.effect` — effect action
- `.is_entry` — whether this is an entry transition

---

## Issue 2: Activity Parameters and Nested Actions — ✅ FIXED

**Status:** Resolved in v0.7.0 (improved in v0.8.0)

The `Action` class now correctly extracts:

```python
from sysmlpy import loads

text = """package Test {
    action def SimpleActivity {
        in inputParam : Real;
        out outputParam : Boolean;
        
        action stepOne { in data : Real; }
        action stepTwo { out result : Boolean; }
    }
}"""

model = loads(text)
action = model.children[0].children[0]

print(f"Inputs: {action.action_inputs}")    # [('inputParam', 'Real')]
print(f"Outputs: {action.action_outputs}")  # [('outputParam', 'Boolean')]
print(f"Nested: {[a.name for a in action.children]}")  # ['stepOne', 'stepTwo']
```

---

## New Feature: `.parent` Property — ✅ ADDED

Every element now has a `.parent` attribute that references its containing element:

```python
model = loads(text)
pkg = model.children[0]
state = pkg.children[0]

print(state.parent.name)       # Package name
print(state.transitions[0].parent.name)  # State name

for nested in state.children:
    print(f"{nested.name} → parent: {nested.parent.name}")
```

This works for:
- `Model` → `Package`
- `Package` → children (`Part`, `Item`, `State`, `Action`, etc.)
- `State` → nested `State` objects
- `State` → `Transition` objects
- `Action` → nested `Action` objects

---

## Answers to Your Questions

### 1. Is behavioral modeling (states/activities) on your roadmap?

Yes. The v0.7.0 and v0.8.0 releases added substantial behavioral modeling support:
- State machines with transitions, entry/exit/do actions
- Activity parameters (in/out) and nested action decomposition
- Parent navigation for all elements

### 2. What's the timeline for fixing these issues?

Both issues are **already fixed** in the current main branch (v0.8.0).

### 3. Would you accept PRs for these fixes?

The fixes have already been implemented and committed. We welcome PRs for:
- Additional `get_definition()` methods on grammar classes (for round-trip serialization)
- More complete behavioral element extraction (e.g., succession connectors, control nodes)
- Conformance test improvements

### 4. Any recommended workarounds in the meantime?

No workarounds needed — the issues are fixed. Upgrade to the latest version:

```bash
pip install git+https://github.com/mycr0ft/sysmlpy.git
```

---

## Conformance Status

The OMG SysML v2 conformance test suite results:

| Suite | Passing | Total | Notes |
|-------|---------|-------|-------|
| simpletests/ | 11 | 37 | Remaining failures are round-trip serialization gaps |
| validation/valid/ | 15 | 34 | Same pattern — parsing works, serialization incomplete |
| grammar_test.py | 54 | 56 | 2 pre-existing Analysis case failures |

The remaining conformance failures are **not parsing failures** — the ANTLR parser correctly parses all input. The failures occur during `loads()` round-trip serialization because some grammar classes are missing `get_definition()` methods. This is a known gap that we're addressing incrementally.

---

## What This Enables

With these fixes, you can now:

✅ Extract state machines with transitions, triggers, and guards  
✅ Extract activity hierarchies with in/out parameters  
✅ Navigate element parent relationships  
✅ Generate executable code from behavioral models  
✅ Complete your SysML → Simulation toolchain

---

## Commit Reference

- **Commit:** `ee195a4` — "feat: Add .parent property to all elements and state machine Python API"
- **CHANGELOG:** Updated in `CHANGELOG.md` v0.8.0 section
