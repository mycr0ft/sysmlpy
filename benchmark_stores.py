#!/usr/bin/env python3
"""Benchmark comparison of InMemoryStore, NetworkXStore, and KuzuStore."""

import time
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sysmlpy.store import InMemoryStore, NetworkXStore, KuzuStore, create_store, REL_PARENT_CHILD

# ── Benchmark configuration ─────────────────────────────────────────────

N_ELEMENTS = 1000    # Number of elements to insert
N_WARMUP = 3         # Warmup runs (discarded)
N_RUNS = 5           # Actual runs (averaged)


def build_chain(store, n):
    """Build a linear chain: root -> child1 -> child2 -> ... -> childN."""
    store.put("root", {"name": "Root", "sysml_type": "part"})
    for i in range(n):
        parent = f"child{i-1}" if i > 0 else "root"
        child = f"child{i}"
        store.put(child, {"name": f"Child_{i}", "sysml_type": "part"}, parent_id=parent)


def build_tree(store, n, branching=3):
    """Build a tree with given branching factor."""
    store.put("root", {"name": "Root", "sysml_type": "part"})
    count = 0
    queue = ["root"]
    while queue and count < n:
        parent = queue.pop(0)
        for b in range(branching):
            if count >= n:
                break
            child = f"node_{count}"
            store.put(child, {"name": f"Node_{count}", "sysml_type": "part"}, parent_id=parent)
            queue.append(child)
            count += 1


