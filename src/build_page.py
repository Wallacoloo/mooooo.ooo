#!/usr/bin/env python3

import sys

from jinja2 import Environment, PackageLoader
import json

def filter_into_tag(value):
    """Given some text, this returns a human-readable tag that closely
    corresponds to the text but is safe to use in a URL.
    Example:
    >>> filter_into_tag("Hello, This is Arnold")
    "hello-this-is-arnold"
    """
    # Replace punctuation with hyphens
    value = value.replace(" ", "-").replace("/", "-").replace(",", "-") \
        .replace(".", "-").replace("!", "-").replace(";", "-") \
        .replace(":", "-").strip()
    # Preserve only alphanumerics and hyphens
    value = "".join(char.lower() for char in value if char.lower() in "abcdefghijklmnopqrstuvwxyz0123456789-")
    # Squash pairs of hyphens
    while len(value) != len(value.replace("--", "-")):
            value = value.replace("--", "-")

    return value


def render_page(config, in_path):
    env = Environment(loader=PackageLoader("__main__", 'templates'), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(in_path)
    
    # Populate template global variables & filters
    env.globals.update(config)
    env.filters["into_tag"] = filter_into_tag

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
