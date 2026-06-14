# Guard Conditions in SysML v2

A guard condition is a boolean expression that controls whether a state machine
transition fires. The condition must evaluate to `true` for the transition to
occur.

## Canonical Keyword: `if`

The official OMG SysML v2 specification uses the keyword **`if`** for guard
conditions. The word `guard` exists only as a metamodel enum value name
(`TransitionFeatureKind::guard`) — it is **not** a keyword in the concrete
syntax.

### Correct syntax

```
transition <name> first <source> [accept <trigger>] [if <condition>] [do <effect>] then <target>;
```

### Mandatory keyword order

1. `transition` keyword
2. `first <source-state>`
3. `accept <trigger>` (optional — must come before `if`)
4. **`if <guard-expression>`** (optional — must come after `accept` and
   **before** `then`)
5. `do <effect>` (optional)
6. `then <target-state>`

## Examples

### Guard with signal trigger and effect

From the official OMG Annex A Vehicle Model:

```sysml
transition off_To_starting
    first off
    accept ignitionCmd : IgnitionCmd via ignitionCmdPort
        if ignitionCmd.ignitionOnOff == IgnitionOnOff::on and brakePedalDepressed
    do send new StartSignal() to controller
    then starting;
```

### Guard with trigger only

From the OMG validation examples:

```sysml
transition 'off-starting'
    first off
    accept 'Vehicle Start Signal'
    if vehicle1_c1.'brake pedal depressed'
    do send new 'Start Signal'() to vehicle1_c1.vehicleController
    then starting;
```

### Guard-only transition (no trigger, no effect)

```sysml
accept SetSpeed if currentSpeed >= minSpeed then cruising;
```

### Guard with compound condition

From Advent of SysML v2:

```sysml
accept StartMission via hmi
if reindeerCount == 9 and totalPower >= 36 [SI::kW]
do send new Command("Gee-up!") via eyelet
then mission;
```

### Guard on a trigger-less transition

```sysml
transition first focus if focus.image.isFocused then shoot;
```

### Change trigger (not a guard, but achieves similar effect)

```sysml
accept when currentSpeed < targetSpeed - tolerance then accelerating;
```

## Action-level conditional succession

Guard conditions also work at the action flow level, not just state transitions:

```sysml
if condition then nextAction;
```

## Common Mistakes

### Mistake 1: Using `guard` instead of `if`

```sysml
// WRONG — 'guard' is not a keyword in the spec
transition first S1 guard condition then S2;

// CORRECT
transition first S1 if condition then S2;
```

(The sysmlpy parser accepts both `if` and `guard` as a compatibility
extension, but the canonical keyword is `if`.)

### Mistake 2: Putting `if` after `then`

```sysml
// WRONG — guard must come BEFORE the target
transition first S1 then condition guard S2;

// CORRECT — guard comes before then
transition first S1 if condition then S2;
```

### Mistake 3: Putting `accept` after `if`

```sysml
// WRONG — accept before if per spec
transition first off if enabled accept TurnOn then on;

// CORRECT
transition first off accept TurnOn if enabled then on;
```

## References

- OMG SysML v2 specification, Section 8.2.2.18.3 "Transition Usages"
- OMG Issue SYSML2_-411 — confirms `accept` must precede `if` in concrete
  syntax
- OMG SysML v2 Release: https://github.com/Systems-Modeling/SysML-v2-Release
- Advent of SysML v2: https://github.com/sensmetry/advent-of-sysml-v2
- Sensmetry SysML Cheatsheet: https://sensmetry.com/sysml-cheatsheet/