def timed(fn, *args, **kwargs):
    """Time a function call, return elapsed in milliseconds."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, result


def benchmark_suite(name, setup_fn, test_fn, warmup=N_WARMUP, runs=N_RUNS):
    """Run benchmark: setup once, then run test_fn multiple times."""
    # Warmup
    for _ in range(warmup):
        store = setup_fn()
        test_fn(store)

    # Actual runs
    times = []
    for _ in range(runs):
        store = setup_fn()
        t, _ = timed(test_fn, store)
        times.append(t)

    avg = sum(times) / len(times)
    best = min(times)
    return avg, best


def main():
    print("=" * 70)
    print("sysmlpy Store Backend Benchmark")
    print(f"Elements: {N_ELEMENTS}, Runs: {N_RUNS} (avg of {N_RUNS})")
    print("=" * 70)

    backends = [
        ("InMemory", InMemoryStore),
        ("NetworkX", NetworkXStore),
        ("Kuzu", KuzuStore),
    ]

    # ── 1. Insert N elements (chain) ────────────────────────────────────
    print("\n1. INSERT (linear chain, {} elements)".format(N_ELEMENTS))
    print("-" * 50)

    for backend_name, store_cls in backends:
        def setup():
            return store_cls()

        def test(store):
            build_chain(store, N_ELEMENTS)

        avg, best = benchmark_suite(backend_name, setup, test)
        print(f"  {backend_name:12s}: avg {avg:8.2f} ms  (best {best:8.2f} ms)")

    # ── 2. Get element by ID ────────────────────────────────────────────
    print("\n2. GET (random access, {} lookups)".format(N_ELEMENTS // 10))
    print("-" * 50)

    for backend_name, store_cls in backends:
        def setup(store_cls=store_cls):
            store = store_cls()
            build_chain(store, N_ELEMENTS)
            return store

        def test(store):
            for i in range(0, N_ELEMENTS, 10):
                store.get(f"child{i}")

        avg, best = benchmark_suite(backend_name, setup, test)
        print(f"  {backend_name:12s}: avg {avg:8.2f} ms  (best {best:8.2f} ms)")

    # ── 3. Query by property ────────────────────────────────────────────
    print("\n3. QUERY (by sysml_type)")
    print("-" * 50)

    for backend_name, store_cls in backends:
        def setup(store_cls=store_cls):
            store = store_cls()
            build_chain(store, N_ELEMENTS)
            return store

        def test(store):
            store.query(sysml_type="part")

        avg, best = benchmark_suite(backend_name, setup, test)
        print(f"  {backend_name:12s}: avg {avg:8.2f} ms  (best {best:8.2f} ms)")

    # ── 4. Children lookup ──────────────────────────────────────────────
    print("\n4. CHILDREN ({} calls)".format(N_ELEMENTS))
    print("-" * 50)

    for backend_name, store_cls in backends:
        def setup(store_cls=store_cls):
            store = store_cls()
            build_chain(store, N_ELEMENTS)
            return store

        def test(store):
            for i in range(N_ELEMENTS):
                store.children(f"child{i}")

        avg, best = benchmark_suite(backend_name, setup, test)
        print(f"  {backend_name:12s}: avg {avg:8.2f} ms  (best {best:8.2f} ms)")

    # ── 5. Shortest path ────────────────────────────────────────────────
    print("\n5. SHORTEST PATH (chain, end-to-end)")
    print("-" * 50)

    for backend_name, store_cls in backends:
        def setup(store_cls=store_cls):
            store = store_cls()
            build_chain(store, N_ELEMENTS)
            return store

        def test(store):
            store.path("root", f"child{N_ELEMENTS-1}")

        avg, best = benchmark_suite(backend_name, setup, test)
        print(f"  {backend_name:12s}: avg {avg:8.2f} ms  (best {best:8.2f} ms)")

    # ── 6. Descendants (full traversal) ─────────────────────────────────
    print("\n6. DESCENDANTS (full tree, {} nodes)".format(N_ELEMENTS))
    print("-" * 50)

    for backend_name, store_cls in backends:
        def setup(store_cls=store_cls):
            store = store_cls()
            build_tree(store, N_ELEMENTS, branching=3)
            return store

        def test(store):
            store.descendants("root")

        avg, best = benchmark_suite(backend_name, setup, test)
        print(f"  {backend_name:12s}: avg {avg:8.2f} ms  (best {best:8.2f} ms)")

    # ── 7. Delete ───────────────────────────────────────────────────────
    print("\n7. DELETE ({} elements)".format(N_ELEMENTS))
    print("-" * 50)

    for backend_name, store_cls in backends:
        def setup(store_cls=store_cls):
            store = store_cls()
            build_chain(store, N_ELEMENTS)
            return store

        def test(store):
            for i in range(N_ELEMENTS):
                store.delete(f"child{i}")

        avg, best = benchmark_suite(backend_name, setup, test)
        print(f"  {backend_name:12s}: avg {avg:8.2f} ms  (best {best:8.2f} ms)")

    # ── 8. Kuzu disk persistence ────────────────────────────────────────
    print("\n8. KUZU DISK PERSISTENCE")
    print("-" * 50)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write to disk (each run gets its own DB to avoid PK conflicts)
        run_idx = [0]
        def setup_disk():
            db_path = os.path.join(tmpdir, f"bench_{run_idx[0]}.db")
            run_idx[0] += 1
            return KuzuStore(database=db_path)

        def test_disk_write(store):
            build_chain(store, N_ELEMENTS)

        avg_w, best_w = benchmark_suite("Kuzu-disk-write", setup_disk, test_disk_write)
        print(f"  Kuzu (disk) write: avg {avg_w:8.2f} ms  (best {best_w:8.2f} ms)")

        # Read after restart (use the last written DB)
        last_db = os.path.join(tmpdir, f"bench_{run_idx[0]-1}.db")
        def setup_read():
            return KuzuStore(database=last_db)

        def test_disk_read(store):
            for i in range(0, N_ELEMENTS, 10):
                store.get(f"child{i}")

        avg_r, best_r = benchmark_suite("Kuzu-disk-read", setup_read, test_disk_read)
        print(f"  Kuzu (disk) read:  avg {avg_r:8.2f} ms  (best {best_r:8.2f} ms) (after restart)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
