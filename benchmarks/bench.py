#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sysmlpy benchmark suite — phase timings on real corpora.

The webinar question is "is Python fast enough to run this?", and the honest
answer needs numbers that are (a) reproducible, (b) per phase, and (c) tracked
across releases.  This script is the harness for that.

Every case is a named measurement with a fixed corpus:

  parse.*        text → parse tree            (DFA-cache cold vs warm)
  model.*        text → public element tree   (parse + grammar classes)
  analyze.*      element tree → findings
  dump.*         model → SysML text
  interchange.*  model → @graph and back
  library.*      the shipped library's symbol index / namespace tables
  gate.*         full `sysmlpy ci` corpus scan (opt-in, minutes)

Usage::

    python benchmarks/bench.py                  # default suite (~2-3 min)
    python benchmarks/bench.py --quick          # fewer repeats, no library cases
    python benchmarks/bench.py --only parse.library_all model.library_all
    python benchmarks/bench.py --cold           # DFA cache disabled (fresh cost)
    python benchmarks/bench.py --json out.json  # machine-readable results
    python benchmarks/bench.py --list

Cold measurements run each case in a subprocess with a throwaway cache dir, so
"cold" means what a first CLI invocation pays — not a warm interpreter.

Results are also appended to ``benchmarks/results/<version>.json`` so a release
can be compared against its predecessor, and printed as a table.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
LIB = SRC / "sysmlpy" / "library"
FIXTURES = ROOT / "tests" / "fixtures"
RESULTS = Path(__file__).resolve().parent / "results"

sys.path.insert(0, str(SRC))

# ---------------------------------------------------------------------------
# corpora
# ---------------------------------------------------------------------------


def library_files():
    return sorted(LIB.rglob("*.sysml"))


def fixture_models():
    """A handful of real models: a runtime showcase, an interface-heavy one,
    and a requirements model — small enough to run per-repeat, varied enough
    to exercise different loaders."""
    picks = [
        FIXTURES / "runtime_showcase" / "spacecraft-comms.sysml",
        FIXTURES / "runtime_showcase" / "delta-v-budget.sysml",
        FIXTURES / "runtime_showcase" / "mass-rollup.sysml",
    ]
    return [p for p in picks if p.exists()]


def synthetic(parts=300):
    body = "\n".join(
        f"part def Comp{i} {{ attribute a{i} : Real := {i}; "
        f"part def Sub{i} {{ attribute b : Boolean; }} }}"
        for i in range(parts))
    return "package Big { " + body + " }"


# ---------------------------------------------------------------------------
# cases
# ---------------------------------------------------------------------------


def _time(fn, repeat, warmup=1):
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - t0)
    return {
        "min": min(samples),
        "median": statistics.median(samples),
        "max": max(samples),
        "n": len(samples),
    }


def case_parse_synthetic(repeat):
    import sysmlpy
    text = synthetic()
    return _time(lambda: sysmlpy.parse(text), repeat)


def case_parse_library(repeat):
    """Parse every library file (no element build)."""
    import sysmlpy
    texts = [p.read_text(encoding="utf-8") for p in library_files()]

    def run():
        for t in texts:
            sysmlpy.parse(t)

    return _time(run, repeat)


def case_model_library(repeat):
    """Parse + build the public element tree for every library file."""
    import sysmlpy
    texts = [p.read_text(encoding="utf-8") for p in library_files()]

    def run():
        for t in texts:
            sysmlpy.loads(t)

    return _time(run, repeat)


def case_load_files_library(repeat):
    """One model from all 58 files — the shape #34 considers for a
    library-wide table."""
    import sysmlpy
    paths = [str(p) for p in library_files()]

    def run():
        sysmlpy.load_files(paths)

    return _time(run, repeat, warmup=0)


def case_analyze_fixtures(repeat):
    import sysmlpy
    models = [sysmlpy.loads(p.read_text(encoding="utf-8")) for p in fixture_models()]

    def run():
        for m in models:
            sysmlpy.analyze(m)

    return _time(run, repeat)


def case_dump_library(repeat):
    import sysmlpy
    models = [sysmlpy.loads(p.read_text(encoding="utf-8")) for p in library_files()]

    def run():
        for m in models:
            m.dump()

    return _time(run, repeat)


def case_interchange_export(repeat):
    import sysmlpy
    from sysmlpy.interchange import to_interchange
    models = [sysmlpy.loads(p.read_text(encoding="utf-8")) for p in fixture_models()]

    def run():
        for m in models:
            to_interchange(m, stable_ids=True)

    return _time(run, repeat)


def case_interchange_roundtrip(repeat):
    import sysmlpy
    from sysmlpy.interchange import from_interchange, to_interchange
    models = [sysmlpy.loads(p.read_text(encoding="utf-8")) for p in fixture_models()]

    def run():
        for m in models:
            from_interchange(to_interchange(m, stable_ids=True))

    return _time(run, repeat)


def case_library_index(repeat):
    """Build the library symbol index (the analyzer's pre-filter)."""
    from sysmlpy.semantic import LibrarySymbolIndex
    LibrarySymbolIndex.clear_cache()

    def run():
        LibrarySymbolIndex.clear_cache()
        LibrarySymbolIndex.get_symbols()

    return _time(run, repeat, warmup=0)


