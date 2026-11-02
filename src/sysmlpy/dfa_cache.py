# -*- coding: utf-8 -*-
"""Persistent ANTLR DFA cache (v0.84.0 — Adoption Roadmap Goal 11 Batch 5).

The generated SysML v2 parser/lexer share class-level ATN + DFA caches,
so prediction structures are built once per *process* — but every fresh
process (CLI invocation, LSP session start, first test run) pays that
cold-start cost again.  On a 27 KB model the first parse measured
**8.4 s** versus **1.2 s** for an in-process warm parse: ~85 % of the
first parse is adaptive-prediction DFA construction.

This module serializes the warmed parser + lexer ATN/DFA graphs with
``pickle`` after a successful parse and reinstalls them at the start of
subsequent processes, eliminating the cold start.

Both grammars are covered (#35): the SysML v2 parser/lexer and the KerML
parser/lexer (``sysmlpy.kerml``) each have their own key and cache file,
so a grammar change in one never invalidates the other.  A target is only
loaded/saved when its parser was actually used in this process — the
SysML path never imports the KerML classes, and vice versa.

Design notes
------------
* The *whole* reachable graph is pickled (ATN objects, DFA states, the
  prediction-context cache) and assigned back to the generated classes'
  class attributes on load.  Pickle preserves shared substructures, so
  the restored graph is self-consistent — no state re-wiring needed.
* The cache file is keyed by SHA-1 of both serialized ATNs + the
  antlr4 runtime version + the sysmlpy version + pickle protocol, so a
  stale or regenerated grammar can never load a mismatched cache.
* Cache failures must never break parsing: every load/save is wrapped
  and degrades to the normal (uncached) behavior with a one-time
  warning.
* Trust: the cache is read from the user's own cache directory
  (``XDG_CACHE_HOME``/``~/.cache/sysmlpy`` or an explicit override) —
  like any Python pickle it must only contain locally generated data;
  point the directory at a trusted location or disable with
  ``SYSMLPY_DFA_CACHE=off`` (the old misspelling ``SYSSMLPY_DFA_CACHE`` is
  still read as an alias).
"""

from __future__ import annotations

import hashlib
import os
import pickle
import threading
import warnings
from typing import Any, Dict, Optional, Tuple

_CACHE_PROTOCOL = 4          # stable across Python 3.8+; avoids protocol drift
_MAX_CACHE_BYTES = 256 * 1024 * 1024   # refuse absurd cache files on load

#: Grammar families with their own parser/lexer pair and cache file.
#  Each target is keyed by its own serialized ATNs, so a SysML grammar
#  change never invalidates (or corrupts) the KerML cache and vice versa
#  (#35: KerML used to parse cold on every run — Occurrences.kerml ~11 s).
_TARGETS = ("sysml", "kerml")

# RLock: stats()/set_dfa_cache() re-enter while held
_lock = threading.RLock()
_state: Dict[str, Any] = {
    "enabled": None,        # None = not overridden by set_dfa_cache()
    "directory": None,      # None = default (env/XDG/~/.cache/sysmlpy)
    #: per-target load/save bookkeeping, see ``_tstate``
    "targets": {},
    #: targets whose parser actually ran in this process (exit-hook scope)
    "used": set(),
}


def _tstate(target: str = "sysml") -> Dict[str, Any]:
    """Per-target bookkeeping dict (created on demand)."""
    with _lock:
        states = _state["targets"]
        if target not in states:
            states[target] = {
                "load_attempted": False,
                "loaded": False,
                "file_states": 0,     # DFA states in the cache file at load
                "save_attempted": False,
                "saved": False,
                "saved_states": 0,
            }
        return states[target]


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------


_ENV_VARS = ("SYSMLPY_DFA_CACHE", "SYSSMLPY_DFA_CACHE")
"""Cache env var, canonical first.

``SYSSMLPY_DFA_CACHE`` (three S) is the historic misspelling that shipped
in earlier releases; it never matched the package name.  Both spellings are
read — canonical first — so existing scripts keep working.
"""


def _env_value() -> str:
    for name in _ENV_VARS:
        val = os.environ.get(name)
        if val is not None and val.strip():
            return val.strip()
    return ""


def _env_disabled() -> bool:
    return _env_value().lower() in (
        "0", "off", "false", "no", "disable", "disabled")


def _env_directory() -> Optional[str]:
    val = _env_value()
    if val and val.lower() not in (
            "0", "off", "false", "no", "disable", "disabled", "on", "1",
            "true", "yes", "enable", "enabled"):
        return val
    return None


def is_enabled() -> bool:
    """Whether the DFA cache should participate in parsing."""
    with _lock:
        if _state["enabled"] is not None:
            return _state["enabled"]
    return not _env_disabled()


