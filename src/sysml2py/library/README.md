# SysML v2 Standard Library

This directory contains the normative SysML v2 and KerML standard library files,
copied verbatim from the **SysML-v2-Pilot-Implementation-2026-03** release.

## Layout

| Directory | Contents |
|-----------|----------|
| `kernel/`  | 36 KerML kernel library files (`.kerml`), flattened from `Kernel Libraries/*/` |
| `systems/` | 21 SysML systems library files (`.sysml`), from `Systems Library/` |
| `domain/`  | 37 SysML domain library files (`.sysml`), organized by subdirectory |

The `kernel/` and `systems/` directories are intentionally flat (no subdirectory
nesting), matching the layout used by the `org.omg.sysml.xpect.tests` project in
the Pilot Implementation.

## Domain Library Subdirectories

```
domain/
  Analysis/              AnalysisTooling, SampledFunctions, StateSpaceRepresentation, TradeStudies
  Cause and Effect/      CausationConnections, CauseAndEffect
  Geometry/              ShapeItems, SpatialItems
  Metadata/              ImageMetadata, ModelingMetadata, ParametersOfInterestMetadata, RiskMetadata
  Quantities and Units/  ISQ, ISQBase, SI, SIPrefixes, ... (22 files)
  Requirement Derivation/ DerivationConnections, RequirementDerivation
```

## Purpose

These files are bundled with sysml2py for two reasons:

1. **Conformance tests** — the test suite under `tests/sysmlv2/` parses files that
   import from this library (e.g., `private import SI::kg;`). Having the library
   co-located with the package makes the test suite self-contained.

2. **Future import resolution** — once sysml2py implements `import` / `AliasMember`
   support, it can locate these files via:
   ```python
   import importlib.resources
   lib = importlib.resources.files("sysml2py") / "library"
   ```

## Source and License

**Source:** [SysML-v2-Pilot-Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation),
tag `2026-03`.

**License:** GNU Lesser General Public License v3.0 (see `LICENSE`). The library
files are copyright © Object Management Group (OMG). sysml2py itself is MIT-licensed;
this bundled library content is separately covered by LGPL-3.0.
