# sysmlpy Behavior Support - Evaluation & Feature Requests

**Date:** 2026-05-15  
**sysmlpy Version:** 0.6.0 (commit 4716d64)  
**Evaluator:** SysML Bridge Project  
**Context:** Building state machine and activity diagram code generation for UAV mission behaviors

---

## Executive Summary

**Goal:** Extract state machines and activity diagrams from SysML to generate executable Python code for autonomous UAV missions.

**Current Status:**
- ✅ **Action definitions parse successfully**
- ⚠️ **State machines crash** (AttributeError)
- ⚠️ **Nested actions not extracted**
- ⚠️ **Action inputs/outputs not extracted**
- ⚠️ **Transitions not accessible**

**Recommendation:** sysmlpy has the foundation but needs several features to support behavior modeling.

---

## Test Results

### Test 1: Activity Diagrams ⚠️ PARTIAL

**Test Model:**
```sysml
action def ReconMission {
    in targetAltitude : Real;
    in targetLocation : String;
    out missionSuccess : Boolean;
    
    action takeOff {
        in altitude : Real;
        out success : Boolean;
    }
    
    action navigateToTarget {
        in destination : String;
        out arrived : Boolean;
    }
}
```

**Results:**
```python
model = loads(sysml_text)
actions = model.packages[0].actions  # ✅ Works

len(actions)  # Returns: 1 (ReconMission)
# ✅ Top-level action found

actions[0].action_inputs  # Returns: [] 
# ⚠️ Should be: [targetAltitude, targetLocation]

actions[0].action_outputs  # Returns: []
# ⚠️ Should be: [missionSuccess]

actions[0].actions  # Returns: []
# ⚠️ Should be: [takeOff, navigateToTarget]
```

**Conclusion:** Actions parse but nested structure not extracted.

---

### Test 2: State Machines ❌ FAILS

**Test Model:**
```sysml
state def SimpleMissionSM {
    state idle;
    state armed;
    state flying;
    
    transition idle_to_armed
        first idle
        then armed;
}
```

**Results:**
```python
model = loads(sysml_text)
# ❌ Crashes with:
# AttributeError: 'BehaviorUsageMember' object has no attribute 'get_definition'
```

**Error Stack:**
```
File "sysmlpy/grammar/classes.py", line 854
    output["ownedRelationship"].append(child.get_definition())
AttributeError: 'BehaviorUsageMember' object has no attribute 'get_definition'
```

**Conclusion:** State machine parsing is broken.

---

### Test 3: State Machine with Entry/Exit Actions ❌ FAILS

**Test Model:**
```sysml
state def ComplexMissionSM {
    state idle {
        entry action idle_entry;
        exit action idle_exit;
    }
}
```

**Results:**
```python
model = loads(sysml_text)
# ❌ Crashes with:
# AttributeError: 'EntryActionMember' object has no attribute 'get_definition'
```

**Conclusion:** Entry/exit actions not supported.

---

## What's Missing

### Critical Features (Blocking)

1. **State Machine Parsing**
   - **Issue:** `BehaviorUsageMember` missing `get_definition()`
   - **Impact:** Cannot load any state machine models
   - **Priority:** 🔴 **CRITICAL** - Complete blocker

2. **Entry/Exit Actions**
   - **Issue:** `EntryActionMember` missing `get_definition()`
   - **Impact:** Cannot use entry/exit/do actions in states
   - **Priority:** 🔴 **CRITICAL** - Common pattern

3. **Nested Action Extraction**
   - **Issue:** `Action.actions` always returns `[]`
   - **Impact:** Cannot extract action sequences
   - **Priority:** 🔴 **CRITICAL** - Core feature

4. **Action Input/Output Parameters**
   - **Issue:** `action.action_inputs` and `action.action_outputs` return `[]`
   - **Impact:** Cannot determine action signatures
   - **Priority:** 🔴 **CRITICAL** - Core feature

### Important Features (Needed)

5. **Transition Extraction**
   - **Issue:** No way to access transitions between states
   - **Need:** `state.transitions` or `statemachine.transitions`
   - **Priority:** 🟡 **HIGH** - Core state machine feature

