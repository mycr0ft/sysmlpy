#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the interactive REPL (sysmlpy repl).

Covers:
- session submission: parse, ✓ confirmation, parse-error recovery
- member-granularity merge with note: lines (ipython_magic semantics)
- %list / %show / %dump / %values
- %eval with expressions and %set what-if bindings
- %calc invocation with positional arguments
- %check constraint reporting
- %sim / %send / %step / %state simulator session
- %view rendering
- %load / %save file round-trip
- %reset and %quit
- multi-line bracket accumulation in the loop
- expression fallback for non-declaration input
"""

import pytest

from sysmlpy.repl import ReplSession, run_repl, _balanced


# ---------------------------------------------------------------------------
# session
# ---------------------------------------------------------------------------


class TestSession:
    def test_submit_ok(self):
        s = ReplSession()
        r = s.submit("package P { part def Wheel; }")
        assert r.ok
        assert any("P" in ln for ln in r.lines)
        assert s.model is not None
        assert s.model.children[0].name == "P"

    def test_submit_parse_error_leaves_session_untouched(self):
        s = ReplSession()
        s.submit("package P { part def Wheel; }")
        before = len(s.model.children[0].children)
        r = s.submit("package P { part def Broken {")
        assert not r.ok
        assert any(ln.startswith("error:") for ln in r.lines)
        assert len(s.model.children[0].children) == before

    def test_merge_new_package_appends(self):
        s = ReplSession()
        s.submit("package P { part def A; }")
        s.submit("package Q { part def B; }")
        names = [c.name for c in s.model.children]
        assert names == ["P", "Q"]

    def test_merge_same_package_keeps_other_members(self):
        s = ReplSession()
        s.submit("package P { part def A; part def B; }")
        r = s.submit("package P { part def B; attribute x : Real; }")
        assert r.ok
        pkg = s.model.children[0]
        names = [c.name for c in pkg.children]
        assert "A" in names          # preserved
        assert names.count("B") == 1  # replaced, not duplicated
        assert "x" in names          # added
        assert any("replaced" in ln for ln in r.lines)

    def test_find_elements(self):
        s = ReplSession()
        s.submit("package P { part def Wheel { attribute diameter : Real; } }")
        hits = s.find_elements("diameter")
        assert len(hits) == 1
        assert hits[0].__class__.__name__ == "Attribute"

    def test_element_names_skip_uuids(self):
        s = ReplSession()
        s.submit("package P { part def Wheel; }")
        names = s.element_names()
        assert "P" in names and "Wheel" in names
        assert not any(len(n) == 36 and n.count("-") == 4 for n in names)


# ---------------------------------------------------------------------------
# commands (driven through the loop, headlessly)
# ---------------------------------------------------------------------------


def drive(lines, files=()):
    """Run the REPL on scripted input; return (output_lines, session)."""
    out = []
    it = iter(lines)

    def inp(prompt):
        return next(it)

    def outp(text):
        out.append(text)

    s = run_repl(session=None if not files else None,
                 input_func=inp, output=outp, banner=False)
    return out, s


class TestCommands:
    def _session(self):
        s = ReplSession()
        s.submit("package Demo { "
                 "part def Wheel { attribute diameter : Real = 16.0; } "
                 "part def Bike { attribute wheels : Integer = 2; } "
                 "}")
        return s

    def _drive(self, s, lines):
        out = []
        it = iter(lines)

        def inp(prompt):
            return next(it)

        def outp(text):
            out.append(text)

        run_repl(session=s, input_func=inp, output=outp, banner=False)
        return out

    def test_list(self):
        s = self._session()
        out = self._drive(s, ["%list", "%quit"])
        assert any("Demo" in ln for ln in out)

    def test_list_named(self):
        s = self._session()
        out = self._drive(s, ["%list diameter", "%quit"])
        assert any("diameter" in ln for ln in out)

    def test_dump_round_trips(self):
        s = self._session()
        out = self._drive(s, ["%dump", "%quit"])
        assert any("part def Wheel" in ln for ln in out)

    def test_eval_expression(self):
        s = self._session()
        out = self._drive(s, ["%eval 6 * 7", "%quit"])
        assert any(ln.strip() == "= 42" for ln in out)

    def test_set_and_eval_binding(self):
        s = self._session()
        out = self._drive(s, ["%set d = 2.0", "%eval diameter * wheels",
                              "%quit"])
        assert any("= 32.0" in ln or ln.strip() == "= 32.0" for ln in out)

    def test_calc(self):
        s = ReplSession()
        s.submit("package C { calc def add { in x; in y; "
                 "return : Real = x + y; } }")
        out = self._drive(s, ["%calc add 10, 20", "%quit"])
        assert any("= 30" in ln for ln in out)

    def test_check(self):
        s = ReplSession()
        s.submit("package C { part def P { attribute mass : Real = 1200; "
                 "constraint c1 { mass > 1000 } "
                 "constraint c2 { mass > 5000 } } }")
        out = self._drive(s, ["%check", "%quit"])
        assert any("c1" in ln for ln in out)
        assert any("c2" in ln for ln in out)

    def test_sim_send_step(self):
        s = ReplSession()
        s.submit("package M { state def SM { "
                 "entry; then idle; "
                 "state idle; state running; "
                 "transition first idle accept Go then running; "
                 "transition first running then done; } }")
        out = self._drive(s, ["%sim", "%state", "%send Go", "%step",
                              "%quit"])
        assert any("state: 'idle'" in ln for ln in out)
        assert any("'running'" in ln for ln in out)

    def test_view(self):
        s = self._session()
        out = self._drive(s, ["%view Demo pkg", "%quit"])
        assert any("package" in ln.lower() for ln in out)

    def test_load_and_save(self, tmp_path):
        src = tmp_path / "m.sysml"
        src.write_text("package L { part def X; }")
        dst = tmp_path / "out.sysml"
        s = ReplSession()
        out = self._drive(s, [f"%load {src}", f"%save {dst}", "%quit"])
        assert any("wrote" in ln for ln in out)
        assert "part def X" in dst.read_text()

    def test_reset(self):
        s = self._session()
        out = self._drive(s, ["%reset", "%list", "%quit"])
        assert any("session cleared" in ln for ln in out)
        assert s.model is None

    def test_quit_returns_session(self):
        s = self._session()
        out = self._drive(s, ["%quit"])
        assert s.model is not None

    def test_unknown_command(self):
        s = self._session()
        out = self._drive(s, ["%frobnicate", "%quit"])
        assert any("unknown command" in ln for ln in out)

    def test_values_shows_attributes(self):
        s = self._session()
        out = self._drive(s, ["%values", "%quit"])
        assert any("diameter" in ln for ln in out)

    def test_qualified_name_skips_uuid_root(self):
        s = self._session()
        out = self._drive(s, ["%list diameter", "%quit"])
        assert any("Demo::" in ln and "::diameter" in ln for ln in out)
        # no UUID segment leaks into the displayed path
        import re as _re
        assert not any(
            _re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", ln) for ln in out)

    def test_help_lists_commands(self):
        s = ReplSession()
        out = self._drive(s, ["%help", "%quit"])
        assert any("%eval" in ln for ln in out)


# ---------------------------------------------------------------------------
# the loop
# ---------------------------------------------------------------------------


class TestLoop:
    def test_multi_line_accumulation(self):
        out = []
        it = iter(["package M {", "part def Wheel;", "}", "%quit"])

        def inp(prompt):
            return next(it)

        lines = []
        run_repl(input_func=inp, output=lines.append, banner=False)
        assert any("M" in ln for ln in lines)

    def test_parse_error_then_recovery(self):
        out = []
        it = iter(["package P { part def W { x } }", "%dump", "%quit"])

        def inp(prompt):
            return next(it)

        run_repl(input_func=inp, output=out.append, banner=False)
        # The error is reported; the session still answers %dump.
        assert any(ln.startswith("error:") for ln in out)
        assert any("(no model loaded)" in ln for ln in out)

    def test_expression_fallback(self):
        out = []
        it = iter(["40 + 2", "%quit"])

        def inp(prompt):
            return next(it)

        run_repl(input_func=inp, output=out.append, banner=False)
        assert any(ln.strip() == "= 42" for ln in out)

    def test_eof_exits(self):
        out = []

        def inp(prompt):
            raise EOFError

        s = run_repl(input_func=inp, output=out.append, banner=False)
        assert isinstance(s, object)

    def test_balanced(self):
        assert _balanced("package P { part def W; }")
        assert not _balanced("package P {")
        assert _balanced('doc /* "braces" */ { }')  # strings ignored


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_repl_smoke(tmp_path, capsys, monkeypatch):
    from sysmlpy.__main__ import main

    model = tmp_path / "m.sysml"
    model.write_text("package P { part def W; }")
    inputs = iter(["%list", "%quit"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    rc = main(["repl", str(model)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "P" in out