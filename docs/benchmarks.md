# Benchmarks

Performance numbers for sysmlpy, per phase, on real corpora — the answer to
"is Python fast enough to run this?" needs measurements, not assurances.

## Running

```bash
python benchmarks/bench.py                  # default suite (~2-3 min)
python benchmarks/bench.py --quick          # 1 repeat, skip the library/gate cases
python benchmarks/bench.py --list           # case names
python benchmarks/bench.py --only parse.library_all model.library_all
python benchmarks/bench.py --cold           # fresh process + throwaway DFA cache
python benchmarks/bench.py --repeat 5 --json /tmp/bench.json
```

Every run writes `benchmarks/results/<version>-<mode>.json`, so a release can be
diffed against its predecessor:

```bash
python - <<'PY'
import json, pathlib
a = json.loads(pathlib.Path("benchmarks/results/0.103.3-warm.json").read_text())
b = json.loads(pathlib.Path("benchmarks/results/0.104.0-warm.json").read_text())
for name in sorted(set(a["cases"]) & set(b["cases"])):
    if "min" in a["cases"][name] and "min" in b["cases"][name]:
        print(f"{name:26} {a['cases'][name]['min']:7.3f} → {b['cases'][name]['min']:7.3f} s")
PY
```

**Mode matters.** `--cold` runs each case in a subprocess with a throwaway
`SYSMLPY_DFA_CACHE`, which is what a first CLI invocation or LSP start pays.
Warm mode reuses the persistent cache and the in-process ATN/DFA state.

## Cases

| case | measures |
|------|----------|
| `parse.synthetic` | 300 part definitions → parse tree (kept for continuity with the v0.84.0 harness) |
| `parse.library_all` | parse all 58 library `.sysml` files, no element build |
| `model.library_all` | same corpus, parse **and** build the public element tree |
| `load_files.library_all` | one model from all 58 files (the shape #34 evaluates) |
| `analyze.fixtures` | `analyze()` on three real fixture models |
| `dump.library_all` | model → SysML text for the whole library |
| `interchange.export` | `to_interchange(stable_ids=True)` on the fixtures |
| `interchange.roundtrip` | `from_interchange(to_interchange(m))` |
| `library.index` | `LibrarySymbolIndex.get_symbols()` — the analyzer's pre-filter |
| `library.tables` | per-namespace tables for ISQ/ISQBase/ScalarValues/VectorFunctions |
| `library.exists` | `exists_in_loaded_model` on eight qualified/short names |
| `gate.scan` | full `sysmlpy ci` corpus scan (minutes, opt-in) |

## 0.104.0 delta (issue #34 — library facts index)

Warm, single repeat, same box (n=1: ±15 % noise):

```
case                        0.103.3      0.104.0     change
library.index               29.62 s      0.021 s     1400x
library.exists (8 lookups)  not measured 16 ms       (previously loaded models per miss)
library.tables              21.8 s       21.8 s      unchanged — still model-backed
model.library_all           18.31 s      17.66 s     unchanged (parse-bound)
analyze.fixtures            1.84 s       0.98 s      -47 %
```

The facts index is the one case that changed character: `get_symbols()` reads a
persisted record instead of scraping every file, and `exists_in_loaded_model()`
answers name-level truth without loading a library model.

**Cold cost depends entirely on the DFA cache.** With a warm persistent DFA
cache the build is 24.6 s on 8 cores; from a machine that has never parsed the
library it is **276 s**, because every parse pays DFA construction (measured on
the 0.104.0 wheel, 8 workers, `SYSMLPY_DFA_CACHE=off`).  That is why 0.104.1
ships a prebuilt snapshot: 0.02 s to read, validated against build id + content
digest, so it is never used when it could be wrong.

## 0.104.2 — cold analyze, fresh install

The snapshot must be usable when the caller passes explicit roots, because that
is what `analyze(model, library=[...])` does.  It was not, and a cold analyze
paid a 276 s rebuild:

```
fresh venv, no DFA cache, no facts cache     0.103.3      0.104.1      0.104.2
analyze(model importing ISQ::*)              43.5 s       190.5 s      10.9 s
warm analyze                                 43.5 s       <0.1 s       <0.1 s
```

The rule now: the snapshot is tried for **any** roots and accepted only when the
digest it carries matches the roots' own digest, so a custom library fails the
check and builds, while the bundled library answers instantly however the caller
named it.

## Baseline — 0.103.3

Linux, Python 3.13.5, one repeat (n=1: treat ±15 % as noise; use `--repeat 5`
for anything you publish).

```
case                        cold          warm
parse.synthetic             910 ms        1.24 s
parse.library_all           17.95 s       17.76 s
model.library_all           18.09 s       18.31 s
analyze.fixtures            -             1.84 s
dump.library_all            -             7.23 s
interchange.export          -             541 ms
interchange.roundtrip       -             656 ms
library.index               53.48 s       29.62 s
```

Ad-hoc measurements from the same box, for cases the default suite skips:

```
58 .sysml files → one Model (load_files)     20.5 s    7,152 elements
one SymbolTable.build_from_model over it     34.2 s    58 top-level namespaces
whole library including .kerml               fails: the SysML loader rejects KerML syntax
```

Reading of the baseline: **the analyzer's library index is the dominant cost**
(29.6 s warm / 53.5 s cold), more than parsing the entire library. That is the
component #34 replaces, and the reason its cache design matters more than the
parser's.
