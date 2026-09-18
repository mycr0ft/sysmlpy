"""Interactive SysML v2 REPL for sysmlpy (new tool, v0.93.x).

Run with::

    sysmlpy repl [FILE ...]          # python -m sysmlpy repl

Inspired by the OpenSysML ``sysml`` REPL (Open-MBEE/OpenSysML): each
submission is a declaration or an expression, declarations accumulate
into a session model, and meta-commands begin with ``%``.

Session semantics (shared with :mod:`sysmlpy.ipython_magic`):

- a submission adds to whatever namespace the session already holds —
  re-entering ``package Demo { … }`` merges at member granularity
  (a re-declared member replaces the prior one, the other members are
  kept, and a ``note:`` line reports what was replaced);
- parse errors leave the session untouched;
- ``%set NAME=VALUE`` bindings feed ``%eval`` / ``%check`` what-if
  values, exactly like ``sysmlpy eval --set``.

Commands (``%help`` lists them)::

    %list [NAME]     packages, or elements matching NAME
    %show NAME       repr() of a named element
    %dump            round-tripped SysML text of the session model
    %eval EXPR       evaluate an expression against the session model
    %set N=V         bind a what-if value (number/bool/string/unit)
    %bindings        show current what-if bindings
    %calc NAME a, b  invoke a calc def with positional literal arguments
    %check           check the model's constraints
    %values          collected attribute values
    %sim [FOCUS]     start a simulator session on a state machine
    %send TRIGGER    fire a trigger in the active simulator session
    %step            fire one completion step in the session
    %state           show the active simulator session's state
    %view NAME [V]   render a view (gv, pkg, afv, iv, stv, tab, dvt, matrix)
    %load PATH       parse a file and merge it into the session
    %save PATH       write the session model's SysML text to PATH
    %reset           discard the session model and bindings
    %quit            leave the REPL (Ctrl-D also works)

The module keeps I/O injectable (``input_func``/``output``) so tests can
drive it headlessly — the same pattern :func:`sysmlpy.sim.run_tui` uses.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import sysmlpy

__all__ = ["ReplSession", "SubmitResult", "main", "run_repl"]


# ---------------------------------------------------------------------------
# session
# ---------------------------------------------------------------------------

class SubmitResult:
    """Outcome of one submission (declarations or parse failure)."""

    def __init__(self, ok: bool, lines: List[str]):
        self.ok = ok
        self.lines = lines

    def __iter__(self):
        return iter(self.lines)


class ReplSession:
    """Accumulating SysML session: parse, merge, query, evaluate, simulate."""

    def __init__(self):
        #: the session model (None until the first successful submission)
        self.model = None
        #: what-if bindings for %eval / %check (NAME -> parsed literal)
        self.bindings: Dict[str, Any] = {}
        #: active simulator session from %sim (a StateSimulator or None)
        self.sim = None

    # -- submission ---------------------------------------------------------

    def submit(self, source: str) -> SubmitResult:
        """Parse *source* and merge it into the session model.

        Returns a result whose lines are the confirmation/diagnostic
        text; the session is untouched on parse errors.
        """
        try:
            model = sysmlpy.loads(source)
        except Exception as e:  # noqa: BLE001 - reported, not raised
            return SubmitResult(False, [f"error: {e}"])

        if self.model is None:
            self.model = model
            names = [getattr(c, "name", "?") or "?" for c in model.children]
            lines = [f"✓ {', '.join(names) if names else '(empty)'}"]
            return SubmitResult(True, lines)

        replaced = self._merge(model)
        lines = ["✓ merged"]
        for name in replaced:
            lines.append(f"note: {name} replaced the previous declaration")
        return SubmitResult(True, lines)

    def _merge(self, model) -> List[str]:
        """Member-granularity merge (ipython_magic semantics).

        Within a package of the same name, a re-declared element (matched
        by name + sysml_type) replaces the prior one; other members are
        preserved. New packages are appended. Returns the replaced
        member names.
        """
        replaced: List[str] = []
        for pkg in getattr(model, "packages", []) or model.children:
            pkg_name = getattr(pkg, "name", None)
            existing = next(
                (c for c in self.model.children
                 if getattr(c, "name", None) == pkg_name
                 and c.__class__.__name__ == "Package"),
                None,
            ) if pkg_name else None
            if existing is None or existing is pkg:
                if existing is not pkg:
                    self.model.children.append(pkg)
                continue
            for member in getattr(pkg, "children", []) or []:
                key = (getattr(member, "name", None),
                       getattr(member, "sysml_type", None))
                for i, old in enumerate(existing.children):
                    if ((getattr(old, "name", None),
                         getattr(old, "sysml_type", None)) == key):
                        existing.children[i] = member
                        replaced.append(str(key[0]))
                        break
                else:
                    existing.children.append(member)
        return replaced

    # -- element lookup ------------------------------------------------------

    def find_elements(self, name: str) -> List[Any]:
        """Every element in the session tree whose name matches exactly."""
        out: List[Any] = []

        def walk(node):
            for ch in getattr(node, "children", []) or []:
                if getattr(ch, "name", None) == name:
                    out.append(ch)
                walk(ch)

        if self.model is not None:
            walk(self.model)
        return out

    def element_names(self) -> List[str]:
        """All declared names in the session tree (for completion)."""
        names: List[str] = []

        def walk(node):
            for ch in getattr(node, "children", []) or []:
                n = getattr(ch, "name", None)
                if n and not re.fullmatch(
                        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                        r"[0-9a-f]{4}-[0-9a-f]{12}", str(n)):
                    names.append(str(n))
                walk(ch)

        if self.model is not None:
            walk(self.model)
        return names

    # -- value parsing -------------------------------------------------------

    @staticmethod
    def parse_value(text: str) -> Any:
        """Parse a ``%set`` / ``%calc`` literal: bool, number, unit, string."""
        from sysmlpy.usage import ureg

        raw = text.strip()
        low = raw.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        try:
            return ureg(raw)
        except Exception:
            pass
        return raw


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

_VIEWS = {
    "gv": "as_general_view",
    "pkg": "as_package_view",
    "afv": "as_action_flow_view",
    "iv": "as_interconnection_view",
    "stv": "as_state_transition_view",
    "tab": "as_tabular_view",
    "dvt": "as_data_value_tabular_view",
    "matrix": "as_relationship_matrix_view",
}


def _format_value(value) -> str:
    if isinstance(value, bool):
        return str(value)
    if value is None:
        return "null"
    return str(value)


def _run_command(session: ReplSession, line: str,
                 output: Callable[[str], None]) -> bool:
    """Execute one ``%`` command; returns False only for %quit."""
    parts = line[1:].split()
    cmd = parts[0].lower() if parts else "help"
    rest = line[1 + len(parts[0]):].strip() if parts else ""

    if cmd in ("quit", "exit", "q"):
        return False

    if cmd == "help":
        output(__doc__.split("Commands (``%help`` lists them)::")[1]
               .split("The module keeps")[0].rstrip())
        return True

    if cmd == "list":
        if session.model is None:
            output("(no model loaded)")
            return True
        if rest:
            hits = session.find_elements(rest)
            if not hits:
                output(f"(no elements named {rest!r})")
            for el in hits:
                qn = _qualified_name(el)
                output(f"{el.__class__.__name__} {qn}")
        else:
            for c in session.model.children:
                n = len(getattr(c, "children", []) or [])
                output(f"{c.__class__.__name__} {getattr(c, 'name', '?')} "
                       f"({n} member(s))")
        return True

    if cmd == "show":
        hits = session.find_elements(rest) if rest else []
        if not hits:
            output(f"(no elements named {rest!r})")
            return True
        output(repr(hits[0]))
        return True

    if cmd == "dump":
        if session.model is None:
            output("(no model loaded)")
            return True
        try:
            output(session.model.dump())
        except Exception as e:  # noqa: BLE001
            output(f"error: {e}")
        return True

    if cmd == "eval":
        if session.model is None:
            output("(no model loaded)")
            return True
        from sysmlpy.evaluator import evaluate_expression, EvaluationError
        try:
            value = evaluate_expression(rest, model=session.model,
                                        bindings=dict(session.bindings))
            output(f"= {_format_value(value)}")
        except (EvaluationError, Exception) as e:  # noqa: BLE001
            output(f"error: {e}")
        return True

    if cmd == "set":
        if "=" not in rest:
            output("usage: %set NAME=VALUE")
            return True
        name, _, raw = rest.partition("=")
        session.bindings[name.strip()] = session.parse_value(raw)
        output(f"✓ {name.strip()} = "
               f"{_format_value(session.bindings[name.strip()])}")
        return True

    if cmd == "bindings":
        if not session.bindings:
            output("(no bindings)")
            return True
        for k, v in session.bindings.items():
            output(f"{k} = {_format_value(v)}")
        return True

    if cmd == "calc":
        if session.model is None:
            output("(no model loaded)")
            return True
        from sysmlpy.evaluator import evaluate_calculation, EvaluationError
        toks = [t for t in rest.split(",") if t.strip()] if rest else []
        # %calc NAME [arg, arg, ...]
        name, _, argtext = rest.partition(" ")
        toks = [t.strip() for t in argtext.split(",") if t.strip()]
        args = [session.parse_value(t) for t in toks]
        try:
            value = evaluate_calculation(session.model, name, args=args)
            output(f"= {_format_value(value)}")
        except Exception as e:  # noqa: BLE001
            output(f"error: {e}")
        return True

    if cmd == "check":
        if session.model is None:
            output("(no model loaded)")
            return True
        from sysmlpy.evaluator import check_constraints
        report = check_constraints(session.model,
                                   bindings=dict(session.bindings))
        output(report.to_text())
        return True

    if cmd == "values":
        if session.model is None:
            output("(no model loaded)")
            return True
        from sysmlpy.evaluator import collect_values
        values = collect_values(session.model,
                                bindings=dict(session.bindings))
        # collect_values returns a plain dict; don't getattr("values")
        # (that returns the dict method, not the items).
        items = values if isinstance(values, dict) else getattr(
            values, "values", {})
        try:
            pairs = sorted(items.items())
        except AttributeError:
            pairs = []
        if not pairs:
            output("(no attribute values)")
        for k, v in pairs:
            output(f"{k} = {_format_value(v)}")
        return True

    if cmd == "sim":
        if session.model is None:
            output("(no model loaded)")
            return True
        from sysmlpy.sim import StateSimulator, SimulationError
        try:
            session.sim = StateSimulator(session.model,
                                         focus=rest or None,
                                         values=dict(session.bindings))
        except (SimulationError, ImportError) as e:
            output(f"error: {e}")
            return True
        for note in session.sim.notes:
            output(f"note: {note}")
        output(f"state: {session.sim.state!r}")
        return True

    if cmd == "send":
        if session.sim is None:
            output("(no simulator session — run %sim first)")
            return True
        fired = session.sim.send(rest)
        output(f"{'fired' if fired else 'blocked'} -> "
               f"{session.sim.state!r}")
        return True

    if cmd == "step":
        if session.sim is None:
            output("(no simulator session — run %sim first)")
            return True
        session.sim.step()
        output(f"state: {session.sim.state!r}")
        return True

    if cmd == "state":
        if session.sim is None:
            output("(no simulator session — run %sim first)")
            return True
        output(f"state: {session.sim.state!r}")
        return True

    if cmd == "view":
        if session.model is None:
            output("(no model loaded)")
            return True
        import shlex
        toks = shlex.split(rest)
        if not toks:
            output("usage: %view NAME [gv|pkg|afv|iv|stv|tab|dvt|matrix]")
            return True
        focus = toks[0]
        view = toks[1].lower() if len(toks) > 1 else "pkg"
        fn_name = _VIEWS.get(view)
        if fn_name is None:
            output(f"error: unknown view {view!r} — "
                   f"choose from {', '.join(_VIEWS)}")
            return True
        import sysmlpy.plantuml as pu
        try:
            fn = getattr(pu, fn_name)
            if fn_name == "as_tabular_view" or fn_name == "as_data_value_tabular_view":
                text = fn(session.model, focus=focus, output_format="markdown")
            else:
                text = fn(session.model, focus=focus)
            output(str(text))
        except Exception as e:  # noqa: BLE001
            output(f"error: {e}")
        return True

    if cmd == "load":
        path = Path(rest).expanduser()
        if not path.exists():
            output(f"error: file '{path}' not found")
            return True
        result = session.submit(path.read_text(encoding="utf-8"))
        for ln in result:
            output(ln)
        return True

    if cmd == "save":
        if session.model is None:
            output("(no model loaded)")
            return True
        path = Path(rest).expanduser()
        try:
            path.write_text(session.model.dump() + "\n", encoding="utf-8")
            output(f"wrote {path}")
        except Exception as e:  # noqa: BLE001
            output(f"error: {e}")
        return True

    if cmd == "reset":
        session.model = None
        session.bindings.clear()
        session.sim = None
        output("session cleared")
        return True

    output(f"error: unknown command %{cmd} — %help lists commands")
    return True


def _qualified_name(el) -> str:
    parts: List[str] = []
    node = el
    while node is not None:
        n = getattr(node, "name", None)
        if n and not re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                r"[0-9a-f]{4}-[0-9a-f]{12}", str(n)):
            parts.append(str(n))
        node = getattr(node, "parent", None)
    return "::".join(reversed(parts))


# ---------------------------------------------------------------------------
# the loop
# ---------------------------------------------------------------------------

_OPEN = "([{"
_CLOSE = ")]}"


def _balanced(text: str) -> bool:
    """True when no bracket remains open (string literals ignored)."""
    stripped = re.sub(r'"[^"]*"|\'[^\']*\'', "", text)
    depth = 0
    for ch in stripped:
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
            if depth < 0:
                return True  # unbalanced the other way — let parse report it
    return depth <= 0


class _Completer:
    """Readline completion: %commands and session element names."""

    def __init__(self, session: ReplSession):
        self.session = session
        self.commands = [
            "%help", "%list", "%show", "%dump", "%eval", "%set",
            "%bindings", "%calc", "%check", "%values", "%sim", "%send",
            "%step", "%state", "%view", "%load", "%save", "%reset",
            "%quit",
        ]

    def complete(self, text: str, state: int):
        opts: List[str] = []
        if text.startswith("%"):
            opts = [c for c in self.commands if c.startswith(text)]
        else:
            opts = [n for n in self.session.element_names()
                    if n.startswith(text)]
        return opts[state] if state < len(opts) else None


def run_repl(session: Optional[ReplSession] = None,
             input_func: Optional[Callable[[str], str]] = None,
             output: Callable[[str], None] = print,
             banner: bool = True) -> ReplSession:
    """Run the read-eval-print loop; returns the session on exit.

    A submission continues onto the next line (``...>``) while any
    bracket stays open, so multi-line declarations work naturally.
    Lines starting with ``%`` are meta-commands; anything else is a
    SysML submission, or — if it fails to parse — an expression.
    """
    if input_func is None:
        input_func = input  # resolved at call time (test monkeypatching)
    session = session or ReplSession()
    if banner:
        output(f"sysmlpy {sysmlpy.__version__} REPL — %help for commands, "
               "Ctrl-D to exit")

    # Readline completion when interactive (never required).
    try:
        import readline
        completer = _Completer(session)
        readline.set_completer(completer.complete)
        readline.parse_and_bind("tab: complete")
    except Exception:  # noqa: BLE001 - readline optional
        pass

    while True:
        try:
            line = input_func("sysml> ")
        except EOFError:
            output("")
            return session
        except KeyboardInterrupt:
            output("^C (use %quit to exit)")
            continue

        if not line.strip():
            continue

        if line.lstrip().startswith("%"):
            if not _run_command(session, line.strip(), output):
                return session
            continue

        # Accumulate until brackets balance.
        chunks = [line]
        while not _balanced("\n".join(chunks)):
            try:
                more = input_func("...> ")
            except (EOFError, KeyboardInterrupt):
                output("error: unfinished declaration discarded")
                chunks = []
                break
            chunks.append(more)
        if not chunks:
            continue
        source = "\n".join(chunks)

        result = session.submit(source)
        if not result.ok and _looks_like_expression(source):
            # Not a declaration — try it as an expression.
            from sysmlpy.evaluator import evaluate_expression
            try:
                value = evaluate_expression(source, model=session.model,
                                            bindings=dict(session.bindings))
                output(f"= {_format_value(value)}")
                continue
            except Exception:  # noqa: BLE001 - fall through to parse error
                pass
        for ln in result:
            output(ln)
    # unreachable


def _looks_like_expression(text: str) -> bool:
    """Heuristic: an operator/paren line that cannot start a declaration."""
    return bool(re.search(r"[+\-*/^<>=]|^[0-9.()]", text.strip())) and \
        not re.match(r"\s*(abstract|individual|package|library|part|item|"
                     r"attribute|port|action|state|calc|constraint|"
                     r"requirement|interface|connection|allocation|flow|"
                     r"metadata|rendering|view|viewpoint|concern|analysis|"
                     r"verification|use\s+case|enum|import|ref|perform|"
                     r"exhibit|alias|succession|message|bind|variant|"
                     r"abstract|doc|comment)\b", text, re.IGNORECASE)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry: ``sysmlpy repl [FILE ...] [-l LIBRARY]``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="sysmlpy repl",
        description="Interactive SysML v2 REPL (declarations accumulate "
                    "into a session model; %commands inspect it).",
    )
    parser.add_argument("files", nargs="*", metavar="FILE",
                        help="model file(s) to load into the session first")
    parser.add_argument("-l", "--library", default=None,
                        help="path to SysML v2 library files")
    parser.add_argument("--no-banner", action="store_true",
                        help="suppress the startup banner")
    args = parser.parse_args(argv)

    session = ReplSession()
    for f in args.files:
        path = Path(f)
        if not path.exists():
            print(f"error: file '{path}' not found", file=sys.stderr)
            return 2
        result = session.submit(path.read_text(encoding="utf-8"))
        for ln in result:
            print(ln)
    if args.library:
        print(f"note: -l/--library is accepted for parity with other "
              f"subcommands but submissions parse without it", file=sys.stderr)

    run_repl(session, banner=not args.no_banner)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())