# Stable Element Identities — Scoping for Idempotent Interchange

> **Status:** scope / not yet implemented
> **For:** projects that need the same SysML v2 model to produce the
> *same element identifiers* across parses, tools, and incremental
> edits — not just across round-trips.
> **Companion demo:** `examples/element_identity.py` (what exists today)

---

## 1. Problem statement

sysmlpy's interchange layer already assigns every element a
deterministic `@id` (uuid5 under a fixed namespace). That satisfies the
"parse the same text twice, get identical JSON" level of idempotency.
It does **not** survive edits that change structure before the element
in question. Verified behaviour (probes, 2026-09-28):

| Edit before `part def Engine` | Engine's `@id` |
|---|---|
| none (same text) | `sysml:d1959147…` — stable |
| ancestor package renamed `P` → `Q` | **stable** (wrapper nodes are unnamed; the hash chain runs through them) |
| sibling declared *after* it | **stable** (its own index is unchanged) |
| sibling declared *before* it | **shifts** — new uuid5 |
| element moved one nesting level deeper | **shifts** — new uuid5 |

So the current id encodes *structural position* (depth + sibling
index), not *what the element is*. Diff-friendly for unchanged text,
fragile for evolving models — the exact case a persistent store
(kuzu/networkx/cayley backend) or a cross-tool traceability pipeline
cares about.

## 2. Idempotency levels

| Level | Guarantee | Today |
|---|---|---|
| L0 | dump → parse → dump is fixed-point | ✅ |
| L1 | same text re-parsed → identical `@graph` | ✅ (uuid5 position ids) |
| L2 | insertion/reordering elsewhere in the document keeps ids of untouched elements | ❌ |
| L3 | same element across independently maintained documents (renamed parents, split packages) resolves to one identity | ❌ |

The store layer (`store.py`) is already keyed by element UUID and is
the natural consumer of L2; multi-repo/ ReqIF traceability wants L3.

## 3. Options

### A. Content-addressed uuid5 (recommended for L2)

Replace `_child_id(parent_id, key, index)` with a hash over the
element's *identity path*: resolved qualified name + `@type`
(+ occurrence index among content-identical siblings as tie-breaker).

- Pros: pure-python change localized to `interchange.py`; ids stable
  under insertion/reorder elsewhere; no source changes needed; the
  namespace/`sysml:` prefix machinery stays.
- Cons (measured): name collisions are real — two sibling
  `part def Engine` declarations hash to the same key. Tie-breaker
  (occurrence index among same-key siblings) reintroduces position
  sensitivity *only within the colliding group*, which is an acceptable
  degradation: untouched elements outside the group keep their ids.
- Needs the resolver: qualified names require `semantic.py`'s
  SymbolTable walk during export (already importable; export currently
  stays resolver-free).

### B. Canonical-subtree hashing (L2 robust, heavier)

Hash a canonical serialization of the element's *subtree* (sorted keys,
ids replaced by recursion). Collision-tolerant and rename-resistant
within the subtree; survives re-parenting only if the parent name is
part of the QN anyway. More implementation and spec work (canonical
form must be pinned by tests, like JSON canonicalization); use only if
A's tie-breaker behaviour is unacceptable.

### C. Source-carried explicit ids (L3, spec-aligned)

SysML v2's interchange `@id` is tool-assigned; the textual syntax has no
standard id slot. For cross-document identity, carry ids explicitly:

- doc-comment convention: `doc /* @id: sysml:… */` (already parsed as
  `.doc` on every element since v0.96.1);
- or a sidecar mapping file (text → id) maintained by the project.

Exporter honors an explicit id when present, mints per option A
otherwise. This is the only scheme that survives arbitrary re-factoring
and is honest about identity being *assigned*, not derived. Cost: a
convention the other project must adopt and preserve.

### D. Do nothing for L3

Match on resolved qualified names at query time (semantic.py already
resolves across imports). No id stability needed if consumers can key
on `P::Sub::Engine`. Often sufficient; cheapest.

## 4. Recommended scope

Phase 1 (L2) — **IMPLEMENTED (v0.96.3)**:

1. ✅ `interchange.py`: `to_interchange(..., stable_ids=False)` — when
   True, ids are uuid5 over the **declared** qualified-name path
   (syntax-derived, no resolver: `P.Engine.power` style chains of
   `Identification.declaredName` from root) + `@type`; anonymous /
   unresolved elements hash the nearest named anchor plus the
   structural path from it (option-A resolved-QN variant deliberately
   deferred — declared path keeps export resolver-free and
   machine-independent).
