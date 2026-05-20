#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage abstraction layer for sysmlpy.

Provides a protocol-based storage backend that supports:
- InMemoryStore: dict/tree storage (current behavior, backward compatible)
- NetworkXStore: graph database storage (analysis, queries, scale)

Elements are identified by stable UUIDs, not names. Names remain the user-facing
identity while UUIDs provide persistence and graph connectivity.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Iterator
import uuid


# ── Relationship types ──────────────────────────────────────────────────────

REL_PARENT_CHILD = "parent_child"
REL_TYPED_BY = "typed_by"
REL_SPECIALIZES = "specializes"
REL_SUBSETS = "subsets"
REL_REDEFINES = "redefines"
REL_CONNECTS = "connects"
REL_FLOWS = "flows"
REL_TRANSITIONS = "transitions"
REL_SATISFIES = "satisfies"
REL_DERIVES = "derives"
REL_REFINES = "refines"
REL_VERIFIES = "verifies"


# ── Store Protocol ──────────────────────────────────────────────────────────

class Store(ABC):
    """Abstract storage backend for sysmlpy elements.

    All element data is stored as dicts keyed by UUID. Relationships are
    stored as typed edges between element UUIDs.

    Subclasses must implement: put, get, delete, children, parents,
    relationships, and query.
    """

    @abstractmethod
    def put(self, element_id: str, data: dict,
            parent_id: Optional[str] = None,
            rel_type: str = REL_PARENT_CHILD) -> None:
        """Store an element.

        Parameters
        ----------
        element_id : str
            Unique identifier for the element (UUID).
        data : dict
            Element properties (name, sysml_type, custom attrs, etc.).
        parent_id : str, optional
            Parent element ID. If provided, creates a relationship edge.
        rel_type : str
            Type of relationship to parent (default: parent_child).
        """

    @abstractmethod
    def get(self, element_id: str) -> Optional[dict]:
        """Retrieve element data by ID.

        Returns None if element does not exist.
        """

    @abstractmethod
    def delete(self, element_id: str) -> bool:
        """Remove an element and all its relationships.

        Returns True if element existed and was removed.
        """

    @abstractmethod
    def children(self, parent_id: str, rel_type: str = REL_PARENT_CHILD) -> list[str]:
        """Return child element IDs for a given parent.

        Parameters
        ----------
        parent_id : str
            The parent element's UUID.
        rel_type : str
            Filter by relationship type (default: parent_child).

        Returns
        -------
        list[str]
            Ordered list of child element UUIDs.
        """

    @abstractmethod
    def parents(self, child_id: str, rel_type: Optional[str] = None) -> list[str]:
        """Return parent element IDs for a given child.

        Parameters
        ----------
        child_id : str
            The child element's UUID.
        rel_type : str, optional
            Filter by relationship type. If None, returns all parents.

        Returns
        -------
        list[str]
            List of parent element UUIDs.
        """

    @abstractmethod
    def relationships(self, element_id: str,
                      rel_type: Optional[str] = None,
                      direction: str = "both") -> list[tuple[str, str, dict]]:
        """Return relationships for an element.

        Parameters
        ----------
        element_id : str
            The element's UUID.
        rel_type : str, optional
            Filter by relationship type.
        direction : str
            "out" (edges from this element), "in" (edges to this element),
            or "both" (default).

        Returns
        -------
        list[tuple[str, str, dict]]
            List of (target_id, rel_type, edge_data) tuples.
        """

    @abstractmethod
    def query(self, **filters) -> list[str]:
        """Find elements matching property filters.

        Parameters
        ----------
        **filters : dict
            Property name = value pairs to match.
            Special keys:
              - sysml_type: filter by element type
              - name: filter by name (supports '*' wildcard)

        Returns
        -------
        list[str]
            List of matching element UUIDs.
        """

    @abstractmethod
    def has(self, element_id: str) -> bool:
        """Check if an element exists."""

    @abstractmethod
    def __len__(self) -> int:
        """Return total number of elements in the store."""

    @abstractmethod
    def ids(self) -> Iterator[str]:
        """Iterate over all element IDs in the store."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all elements and relationships."""

    def descendants(self, root_id: str, rel_type: str = REL_PARENT_CHILD) -> list[str]:
        """Return all descendant element IDs (recursive children).

        Default implementation uses BFS over children(). Subclasses
        with graph backends may override for better performance.
        """
        result = []
        queue = list(self.children(root_id, rel_type))
        while queue:
            cid = queue.pop(0)
            result.append(cid)
            queue.extend(self.children(cid, rel_type))
        return result

    def ancestors(self, leaf_id: str, rel_type: str = REL_PARENT_CHILD) -> list[str]:
        """Return all ancestor element IDs (recursive parents).

        Default implementation walks up via parents(). Subclasses
        with graph backends may override.
        """
        result = []
        current = leaf_id
        while True:
            parents = self.parents(current, rel_type)
            if not parents:
                break
            pid = parents[0]
            result.append(pid)
            current = pid
        return result

    def path(self, source_id: str, target_id: str,
             rel_type: str = REL_PARENT_CHILD) -> Optional[list[str]]:
        """Find shortest path between two elements.

        Default implementation uses BFS. Graph backends override
        with native shortest-path algorithms.
        """
        if source_id == target_id:
            return [source_id]

        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current, path = queue.pop(0)
            for child_id in self.children(current, rel_type):
                if child_id == target_id:
                    return path + [child_id]
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, path + [child_id]))

        return None


