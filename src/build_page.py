#!/usr/bin/env python3

import json, os, sys

from jinja2 import Environment, PackageLoader


# Directory in which blog entries are stored
BLOG_ENTRY_DIR="blog_entries"
# Directory in which Jinja2 templates are stored
TEMPLATE_DIR="templates"

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

class Page(object):
    def __init__(self, path):
        self.path = path

class BlogEntry(Page):
    def __init__(self, out_path, template):
        super().__init__(out_path)
        self._template = template

    @property
    def title(self):
        return self._template.render(title_only=True).strip()


def get_blog_objects(env):
    blogs = [BlogEntry(os.path.join(BLOG_ENTRY_DIR, path, "index.html"), env.from_string( \
            open(os.path.join(BLOG_ENTRY_DIR, path, "index.html")).read() \
        )) for path in os.listdir("blog_entries")]
    return blogs

def render_page(config, in_path, out_path):
    def to_rel_path(abs_path):
        prefix = "../"*out_path.count("/")
        rel = os.path.join(prefix, abs_path)
        if rel.endswith("index.html") and config["omit_index_from_url"]:
            rel = rel[:-len("index.html")]
        return rel

    env = Environment(loader=PackageLoader("__main__", TEMPLATE_DIR), trim_blocks=True, lstrip_blocks=True)

    # Populate template global variables & filters
    env.globals.update(config)
    env.globals["blog_entries"] = get_blog_objects(env)
    env.globals["pages"] = { "index": Page("index.html"), "about": Page("pages/about/index.html")}
    env.filters["into_tag"] = filter_into_tag
    env.filters["to_rel_path"] = to_rel_path

    template = env.from_string(open(in_path).read())
    return template.render()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: %s <input html template> <config file path> <root build dir> <output path>" %(sys.argv[0] if len(sys.argv) else "build_page.py"))
        sys.exit(1)

    in_path, config_path, build_dir, out_path = sys.argv[1:]

    config = json.loads(open(config_path, "r").read())

    data = render_page(config, in_path, out_path)
    f = open(os.path.join(build_dir, out_path), "w")
    f.write(data)
