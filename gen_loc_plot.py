#!/usr/bin/env python3
"""Generate lines-of-code history plot from git history."""

import subprocess
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def get_loc_history():
    """Get cumulative LOC per commit from git log --numstat."""
    result = subprocess.run(
        ["git", "log", "--reverse", "--numstat", "--format=%ai"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")

    commits = []
    current_date = None
    added = 0
    removed = 0

    for line in lines:
        if not line:
            continue
        # Date line: "2026-05-17 16:21:20 -0500"
        if len(line) >= 19 and line[4] == "-" and line[7] == "-" and ":" in line:
            if current_date is not None:
                commits.append((current_date, added, removed))
            current_date = datetime.datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
            added = 0
            removed = 0
        # Numstat line: added\tremoved\tfile
        elif "\t" in line:
            parts = line.split("\t")
            if len(parts) == 3:
                a, r, f = parts
                # Skip generated/binary/lock files and ANTLR-generated parsers
                skip_extensions = (".svg", ".png", ".lock", ".whl", ".tar.gz")
                skip_patterns = ("antlr4/SysMLv2Parser", "antlr4/SysMLv2Lexer",
                                 "antlr/SysMLv2Parser", "antlr/SysMLv2Lexer",
                                 "ParserListener", "ParserVisitor", "Lexer")
                if f.endswith(skip_extensions):
                    continue
                if any(p in f for p in skip_patterns):
                    continue
                if a != "-":
                    added += int(a)
                if r != "-":
                    removed += int(r)

    if current_date is not None:
        commits.append((current_date, added, removed))

    # Build cumulative totals
    dates = []
    totals = []
    cumulative = 0
    for date, added, removed in commits:
        cumulative += added - removed
        dates.append(date)
        totals.append(cumulative)

    return dates, totals


def main():
    dates, totals = get_loc_history()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dates, totals, color="#2196F3", linewidth=2, marker="o", markersize=3, alpha=0.8)
    ax.fill_between(dates, totals, alpha=0.15, color="#2196F3")

    ax.set_title("Lines of Code Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Lines of Code", fontsize=11)
    ax.grid(True, alpha=0.3)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=45)

    # Annotate last point
    ax.annotate(
        f"{totals[-1]:,} LOC",
        xy=(dates[-1], totals[-1]),
        xytext=(-60, -15),
        textcoords="offset points",
        fontsize=11,
        fontweight="bold",
        color="#2196F3",
        arrowprops=dict(arrowstyle="->", color="#2196F3", lw=1.5),
    )

    plt.tight_layout()
    plt.savefig("loc_history.png", dpi=150, bbox_inches="tight")
    plt.savefig("loc_history.svg", bbox_inches="tight")
    plt.close()

    print(f"Generated loc_history.png and loc_history.svg")
    print(f"Latest: {totals[-1]:,} LOC ({len(dates)} commits)")


if __name__ == "__main__":
    main()
