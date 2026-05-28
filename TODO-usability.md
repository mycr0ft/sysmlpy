# sysmlpy Usability Improvement Backlog

Generated from API audit on 2026-05-27.  
See `AGENTS.md` for codebase conventions before implementing.  
Run `poetry run pytest tests/ -m "not conformance" --tb=short -q` after each change.

---

## Tier 1 — High Impact, Trivial Effort (< 1 hour each)

### T1-1: Export `SysMLSyntaxError` from the package root

**File:** `src/sysmlpy/__init__.py`  
**Problem:** `from sysmlpy import SysMLSyntaxError` raises `ImportError`. Every user who
catches parse errors must know the internal submodule path `sysmlpy.antlr_parser`.

**Fix:**
```python
# Add to imports in __init__.py
from sysmlpy.antlr_parser import SysMLSyntaxError

# Add to __all__
"SysMLSyntaxError",
```

**Test:** `assert sysmlpy.SysMLSyntaxError is not None`

---

### T1-2: Fix stale `load()` and `load_antlr()` docstrings

**File:** `src/sysmlpy/__init__.py` lines ~102 and ~170  
**Problem:** Both docstrings say "Returns: dict" but both functions return `Model`.
This is a copy-paste from the old grammar-level API.

**Fix:** Change "Returns: dict" to "Returns: Model" in both docstrings.
Also add return type annotations:
```python
def load(fp) -> Model:
def load_antlr(fp, ...) -> Model:
def loads(s: str, library=None) -> Model:
```

---

### T1-3: Remove `print()` side effect on parse error

**File:** `src/sysmlpy/__init__.py` line ~98  
**Problem:** Library code prints to stdout when a `SysMLSyntaxError` is raised,
even when the caller is catching the exception. Pollutes CI pipelines.

**Fix:** Delete this line:
```python
print("ANTLR4 returned the following error: {}".format(e))
```

**Note:** The exception message already contains the full error text — the print is redundant.

---

### T1-4: Add `find_one()` to `Searchable`

**File:** `src/sysmlpy/navigate.py`  
**Problem:** `model.find('Engine')[0]` silently raises `IndexError` when nothing
is found. This is the most common debugging trap in the codebase.

**Fix:** Add to the `Searchable` mixin:
```python
def find_one(self, name=None, *, sysml_type=None):
    """Return the single matching element, or None if not found.

    Raises LookupError if more than one match is found.
    Use find() if you expect multiple results.
    """
    results = self.find(name, type=sysml_type)
    if not results:
        return None
    if len(results) > 1:
        raise LookupError(
            f"find_one: {len(results)} matches for {name!r}, expected at most 1"
        )
    return results[0]
```

**Tests to add:** `tests/navigate_test.py`
- Returns element when exactly one match
- Returns None when no match (does NOT raise)
- Raises LookupError when multiple matches

---

## Tier 2 — High Impact, Medium Effort (1–3 hours each)

### T2-1: Add `add_child()` as a public alias for `_set_child()`

**File:** `src/sysmlpy/usage.py`, `src/sysmlpy/definition.py`  
**Problem:** The entire mutation API is underscore-private while the README
documents `_set_child()` as the primary way to build models. When a user calls
`parent.children.append(child)` directly, `child.parent` is never set, silently
breaking `path_between()` and parent-traversal logic.

**Fix:** Add public `add_child()` on `Usage`, `Package`, and `Model`:
```python
def add_child(self, child) -> 'Usage':
    """Add *child* to this element and set child.parent.

    Returns self for chaining:
        pkg.add_child(Part(name='engine')).add_child(Part(name='wheel'))
    """
    self.children.append(child)
    child.parent = self
    return self
```

Keep `_set_child()` as a backward-compatible alias pointing to `add_child()`.

**Tests to add:** `tests/class_test.py`
- `add_child()` sets `child.parent` correctly
- `add_child()` returns `self` (fluent)
- Chained calls work

---

### T2-2: Add `__iter__`, `__len__`, `__contains__` to `Model`, `Package`, and `Usage`

**File:** `src/sysmlpy/navigate.py` (add to `Searchable` mixin)  
**Problem:** The most natural Python iteration patterns fail:
```python
for pkg in model:      # TypeError: 'Model' object is not iterable
len(model)             # TypeError: object of type 'Model' has no len()
'Engine' in model      # TypeError
```

**Fix:** Add to `Searchable`:
```python
def __iter__(self):
    """Iterate over direct children."""
    return iter(self.children)

def __len__(self) -> int:
    """Return the number of direct children."""
    return len(self.children)

def __contains__(self, item) -> bool:
    """True if item is a direct child, or if a string matches any child's name."""
    if isinstance(item, str):
        return any(getattr(c, 'name', None) == item for c in self.children)
    return item in self.children
```

**Tests to add:** `tests/navigate_test.py`
- `for x in model` iterates children
- `len(model)` returns child count
- `'PackageName' in model` returns True/False by name
- `part_instance in package` returns True/False by identity

