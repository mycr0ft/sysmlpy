#!/usr/bin/env python3
"""Parse a single SysML v2 file with sysmlpy and exit 0 on success.

Used by the corpus sweep (tmp/corpus_sweep.py). Prints the element count
on success; the last error line on failure. Bare top-level snippets
(no enclosing package — OMG Simple Tests style) are wrapped in a
synthetic package via loads_wrapped, matching Model.load's strict
"must be encapsulated by a package" contract without rejecting them.
"""
import sys

sys.path.insert(0, "/storage16/home/jfox/proj/sysmlpy/src")

from sysmlpy import loads_wrapped  # noqa: E402


def main() -> int:
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
    except UnicodeDecodeError:
        with open(path, encoding="latin-1") as fh:
            src = fh.read()
    try:
        model = loads_wrapped(src)
        print(model.count())
        return 0
    except Exception as e:  # noqa: BLE001 — the sweep records the type+msg
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())