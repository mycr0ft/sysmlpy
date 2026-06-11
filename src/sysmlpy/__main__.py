#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line interface for sysmlpy."""

import argparse
import sys
from pathlib import Path

from sysmlpy import loads


def main():
    parser = argparse.ArgumentParser(
        prog="sysmlpy",
        description="Parse SysML v2 files and display their Python representation"
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the SysML v2 file to parse"
    )
    parser.add_argument(
        "--python",
        action="store_true",
        help="Display the Python repr() representation of the parsed model"
    )
    parser.add_argument(
        "-l", "--library",
        type=str,
        help="Path to SysML v2 library files to use for parsing"
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Display the SysML text output (dump format)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Display the dictionary/JSON representation"
    )
    parser.add_argument(
        "-i", "--in-place",
        action="store_true",
        help="Format the file in-place (overwrites the input file)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if the file is already formatted; exit 1 if not"
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file_path, 'r') as f:
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
        from sysmlpy import load_grammar
        grammar_dict = load_grammar(content)
        import json
        print(json.dumps(grammar_dict, indent=2))
    elif args.dump or args.in_place or args.check:
        formatted = model.dump()
        if args.check:
            if formatted == content:
                sys.exit(0)
            else:
                print(f"{file_path} would be reformatted")
                sys.exit(1)
        elif args.in_place:
            with open(file_path, 'w') as f:
                f.write(formatted)
            print(f"Formatted {file_path}")
        else:
            print(formatted)
    else:
        # Default or --python flag: show repr()
        print(repr(model))

if __name__ == "__main__":
    main()
