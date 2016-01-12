#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import os.path, sys

from page_info import Page

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: %s <input html template> <root build dir> <output path>" %(sys.argv[0] if len(sys.argv) else "build_page.py"))
        sys.exit(1)

    in_path, build_dir, out_path = sys.argv[1:]

    page = Page(in_path).render()
    f = open(os.path.join(build_dir, out_path), "w")
    f.write(page)
