#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Doc comments, interface ends, and flows — what sysmlpy parses and
where each piece lands.

SysML v2 source → visitor dict → grammar objects → public API elements.
This example walks one model through all three layers and prints what
each layer carries, so the behaviour is visible end to end:

1. **doc comments** — `doc /* ... */` on any element is parsed by the
   visitor into a `Documentation` dict (with the comment text as
   `body`).  At the API layer the text is captured at parse time but is
   *not* surfaced as an attribute on the Part/Requirement object — the
   grammar-level `Documentation` class (`keyword="doc"`, `body`)
   carries it, and `dump()` round-trips it back to SysML text.

2. **interface ends** — `end supplierPort ::> waterTank.waterOut;`
   inside an interface usage is parsed into `InterfaceEnd` dicts by the
   visitor.  The `Interface` API object exposes `.ends` (populated via
   `add_end`) and the Interconnection View renders the ends through the
   dictionary path (`_extract_interface_connections`).

3. **flows** — `flow <source> to <target>;` parses into a `Flow`
   element in the part's children; the visitor models it as a
   `FlowConnectionUsage` with `FlowEnd` members, and the Interconnection
   View emits a `flow` edge for it.

Run:  python examples/doc_ends_flows.py
"""

import sys

from sysmlpy import loads, as_interconnection_view, loads_partial
from sysmlpy.formatting import classtree

SOURCE = """\
package WaterSystem {
    doc /* package doc: the coffee water loop */

    part def WaterTank {
        doc /* stores the water */
        port waterOut;
    }

    part def Brewer {
        doc /* heats and brews */
        port waterInlet;
    }

    interface def WaterSupply {
        doc /* the supply contract */
        end supplierPort;
        end consumerPort;
    }

    part def CoffeeMachine {
        doc /* makes coffee */
        part waterTank : WaterTank;
        part brewer : Brewer;

        interface waterLine : WaterSupply {
            doc /* internal plumbing */
            end supplierPort ::> waterTank.waterOut;
            end consumerPort ::> brewer.waterInlet;
        }

        connect waterTank.waterOut to brewer.waterInlet;

        flow waterTank.waterOut to brewer.waterInlet;
    }
}
"""


def banner(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def section_1_api_tree():
    banner("1. Public API tree (loads)")
    model = loads(SOURCE)
    package = model.children[0]

    def walk(el, depth=0):
        kind = type(el).__name__
        name = getattr(el, "name", "?")
        print("  " * depth + "- " + kind + ": " + str(name))
        for child in (el.children or []):
            walk(child, depth + 1)

    walk(package)
    return model, package


def section_2_doc(model, package):
    banner("2. doc comments — where the text lives")
    # dump() round-trip: doc on a REQUIREMENT def round-trips, and doc
    # on a part def survives only when it is the sole body item — mixed
    # with attributes/ports (as here), the visitor drops it. Same for
    # package-level doc and doc on a nested interface usage.
    dumped = classtree(model).dump()
    for needle in ("stores the water", "makes coffee", "heats and brews",
                   "the coffee water loop", "internal plumbing"):
        print("  %-28r in dump(): %s" % (needle, needle in dumped))
    solo = classtree(loads(
        "package P { part def T { doc /* solo doc */ } }")).dump()
    print("  %-28r in dump(): %s  (doc as the only body item)"
          % ("solo doc", "solo doc" in solo))

    # Visitor-dict level: the Documentation element with its body
    raw = loads_partial(SOURCE)
    text = json_text = None
    import json
    text = json.dumps(raw, default=str)
    for needle in ("/* package doc: the coffee water loop */",
                   "/* stores the water */",
                   "/* makes coffee */",
                   "/* internal plumbing */"):
        print("  visitor dict has %-38r: %s" % (needle, needle in text))

    # API level: doc text is not exposed as a .doc attribute on the
    # element; it lives in the grammar's Documentation objects and is
    # recovered by dump() (and by re-parsing the dumped text).
    print("  API element exposes .doc attribute:", hasattr(package, "doc"))
    print("  -> doc text is parsed into the visitor dict; dump() keeps it")
    print("     only when doc is the sole body item (requirement bodies")
    print("     excepted). Package-level + nested-usage doc are visitor gaps.")


def section_3_interface_ends(package, model):
    banner("3. interface ends")
    machine = next(c for c in package.children
                   if getattr(c, "name", "") == "CoffeeMachine")
    iface = next(c for c in machine.children
                 if type(c).__name__ == "Interface")
    print("  interface:", iface.name)
    print("  .ends via add_end():", iface.ends)
    print("  .iface_connections:", iface.iface_connections)

    # The raw visitor dict carries the ends at BOTH levels — the
    # interface def's bare ends and the usage's ::> ends (with the
    # ::> target as a structured feature chain):
    raw = loads_partial(SOURCE)
    import json as _json
    text = _json.dumps(raw, default=str)
    print("  visitor dict has DefaultInterfaceEnd:",
          text.count('"DefaultInterfaceEnd"'), "entries (both levels)")
    print("  visitor dict has supplierPort:", text.count("supplierPort"), "mentions")
    print("  visitor dict has the ::> feature chain:",
          '"OwnedFeatureChain"' in text)

    # And the Interconnection View renders the interface:
    view = as_interconnection_view(model)
    print("  IV view mentions interface:", "interface" in view)


def section_4_flows(package, model):
    banner("4. flows and connections")
    machine = next(c for c in package.children
                   if getattr(c, "name", "") == "CoffeeMachine")
    for child in machine.children:
        if type(child).__name__ in ("Connection", "Flow"):
            print("  %s  (from %r)" % (type(child).__name__,
                                       getattr(child, "name", None) or "anonymous"))

    view = as_interconnection_view(model)
    flow_lines = [line.strip() for line in view.splitlines()
                  if "flow" in line.lower() or "-[thickness" in line]
    print("  IV flow/connection edges:")
    for line in flow_lines[:8]:
        print("   ", line)


def main():
    model, package = section_1_api_tree()
    section_2_doc(model, package)
    section_3_interface_ends(package, model)
    section_4_flows(package, model)
    banner("done")


if __name__ == "__main__":
    main()