def set_dfa_cache(enabled: Optional[bool] = None,
                  directory: Optional[str] = None) -> Dict[str, Any]:
    """Configure the persistent DFA cache.

    Parameters
    ----------
    enabled : bool, optional
        ``True``/``False`` force the cache on/off for this process;
        ``None`` (default) keeps the ``SYSMLPY_DFA_CACHE`` env default.
    directory : str, optional
        Override the cache directory for this process; ``None`` keeps
        the env/default location.

    Returns
    -------
    dict
        ``{"enabled": bool, "directory": str}`` — the effective settings.
    """
    with _lock:
        if enabled is not None:
            _state["enabled"] = bool(enabled)
        if directory is not None:
            _state["directory"] = directory
        return {"enabled": is_enabled(),
                "directory": _cache_directory()}


def _cache_directory() -> str:
    with _lock:
        override = _state["directory"]
    if override:
        return override
    env_dir = _env_directory()
    if env_dir:
        return env_dir
    root = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser(
        os.path.join("~", ".cache"))
    return os.path.join(root, "sysmlpy")


def cache_key(target: str = "sysml") -> str:
    """Stable key binding one target's cache file to its grammar + runtime."""
    import antlr4 as _antlr4

    P, L = _target_classes(target)
    Pmod, Lmod = _target_modules(target)
    parts = [
        target,
        _serialized_atn(Pmod, P),
        _serialized_atn(Lmod, L),
        getattr(P, "grammarFileName", target + "Parser.g4"),
        getattr(L, "grammarFileName", target + "Lexer.g4"),
        "antlr4=" + getattr(_antlr4, "__version__", "unknown"),
        "sysmlpy=" + _sysmlpy_version(),
        f"pickle={_CACHE_PROTOCOL}",
    ]
    h = hashlib.sha1()
    for part in parts:
        # serializedATN() is a list of ints — pickle gives a stable
        # byte form for both lists and strings
        h.update(hashlib.sha1(
            pickle.dumps(part, protocol=_CACHE_PROTOCOL)).digest())
        h.update(b"\x00")
    return h.hexdigest()


def _sysmlpy_version() -> str:
    try:
        import sysmlpy
        return getattr(sysmlpy, "__version__", "unknown")
    except Exception:
        return "unknown"


def cache_file(target: str = "sysml") -> str:
    """Full path of the DFA cache file for this target's grammar version.

    The SysML file keeps its historical ``dfa-<key>.pkl`` name so caches
    written by earlier releases stay valid; every other family is prefixed
    with its name (``dfa-kerml-<key>.pkl``).
    """
    prefix = "dfa" if target == "sysml" else "dfa-" + target
    return os.path.join(_cache_directory(),
                        "%s-%s.pkl" % (prefix, cache_key(target)[:16]))


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------


def _target_classes(target: str = "sysml") -> Tuple[type, type]:
    """(parser, lexer) classes for a grammar family."""
    if target == "kerml":
        from sysmlpy.kerml.KerMLLexer import KerMLLexer as _Lexer
        from sysmlpy.kerml.KerMLParser import KerMLParser as _Parser
        return _Parser, _Lexer
    # NB: ``sysmlpy.antlr`` is a namespace package whose submodule names
    # shadow the class names — import the classes from their modules
    from sysmlpy.antlr.SysMLv2Lexer import SysMLv2Lexer as _Lexer
    from sysmlpy.antlr.SysMLv2Parser import SysMLv2Parser as _Parser
    return _Parser, _Lexer


def _target_modules(target: str = "sysml") -> Tuple[Any, Any]:
    """(parser_module, lexer_module) — where ANTLR puts ``serializedATN()``.

    The generated code defines ``serializedATN`` as a MODULE-level function
    (the class carries only ``atn``/``decisionsToDFA``); keying on the class
    attribute silently fails, so resolve the modules explicitly.
    """
    if target == "kerml":
        import sysmlpy.kerml.KerMLLexer as _Lmod
        import sysmlpy.kerml.KerMLParser as _Pmod
        return _Pmod, _Lmod
    import sysmlpy.antlr.SysMLv2Lexer as _Lmod
    import sysmlpy.antlr.SysMLv2Parser as _Pmod
    return _Pmod, _Lmod


def _serialized_atn(module: Any, cls: type) -> Any:
    """The serialized ATN for a generated parser/lexer (see above)."""
    fn = getattr(module, "serializedATN", None)
    if callable(fn):
        return fn()
    fn = getattr(cls, "serializedATN", None)
    if callable(fn):
        return fn()
    raise AttributeError(
        f"{getattr(cls, '__name__', cls)} exposes no serializedATN()")


def _classes() -> Tuple[type, type]:
    """Backwards-compatible alias for the SysML parser/lexer pair."""
    return _target_classes("sysml")