6. **Control Flow Extraction**
   - **Issue:** No way to extract `first`, `then`, `if`, `else` flow
   - **Need:** Activity control flow graph
   - **Priority:** 🟡 **HIGH** - Core activity feature

7. **Decision Nodes**
   - **Issue:** No support for conditional branching
   - **Need:** `if (condition) then ... else ...`
   - **Priority:** 🟡 **HIGH** - Common pattern

8. **Parallel Nodes**
   - **Issue:** No support for concurrent actions
   - **Need:** `fork`/`join` semantics
   - **Priority:** 🟠 **MEDIUM** - Advanced feature

---

## Proposed API

### What We Need

```python
from sysmlpy import loads

model = loads(sysml_text)

# ========== State Machines ==========

statemachine = model.packages[0].states[0]  # Should work without crashing

# Access states
statemachine.states  # List[State]
# Returns: [idle, armed, flying, landed]

# Access transitions
statemachine.transitions  # List[Transition]  # NEW!
# Returns: [idle_to_armed, armed_to_flying, ...]

for transition in statemachine.transitions:
    transition.name          # "idle_to_armed"
    transition.source_state  # State object (idle)
    transition.target_state  # State object (armed)
    transition.guard         # Optional condition
    transition.effect        # Optional action

# Access nested states
state = statemachine.states[0]
state.nested_states  # List[State] for hierarchical states

# Access entry/exit/do actions
state.entry_action   # Action object or None
state.exit_action    # Action object or None
state.do_activity    # Action object or None


# ========== Activities ==========

activity = model.packages[0].actions[0]

# Access inputs/outputs (FIXED)
activity.action_inputs   # List[Parameter]
# Returns: [Parameter(name="targetAltitude", type=Real), ...]

activity.action_outputs  # List[Parameter]
# Returns: [Parameter(name="missionSuccess", type=Boolean)]

# Access nested actions (FIXED)
activity.actions  # List[Action]
# Returns: [takeOff, navigateToTarget, ...]

# Access control flow (NEW!)
activity.control_flow  # List[ControlFlow]  # NEW!
# Returns edges between actions

for flow in activity.control_flow:
    flow.source      # Action object
    flow.target      # Action object
    flow.guard       # Optional condition (for decisions)

# Access decision nodes (NEW!)
activity.decisions  # List[DecisionNode]  # NEW!

for decision in activity.decisions:
    decision.condition     # Boolean expression
    decision.true_branch   # Action or flow
    decision.false_branch  # Action or flow
```

---

## Use Case: Why We Need This

### Our Goal
Generate Python code from SysML behaviors:

```sysml
state def UAVMission {
    state idle {
        entry action startup_systems;
    }
    
    state flying {
        do action maintain_altitude;
    }
    
    transition launch
        first idle
        then flying
        if power_level > 80;
}
```

### Desired Output
```python
class UAVMission:
    def __init__(self):
        self.state = "idle"
    
    def on_enter_idle(self):
        self.startup_systems()
    
    def on_during_flying(self):
        self.maintain_altitude()
    
    def transition(self):
        if self.state == "idle" and self.power_level > 80:
            self.state = "flying"
```

### What's Blocking Us
1. ❌ Can't parse state machines at all (crashes)
2. ❌ Can't extract transitions (not exposed)
3. ❌ Can't extract entry/exit actions (crashes)
4. ❌ Can't extract guard conditions (not exposed)

---

## Workaround Options

### Option 1: Grammar-Level Parsing ⚠️ FRAGILE

```python
# Bypass Python API, parse grammar directly
grammar = action.grammar.get_definition()
body = grammar['body']['items']
# ... manually traverse nested dict structure

# Pros: Might work now
# Cons: Brittle, no guarantees, will break
```

### Option 2: Wait for Fixes ⏳ BLOCKED

```python
# Wait for sysmlpy to fix issues
# Estimated time: Unknown
# Pros: Clean API eventually
# Cons: Project blocked
```

### Option 3: Fork and Fix 🔧 EXPENSIVE

```python
# Fork sysmlpy, implement missing features ourselves
# Estimated time: 1-2 weeks
# Pros: Full control
# Cons: Maintenance burden, divergence
```

