# -*- coding: utf-8 -*-
"""Tests for markdown table pretty-printing (sysmlpy.mdtables)."""
from __future__ import annotations

import sysmlpy  # noqa: E402
from sysmlpy.mdtables import (  # noqa: E402
    display_width,
    format_table,
    pretty_markdown_tables,
)


def test_display_width_counts_escaped_pipe_as_one():
    assert display_width(r"a\|b") == 3


def test_display_width_east_asian_and_combining():
    assert display_width("✓") == 1          # Ambiguous -> narrow
    assert display_width("中") == 2          # Wide
    assert display_width("é") == 1          # e + combining acute


def test_format_table_pads_all_pipes_aligned():
    lines = format_table(["Name", "Value"],
                         [["mass", "12"], ["speed", "3"]])
    assert len({len(l) for l in lines}) == 1        # every line same length
    assert lines[0] == "| Name  | Value |"
    assert lines[1] == "| ----- | ----- |"
    assert lines[2] == "| mass  | 12    |"
    assert lines[3] == "| speed | 3     |"
    # widths come from header AND rows: "speed" widens column 1


def test_format_table_alignment_markers():
    lines = format_table(["L", "C", "R"],
                         [["a", "b", "c"]],
                         align=["---", ":-:", "--:"])
    assert lines[1] == "| --- | :-: | --: |"   # colons on the correct side
    assert lines[2] == "| a   |  b  |   c |"


def test_format_table_check_mark_counts_one():
    lines = format_table(["Req", "Cov"], [["MaxMass", "S✓"], ["x", "y"]])
    assert lines[2] == "| MaxMass | S✓  |"
    assert lines[3] == "| x       | y   |"


def test_pretty_repads_ragged_table():
    ragged = ("| a | bb |\n"
              "| --- | --- |\n"
              "| c | d |\n"
              "| eeee | f |")
    out = pretty_markdown_tables(ragged)
    lines = out.splitlines()
    assert lines[0] == "| a    | bb  |"
    assert lines[3] == "| eeee | f   |"
    assert len({len(l) for l in lines}) == 1


def test_pretty_leaves_non_tables_untouched():
    text = ("# Title\n\n"
            "prose | with pipes\n\n"
            "| a | b |\n"
            "no separator follows\n")
    assert pretty_markdown_tables(text) == text


def test_pretty_preserves_alignment_colons():
    ragged = ("| a | b |\n"
              "| :-- | --: |\n"
              "| c | d |")
    out = pretty_markdown_tables(ragged)
    lines = out.splitlines()
    # separator keeps its colons (left/right), padded to the column width
    assert lines[1] == "| :-- | --: |"
    assert lines[2] == "| c   |   d |"


def test_relationship_matrix_view_markdown_is_aligned():
    model = sysmlpy.loads("""
    package P {
        requirement MaxMass;
        part myCar {
            satisfy MaxMass;
        }
    }
    """)
    from sysmlpy.plantuml import as_relationship_matrix_view
    md = as_relationship_matrix_view(model, output_format="markdown")
    table_lines = [l for l in md.splitlines() if l.startswith("|")]
    assert len(table_lines) > 2
    assert len({len(l) for l in table_lines}) == 1   # all pipes aligned


def test_traceability_markdown_is_aligned():
    from sysmlpy.traceability import extract_traceability
    model = sysmlpy.loads("""
    package P {
        requirement MaxMass {
            doc /* mass limit */
        }
        part myCar {
            satisfy MaxMass;
        }
    }
    """)
    md = extract_traceability(model).to_markdown()
    table_lines = [l for l in md.splitlines() if l.startswith("|")]
    assert len(table_lines) >= 3
    assert len({len(l) for l in table_lines}) == 1, table_lines