def _payload(target: str = "sysml") -> Tuple[Any, ...]:
    """The pickled state: parser + lexer ATN/DFA/context-cache attrs."""
    P, L = _target_classes(target)
    return (P.atn, P.decisionsToDFA, P.sharedContextCache,
            L.atn, L.decisionsToDFA)


def _rebind_empty_contexts(payload: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Re-point pickled empty prediction contexts at the live singleton.

    ``EmptyPredictionContext`` is identity-comparable in the runtime
    (``__eq__`` is ``self is other`` and ``isEmpty()`` is
    ``self is self.EMPTY``), so unpickled copies must be replaced by the
    live ``PredictionContext.EMPTY`` singleton, and the shared cache
    rebuilt, or prediction diverges from the pristine parser.
    """
    from antlr4.PredictionContext import (
        PredictionContext as _PC,
        PredictionContextCache,
        EmptyPredictionContext,
    )
    from antlr4.atn.SemanticContext import SemanticContext
    from antlr4.dfa.DFAState import PredPrediction as _PredPrediction

    live_empty = _PC.EMPTY
    live_none = SemanticContext.NONE
    seen: set = set()

    def fix(ctx):
        if ctx is None:
            return None
        if isinstance(ctx, EmptyPredictionContext):
            return live_empty
        cid = id(ctx)
        if cid in seen:
            return ctx
        seen.add(cid)
        # NB: SingletonPredictionContext stores its parent as
        # ``parentCtx``; ArrayPredictionContext as ``parents``
        parent = getattr(ctx, "parentCtx", None)
        if parent is not None:
            ctx.parentCtx = fix(parent)
        parents = getattr(ctx, "parents", None)
        if parents is not None:
            ctx.parents = [fix(p) for p in parents]
        return ctx

    def fix_sem(sc):
        if sc is None:
            return None
        if isinstance(sc, type(live_none)):
            return live_none
        return sc

    P_ctx = payload[2]
    rebuilt = PredictionContextCache()
    for ctx in P_ctx.cache.values():
        rebuilt.add(fix(ctx))

    # DFA config sets also hold prediction contexts that never made it
    # into the shared cache — rebind those graphs as well
    for dfa_list in (payload[1], payload[4]):
        for dfa in dfa_list:
            for state in dfa.states.values():
                configs = getattr(state, "configs", None)
                if configs is None:
                    continue
                for cfg in getattr(configs, "configs", []) or []:
                    context = getattr(cfg, "context", None)
                    if context is not None:
                        cfg.context = fix(context)
                    cfg.semanticContext = fix_sem(
                        getattr(cfg, "semanticContext", None))
                predicates = getattr(state, "predicates", None)
                if predicates:
                    # antlr4 >= 4.10 stores PredPrediction objects here
                    # (alt/pred slots, pred-first constructor); older
                    # runtimes used (alt, pred) tuples. Normalize the
                    # SemanticContext on either shape — a blind tuple
                    # unpack crashes on the object form ("cannot unpack
                    # non-iterable PredPrediction object"), silently
                    # disabling the persisted cache.
                    fixed_preds = []
                    for entry in predicates:
                        if isinstance(entry, _PredPrediction):
                            if isinstance(entry.pred, type(live_none)):
                                entry.pred = live_none
                            fixed_preds.append(entry)
                        else:
                            alt, pred = entry
                            fixed_preds.append(
                                (alt,
                                 live_none
                                 if isinstance(pred, type(live_none))
                                 else pred))
                    state.predicates = fixed_preds
    return (payload[0], payload[1], rebuilt, payload[3], payload[4])


def _install(payload: Tuple[Any, ...], target: str = "sysml") -> None:
    payload = _rebind_empty_contexts(payload)
    P_atn, P_dfa, P_ctx, L_atn, L_dfa = payload
    P, L = _target_classes(target)
    P.atn = P_atn
    P.decisionsToDFA = P_dfa
    P.sharedContextCache = P_ctx
    L.atn = L_atn
    L.decisionsToDFA = L_dfa


def load_dfa_cache(path: Optional[str] = None,
                   target: str = "sysml") -> bool:
    """Try to install a persisted DFA cache.  Returns True on success.

    Safe to call repeatedly (loads at most once per process per target)
    and never raises: any problem falls back to the normal uncached path
    with a one-time warning.
    """
    state = _tstate(target)
    with _lock:
        if state["load_attempted"]:
            return state["loaded"]
        state["load_attempted"] = True
    if not is_enabled():
        return False
    try:
        path = path or cache_file(target)
        if not os.path.isfile(path):
            return False
        if os.path.getsize(path) > _MAX_CACHE_BYTES:
            raise ValueError("cache file exceeds size guard")
        with open(path, "rb") as f:
            payload = pickle.load(f)
        if not isinstance(payload, tuple) or len(payload) != 5:
            raise ValueError("unexpected cache payload shape")
        file_states = sum(len(dfa.states) for dfa in payload[1])
        file_states += sum(len(dfa.states) for dfa in payload[4])
        with _lock:
            _install(payload, target)
            state["loaded"] = True
            state["file_states"] = file_states
        return True
    except Exception as exc:
        warnings.warn(
            f"DFA cache load failed ({type(exc).__name__}: {exc}); "
            f"parsing continues without it", stacklevel=3)
        return False


def save_dfa_cache(path: Optional[str] = None,
                   target: str = "sysml",
                   force: bool = False) -> bool:
    """Persist one target's (warm) DFA cache.  Returns True when written.

    Never raises; failures degrade to a one-time warning.  Skipped when
    the cache is disabled or nothing new to save.  ``force`` re-attempts a
    save in a process that already saved (the exit hook uses it), still
    only when the in-process DFA is strictly warmer than the file.
    """
    state = _tstate(target)
    with _lock:
        if state["save_attempted"] and not force:
            return state["saved"]
        state["save_attempted"] = True
    if not is_enabled():
        return False
    try:
        path = path or cache_file(target)
        warm_states = sum(len(dfa.states) for dfa in _payload(target)[1])
        warm_states += sum(len(dfa.states) for dfa in _payload(target)[4])
        with _lock:
            file_states = state["file_states"]
        if os.path.isfile(path) and warm_states <= file_states:
            # Nothing learned beyond what the file already holds.
            with _lock:
                state["saved"] = False
            return False
        # Fresh write, or a strictly warmer in-process cache: supersede
        # the file so DFA states learned since its last write (e.g. new
        # grammar paths like the short-name `<...>` forms) persist.
        payload = _payload(target)
        blob = pickle.dumps(payload, protocol=_CACHE_PROTOCOL)
        states = sum(len(dfa.states) for dfa in payload[1])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp-%d" % os.getpid()
        with open(tmp, "wb") as f:
            f.write(blob)
        os.replace(tmp, path)
        with _lock:
            state["saved"] = True
            state["saved_states"] = states
        return True
    except Exception as exc:
        warnings.warn(
            f"DFA cache save failed ({type(exc).__name__}: {exc}); "
            f"parsing continues without it", stacklevel=3)
        return False


def maybe_load(target: str = "sysml") -> None:
    """Lazy hook: attempt the cache load once per process for *target*.

    Called from the parse paths, so it must never raise — a cache problem
    may only cost speed, never a parse.
    """
    try:
        load_dfa_cache(target=target)
    except Exception:
        pass
    with _lock:
        _state["used"].add(target)
    _register_atexit()


def maybe_save(target: str = "sysml") -> None:
    """Lazy hook: persist *target*'s warm cache once per process."""
    try:
        save_dfa_cache(target=target)
    except Exception:
        pass
    with _lock:
        _state["used"].add(target)
    _register_atexit()


def _register_atexit() -> None:
    """Persist every used target's warm DFA states when the process ends.

    A once-per-process save (``maybe_save``) is not enough for multi-file
    work: the library-index walk parses ~36 .kerml files, and saving after
    the FIRST of them persisted 558 of the 1,622 states the run warmed —
    the next process then re-derived the rest.  Saving again at exit (only
    when strictly warmer than the file) makes the cache converge on the
    real workload.
    """
    with _lock:
        if _state.get("atexit_registered"):
            return
        _state["atexit_registered"] = True
    import atexit
    atexit.register(_save_all_used)


def _save_all_used() -> None:
    import warnings as _warnings
    with _lock:
        used = sorted(_state.get("used", ()))
    for target in used:
        try:
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore")
                save_dfa_cache(target=target, force=True)
        except Exception:
            pass


def targets() -> Tuple[str, ...]:
    """Grammar families with a persistent DFA cache."""
    return _TARGETS


def reset_for_tests() -> None:
    """Reset process state (load/save flags); used by the test suite."""
    with _lock:
        _state["targets"] = {}
        if isinstance(_state.get("used"), set):
            _state["used"].clear()


def stats(target: Optional[str] = None) -> Dict[str, Any]:
    """Current cache state (for tests and diagnostics).

    Without *target* the SysML entry is reported at the top level (the
    historical shape); every family also appears under ``targets``.
    """
    name = target or "sysml"
    state = _tstate(name)
    with _lock:
        return {
            "enabled": is_enabled(),
            "directory": _cache_directory(),
            "target": name,
            "file": cache_file(name),
            "key": cache_key(name),
            "load_attempted": state["load_attempted"],
            "loaded": state["loaded"],
            "file_states": state["file_states"],
            "save_attempted": state["save_attempted"],
            "saved": state["saved"],
            "saved_states": state["saved_states"],
            "targets": {t: _tstate(t) for t in _TARGETS},
        }
