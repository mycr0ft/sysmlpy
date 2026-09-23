#!/usr/bin/env python3
"""kerml.py parser battery: parse() over syntax cases + the full
.kerml corpus."""
import sys
from pathlib import Path

sys.path.insert(0, "/storage16/home/jfox/proj/sysmlpy/src")

from sysmlpy.kerml.kerml import parse, KerMLSyntaxError  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  [{detail}]")


print("== kerml.parse: syntax ==")
cases_ok = [
    "package P;",
    "class C;",
    "abstract classifier Anything;",
    "datatype D specializes Anything;",
    "feature f: T[1] subsets s redefines r;",
    "assoc A { end x: T1; }",
    "behavior B { step s1; succession s first s1 then s2; }",
    "function f { in x: T1; return r : T2; }",
    "standard library package P { private import Q::*; }",
    "private import Base::Anything;",
    "doc /* note */",
    "comment /* regular */",
    "type T conjugates C;",
    "metadata m about t;",
]
for src in cases_ok:
    try:
        parse(src)
        check(f"parse: {src[:44]}", True)
    except KerMLSyntaxError as e:
        check(f"parse: {src[:44]}", False, str(e)[:100])

print()
print("== corpus: parse() over the OMG + bundled .kerml tree ==")
REPO = Path("/storage16/home/jfox/proj/third_party/SysML-v2-Release")
roots = [REPO / "kerml/src/examples", REPO / "sysml.library/Kernel Libraries",
         Path("/storage16/home/jfox/proj/sysmlpy/src/sysmlpy/library/kernel")]
ok = total = 0
for root in roots:
    for fp in sorted(root.rglob("*.kerml")):
        total += 1
        try:
            parse(fp.read_text(encoding="utf-8", errors="replace"))
            ok += 1
        except Exception as e:  # noqa: BLE001
            FAIL.append(str(fp))
            print(f"  FAIL {fp.name}: {str(e)[:90]}")
check(f"corpus parse ({ok}/{total})", ok == total, f"{ok}/{total}")

print()
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    sys.exit(1)