2. ✅ Anonymous elements keep anchor-relative keys — documented that
   anonymous identity follows the nearest declared ancestor.
3. ✅ Tests (`tests/interchange_test.py::TestStableIds`): L1
   byte-identity, the §1 edit matrix as parametrized cases
   (sibling before/after, inner-feature insertion), ancestor-rename
   and re-nesting identity-follows-content semantics, collision-group
   uniqueness, graph-wide uniqueness on the rich model, round trip,
   and default-path invariance (`stable_ids=False` byte-identical to
   the v0.63.0 behaviour).
4. ✅ `store.py` upsert verified on the memory backend: same stable id
   updates the stored element in place (stores are UUID-keyed by
   design).  networkx/kuzu/cayley backends are optional-dependency
   gated in this environment (their test failures are pre-existing,
   unrelated to ids).
5. ✅ CLI: `sysmlpy export --stable-ids`.

Phase 2 (L3) — **IMPLEMENTED (v0.96.3, registry variant)**:

- `reconcile_ids(document, registry)` — adopt ids from a previous
  export (dict, JSON text, or a filesystem `Path`/path str).
  Injective matching: (declaredName, @type) must be unique on BOTH
  sides, each registry id adopted at most once; ambiguous keys keep
  derived ids.
- `to_interchange(..., reconcile_with=...)` convenience — implies
  `stable_ids=True`.
- **Nested-ref remap:** adoption rewrites not just the element's
  top-level `@id` but every nested `{"@id": <derived>}` reference
  pointing at it (typed-by references, member chains) — without the
  remap, documents whose *identity* was reconciled dangle on import
  (found by `test_reconcile_result_round_trips` during this build).
- CLI: `sysmlpy export --reconcile-with model.json -o model.json` —
  idempotent fixed point after the first export.