# ── InMemory Store ──────────────────────────────────────────────────────────

class InMemoryStore(Store):
    """Dict-based storage backend. Mirrors current sysmlpy behavior.

    Elements are stored in a flat dict keyed by UUID. Parent-child
    relationships are tracked via adjacency lists. This backend provides
    O(1) lookups and is fully backward compatible with the existing API.
    """

    def __init__(self):
        self._elements: dict[str, dict] = {}
        self._children: dict[str, list[str]] = {}
        self._parents: dict[str, list[str]] = {}
        self._edges: dict[str, list[tuple[str, str, dict]]] = {}

    def put(self, element_id: str, data: dict,
            parent_id: Optional[str] = None,
            rel_type: str = REL_PARENT_CHILD) -> None:
        """Store an element and optionally link it to a parent.

        Parameters
        ----------
        element_id : str
            Unique identifier for the element.
        data : dict
            Element attributes (e.g., {'name': 'Wheel', 'sysml_type': 'part'}).
        parent_id : str, optional
            Parent element ID to establish a parent-child relationship.
        rel_type : str, optional
            Relationship type. Default is REL_PARENT_CHILD.
        """
        self._elements[element_id] = data

        if parent_id is not None:
            self._children.setdefault(parent_id, []).append(element_id)
            self._parents.setdefault(element_id, []).append(parent_id)

            edge_data = {"rel_type": rel_type}
            self._edges.setdefault(parent_id, []).append((element_id, rel_type, edge_data))
            self._edges.setdefault(element_id, []).append((parent_id, rel_type, edge_data))

    def get(self, element_id: str) -> Optional[dict]:
        """Retrieve an element's data by ID.

        Parameters
        ----------
        element_id : str
            Unique identifier for the element.

        Returns
        -------
        dict or None
            Element data dict, or None if not found.
        """
        return self._elements.get(element_id)

    def delete(self, element_id: str) -> bool:
        """Remove an element and all its relationships.

        Parameters
        ----------
        element_id : str
            Unique identifier for the element to remove.

        Returns
        -------
        bool
            True if the element was found and deleted, False otherwise.
        """
        if element_id not in self._elements:
            return False

        del self._elements[element_id]

        for pid in self._parents.pop(element_id, []):
            if pid in self._children:
                self._children[pid] = [c for c in self._children[pid] if c != element_id]

        for cid in self._children.pop(element_id, []):
            if cid in self._parents:
                self._parents[cid] = [p for p in self._parents[cid] if p != element_id]

        self._edges.pop(element_id, None)
        for eid in list(self._edges.keys()):
            self._edges[eid] = [(t, r, d) for t, r, d in self._edges[eid]
                                if t != element_id]

        return True

    def children(self, parent_id: str, rel_type: str = REL_PARENT_CHILD) -> list[str]:
        """Get the IDs of child elements for a given parent.

        Parameters
        ----------
        parent_id : str
            Parent element ID.
        rel_type : str, optional
            Filter by relationship type. Default is REL_PARENT_CHILD.

        Returns
        -------
        list of str
            List of child element IDs.
        """
        return self._children.get(parent_id, []).copy()

    def parents(self, child_id: str, rel_type: Optional[str] = None) -> list[str]:
        """Get the IDs of parent elements for a given child.

        Parameters
        ----------
        child_id : str
            Child element ID.
        rel_type : str, optional
            Filter by relationship type (unused in this implementation).

        Returns
        -------
        list of str
            List of parent element IDs.
        """
        return self._parents.get(child_id, []).copy()

    def relationships(self, element_id: str,
                      rel_type: Optional[str] = None,
                      direction: str = "both") -> list[tuple[str, str, dict]]:
        """Get all relationships for an element.

        Parameters
        ----------
        element_id : str
            Element ID to query.
        rel_type : str, optional
            Filter by relationship type.
        direction : str, optional
            Direction filter (unused in this implementation).

        Returns
        -------
        list of tuple
            List of (target_id, rel_type, edge_data) tuples.
        """
        edges = self._edges.get(element_id, [])
        if rel_type:
            edges = [(t, r, d) for t, r, d in edges if r == rel_type]
        return edges.copy()

    def query(self, **filters) -> list[str]:
        """Query elements by attribute filters.

        Parameters
        ----------
        **filters : dict
            Attribute name=value pairs to match. Supports glob patterns
            with '*' for the 'name' field.

        Returns
        -------
        list of str
            List of matching element IDs.

        Examples
        --------
        >>> store.query(sysml_type='part')
        ['uuid1', 'uuid2']
        >>> store.query(name='*Wheel*')
        ['uuid3']
        """
        results = []
        for eid, data in self._elements.items():
            match = True
            for key, value in filters.items():
                if key == "name" and "*" in str(value):
                    import fnmatch
                    if not fnmatch.fnmatch(data.get("name", ""), value):
                        match = False
                        break
                elif data.get(key) != value:
                    match = False
                    break
            if match:
                results.append(eid)
        return results

    def has(self, element_id: str) -> bool:
        """Check if an element exists in the store.

        Parameters
        ----------
        element_id : str
            Element ID to check.

        Returns
        -------
        bool
            True if the element exists, False otherwise.
        """
        return element_id in self._elements

    def __len__(self) -> int:
        """Return the number of elements in the store.

        Returns
        -------
        int
            Number of stored elements.
        """
        return len(self._elements)

    def ids(self) -> Iterator[str]:
        """Iterate over all element IDs in the store.

        Returns
        -------
        iterator of str
            Iterator over element IDs.
        """
        return iter(self._elements.keys())

    def clear(self) -> None:
        """Remove all elements and relationships from the store."""
        self._elements.clear()
        self._children.clear()
        self._parents.clear()
        self._edges.clear()


