#!/usr/bin/env python3
"""Tests for the CayleyStore graph database backend.

Note: These tests require a running Cayley instance at localhost:64210.
Tests are skipped if Cayley is not available.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Check if Cayley is available
try:
    import requests
    resp = requests.get("http://localhost:64210/", timeout=2)
    CAYLEY_AVAILABLE = resp.status_code == 200
except Exception:
    CAYLEY_AVAILABLE = False

pytestmark = pytest.mark.skipif(not CAYLEY_AVAILABLE, reason="Cayley not available at localhost:64210")

from sysmlpy.store import (
    CayleyStore, create_store,
    REL_PARENT_CHILD, REL_TYPED_BY, REL_SPECIALIZES
)


@pytest.fixture
def store():
    """Create a CayleyStore with a unique label for testing."""
    import uuid
    import time
    # Use timestamp + uuid to ensure uniqueness across test runs
    label = f"test_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"
    s = CayleyStore(label=label)
    yield s


class TestCayleyStoreBasic:
    """Test basic CRUD operations."""

    def test_put_and_get(self, store):
        store.put("e1", {"name": "Wheel", "sysml_type": "part"})
        result = store.get("e1")
        assert result["name"] == "Wheel"
        assert result["sysml_type"] == "part"

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent") is None

    def test_has(self, store):
        store.put("e1", {"name": "Wheel"})
        assert store.has("e1") is True
        assert store.has("e2") is False

    def test_len(self, store):
        assert len(store) == 0
        store.put("e1", {"name": "A"})
        store.put("e2", {"name": "B"})
        assert len(store) == 2

    def test_ids(self, store):
        store.put("e1", {"name": "A"})
        store.put("e2", {"name": "B"})
        ids = list(store.ids())
        assert set(ids) == {"e1", "e2"}


class TestCayleyStoreRelationships:
    """Test parent-child and relationship operations."""

    def test_put_with_parent(self, store):
        store.put("parent", {"name": "Vehicle"})
        store.put("child", {"name": "Wheel"}, parent_id="parent")
        children = store.children("parent")
        assert "child" in children

    def test_children(self, store):
        store.put("p", {"name": "Vehicle"})
        store.put("c1", {"name": "Wheel1"}, parent_id="p")
        store.put("c2", {"name": "Wheel2"}, parent_id="p")
        children = store.children("p")
        assert set(children) == {"c1", "c2"}

    def test_children_empty(self, store):
        store.put("p", {"name": "Vehicle"})
        assert store.children("p") == []

    def test_children_by_rel_type(self, store):
        import uuid
        prefix = uuid.uuid4().hex[:6]
        store.put(f"{prefix}_p", {"name": "Vehicle"})
        store.put(f"{prefix}_c1", {"name": "Wheel"}, parent_id=f"{prefix}_p", rel_type=REL_PARENT_CHILD)
        store.put(f"{prefix}_c2", {"name": "Engine"}, parent_id=f"{prefix}_p", rel_type=REL_TYPED_BY)
        assert f"{prefix}_c1" in store.children(f"{prefix}_p", REL_PARENT_CHILD)
        assert f"{prefix}_c2" not in store.children(f"{prefix}_p", REL_PARENT_CHILD)
        assert f"{prefix}_c2" in store.children(f"{prefix}_p", REL_TYPED_BY)

    def test_relationships_out(self, store):
        import uuid
        prefix = uuid.uuid4().hex[:6]
        store.put(f"{prefix}_p", {"name": "Vehicle"})
        store.put(f"{prefix}_c", {"name": "Wheel"}, parent_id=f"{prefix}_p")
        rels = store.relationships(f"{prefix}_p", direction="out")
        assert len(rels) == 1
        assert rels[0][0] == f"{prefix}_c"
        assert rels[0][1] == REL_PARENT_CHILD


class TestCayleyStoreQuery:
    """Test query operations."""

    def test_query_by_sysml_type(self, store):
        import uuid
        prefix = uuid.uuid4().hex[:6]
        store.put(f"{prefix}_e1", {"name": "Wheel", "sysml_type": "part"})
        store.put(f"{prefix}_e2", {"name": "Engine", "sysml_type": "part"})
        store.put(f"{prefix}_e3", {"name": "Speed", "sysml_type": "attribute"})
        results = store.query(sysml_type="part")
        assert set(results) == {f"{prefix}_e1", f"{prefix}_e2"}

    def test_query_by_name(self, store):
        import uuid
        prefix = uuid.uuid4().hex[:6]
        store.put(f"{prefix}_e1", {"name": f"Wheel_{prefix}", "sysml_type": "part"})
        store.put(f"{prefix}_e2", {"name": f"Engine_{prefix}", "sysml_type": "part"})
        results = store.query(name=f"Wheel_{prefix}")
        assert results == [f"{prefix}_e1"]


class TestCayleyStoreGraph:
    """Test graph-specific operations."""

    def test_descendants(self, store):
        store.put("root", {"name": "Vehicle"})
        store.put("child1", {"name": "Chassis"}, parent_id="root")
        store.put("child2", {"name": "Wheel"}, parent_id="child1")
        descendants = store.descendants("root")
        assert set(descendants) == {"child1", "child2"}

    def test_ancestors(self, store):
        store.put("root", {"name": "Vehicle"})
        store.put("child1", {"name": "Chassis"}, parent_id="root")
        store.put("child2", {"name": "Wheel"}, parent_id="child1")
        ancestors = store.ancestors("child2")
        assert set(ancestors) == {"root", "child1"}

    def test_path(self, store):
        store.put("a", {"name": "A"})
        store.put("b", {"name": "B"}, parent_id="a")
        store.put("c", {"name": "C"}, parent_id="b")
        store.put("d", {"name": "D"}, parent_id="c")
        path = store.path("a", "d")
        assert path is not None
        assert path == ["a", "b", "c", "d"]

    def test_path_no_path(self, store):
        import uuid
        prefix = uuid.uuid4().hex[:6]
        store.put(f"{prefix}_a", {"name": "A"})
        store.put(f"{prefix}_b", {"name": "B"})
        assert store.path(f"{prefix}_a", f"{prefix}_b") is None

    def test_connected_components(self, store):
        store.put("a1", {"name": "A1"})
        store.put("a2", {"name": "A2"}, parent_id="a1")
        store.put("b1", {"name": "B1"})
        store.put("b2", {"name": "B2"}, parent_id="b1")
        components = store.connected_components()
        assert len(components) == 2

    def test_centrality(self, store):
        store.put("center", {"name": "Center"})
        store.put("leaf1", {"name": "Leaf1"}, parent_id="center")
        store.put("leaf2", {"name": "Leaf2"}, parent_id="center")
        centrality = store.centrality()
        assert centrality["center"] > centrality["leaf1"]

    def test_stats(self, store):
        import uuid
        prefix = uuid.uuid4().hex[:6]
        store.put(f"{prefix}_a", {"name": "A"})
        store.put(f"{prefix}_b", {"name": "B"}, parent_id=f"{prefix}_a")
        stats = store.stats()
        assert stats["nodes"] == 2
        assert stats["edges"] == 1


class TestCreateStore:
    """Test the factory function."""

    def test_create_cayley(self):
        store = create_store("cayley")
        assert isinstance(store, CayleyStore)

    def test_create_cayley_alias(self):
        store = create_store("cayleydb")
        assert isinstance(store, CayleyStore)

    def test_create_cayley_with_params(self):
        store = create_store("cayley", host="localhost", port=64210, label="test")
        assert isinstance(store, CayleyStore)
        assert store._label == "test"
