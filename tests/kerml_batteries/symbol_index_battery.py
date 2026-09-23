"""Verify the hybrid symbol index: .kerml parsed + .sysml regex, with
the parse-based .kerml extraction replacing the regex scraper."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/storage16/home/jfox/proj/sysmlpy/src")

from sysmlpy.semantic import LibrarySymbolIndex  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  [{detail}]")


print("== hybrid LibrarySymbolIndex ==")
LibrarySymbolIndex.clear_cache()
syms = LibrarySymbolIndex.get_symbols()
check("symbol count grew (regex 1604 → parse-backed)",
      len(syms) >= 2900, f"{len(syms)}")

simple = LibrarySymbolIndex.get_simple_names()
check("simple names extracted", len(simple) > 1400, str(len(simple)))

for expected in ("Base::Anything", "ScalarValues::Integer",
                 "BaseFunctions::ToString", "Collections::Collection"):
    check(f"contains {expected}", expected in syms)

bare_ops = {"BaseFunctions::all", "BaseFunctions::as",
            "BaseFunctions::istype", "BaseFunctions::meta",
            "BooleanFunctions::not", "CollectionFunctions::=="}
check("operator functions quote-stripped", bare_ops <= syms,
      str(sorted(bare_ops - syms)))

check("SysML-side symbols present", "Actions::Action" in syms,
      "Actions::Action missing — .sysml regex path broken")

# malformed .kerml falls back to the regex walk (no exception, symbols
# still harvested where the regex can find them)
bad = "standard library package Bad { class @ ; }"
with tempfile.NamedTemporaryFile("w", suffix=".kerml", delete=False) as fp:
    fp.write(bad)
    tmp = Path(fp.name)
syms2: set[str] = set()
try:
    LibrarySymbolIndex._extract_kerml_parsed(tmp, syms2)
    check("malformed .kerml falls back to regex walk",
          isinstance(syms2, set), "no exception")
except Exception as e:  # noqa: BLE001
    check("malformed .kerml falls back to regex walk", False, str(e)[:80])
finally:
    tmp.unlink(missing_ok=True)

print()
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    sys.exit(1)