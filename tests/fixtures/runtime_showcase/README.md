# Runtime showcase fixtures

These five SysML v2 models come from the OpenSysML project's
`examples/runtime-showcase/` directory (Open-MBEE/OpenSysML, Apache-2.0),
downloaded 2026-09-18, commit 1e44c746.

They are used as comparison fixtures: the same models that the OpenSysML
runtime showcase exercises (mass rollup with an unvalued leaf, delta-v
analysis with unit-dimension defects, mission sequencing, reliability
across missions, spacecraft comms with a clocked state machine) are parsed,
analyzed, evaluated and simulated by sysmlpy so the two projects' behavior
can be compared on identical inputs.

- `delta-v-budget.sysml` — analysis case over the rocket equation; the
  showcase runs it two ways (margin satisfied / `required` rebound so the
  objective fails) and separately shows `InjectionDeltaV` typing a
  gravitational parameter as a force so the runtime refuses the result.
- `mass-rollup.sysml` — recursive `totalMass` rollup over subcomponents;
  the showcase shows one unvalued leaf making the total incomputable.
- `mission-sequence.sysml` — mission phases with successions.
- `reliability.sysml` — a reliability requirement asserted of two missions.
- `spacecraft-comms.sysml` — clocked state machine.

Changes vs upstream: none to the model text.