# ── NetworkX Store ──────────────────────────────────────────────────────────

class NetworkXStore(Store):
    """Graph database storage backend using NetworkX.

    Elements are nodes with properties stored as node attributes.
    Relationships are directed edges with typed labels. This backend
    enables graph analysis (shortest paths, centrality, cycles) and
    scales to projects that exceed simple tree structures.

    Requires: pip install networkx
    """

    def __init__(self, directed: bool = True):
        """Initialize a NetworkX-based graph store.

        Parameters
        ----------
        directed : bool
            If True (default), creates a MultiDiGraph. If False, creates
            a MultiGraph for undirected relationships.
        """
        import networkx as nx
        if directed:
            self._graph = nx.MultiDiGraph()
        else:
            self._graph = nx.MultiGraph()
        self._nx = nx

    def put(self, element_id: str, data: dict,
            parent_id: Optional[str] = None,
            rel_type: str = REL_PARENT_CHILD) -> None:
        """Store an element as a graph node and optionally add an edge to a parent.

        Parameters
        ----------
        element_id : str
            Unique identifier for the element.
        data : dict
            Element attributes stored as node properties.
        parent_id : str, optional
            Parent element ID to create a directed edge.
        rel_type : str, optional
            Edge label/type. Default is REL_PARENT_CHILD.
        """

        if parent_id is not None:
            self._graph.add_edge(parent_id, element_id,
                                  rel_type=rel_type, **{"_rel": rel_type})

    def get(self, element_id: str) -> Optional[dict]:
        """Retrieve a node's attributes by ID.

        Parameters
        ----------
        element_id : str
            Node ID to look up.

        Returns
        -------
        dict or None
            Node attributes dict, or None if not found.
        """
        if not self._graph.has_node(element_id):
            return None
        return dict(self._graph.nodes[element_id])

    def delete(self, element_id: str) -> bool:
        """Remove a node and all its incident edges.

        Parameters
        ----------
        element_id : str
            Node ID to remove.

        Returns
        -------
        bool
            True if the node was found and deleted, False otherwise.
        """
        if not self._graph.has_node(element_id):
            return False
        self._graph.remove_node(element_id)
        return True

    def children(self, parent_id: str, rel_type: str = REL_PARENT_CHILD) -> list[str]:
        """Get child element IDs connected by outgoing edges of the given type.

        Parameters
        ----------
        parent_id : str
            Parent node ID.
        rel_type : str
            Filter by edge relationship type. Default is REL_PARENT_CHILD.

        Returns
        -------
        list[str]
            List of child node IDs.
        """
        if not self._graph.has_node(parent_id):
            return []
        result = []
        for _, child, data in self._graph.out_edges(parent_id, data=True):
            if data.get("rel_type") == rel_type:
                result.append(child)
        return result

    def parents(self, child_id: str, rel_type: Optional[str] = None) -> list[str]:
        """Get parent element IDs connected by incoming edges.

        Parameters
        ----------
        child_id : str
            Child node ID.
        rel_type : str, optional
            Filter by edge relationship type. If None, returns all parents.

        Returns
        -------
        list[str]
            List of parent node IDs.
        """
        if not self._graph.has_node(child_id):
            return []
        result = []
        for parent, _, data in self._graph.in_edges(child_id, data=True):
            if rel_type is None or data.get("rel_type") == rel_type:
                result.append(parent)
        return result

    def relationships(self, element_id: str,
                      rel_type: Optional[str] = None,
                      direction: str = "both") -> list[tuple[str, str, dict]]:
        """Get all relationships (edges) connected to a node.

        Parameters
        ----------
        element_id : str
            Node ID to query.
        rel_type : str, optional
            Filter by edge relationship type.
        direction : str
            "out" (outgoing edges), "in" (incoming edges), or "both" (default).

        Returns
        -------
        list[tuple[str, str, dict]]
            List of (target_id, rel_type, edge_data) tuples.
        """
        if not self._graph.has_node(element_id):
            return []

        edges = []
        if direction in ("out", "both"):
            for _, target, data in self._graph.out_edges(element_id, data=True):
                rt = data.get("rel_type", "")
                if rel_type is None or rt == rel_type:
                    edges.append((target, rt, dict(data)))
        if direction in ("in", "both"):
            for source, _, data in self._graph.in_edges(element_id, data=True):
                rt = data.get("rel_type", "")
                if rel_type is None or rt == rel_type:
                    edges.append((source, rt, dict(data)))
        return edges

    def query(self, **filters) -> list[str]:
        """Find nodes matching property filters.

        Parameters
        ----------
        **filters : dict
            Node attribute name=value pairs to match.
            Supports glob patterns with '*' for the 'name' field.

        Returns
        -------
        list[str]
            List of matching node IDs.
        """
        results = []
        for node, data in self._graph.nodes(data=True):
            match = True
            for key, value in filters.items():
                if key == "name" and "*" in str(value):
                    import fnmatch
                    if not fnmatch.fnmatch(data.get("name", ""), value):
                        match = False
                        break
                elif data.get(key) != value:
                    match = False
                    break
            if match:
                results.append(node)
        return results

    def has(self, element_id: str) -> bool:
        """Check if a node exists in the graph.

        Parameters
        ----------
        element_id : str
            Node ID to check.

        Returns
        -------
        bool
            True if the node exists, False otherwise.
        """
        return self._graph.has_node(element_id)

    def __len__(self) -> int:
        """Return the number of nodes in the graph.

        Returns
        -------
        int
            Number of nodes.
        """
        return self._graph.number_of_nodes()

    def ids(self) -> Iterator[str]:
        """Iterate over all node IDs in the graph.

        Returns
        -------
        iterator of str
            Iterator over node IDs.
        """
        return iter(self._graph.nodes())

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        self._graph.clear()

    # ── Graph-specific methods ──────────────────────────────────────────

    def descendants(self, root_id: str, rel_type: str = REL_PARENT_CHILD) -> list[str]:
        """Return all descendants via BFS on the graph."""
        if not self._graph.has_node(root_id):
            return []
        try:
            return list(self._nx.descendants(self._graph, root_id))
        except self._nx.NetworkXError:
            return []

    def ancestors(self, leaf_id: str, rel_type: str = REL_PARENT_CHILD) -> list[str]:
        """Return all ancestors via reverse BFS on the graph."""
        if not self._graph.has_node(leaf_id):
            return []
        try:
            return list(self._nx.ancestors(self._graph, leaf_id))
        except self._nx.NetworkXError:
            return []

    def path(self, source_id: str, target_id: str,
             rel_type: str = REL_PARENT_CHILD) -> Optional[list[str]]:
        """Find shortest path using NetworkX native algorithm."""
        if not self._graph.has_node(source_id) or not self._graph.has_node(target_id):
            return None
        try:
            return self._nx.shortest_path(self._graph, source_id, target_id)
        except self._nx.NetworkXNoPath:
            return None

    def connected_components(self, rel_type: Optional[str] = None) -> list[set[str]]:
        """Return weakly connected components of the graph.

        Parameters
        ----------
        rel_type : str, optional
            If provided, only considers edges of this relationship type.

        Returns
        -------
        list[set[str]]
            List of sets, each containing node IDs in a connected component.
        """
        if rel_type:
            subgraph = self._nx.subgraph_view(
                self._graph,
                edge_filter=lambda e: self._graph.edges[e].get("rel_type") == rel_type
            )
            return list(self._nx.weakly_connected_components(subgraph))
        return list(self._nx.weakly_connected_components(self._graph))

    def cycles(self, rel_type: Optional[str] = None) -> list[list[str]]:
        """Find all simple cycles in the graph.

        Parameters
        ----------
        rel_type : str, optional
            If provided, only considers edges of this relationship type.

        Returns
        -------
        list[list[str]]
            List of cycles, each represented as a list of node IDs.
        """
        if rel_type:
            subgraph = self._nx.subgraph_view(
                self._graph,
                edge_filter=lambda e: self._graph.edges[e].get("rel_type") == rel_type
            )
            return list(self._nx.simple_cycles(subgraph))
        return list(self._nx.simple_cycles(self._graph))

    def centrality(self, rel_type: Optional[str] = None) -> dict[str, float]:
        """Compute degree centrality for all nodes.

        Parameters
        ----------
        rel_type : str, optional
            If provided, only considers edges of this relationship type.

        Returns
        -------
        dict[str, float]
            Mapping of node ID to centrality score (0.0 to 1.0).
        """
        if rel_type:
            subgraph = self._nx.subgraph_view(
                self._graph,
                edge_filter=lambda e: self._graph.edges[e].get("rel_type") == rel_type
            )
            return self._nx.degree_centrality(subgraph)
        return self._nx.degree_centrality(self._graph)

    def subgraph(self, element_ids: list[str]) -> "NetworkXStore":
        """Create a new store containing only the specified elements and their edges.

        Parameters
        ----------
        element_ids : list[str]
            Node IDs to include in the subgraph.

        Returns
        -------
        NetworkXStore
            A new store with a copy of the induced subgraph.
        """
        new_store = NetworkXStore()
        new_store._graph = self._graph.subgraph(element_ids).copy()
        return new_store

    def export_graphml(self, path: str) -> None:
        """Export the graph to GraphML format for visualization in external tools.

        Parameters
        ----------
        path : str
            File path to write the GraphML file to.
        """
        self._nx.write_graphml(self._graph, path)

    def stats(self) -> dict:
        """Compute summary statistics about the graph.

        Returns
        -------
        dict
            Dictionary with keys: nodes, edges, density, is_connected, avg_degree.
        """
        return {
            "nodes": self._graph.number_of_nodes(),
            "edges": self._graph.number_of_edges(),
            "density": self._nx.density(self._graph),
            "is_connected": self._nx.is_weakly_connected(self._graph) if self._graph.number_of_nodes() > 0 else True,
            "avg_degree": sum(dict(self._graph.degree()).values()) / max(self._graph.number_of_nodes(), 1),
        }


# ── ID Generation ───────────────────────────────────────────────────────────

def new_id() -> str:
    """Generate a new stable UUID for an element."""
    return str(uuid.uuid4())


# ── Store Factory ───────────────────────────────────────────────────────────

def create_store(backend: str = "memory", **kwargs) -> Store:
    """Create a storage backend by name.

    Parameters
    ----------
    backend : str
        "memory" for InMemoryStore, "networkx" for NetworkXStore.
    **kwargs
        Passed to the store constructor.

    Returns
    -------
    Store
        An initialized storage backend.
    """
    backends = {
        "memory": InMemoryStore,
        "inmemory": InMemoryStore,
        "networkx": NetworkXStore,
        "nx": NetworkXStore,
        "graph": NetworkXStore,
    }
    cls = backends.get(backend.lower())
    if cls is None:
        raise ValueError(f"Unknown backend: {backend}. Choose from: {list(backends.keys())}")
    return cls(**kwargs)
