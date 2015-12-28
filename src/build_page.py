#!/usr/bin/env python3

import sys

from jinja2 import Environment, PackageLoader
import json


# Read configuration details from file (contact accounts, etc)
config = json.loads(open("config.json", "r").read())

def render_page(in_path):
    env = Environment(loader=PackageLoader("__main__", 'templates'))
    template = env.get_template(in_path)
    
    params = config

    return template.render(**params)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input html template> <output path>" %(sys.argv[0] if len(sys.argv) else "build_page.py"))
        sys.exit(1)

    in_path, out_path = sys.argv[1:]
    # Remove the assumed 'templates/' path prefix.
    if in_path.startswith("templates/"):
        in_path = in_path[len("templates/"):]
    data = render_page(in_path)
    f = open(out_path, "w")
    f.write(data)
