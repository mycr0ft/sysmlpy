#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the packaged library-facts snapshot.

The facts index for the bundled library is shipped as
``src/sysmlpy/library_facts.json`` so a first run costs 0.2 s instead of a
~4-minute build (without a warm DFA cache, every parse pays DFA construction).
The snapshot is validated against the build id and the library content digest,
so a stale one is a miss — but shipping a stale one wastes the whole benefit,
which is why `tests/library_facts_test.py` fails when it does not match.

Run this after any change to `src/sysmlpy/library/` **and after every version
bump** (the build id carries the version), then commit the result:

    python scripts/gen_library_facts.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sysmlpy import library_facts  # noqa: E402


def main() -> int:
    paths = library_facts._library_files(None)
    digest = library_facts.set_digest(paths)
    facts = library_facts.build(None)
    payload = {
        "build": library_facts.build_id(),
        "digest": digest,
        "version": library_facts.FACTS_VERSION,
        "facts": facts,
    }
    target = library_facts.snapshot_path()
    target.write_text(json.dumps(payload, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    members = sum(len(ns["members"]) for ns in facts.values())
    reexports = sum(len(ns["reexports"]) for ns in facts.values())
    size = target.stat().st_size
    print(f"wrote {target} ({size/1024:.0f} KiB)")
    print(f"  build {payload['build']}  digest {digest[:16]}…")
    print(f"  {len(facts)} namespaces, {members} members, {reexports} re-exports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