---

### T2-3: Add `__str__` returning SysML text

**File:** `src/sysmlpy/usage.py`, `src/sysmlpy/definition.py`  
**Problem:** `print(part)` gives `Part(name='engine')` rather than `part engine;`.
Users expect `str()` to give a human-readable representation. `repr()` (the
constructor-mirroring form) is more appropriate for debugging.

**Fix:** Add `__str__` to `Usage`, `Package`, and `Model` delegating to `dump()`:
```python
def __str__(self) -> str:
    """Return the SysML v2 text representation of this element."""
    try:
        return self.dump()
    except Exception:
        return repr(self)   # graceful fallback
```

**Tests to add:** `tests/repr_test.py`
- `str(part)` returns the SysML text (contains `part` keyword)
- `str(part_def)` returns the SysML text (contains `part def` keywords)
- `repr(part)` still returns `Part(name='engine')`
- `str()` and `repr()` are different

---

### T2-4: Add `strict=True` and `AnalysisResult` to `analyze()`

**File:** `src/sysmlpy/semantic.py`, `src/sysmlpy/__init__.py`  
**Problem:** Callers must write a 3-line filter loop every time they want to
raise on errors. No direct `.errors` / `.warnings` access.

**Fix A — strict flag (minimal):**
```python
def analyze(model, *, library=None, filename=None,
            style_checks=True, strict=False) -> list[SemanticIssue]:
    issues = ...  # existing logic
    if strict:
        errors = [i for i in issues if i.severity == 'error']
        if errors:
            msg = "\n".join(f"[{i.code}] {i.message}" for i in errors)
            raise ValueError(f"Semantic errors found:\n{msg}")
    return issues
```

