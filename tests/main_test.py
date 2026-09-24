#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 29 23:20:18 2023

@author: mycr0ft
"""
import pytest

from sysmlpy import load, loads, load_grammar
from sysmlpy.formatting import classtree

from sysmlpy.antlr_parser import SysMLSyntaxError

from .functions import strip_ws


def test_grammar_load_fromfile(single_package):
    with open("temp.txt", "w") as f:
        f.write(single_package)
    f.close()

    f = open("temp.txt", "r")
    grammar = load_grammar(f)
    assert strip_ws(classtree(grammar).dump()) == strip_ws(single_package)


def test_grammar_invalid_input():
    with pytest.raises(TypeError):
        load_grammar({})


def test_load_fromfile(single_package):
    with open("temp.txt", "w") as f:
        f.write(single_package)
    f.close()

    f = open("temp.txt", "r")
    model = load(f)
    assert strip_ws(model.dump()) == strip_ws(single_package)


def test_load_fromfile_error(single_package):
    with pytest.raises(TypeError):
        load("string")


def test_load_fromstr(single_package):
    model = loads(single_package)
    assert strip_ws(model.dump()) == strip_ws(single_package)


def test_load_fromstr_error(single_package):
    with pytest.raises(TypeError):
        loads({})


def test_invalid_sysml():
    with pytest.raises(SysMLSyntaxError):
        loads("error")


def test_loads_wrapped_bare_definition():
    """loads_wrapped accepts bare top-level definitions (OMG snippet
    style, e.g. Simple Tests/DecisionTest.sysml) by synthesizing a
    package wrapper."""
    from sysmlpy import loads_wrapped
    m = loads_wrapped("part def Camera;\n")
    assert len(m.children) == 1
    assert type(m.children[0]).__name__ == "Package"
    pk = m.children[0]
    assert [type(c).__name__ for c in pk.children] == ["Part"]


def test_loads_wrapped_passthrough_packaged():
    """Content already in a package passes through untouched (no
    double wrap)."""
    from sysmlpy import loads_wrapped
    text = "package P {\n    part def C;\n}\n"
    m = loads_wrapped(text)
    assert len(m.children) == 1
    assert m.children[0].name == "P"


def test_loads_wrapped_standard_library_package():
    """`standard library package` headers also pass through."""
    from sysmlpy import loads_wrapped
    text = "standard library package Foo {\n    part def Bar;\n}\n"
    m = loads_wrapped(text)
    assert len(m.children) == 1


def test_loads_wrapped_custom_package_name():
    from sysmlpy import loads_wrapped
    m = loads_wrapped("part def Camera;\n", package_name="OMG")
    assert m.children[0].name == "OMG"


def test_load_wrapped_file_pointer_and_typecheck():
    import io
    from sysmlpy import load_wrapped
    m = load_wrapped(io.StringIO("port def C;\n"))
    assert type(m.children[0]).__name__ == "Package"
    with pytest.raises(TypeError):
        load_wrapped("port def C;\n")   # str is not file-like


def test_loads_wrapped_omg_corpus_snippets():
    """The three package-less OMG corpus files now parse via
    loads_wrapped (regression for the corpus sweep 'package-less
    rejects')."""
    import os
    base = os.environ.get("OMG_CORPUS_ROOT")
    if not base or not os.path.isdir(base):
        pytest.skip("OMG corpus not available")
    from sysmlpy import loads_wrapped
    for rel in ("examples/Simple Tests/DecisionTest.sysml",
                "examples/Simple Tests/ControlNodeTest.sysml",
                "examples/Camera Example/Camera.sysml"):
        with open(os.path.join(base, rel), encoding="utf-8") as fh:
            m = loads_wrapped(fh.read())
        assert len(m.children) == 1


def test_loads_wrapped_roundtrip():
    """Wrapped snippets round-trip through classtree().dump()."""
    from sysmlpy import loads_wrapped
    text = "action def DecisionTest {\n    action A1;\n}\n"
    m = loads_wrapped(text)
    dumped = classtree(m).dump()
    m2 = loads(dumped)
    assert len(m2.children) == 1
