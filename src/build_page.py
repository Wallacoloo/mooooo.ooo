#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import sys, jsonpickle

from page_info import Page

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input html template> <output>" %sys.argv[0])
        sys.exit(1)

    in_path, out_path = sys.argv[1:]

    page = Page.from_unknown_type(src_filename=in_path)
    if out_path.endswith(".srcinfo"):
        output = page.get_src_info()
    elif out_path.endswith(".build"):
        output = page.get_build()
    serialized = jsonpickle.encode(output)
    out_file = open(out_path, "w+")
    out_file.write(serialized)

