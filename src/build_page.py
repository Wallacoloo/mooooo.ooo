#!/usr/bin/env python3

import sys

from jinja2 import Environment, PackageLoader
import json



def render_page(config, in_path):
    env = Environment(loader=PackageLoader("__main__", 'templates'), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(in_path)
    
    env.globals.update(config)

    return template.render()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: %s <input html template> <config file path> <output path>" %(sys.argv[0] if len(sys.argv) else "build_page.py"))
        sys.exit(1)

    in_path, config_path, out_path = sys.argv[1:]
    # Remove the assumed 'templates/' path prefix.
    if in_path.startswith("templates/"):
        in_path = in_path[len("templates/"):]

    config = json.loads(open(config_path, "r").read())

    data = render_page(config, in_path)
    f = open(out_path, "w")
    f.write(data)
