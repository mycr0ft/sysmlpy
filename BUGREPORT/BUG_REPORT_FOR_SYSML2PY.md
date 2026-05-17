# sysmlpy Bug Report: State Machine and Activity Support

**Reporter:** User via SysML-to-Simulation Bridge Project  
**Date:** 2026-05-15  
**Version:** sysmlpy 0.6.0 (commit 4716d64 - latest main branch)  
**Python:** 3.12  
**OS:** macOS (Apple Silicon)

---

## Summary

Two issues with behavioral modeling support:

1. **🔴 CRITICAL:** State machines with transitions crash with `AttributeError`
2. **⚠️ HIGH:** Activity parameters and nested actions not extracted

---

## Issue 1: State Machine Parsing Crashes

### Minimal Reproducer

**File:** `minimal_state_crash.sysml`
```sysml
package MinimalStateMachineTest {
    state def SimpleSM {
        state stateA;
        state stateB;
        
        transition a_to_b
            first stateA
            then stateB;
    }
}
```

**Python:**
```python
from sysmlpy import loads

with open('minimal_state_crash.sysml', 'r') as f:
    model = loads(f.read())  # Crashes here
```

### Error

```
AttributeError: 'BehaviorUsageMember' object has no attribute 'get_definition'

Traceback:
  File "sysmlpy/grammar/classes.py", line 854, in get_definition
    output["ownedRelationship"].append(child.get_definition())
                                       ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'BehaviorUsageMember' object has no attribute 'get_definition'
```

### Root Cause

The `BehaviorUsageMember` grammar class is missing the `get_definition()` method, which is called when parsing state machine bodies.

### Impact

- **Cannot load ANY state machine models** with transitions
- Blocks all state machine use cases
- Makes behavioral modeling impossible

### Workaround

None. Removing the transition makes it parse, but then it's not a useful state machine.

---

## Issue 2: Activity Parameters and Nested Actions Not Extracted

### Minimal Reproducer

**File:** `minimal_activity_test.sysml`
```sysml
package MinimalActivityTest {
    action def SimpleActivity {
        in inputParam : Real;
        out outputParam : Boolean;
        
        action stepOne {
            in data : Real;
        }
        
        action stepTwo {
            out result : Boolean;
        }
    }
}
```

**Python:**
```python
from sysmlpy import loads

with open('minimal_activity_test.sysml', 'r') as f:
    model = loads(f.read())

action = model.packages[0].actions[0]

print(f'Inputs: {len(action.action_inputs)}')     # Expected: 1, Actual: 0
print(f'Outputs: {len(action.action_outputs)}')   # Expected: 1, Actual: 0
print(f'Nested: {len(action.actions)}')           # Expected: 2, Actual: 0
```

### Expected Behavior

- `action.action_inputs` should contain `[Parameter(name="inputParam", type=Real)]`
- `action.action_outputs` should contain `[Parameter(name="outputParam", type=Boolean)]`
- `action.actions` should contain `[Action(name="stepOne"), Action(name="stepTwo")]`

### Actual Behavior

All three lists are empty `[]`.

### Impact

- Cannot extract action signatures
- Cannot extract action decomposition
- Cannot generate executable code from activities
- Activity diagrams are effectively read-only

### Workaround

Could potentially parse `action.grammar.get_definition()` manually, but this is fragile and undocumented.

---

## Additional Context

### What Works Well

We've successfully used sysmlpy for structural modeling:
- Parts, attributes, packages ✅
- Type specialization/inheritance ✅
- Nested parts and sensors ✅
- Built 3 production bridges (AFSIM, Gazebo, JSBSim) using sysmlpy

**sysmlpy is excellent for structural models!**

### What We're Trying To Do

Generate executable Python code from SysML behaviors for autonomous UAV missions:

```sysml
state def UAVMission {
    state idle;
    state flying;
    
    transition launch
        first idle
        then flying;
}
```

→ Generate Python state machine code for simulation

### Related Issues

Also found similar issue with `EntryActionMember`:
```sysml
state idle {
    entry action startup;  // Crashes: EntryActionMember missing get_definition()
}
```

---

## Proposed Fixes

### Issue 1: State Machine Crash

Add `get_definition()` method to `BehaviorUsageMember` class in `grammar/classes.py`:

```python
class BehaviorUsageMember:
    def get_definition(self):
        # Return appropriate definition structure
        # (Similar to other *Member classes)
        pass
```

### Issue 2: Activity Extraction

Populate `Action.actions`, `Action.action_inputs`, and `Action.action_outputs` during parsing:

```python
class Action:
    def _load_nested_actions(self):
        # Extract nested actions from grammar
        # Populate self.actions list
        pass
    
    def _load_parameters(self):
        # Extract in/out parameters from grammar
        # Populate action_inputs and action_outputs
        pass
```

---

## Test Files

Attached minimal reproducers:
1. `minimal_state_crash.sysml` - Crashes sysmlpy
2. `minimal_activity_test.sysml` - Loads but doesn't extract structure
3. `test_behavior_bugs.py` - Automated test script

To run:
```bash
pip install sysmlpy
python test_behavior_bugs.py
```

---

## Questions

1. Is behavioral modeling (states/activities) on your roadmap?
2. What's the timeline for fixing these issues?
3. Would you accept PRs for these fixes? (We're willing to help!)
4. Any recommended workarounds in the meantime?

---

## Impact if Fixed

✅ Could extract state machines  
✅ Could extract activity hierarchies  
✅ Could generate Python/C++/etc code from behaviors  
✅ Would complete our SysML → Simulation toolchain

This would enable **complete model-based systems engineering** workflows from SysML to executable simulation.

---

## Version Info

```bash
$ python -c "import sysmlpy; print(sysmlpy.__version__)"
0.6.0

$ cd sysmlpy && git log -1 --oneline
4716d64 Add case body parser, objective member, and usage prefix direction extraction
```

---

**Thank you for building sysmlpy!** It's been incredibly useful for our structural modeling. We'd love to extend it to behavioral modeling as well.
