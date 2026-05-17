#!/usr/bin/env python3
"""Test the new transition extraction feature in sysmlpy v0.8.0"""

from sysmlpy import loads

print("="*70)
print("TRANSITION EXTRACTION TEST - v0.8.0")
print("="*70)

# Test 1: Simple transition
print("\n1. SIMPLE TRANSITION TEST")
print("-"*70)

model_text = """
package Test {
    state def SimpleSM {
        state Idle;
        state Active;
        
        transition start
            first Idle
            then Active;
    }
}
"""

try:
    model = loads(model_text)
    state_def = model.packages[0].states[0]
    
    print(f"State: {state_def.name}")
    print(f"Nested states: {[s.name for s in state_def.states]}")
    print(f"Transitions: {len(state_def.transitions)}")
    
    if state_def.transitions:
        print("✓ SUCCESS: Transitions extracted!")
        for trans in state_def.transitions:
            print(f"  Transition: {trans.name if hasattr(trans, 'name') else 'unnamed'}")
            if hasattr(trans, 'target'):
                print(f"    target: {trans.target}")
            if hasattr(trans, 'guard'):
                print(f"    guard: {trans.guard}")
            if hasattr(trans, 'trigger'):
                print(f"    trigger: {trans.trigger}")
            if hasattr(trans, 'effect'):
                print(f"    effect: {trans.effect}")
            
            # Show all attributes
            print(f"    Available attributes: {[a for a in dir(trans) if not a.startswith('_') and not callable(getattr(trans, a))]}")
    else:
        print("✗ FAIL: No transitions extracted")
        print(f"  state_def is_definition: {state_def.is_definition}")
        print(f"  state_def.grammar: {type(state_def.grammar).__name__}")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Multiple transitions
print("\n\n2. MULTIPLE TRANSITIONS TEST")
print("-"*70)

model_text2 = """
package Test {
    state def FlightController {
        state Idle;
        state Takeoff;
        state Cruise;
        state Landing;
        
        transition start
            first Idle
            then Takeoff;
            
        transition climb_complete
            first Takeoff
            then Cruise;
            
        transition begin_descent
            first Cruise
            then Landing;
    }
}
"""

try:
    model = loads(model_text2)
    state_def = model.packages[0].states[0]
    
    print(f"State: {state_def.name}")
    print(f"States: {[s.name for s in state_def.states]}")
    print(f"Transitions: {len(state_def.transitions)}")
    
    if len(state_def.transitions) == 3:
        print("✓ SUCCESS: All 3 transitions extracted!")
        for trans in state_def.transitions:
            name = trans.name if hasattr(trans, 'name') else 'unnamed'
            target = trans.target if hasattr(trans, 'target') else 'no target'
            print(f"  {name} -> {target}")
    elif state_def.transitions:
        print(f"⚠ PARTIAL: Only {len(state_def.transitions)}/3 transitions extracted")
    else:
        print("✗ FAIL: No transitions extracted")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Entry/exit actions
print("\n\n3. ENTRY/EXIT ACTIONS TEST")
print("-"*70)

# Note: Based on changelog, entry/exit/do actions should work now
model_text3 = """
package Test {
    state def StateMachineWithActions {
        state Idle;
        state Active;
        
        transition start
            first Idle
            then Active;
    }
}
"""

try:
    model = loads(model_text3)
    state_def = model.packages[0].states[0]
    
    print(f"State: {state_def.name}")
    
    # Check for new action attributes
    if hasattr(state_def, 'entry_actions'):
        print(f"✓ entry_actions attribute exists: {len(state_def.entry_actions)}")
    else:
        print(f"✗ No entry_actions attribute")
        
    if hasattr(state_def, 'exit_actions'):
        print(f"✓ exit_actions attribute exists: {len(state_def.exit_actions)}")
    else:
        print(f"✗ No exit_actions attribute")
        
    if hasattr(state_def, 'do_actions'):
        print(f"✓ do_actions attribute exists: {len(state_def.do_actions)}")
    else:
        print(f"✗ No do_actions attribute")
        
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 4: Parent property
print("\n\n4. PARENT PROPERTY TEST")
print("-"*70)

model_text4 = """
package Test {
    state def ParentStateMachine {
        state Parent {
            state Child1;
            state Child2;
        }
    }
}
"""

try:
    model = loads(model_text4)
    state_def = model.packages[0].states[0]
    
    print(f"Top state: {state_def.name}")
    
    if hasattr(state_def, 'parent'):
        print(f"✓ parent attribute exists: {state_def.parent}")
    else:
        print(f"✗ No parent attribute")
    
    if state_def.states:
        parent_state = state_def.states[0]
        print(f"\nNested state: {parent_state.name}")
        
        if hasattr(parent_state, 'parent'):
            print(f"✓ nested state has parent: {parent_state.parent}")
        else:
            print(f"✗ nested state has no parent")
            
        if parent_state.states:
            child_state = parent_state.states[0]
            print(f"\nChild state: {child_state.name}")
            
            if hasattr(child_state, 'parent'):
                print(f"✓ child state has parent: {child_state.parent}")
                if hasattr(child_state.parent, 'name'):
                    print(f"  parent name: {child_state.parent.name}")
            else:
                print(f"✗ child state has no parent")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("""
Testing new features from sysmlpy v0.8.0:
- State.transitions (list of Transition objects)
- Transition.target, .trigger, .guard, .effect
- State.entry_actions, .exit_actions, .do_actions
- .parent property on all elements
""")