**Fix B — AnalysisResult (richer, backward-compatible since it's a list subclass):**
```python
class AnalysisResult(list):
    """A list of SemanticIssue with convenience accessors."""

    @property
    def errors(self) -> list[SemanticIssue]:
        return [i for i in self if i.severity == 'error']

    @property
    def warnings(self) -> list[SemanticIssue]:
        return [i for i in self if i.severity == 'warning']

    def raise_on_errors(self, message: str = "Semantic errors found") -> 'AnalysisResult':
        if self.errors:
            details = "\n".join(f"  [{i.code}] {i.message}" for i in self.errors)
            raise ValueError(f"{message}:\n{details}")
        return self

    def __bool__(self) -> bool:
        """True if there are no errors (warnings are acceptable)."""
        return len(self.errors) == 0
```

Recommend implementing **both** (strict for quick scripts, AnalysisResult for production code).

**Tests to add:** `tests/semantic_test.py`
- `analyze(model, strict=True)` raises ValueError when model has errors
- `analyze(model, strict=True)` does not raise when model is clean
- `result.errors` returns only error-severity issues
- `result.warnings` returns only warning-severity issues
- `result.raise_on_errors()` raises ValueError
- `bool(result)` is True for clean model, False for errored model
- `AnalysisResult` is still iterable as a list (backward compat)

---

### T2-5: Rename `type=` parameter in `find()` to `sysml_type=`

**File:** `src/sysmlpy/navigate.py`  
**Problem:** `find(name, type=None)` shadows the Python builtin `type`. The
parameter is used inside the method body both as a value and as a class check,
which is confusing to read and breaks code completion in some IDEs.

**Fix:**
```python
def find(self, name=None, *, sysml_type=None, recursive=True):
    ...
```

Add a backward-compatible shim:
```python
def find(self, name=None, *, sysml_type=None, type=None, recursive=True):
    if type is not None and sysml_type is None:
        import warnings
        warnings.warn(
            "find(type=...) is deprecated; use find(sysml_type=...) instead",
            DeprecationWarning, stacklevel=2
        )
        sysml_type = type
```

Also update `all()` and `find_all()` to use `sysml_type=`.

**Tests to add:** `tests/navigate_test.py`
- `find(sysml_type='part')` returns parts
- `find(type='part')` still works but emits DeprecationWarning
- `find_one(sysml_type='part')` works

---

## Tier 3 — Polish (lower urgency)

### T3-1: Add `_repr_html_` for Jupyter notebook display

**File:** `src/sysmlpy/definition.py`, `src/sysmlpy/usage.py`  
**Problem:** In Jupyter, `model` displays as a plain string. A collapsible HTML
tree would make sysmlpy much more pleasant for interactive exploration.

**Fix:** Add to `Model` and `Package`:
```python
def _repr_html_(self) -> str:
    """Jupyter-friendly HTML tree representation."""
    def _render(elem, depth=0):
        name = getattr(elem, 'name', '?')
        stype = getattr(elem, 'sysml_type', type(elem).__name__)
        is_def = getattr(elem, 'is_definition', False)
        badge = f'<code style="color:#888;font-size:0.8em">{stype}{"_def" if is_def else ""}</code>'
        children = getattr(elem, 'children', [])
        if children:
            inner = ''.join(_render(c, depth+1) for c in children)
            return (f'<details open><summary>{badge} <b>{name}</b></summary>'
                    f'<div style="margin-left:1em">{inner}</div></details>')
        return f'<div>{badge} {name}</div>'
    return f'<div style="font-family:monospace">{_render(self)}</div>'
```

---

### T3-2: Non-raising parse variant `sysmlpy.parse()`

**File:** `src/sysmlpy/__init__.py`  
**Problem:** There is no way to attempt a parse without it raising on syntax
errors. IDE integrations and linters need to collect errors as data, not
exceptions.

**Fix:** Add a `parse()` function alongside `loads()`:
```python
def parse(s: str, library=None) -> tuple[Model | None, list[str]]:
    """Parse SysML source, returning (model, errors) rather than raising.

    Returns:
        (Model, [])          on success
        (None, [error_str])  on syntax error
    """
    try:
        return loads(s, library=library), []
    except SysMLSyntaxError as e:
        return None, str(e).splitlines()
```

---

### T3-3: Stabilize mutation API — make private methods public

**Files:** `src/sysmlpy/usage.py`, `src/sysmlpy/definition.py`  
**Problem:** The README and test suite treat these as normal API, but the
underscore prefix signals they are private/internal. This creates a false
expectation of instability for documented functionality.

**Methods to promote** (add public alias, keep private name for compat):

| Private | Public |
|---------|--------|
| `_set_child(child)` | `add_child(child)` ← already in T2-1 |
| `_set_name(name)` | `rename(name)` or `set_name(name)` |
| `_set_typed_by(defn)` | `set_typed_by(defn)` |
| `_set_specializes(*parents)` | `set_specializes(*parents)` |
| `_set_subsets(*parents)` | `set_subsets(*parents)` |
| `_set_redefines(parent)` | `set_redefines(parent)` |
| `_get_child(path)` | `get_child(path)` |

---

### T3-4: Fix `grammar = True` placeholder in `UseCase` and `Action`

**File:** `src/sysmlpy/usage.py`  
**Problem:** When a `UseCase` or `Action` is created as a usage (not a definition),
some code paths assign `self.grammar = True` as a placeholder. Any downstream
code calling `self.grammar.some_method()` gets an obscure
`AttributeError: 'bool' object has no attribute 'some_method'`.

**Fix:** Replace `self.grammar = True` with `self.grammar = None` and add guard
checks in the methods that access `self.grammar`:
```python
# Instead of:
self.grammar = True

# Use:
self.grammar = None  # grammar not populated for usage-form; use dump() for output
```

---

### T3-5: Add `return type annotations` to all public functions

**Files:** `src/sysmlpy/__init__.py`, `src/sysmlpy/navigate.py`, `src/sysmlpy/usage.py`

Incomplete annotations make pyright/mypy unhelpful. Priority order:

| Function | Current | Target |
|----------|---------|--------|
| `loads()` | `-> (none)` | `-> Model` |
| `load()` | `-> (none)` | `-> Model` |
| `load_antlr()` | `-> (none)` | `-> Model` |
| `Searchable.find()` | `-> (none)` | `-> list[Searchable]` |
| `Searchable.all()` | `-> (none)` | `-> list[Searchable]` |
| `Usage.dump()` | `-> (none)` | `-> str` |
| `Package.dump()` | `-> (none)` | `-> str` |
| `Model.dump()` | `-> (none)` | `-> str` |
| All Usage `__init__` | missing | add param types |

---

## Implementation Order

For an agent picking up this file:

1. Start with **T1-1 through T1-4** — all are in different files, can be done
   independently and in parallel. Each is < 30 minutes.
2. Then **T2-1** (`add_child`) — unblocks all model-building use cases.
3. Then **T2-2** (`__iter__` / `__len__`) — very mechanical, no surprises.
4. Then **T2-3** (`__str__`) — one-liner per class.
5. Then **T2-4** (`AnalysisResult`) — most impactful for production users.
6. Then **T2-5** (rename `type=`) — requires touching tests but very mechanical.
7. Tier 3 items can be picked up in any order.

After each item, run:
```bash
poetry run pytest tests/ -m "not conformance" --tb=short -q
```
and confirm the only failures are the known 16 control-flow grammar tests
(which are deferred — see AGENTS.md).

---

## Background Reading

- `src/sysmlpy/navigate.py` — `Searchable` mixin with `find()`, `all()`, typed accessors
- `src/sysmlpy/usage.py` — `Usage` base class (lines 90–450)
- `src/sysmlpy/definition.py` — `Model` and `Package`
- `src/sysmlpy/__init__.py` — public API entry points
- `src/sysmlpy/semantic.py` — `analyze()` and `SemanticIssue`
- `tests/class_test.py` — existing mutation API tests (uses `_set_child`)
- `tests/navigate_test.py` — existing `find()` tests
