# Control Flow Node Implementation Status

**Branch:** `feature/control-flow-fixes`  
**Version:** v0.28.2  
**Date:** 2026-05-26

---

## Test Results

| Category | Passing | Total | Percentage |
|----------|---------|-------|------------|
| **All Grammar Tests** | 65 | 77 | 84.4% |
| **Control Flow Tests** | 2 | 14 | 14.3% |
| **Non-Control-Flow Tests** | 63 | 63 | 100% |

---

## ✅ Completed (2 tests)

### 1. TerminateNode
**Test:** `test_Terminate_Node`  
**Status:** ✅ PASSING

**Implementation:**
- Added `TerminateNode` class (lines 2920-2971 in `grammar/classes.py`)
- Added `TerminateNode` to `ActionNode` supported types list
- Follows same pattern as `SendNode`/`AcceptNode`

**Syntax Supported:**
```sysml
action def TestAction {
    terminate {
        action process;
    }
}
```

**Files Changed:**
- `src/sysmlpy/grammar/classes.py` (+52 lines)

---

### 2. SendNode (basic)
**Test:** `test_Send_Node`  
**Status:** ✅ PASSING

**Fix:**
- Fixed `ActionNodeUsageDeclaration.dump()` to return empty string when declaration is None
- Previously output "action" keyword even when no explicit declaration existed

**Syntax Supported:**
```sysml
action def TestAction {
    send msg {
        action process;
    }
}
```

**Files Changed:**
- `src/sysmlpy/grammar/classes.py` (1 line change)

---

## ❌ Remaining Work (12 tests)

### 1. SendNode with via/to (1 test)
**Test:** `test_Send_Node_Via_To`  
**Error:** `ValueError: The name of the element did not match.`  
**Root Cause:** `EmptyParameterMember` expects `featureChain` key but visitor returns `ownedRelatedElement`

**Syntax:**
```sysml
action def TestAction {
    send msg via chan to dest {
        action process;
    }
}
```

**Fix Required:**
- Update `_visit_node_parameter_member()` or `_visit_node_parameter()` in `antlr_visitor.py`
- Or update `EmptyParameterMember.__init__()` to handle both structures

**Estimated Time:** 1-2 hours

---

### 2. IfNode Tests (3 tests)
**Tests:**
- `test_Control_Flow_If`
- `test_Control_Flow_If_Else`
- `test_Control_Flow_If_ElseIf_Else`

**Error:** Output mismatch - extra "action" keyword appearing

**Syntax:**
```sysml
action def TestAction {
    if (x > 0) {
        action doSomething;
    }
}
```

**Fix Required:**
- Verify `IfNodeDeclaration.dump()` handles condition expression
- Add `else` and `elseif` clause handling
- Check condition expression serialization

**Estimated Time:** 3-4 hours

---

### 3. WhileLoopNode Tests (3 tests)
**Tests:**
- `test_Control_Flow_While`
- `test_Control_Flow_Loop`
- `test_Control_Flow_Loop_Until`
- `test_Control_Flow_While_Until`

**Error:** Output mismatch - condition/until clause issues

**Syntax:**
```sysml
action def TestAction {
    while (x > 0) {
        action process;
    }
}
```

**Fix Required:**
- Verify `WhileLoopNodeDeclaration.dump()` handles condition
- Add `until` clause handling
- Check condition expression serialization

**Estimated Time:** 3-4 hours

---

### 4. ControlNode Tests (4 tests)
**Tests:**
- `test_Control_Flow_Merge`
- `test_Control_Flow_Decision`
- `test_Control_Flow_Fork`
- `test_Control_Flow_Join`

**Error:** Output mismatch - keyword handling

**Syntax:**
```sysml
action def TestAction {
    merge {
        action process;
    }
    decision {
        action process;
    }
    fork {
        action process;
    }
    join {
        action process;
    }
}
```

**Fix Required:**
- Verify `ControlNodeDeclaration.dump()` outputs correct keyword
- Check all four keywords: merge, decision, fork, join

**Estimated Time:** 2-3 hours

---

### 5. ForLoopNode (1 test)
**Test:** None currently (grammar class exists but no test)

**Syntax:**
```sysml
action def TestAction {
    for (x in items) {
        action process;
    }
}
```

**Status:** Grammar class exists, needs test and verification

**Estimated Time:** 2-3 hours (including test creation)

---

## Implementation Pattern

All control flow nodes follow this pattern:

```python
class ControlFlowNode:
    # ControlFlowNode :
    #   prefix=OccurrenceUsagePrefix declaration=ControlFlowNodeDeclaration body=ActionBody
    # ;
    def __init__(self, definition):
        self.prefix = None
        self.declaration = None
        self.body = None
        if valid_definition(definition, self.__class__.__name__):
            if definition.get("prefix") is not None:
                self.prefix = OccurrenceUsagePrefix(definition["prefix"])
            if definition.get("declaration") is not None:
                self.declaration = ControlFlowNodeDeclaration(definition["declaration"])
            if definition.get("body") is not None:
                self.body = ActionBody(definition["body"])

    def dump(self):
        output = []
        if self.prefix is not None:
            output.append(self.prefix.dump())
        if self.declaration is not None:
            output.append(self.declaration.dump())
        if self.body is not None:
            output.append(self.body.dump())
        return " ".join(output)

    def get_definition(self):
        output = {
            "name": self.__class__.__name__,
            "prefix": None,
            "declaration": None,
            "body": None,
        }
        if self.prefix is not None:
            output["prefix"] = self.prefix.get_definition()
        if self.declaration is not None:
            output["declaration"] = self.declaration.get_definition()
        if self.body is not None:
            output["body"] = self.body.get_definition()
        return output
```

---

## Next Steps

### Priority 1: SendNode via/to (1-2 hours)
1. Debug `EmptyParameterMember` structure mismatch
2. Update visitor or grammar class to match
3. Verify `test_Send_Node_Via_To` passes

### Priority 2: ControlNode keywords (2-3 hours)
1. Verify `ControlNodeDeclaration` keyword handling
2. Test all four keywords (merge, decision, fork, join)
3. Run 4 ControlNode tests

### Priority 3: IfNode conditions (3-4 hours)
1. Verify condition expression extraction in visitor
2. Add else/elseif clause handling
3. Test all three IfNode variations

### Priority 4: WhileLoopNode (3-4 hours)
1. Verify condition expression handling
2. Add until clause support
3. Test all variations

### Priority 5: ForLoopNode (2-3 hours)
1. Create test case
2. Verify iteration syntax handling
3. Run test

**Total Estimated Time:** 11-16 hours

---

## Files to Modify

| File | Current Lines | Expected Changes |
|------|---------------|------------------|
| `grammar/classes.py` | 9297 | +100-200 lines |
| `antlr_visitor.py` | 11927 | +50-100 lines |
| `tests/grammar_test.py` | ~1200 | +20-30 lines (new tests) |

---

## Testing Strategy

1. **Start with simplest** - SendNode via/to (structure mismatch fix)
2. **Move to keywords** - ControlNode (4 tests, same pattern)
3. **Handle conditions** - IfNode, WhileLoopNode (expression handling)
4. **Finish with iteration** - ForLoopNode (most complex)

After each fix:
```bash
poetry run pytest tests/grammar_test.py -k "Control_Flow or Send_Node or Terminate_Node" -v
```

---

## Notes

- All 63 non-control-flow tests continue to pass (100%)
- No ANTLR grammar changes needed
- Visitor already creates dicts for all node types
- This is pure Python implementation work
- Pattern established by TerminateNode and SendNode fixes
