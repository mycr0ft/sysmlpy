#!/usr/bin/env python3
"""kerml_visitor battery: structure-extraction cases + full corpus
through parse_to_dict."""
import sys
from pathlib import Path

sys.path.insert(0, "/storage16/home/jfox/proj/sysmlpy/src")

from sysmlpy.kerml.kerml_visitor import parse_to_dict  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  [{detail}]")


print("== visitor: structural extraction ==")
d = parse_to_dict("standard library package Base { abstract classifier Anything {"
                  " feature self: Anything[1] subsets things; } }")
base = d["children"][0]
check("library package name", base.get("declaredName") == "Base", str(base)[:80])
check("package kind", base.get("name") == "library package")
anything = base["children"][0]
check("classifier Anything", anything.get("declaredName") == "Anything"
      and anything.get("name") == "classifier")
self_f = anything["children"][0]
check("feature self typed_by/subsets",
      self_f["typed_by"] == ["Anything"] and self_f["subsets"] == ["things"],
      str(self_f)[:160])

d = parse_to_dict("abstract datatype DataValue specializes Anything { }")
check("datatype specializes", d["children"][0].get("specializes") == ["Anything"])

d = parse_to_dict("class C specializes B, D { }")
check("multi specializes", d["children"][0].get("specializes") == ["B", "D"])

d = parse_to_dict("feature f: T[1] subsets s redefines r references rf { }")
f = d["children"][0]
check("feature all reference kinds",
      f["typed_by"] == ["T"] and f["subsets"] == ["s"]
      and f["redefines"] == ["r"] and f["references"] == ["rf"]
      and f["multiplicity"] == "[1]", str(f)[:160])

d = parse_to_dict("class C { public feature g : T; private feature h; }")
c = d["children"][0]
check("visibility on members",
      c["children"][0].get("visibility") == "public"
      and c["children"][1].get("visibility") == "private",
      str([(k.get("declaredName"), k.get("visibility")) for k in c["children"]]))

d = parse_to_dict("function f { in x: T1; out y: T2; return r : T3; }")
f = d["children"][0]
dirs = [(k.get("declaredName"), k.get("direction"), k.get("is_return"))
        for k in f["children"]]
check("function parameters + return",
      dirs == [("x", "in", None), ("y", "out", None), ("r", None, True)],
      str(dirs))

d = parse_to_dict("assoc A { end x: T1[1]; end y[0..*] : T2; }")
a = d["children"][0]
names = [k.get("declaredName") for k in a["children"]]
check("association ends", names == ["x", "y"], str(names))
check("association end typing",
      [k.get("typed_by") for k in a["children"]] == [["T1"], ["T2"]],
      str([k.get("typed_by") for k in a["children"]]))

d = parse_to_dict("standard library package P { doc /* hi */ class K; }")
p = d["children"][0]
check("doc captured on package", p.get("documentation") == [" hi "],
      str(p.get("documentation")))

print()
print("== corpus: parse_to_dict over the OMG .kerml tree ==")
REPO = Path("/storage16/home/jfox/proj/third_party/SysML-v2-Release")
roots = [REPO / "kerml/src/examples", REPO / "sysml.library/Kernel Libraries",
         Path("/storage16/home/jfox/proj/sysmlpy/src/sysmlpy/library/kernel")]
ok = total = 0
for root in roots:
    for fp in sorted(root.rglob("*.kerml")):
        total += 1
        try:
            dd = parse_to_dict(fp.read_text(encoding="utf-8", errors="replace"))

            def count(nd):
                n = len(nd.get("children", []))
                for k in nd.get("children", []):
                    n += count(k)
                return n

            if count(dd) == 0:
                raise ValueError("0 elements extracted")
            ok += 1
        except Exception as e:  # noqa: BLE001
            FAIL.append(str(fp))
            print(f"  FAIL {fp.name}: {str(e)[:90]}")
check(f"corpus parse_to_dict non-empty ({ok}/{total})", ok == total,
      f"{ok}/{total}")

print()
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    sys.exit(1)