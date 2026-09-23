#!/usr/bin/env python3
"""Corpus-recovery battery: every category from the original sweep is
re-verified against current code. Part of tests/kerml_test.py discovery
via the wrapper; also runnable standalone."""
import sys
from pathlib import Path

sys.path.insert(0, "/storage16/home/jfox/proj/sysmlpy/src")

from sysmlpy import loads  # noqa: E402
from sysmlpy.kerml import parse as kerml_parse  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  [{detail}]")


REPO = Path("/storage16/home/jfox/proj/third_party/SysML-v2-Release")

print("== category A: OMG .kerml corpus (94) all parse ==")
ok = 0
kfiles = sorted((REPO / "kerml/src/examples").rglob("*.kerml")) + \
    sorted((REPO / "sysml.library/Kernel Libraries").rglob("*.kerml"))
for fp in kfiles:
    try:
        kerml_parse(fp.read_text(encoding="utf-8", errors="replace"))
        ok += 1
    except Exception as e:  # noqa: BLE001
        FAIL.append(str(fp))
        print(f"  FAIL {fp.name}: {str(e)[:80]}")
check(f"OMG .kerml parse ({ok}/{len(kfiles)})", ok == len(kfiles))

print()
print("== category B/E: connect [1] with qualified ends (the Annex A bug) ==")
s = """package P {
	interface def IF;
	part p1 { port c1: PC { } }
	part p2 { port c2: PC { } }
	interface i:IF
		connect [1] p1.c1 to p2.c2;
}"""
try:
    loads(s)
    check("connect [1] p1.c1 to p2.c2 (new-line form)", True)
except Exception as e:  # noqa: BLE001
    check("connect [1] p1.c1 to p2.c2 (new-line form)", False, str(e)[:80])

print()
print("== category E full model: Annex A SimpleVehicleModel ==")
p = REPO / "sysml/src/examples/Vehicle Example/SysML v2 Spec Annex A SimpleVehicleModel.sysml"
try:
    m = loads(p.read_text(encoding="utf-8"))
    counts = m.count()
    total = sum(counts.values())
    check(f"Annex A SimpleVehicleModel parses ({total} elements)", total > 200,
          str(counts)[:120])
except Exception as e:  # noqa: BLE001
    check("Annex A SimpleVehicleModel parses", False, str(e)[:120])

print()
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    sys.exit(1)