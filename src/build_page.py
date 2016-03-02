#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import os.path, sys

from page_info import Page

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input html template> <output path>" %(sys.argv[0] if len(sys.argv) else "build_page.py"))
        sys.exit(1)

    in_path, out_path = sys.argv[1:]

    page = Page(in_path).render()
    if isinstance(page, str):
        # Open the file in text mode
        f = open(out_path, "w+")
    else:
        # Writing binary data (e.g. images)
        f = open(out_path, "wb+")
    f.write(page)
