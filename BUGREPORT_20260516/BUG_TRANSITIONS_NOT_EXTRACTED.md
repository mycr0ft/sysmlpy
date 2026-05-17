# Bug Report: Transitions Not Extracted - Missing TransitionUsageMember Handler

**Version:** sysmlpy v0.8.0 (commit ee195a4)  
**Date:** 2026-05-16  
**Status:** Bug in new transition extraction feature

---

## Summary

The new transition extraction feature in v0.8.0 doesn't work because `State.load_from_grammar()` only checks for `TargetTransitionUsageMember` but the grammar actually contains `TransitionUsageMember`.

---

## Reproduction

```python
from sysmlpy import loads

model = loads("""
package Test {
    state def SimpleSM {
        state Idle;
        state Active;
        
        transition start
            first Idle
            then Active;
    }
}
""")

state_def = model.packages[0].states[0]
print(len(state_def.transitions))  # Expected: 1, Actual: 0
```

---

## Root Cause

**File:** `src/sysmlpy/usage.py`  
**Line:** 2344

```python
elif member_name == 'TargetTransitionUsageMember':
    self._extract_transition(member)
```

**Problem:** The grammar contains `TransitionUsageMember`, not `TargetTransitionUsageMember`.

**Evidence:**
```python
# Debugging shows:
# Item 2: StateBodyItem
#   [0] TransitionUsageMember  ← This is what's actually in the grammar
```

---

## Fix

Add handling for `TransitionUsageMember`:

```python
elif member_name == 'TransitionUsageMember':
    self._extract_transition(member)
elif member_name == 'TargetTransitionUsageMember':
    self._extract_transition(member)
```

Or combine them:

```python
elif member_name in ('TransitionUsageMember', 'TargetTransitionUsageMember'):
    self._extract_transition(member)
```

---

## Affected Code

**src/sysmlpy/usage.py, line ~2344:**

```python
for member in item.children:
    member_name = member.__class__.__name__
    
    if member_name == 'BehaviorUsageMember':
        self._extract_state_from_behavior_member(member)
    elif member_name == 'TargetTransitionUsageMember':  # ← ISSUE HERE
        self._extract_transition(member)
    elif member_name == 'EntryTransitionMember':
        self._extract_entry_transition(member)
```

**Should be:**

```python
for member in item.children:
    member_name = member.__class__.__name__
    
    if member_name == 'BehaviorUsageMember':
        self._extract_state_from_behavior_member(member)
    elif member_name in ('TransitionUsageMember', 'TargetTransitionUsageMember'):
        self._extract_transition(member)
    elif member_name == 'EntryTransitionMember':
        self._extract_entry_transition(member)
```

---

## Testing

After fix, this should work:

```python
# Simple transition
model = loads("""
package Test {
    state def SimpleSM {
        state A;
        state B;
        transition t first A then B;
    }
}
""")

state = model.packages[0].states[0]
assert len(state.transitions) == 1
assert state.transitions[0].target == 'B'

# Multiple transitions
model = loads("""
package Test {
    state def FlightController {
        state Idle;
        state Takeoff;
        state Cruise;
        
        transition start first Idle then Takeoff;
        transition climb first Takeoff then Cruise;
    }
}
""")

state = model.packages[0].states[0]
assert len(state.transitions) == 2
```

---

## Impact

**Current:** Transition extraction doesn't work at all (returns empty list)  
**After fix:** Transitions should be extracted correctly

---

## Notes

- Both `TransitionUsageMember` and `TargetTransitionUsageMember` classes exist in grammar/classes.py
- The extraction method `_extract_transition()` should work with both
- Similar pattern used for entry transitions (`EntryTransitionMember`)
- May be other member types to add: check grammar for complete list

---

## Question for sysmlpy Team

Are there other transition member types we should handle?
- `TransitionUsageMember` (found in testing)
- `TargetTransitionUsageMember` (currently handled)
- `EntryTransitionMember` (currently handled)
- Others?

---

## Files for Testing

We have comprehensive test files ready:
- `test_transitions_v0.8.py` - Tests all new features
- `debug_transitions.py` - Shows grammar structure
- `check_transitions.py` - Simple verification

Can test immediately once fix is pushed!