def case_library_tables(repeat):
    """Per-namespace tables for the facade-heavy namespaces (#34's subject)."""
    from sysmlpy.semantic import LibrarySymbolIndex
    names = ["ISQ", "ISQBase", "ScalarValues", "VectorFunctions"]

    def run():
        LibrarySymbolIndex.clear_cache()
        for n in names:
            LibrarySymbolIndex.library_namespace_table(n)

    return _time(run, repeat, warmup=0)


def case_library_exists(repeat):
    """Qualified-name truth lookups (`exists_in_loaded_model`)."""
    from sysmlpy.semantic import LibrarySymbolIndex
    names = ["ISQ::time", "ISQ::mass", "ScalarValues::Real", "VectorOf",
             "kg", "ft", "Btu_IT", "Gy"]
    LibrarySymbolIndex.clear_cache()

    def run():
        LibrarySymbolIndex.clear_cache()
        for n in names:
            LibrarySymbolIndex.exists_in_loaded_model(n)

    return _time(run, repeat, warmup=0)


def case_gate_scan(repeat):
    """The full advisory gate corpus — minutes, opt-in only."""
    import sysmlpy

    def run():
        sysmlpy.ci([str(LIB), str(FIXTURES)])

    return _time(run, repeat, warmup=0)


CASES = {
    "parse.synthetic": case_parse_synthetic,
    "parse.library_all": case_parse_library,
    "model.library_all": case_model_library,
    "load_files.library_all": case_load_files_library,
    "analyze.fixtures": case_analyze_fixtures,
    "dump.library_all": case_dump_library,
    "interchange.export": case_interchange_export,
    "interchange.roundtrip": case_interchange_roundtrip,
    "library.index": case_library_index,
    "library.tables": case_library_tables,
    "library.exists": case_library_exists,
    "gate.scan": case_gate_scan,
}

QUICK_SKIP = {"library.tables", "library.exists", "gate.scan", "load_files.library_all"}
SLOW = {"gate.scan"}

# ---------------------------------------------------------------------------
# cold execution (subprocess, throwaway DFA cache)
# ---------------------------------------------------------------------------

_CHILD = r"""
import json, sys, time
sys.path.insert(0, {src!r})
import benchmarks.bench as B
fn = B.CASES[{name!r}]
res = fn({repeat!r})
print("RESULT " + json.dumps(res))
"""


def run_cold(name, repeat):
    cache = tempfile.mkdtemp(prefix="sysmlpy-bench-")
    env = dict(os.environ)
    env["SYSMLPY_DFA_CACHE"] = cache
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONPATH"] = str(SRC)
    out = subprocess.run(
        [sys.executable, "-c", _CHILD.format(src=str(SRC), name=name, repeat=repeat)],
        capture_output=True, text=True, env=env, cwd=str(ROOT),
    )
    for line in out.stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):])
    raise RuntimeError(
        f"cold run of {name} produced no result:\n{out.stdout[-1500:]}\n{out.stderr[-1500:]}")


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------


def fmt(s):
    if s is None:
        return "-"
    if s >= 60:
        return f"{s/60:.1f} min"
    if s >= 1:
        return f"{s:.2f} s"
    return f"{s*1000:.0f} ms"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true",
                    help="fewer repeats, skip the expensive library/gate cases")
    ap.add_argument("--cold", action="store_true",
                    help="run each case in a fresh process with a throwaway DFA cache")
    ap.add_argument("--only", nargs="+", metavar="CASE", help="run only these cases")
    ap.add_argument("--repeat", type=int, default=None,
                    help="repeats per case (default 3, or 1 with --quick)")
    ap.add_argument("--json", metavar="PATH", help="write results JSON here")
    ap.add_argument("--list", action="store_true", help="list cases and exit")
    args = ap.parse_args(argv)

    if args.list:
        for name in CASES:
            tags = []
            if name in SLOW:
                tags.append("slow")
            if name in QUICK_SKIP:
                tags.append("skipped by --quick")
            print(f"  {name:26} {' '.join(tags)}")
        return 0

    selected = args.only or [n for n in CASES
                             if not (args.quick and n in QUICK_SKIP)]
    unknown = [n for n in selected if n not in CASES]
    if unknown:
        ap.error(f"unknown case(s): {', '.join(unknown)}")

    repeat = args.repeat if args.repeat is not None else (1 if args.quick else 3)
    import sysmlpy

    results = {
        "version": sysmlpy.__version__,
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "mode": "cold" if args.cold else "warm",
        "repeat": repeat,
        "cases": {},
    }

    print(f"sysmlpy {results['version']}  |  python {results['python']}  |  "
          f"{results['mode']}  |  repeat {repeat}\n")
    header = f"{'case':26} {'min':>10} {'median':>10} {'max':>10}  n"
    print(header)
    print("-" * len(header))

    for name in selected:
        try:
            if args.cold:
                res = run_cold(name, repeat)
            else:
                res = CASES[name](repeat)
        except Exception as exc:  # a case that cannot run here is reported, not fatal
            print(f"{name:26} {'ERROR':>10}  {type(exc).__name__}: {str(exc)[:60]}")
            results["cases"][name] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        results["cases"][name] = res
        print(f"{name:26} {fmt(res['min']):>10} {fmt(res['median']):>10} "
              f"{fmt(res['max']):>10}  {res['n']}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2) + "\n")
        print(f"\nwrote {out}")
    else:
        RESULTS.mkdir(parents=True, exist_ok=True)
        out = RESULTS / f"{results['version']}-{results['mode']}.json"
        out.write_text(json.dumps(results, indent=2) + "\n")
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
