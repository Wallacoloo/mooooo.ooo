#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import os.path, sys

from page_info import Page

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s <input html template>" %sys.argv[0])
        sys.exit(1)

    in_path = sys.argv[1]

    page = Page(in_path)
    rendered = page.render()
    out_path = page.path_in_build_tree
    if isinstance(rendered, str):
        # Open the file in text mode
        f = open(out_path, "w+")
    else:
        # Writing binary data (e.g. images)
        f = open(out_path, "wb+")
    f.write(rendered)
