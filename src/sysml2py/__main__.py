#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line interface for sysml2py."""

import argparse
import sys
from pathlib import Path

from sysml2py import loads


def main():
    parser = argparse.ArgumentParser(
        prog="sysml2py",
        description="Parse SysML v2 files and display their Python representation",
    )
    parser.add_argument("file", type=str, help="Path to the SysML v2 file to parse")
    parser.add_argument(
        "--python",
        action="store_true",
        help="Display the Python repr() representation of the parsed model",
    )
    parser.add_argument(
        "-l",
        "--library",
        type=str,
        help="Path to SysML v2 library files to use for parsing",
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Display the SysML text output (dump format)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Display the dictionary/JSON representation"
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        model = loads(content, library=args.library)
    except Exception as e:
        print(f"Error parsing SysML file: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        from sysml2py import load_grammar

        grammar_dict = load_grammar(content)
        import json

        print(json.dumps(grammar_dict, indent=2))
    elif args.dump:
        print(model.dump())
    else:
        # Default or --python flag: show repr()
        print(repr(model))


if __name__ == "__main__":
    main()