---

## Recommended Approach

### Phase 1: Bug Fixes (sysmlpy team)

**Critical bugs to fix:**
1. Add `get_definition()` to `BehaviorUsageMember`
2. Add `get_definition()` to `EntryActionMember`
3. Fix `Action.actions` to extract nested actions
4. Fix `Action.action_inputs` and `action.action_outputs`

**Estimated effort:** 2-4 hours (if familiar with codebase)

### Phase 2: Feature Additions (sysmlpy team)

**New features to add:**
1. `StateMachine.transitions` property
2. `Transition` class with source/target/guard/effect
3. `Activity.control_flow` property
4. `DecisionNode` class

**Estimated effort:** 1-2 days

### Phase 3: Our Work (can start after Phase 1)

Once bugs are fixed, we can:
1. Extract state machine structure
2. Generate Python state machine code
3. Extract activity structure
4. Generate Python behavior code

**Estimated effort:** 1 week

---

## Test Files for sysmlpy Team

We've created test files that reproduce all issues:

1. **`test_simple_state_machine.sysml`** - Crashes on load
2. **`test_state_machine.sysml`** - Crashes on entry/exit actions
3. **`test_activity_diagram.sysml`** - Loads but doesn't extract nested actions
4. **`test_behavior_parsing.py`** - Python script that demonstrates issues

These can be used for:
- Reproducing bugs
- Regression testing
- Validating fixes

---

## Questions for sysmlpy Developers

1. **Timeline:** What's the timeline for fixing state machine parsing bugs?

2. **API Design:** Are you open to adding `transitions`, `control_flow`, etc. properties?

3. **Contribution:** Would you accept PRs for these features? (We could help implement)

4. **Workaround:** Is there a recommended way to extract this info from grammar directly?

5. **Roadmap:** Is behavior modeling (states/activities) on your roadmap?

---

## Impact Assessment

### If Fixed (Phase 1 only)
✅ Can parse state machines  
✅ Can extract action hierarchies  
✅ Can generate basic state machine code  
⚠️ Still manual extraction of transitions/flow  

### If Fixed (Phase 1 + 2)
✅ Complete state machine support  
✅ Complete activity diagram support  
✅ Clean, maintainable code generation  
✅ **Can proceed with behavior modeling project**  

### If Not Fixed
❌ Project blocked on behaviors  
⚠️ Must use fragile grammar parsing  
⚠️ Or fork and maintain ourselves  

---

## Related Work

### What We've Already Built

Using sysmlpy, we've successfully built:

1. **AFSIM Bridge** - Defense simulation (900 LOC)
2. **Gazebo Bridge** - Robotics simulation (1,350 LOC)
3. **JSBSim Bridge** - Flight dynamics (720 LOC)

All use sysmlpy for:
- ✅ Part definitions
- ✅ Attribute extraction
- ✅ Type inference
- ✅ Nested part hierarchies

**sysmlpy works great for structural modeling!**

Now we want to add **behavioral modeling** using the same approach.

---

## Conclusion

**sysmlpy has excellent potential** for behavior modeling, but needs:

**Critical (blocking):**
1. Fix state machine parsing crash
2. Fix entry/exit action crash
3. Extract nested actions
4. Extract action parameters

**Important (needed for full support):**
5. Expose transitions
6. Expose control flow
7. Support decision/merge nodes

**We're willing to help!** If the sysmlpy team provides guidance, we can contribute PRs for some of these features.

---

## Contact

- **Project:** SysML-to-Simulation Bridges (AFSIM, Gazebo, JSBSim)
- **Use Case:** Autonomous UAV mission behavior generation
- **GitHub:** (provide if you want collaboration)

**We love sysmlpy and want to extend it!** Let us know how we can help make behavior modeling work.

---

**Files Attached:**
- `test_simple_state_machine.sysml` - Minimal failing example
- `test_state_machine.sysml` - Entry/exit action example
- `test_activity_diagram.sysml` - Activity with nested actions
- `test_behavior_parsing.py` - Python test script

**sysmlpy Version Tested:** 0.6.0 (commit 4716d64, latest as of 2026-05-15)
