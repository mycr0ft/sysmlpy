# SysML v2 Coverage Gaps

## Recently Completed

- **All 8 `actionNode` alternatives** (ifNode, whileLoopNode, forLoopNode, controlNode, sendNode, acceptNode, assignmentNode, terminateNode) — grammar classes, ANTLR visitor, round-trip tests
- **Action `first`/`then` succession** — InitialNodeMember, ActionTargetSuccessionMember, GuardedSuccessionMember
- **GridView** — as_tabular_view(), as_data_value_tabular_view(), as_relationship_matrix_view()
- **PlantUML documentation** — README.md and docs/quickstart.md with all 17 view functions documented

---

## HIGH PRIORITY GAPS

### 1. Unhandled ANTLR Visitor Rules — NOW COMPLETE
All 8 `actionNode` alternatives (ifNode, whileLoopNode, forLoopNode, controlNode, sendNode, acceptNode, assignmentNode, terminateNode) now have grammar classes, visitor functions, and round-trip tests.

### 2. 70+ NotImplementedError in classes.py
When parsing certain grammar constructs, `valid_definition()` succeeds but the `__init__` raises `NotImplementedError`. These span:
- `PortionKind`, `FeatureValuePart`, various `*Subclassification*` parts
- `MetadataFeature`, `MetadataFeatureDeclaration`
- `OccurrenceUsagePrefix.usageExtension`
- Many expression sub-classes
- Various `*Membership` and `*Import` classes

### 3. Interface / UseCase / Requirement / Message — bypass grammar tree
These types have dedicated ANTLR parse rules but the visitor produces flat dicts that:
- Skip the `InterfaceUsage`/`InterfaceDefinition` grammar classes
- Never call `ActionBodyItem` for their bodies
- Use custom dict structures that don't round-trip through `get_definition()`

**Affected:** `interface`, `usecase`, `requirement`, `message` definitions/usages.

### 4. Missing specialized PlantUML views
Only activity/action-style views are implemented:
- Requirement diagram view
- State machine view (basic transition test exists but needs full implementation)
- Block definition diagram (BDD) view
- Internal block diagram (IBD) view
- Parametric diagram view
- Package diagram view

### 5. Duplicated code block in antlr_visitor.py
There is a duplicated code block that should be de-duplicated. Search for the duplicated section and refactor.

### 6. `_visit_action_node_member` legacy code
The old code that checked `anm_ctx.sendActionUsage()` and `anm_ctx.acceptActionUsage()` was replaced with `actionNode()` dispatch. The old checks were dead code (ActionNodeMemberContext doesn't have those methods), but send/accept action usage in action bodies is still unhandled.

---

## MEDIUM PRIORITY GAPS

### 7. Missing `__init__.py` exports
`src/sysmlpy/__init__.py` is missing exports for 5 PlantUML view functions:
- `as_requirement_view`
- `as_state_transition_view`
- `as_tabular_view`
- `as_data_value_tabular_view`
- `as_relationship_matrix_view`

### 8. Library import TODO
There are `TODO` markers for library-related features that need implementation.

### 9. `Package.typedby` NotImplementedError
In `sysmlpy/definition.py` or similar, `Package.typedby` raises NotImplementedError.

---

## LOW PRIORITY GAPS

### 10. Missing grammar classes
- `TextualRepresentation`
- `MetadataFeature` / `MetadataFeatureDeclaration`
- `OccurrenceUsageBody` (distinct from `ActionBody`) — used by non-action usages

### 11. Expression sub-classes
Many expression operators (e.g., `ImpliesExpression`, `NullCoalescingExpression`, etc.) have partial implementations with `NotImplementedError` for certain operators.

---

## TECH DEBT

- ANTLR runtime (antlr4-python3-runtime) is a test dependency that isn't installed in CI
- `.g4` grammar file is out of sync with generated parser code
- `pint` dependency stub exists but shouldn't be needed at import time
- Grammar tests depend on ANTLR parser, making them slow and fragile
- `strip_ws` comparison approach loses some formatting fidelity but works for round-trip validation