- Tests (10): rename+insert motivating case, JSON-text registry,
  graph-wide uniqueness after reconcile (the spike's dupes pitfall),
  no-adoption for renamed/ambiguous elements, three-round file
  workflow, injectivity on same-name groups, error guards,
  `reconcile_with=` convenience flag, reconciled round trip.
- Registry-file str/Path disambiguation: a str is treated as a path
  only when it is < 4097 chars, single-line, and exists — otherwise
  it parses as JSON text (a JSON *body* pasted inline must not be
  `open()`ed as a filename).

Remaining gap to full L3: elements renamed so thoroughly that no
declared name matches stay unmatched (fresh derived ids; they become
registry entries on the next write).  The doc-comment `@id:`
convention (option C below) removes even that.

### Phase 2b (L3, source-carried explicit ids) — IMPLEMENTED
(v0.96.4, released on main)

- **Carrier (verified safe-shape):** a ``doc /* @id: … */`` comment
  INSIDE the element's own braces attaches to that element (`.doc`
  on the public tree); doc text survives ``dump()`` → re-parse
  idempotently.  **Pitfall pinned by tests:** a doc statement at
  *sibling* level (outside the element's braces) bubbles to the
  enclosing package — placement decides the owner
  (``test_explicit_id_attach_point_semantics``).
- **Harvest:** ``_harvest_doc_ids(model)`` walks the public tree
  (`.doc` populated on every kind), mapping declared QN path → the
  ``@id:`` token in the comment; the Model root's per-parse uuid
  name is skipped.  Returns ``None`` on plain models so
  ``doc_ids=True`` stays inert (byte-identical to ``stable_ids``
  output — pinned by ``test_plain_models_unaffected``).
- **Precedence:** explicit > registry > derive; never re-minted over
  an explicit id (``_StableIdAssigner(explicit_ids=...)``).
- **Qn-path bridge:** the assigner receives repeat-tail paths
  (``('P','P','P')`` — one segment per declaration/identification
  nesting level); ``_dedupe_repeat_tail`` collapses them so the
  harvest key (``'P.Engine'``) matches.  Adoption gates on the node
  being the Identification whose deduped path == the key (Package
  and PackageDeclaration keep derived ids — probe2j).
- **Duplicate-id export error:** two elements claiming the same
  explicit id (same QN key twice, or different keys → same id
  value) raise ``ValueError`` — enforced on the id VALUE
  (probe2l).
- **Verified end to end:** export → dump → re-parse → export keeps
  the explicit id; full interchange round trip
  (``from_interchange``) keeps it; graph-wide uniqueness; 12 new
  tests (``tests/interchange_test.py::TestDocIds``).
- API: ``to_interchange(..., doc_ids=True)`` (implies
  ``stable_ids``).

Deferred (see §5): import-side re-embedding of explicit ids into
``dump()`` text (``--embed-ids``) — dump shapes are pinned by the
168 round-trip tests; the doc carrier survives dumps as-is for
elements whose bodies start with their doc comment, so full
re-embedding is a tightening, not a correctness gap.

### Design decision recorded: declared-path, not resolved-QN

Option A as scoped mentioned hashing the *resolved* qualified name via
`semantic.py`.  Implementation uses the **declared** path instead
(chain of `Identification.declaredName` from root): resolution depends
on library availability and import resolution, which would make ids
machine-dependent — defeating idempotency.  Consequence: ids follow
declared identity, so renaming an ancestor re-mints descendant ids
(verified in `test_qn_follows_declared_identity`).  The position scheme
accidentally survived ancestor renames; the content scheme intentionally
does not.  Trade-off documented here rather than hidden.

## 5. Risks / open questions

- Resolved-QN depends on import resolution settings; a model whose
  imports resolve differently on another machine gets different ids.
  Mitigation: hash the *declared* QN path (pure syntax) rather than the
  resolved one, and document the difference.
- Changing the default id scheme breaks byte-comparisons against
  previously exported JSON — hence the opt-in flag and a CHANGELOG
  note; consider a `--stable-ids` CLI flag on `sysmlpy export`.
- Same-name sibling collision groups grow/shrink on edit; ids inside
  the group shift by design (tie-breaker index). Acceptable if
  documented; option C removes it entirely.
## 6. Object-model mirror (option D) — `sysmlpy.stable_ids()` (v0.101.0, issue #27)

**Decision.** A downstream consumer asked for deterministic identity on
the *object model* (`repro_05`: every parse of identical text minted a
fresh uuid4 `name` on anonymous members, churning identity maps). Of the
two asks (leave `name=None`, or derive the id from content/position), the
shipped decision is **both, in separate slots**:

- **`name` stays a content slot.** Anonymous members now keep
  `name=None` (the satisfy/verify/dependency members already did).
  Minted uuid4 names churned per parse; a *derived* id placed in `name`
  would be worse — `name` serializes as a `declaredName`, so the model
  would gain declared content it never had.
- **UUIDv5 lives in the id slot**: `sysmlpy.stable_ids(model)` returns
  `{element: "sysml:<uuid5>"}` and `element.stable_id` reads it.

**Contract.**

- Declared (named) elements join through the export's `#qn_registry`
  side table — their id **is** the node `@id` in
  `to_interchange(model, stable_ids=True)`: exact agreement with the
  JSON by construction, for nested members and name-collision groups
  alike.
- Anonymous members derive `uuid5(STABLE_NAMESPACE, qn || struct |type)`
  over the public tree (`children:<index>` chains). Documented bound:
  the JSON flattener walks the rebuilt dict tree (wrapper nodes
  included), so an anonymous member's *string* differs between the
  object model and the JSON while both are content-addressed and stable
  under the same edit classes. Declared-element agreement is the
  load-bearing contract.
- The `Model` root keeps its per-parse uuid (documented above); it is
  not a member, never serializes as content, and is skipped by every
  identity walk (`_MODEL_NAME_RE`).
- Same-name sibling groups: distinct occurrence-indexed ids on both
  sides; ids inside a group shift on group-local insertion (L2
  degradation, unchanged).

**Side-table defect fixed en route (v0.101.0).** The registry's
same-name-sibling branch stored a literal `...` (Ellipsis) placeholder
instead of the second occurrence's node id, and keyed it by the raw
dict-tree qn. It now keys `"<deduped-qn>#<index>"` and carries the
actual node id — the join the object-model mirror relies on.

**Bounds.** Renaming an ancestor re-mints descendant ids (declared-path
hashing, by design — see §2/L2). Programmatic members built without
grammar join the anonymous path. `stable_id` recomputes the map per
access; bulk readers hold `stable_ids(model)` directly.
