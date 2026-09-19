# -*- coding: utf-8 -*-
"""Markdown table pretty-printing for monospace rendering.

Markdown pipe tables read fine in renderers but arrive ragged in a
terminal: every row is ``| a | bb |`` with whatever spacing the
emitter happened to produce. This module re-pads pipe tables so the
pipes line up column-by-column in a monospace font:

    | Name  | Value |
    | ----- | ----- |
    | mass  | 12    |
    | speed | 3     |

Public API
----------
``pretty_markdown_tables(text) -> str``
    Post-process arbitrary markdown: every pipe table (header row +
    ``| --- |`` separator) is re-emitted column-aligned; all other
    lines pass through untouched. Tables without a separator row are
    left alone.

``format_table(header, rows, align=None) -> list of str``
    Build an aligned table directly from final cell strings (escaping,
    where wanted, is the caller's job) — what the view emitters use.

Honest limits
-------------
Alignment is best-effort by construction: it holds in any font that
honours the width rules below, and cannot hold for cells whose
*rendered* width differs from the measured one — emoji and other
beyond-BMP glyphs (ambiguous in most terminal fonts) or cells with
embedded newlines (which GFM tables cannot carry anyway). Widths
follow the East Asian Width convention: Wide/Fullwidth count 2,
combining marks 0, everything else — including the check mark ✓,
which is Ambiguous and renders narrow in common terminal fonts —
counts 1. Escaped characters (``\\|``) count as the single character
they render as.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["pretty_markdown_tables", "format_table", "display_width"]


def display_width(cell: str) -> int:
    """Rendered width of a table cell in a monospace font."""
    width = 0
    i = 0
    while i < len(cell):
        ch = cell[i]
        if ch == "\\" and i + 1 < len(cell):
            ch = cell[i + 1]
            i += 2
        else:
            i += 1
        if unicodedata.combining(ch):
            continue
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def _split_row(line: str):
    """Split a pipe-table line into raw cell texts (escapes preserved)."""
    cells = []
    cur = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            cur.append(line[i:i + 2])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append("".join(cur))
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return cells


def _alignment(cell: str):
    """GFM alignment of a separator cell: left / right / center / None."""
    c = cell.strip()
    left = c.startswith(":")
    right = c.endswith(":") and len(c) > 1 or (c == ":" and left)
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left"
    return None


def _pad(cells, widths, aligns):
    out = []
    for j, c in enumerate(cells):
        pad = widths[j] - display_width(c)
        a = aligns[j] if j < len(aligns) else None
        if a == "right":
            out.append(" " * pad + c)
        elif a == "center":
            half = pad // 2
            out.append(" " * half + c + " " * (pad - half))
        else:
            out.append(c + " " * pad)
    return out


def _emit(cells, widths, aligns):
    return "| " + " | ".join(_pad(cells, widths, aligns)) + " |"


def _is_separator(cells):
    return bool(cells) and all(
        re.fullmatch(r":?-{1,}:?", c.strip()) or c.strip() == ":"
        for c in cells)


def _reemit_table(lines):
    """Re-pad one table block (list of lines) with widths recomputed."""
    blocks = [_split_row(l) for l in lines]
    ncols = max(len(b) for b in blocks)
    aligns = [_alignment(c) for c in blocks[1]] if len(blocks) > 1 \
        else [None] * ncols
    aligns += [None] * (ncols - len(aligns))
    widths = []
    for j in range(ncols):
        w = 0
        for k, b in enumerate(blocks):
            if k != 1 and j < len(b):        # separator never widens a column
                w = max(w, display_width(b[j].strip()))
        widths.append(max(w, 3))
    out = []
    for idx, cells in enumerate(blocks):
        if idx == 1:  # separator: keep its colon style, pad to column width
            row = []
            for j in range(ncols):
                a = aligns[j]
                if a == "center":
                    row.append(":" + "-" * max(1, widths[j] - 2) + ":")
                elif a == "right":
                    row.append("-" * max(1, widths[j] - 1) + ":")
                elif a == "left":
                    row.append(":" + "-" * max(1, widths[j] - 1))
                else:
                    row.append("-" * widths[j])
            out.append("| " + " | ".join(row) + " |")
        else:
            padded = _pad([c.strip() for c in cells], widths, aligns)
            out.append("| " + " | ".join(padded) + " |")
    return out


def pretty_markdown_tables(text: str) -> str:
    """Column-align every pipe table in a markdown document.

    Finds blocks of consecutive ``|``-prefixed lines whose second line
    is a GFM separator row, recomputes each column's width from the
    raw cell contents, and re-emits the block padded. Everything else
    (prose, lists, code fences, tables lacking a separator) passes
    through byte-for-byte.
    """
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        is_table_row = stripped.startswith("|")
        nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
        if is_table_row and nxt.startswith("|") and _is_separator(
                _split_row(nxt)):
            block = [line]
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                block.append(lines[j])
                j += 1
            out.extend(_reemit_table(block))
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def format_table(header, rows, align=None):
    """Build an aligned pipe table; returns the list of lines.

    ``align`` entries follow the GFM separator vocabulary — ``"---"``,
    ``":--"``, ``"--:"``, ``":-:"`` (any dash count) — and control the
    padding side of each column. Cells must be final text (escaping,
    where wanted, is the caller's job); widths are measured from the
    cell contents so every pipe lines up in a monospace font.
    """
    if align is None:
        align = ["---"] * len(header)
    body = [list(map(str, r)) for r in rows]
    ncols = max([len(header)] + [len(r) for r in body])
    widths = [max(3, display_width(str(h))) for h in header]
    widths += [3] * (ncols - len(widths))
    for r in body:
        for j, c in enumerate(r):
            widths[j] = max(widths[j], display_width(c))
    aligns_out = []
    for a in align:
        a = str(a)
        left, right = a.startswith(":"), a.endswith(":") and len(a) > 1
        aligns_out.append("center" if left and right
                          else "right" if right
                          else "left" if left else None)
    aligns_out += [None] * (ncols - len(aligns_out))
    aligns = aligns_out
    lines = [_emit(list(map(str, header)) + [""] * (ncols - len(header)),
                   widths, aligns)]
    sep = []
    for j, a in enumerate(aligns):
        if a == "center":
            sep.append(":" + "-" * (widths[j] - 2) + ":")
        elif a == "right":
            sep.append("-" * (widths[j] - 1) + ":")
        elif a == "left":
            sep.append(":" + "-" * (widths[j] - 1))
        else:
            sep.append("-" * widths[j])
    lines.append("| " + " | ".join(sep) + " |")
    for r in body:
        full = list(r) + [""] * (ncols - len(r))
        lines.append(_emit(full, widths, aligns))
    return lines