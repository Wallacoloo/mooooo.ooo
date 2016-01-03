#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import json, os, subprocess, sys

import dateutil.parser
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

def filter_friendly_date(date):
    """Takes a datetime.datetime object, returns a friendly version of the date, e.g. 'Jan 22, 2015'"""
    return date.strftime("%b %d, %Y")

def get_git_log(filename):
    proc = subprocess.Popen(["git", "log", "--", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    assert stderr == b''
    return str(stdout).replace("\\n", "\n")

def get_authors_of_file(filename):
    """Return a set of Author objects that have commits associated with the
    file"""
    git_log = get_git_log(filename)

    authors = set()
    for line in git_log.split("\n"):
        if line.startswith("Author:"):
            line = line[len("Author:"):]
            name, _email_with_right_angle_bracket = line.split("<")
            name = name.strip()
            authors.add(Author(name))
    return list(authors)

def get_edit_dates_of_file(filename):
    """Returns an ordered list of the dates at which a file was modified,
    according to the git metadata"""
    git_log = get_git_log(filename)

    edit_dates = []
    for line in git_log.split("\n"):
        if line.startswith("Date:"):
            line = line[len("Date:")]
            date = dateutil.parser.parse(line.strip())
            edit_dates.append(date)
    edit_dates.sort()
    return edit_dates

class Page(object):
    def __init__(self, path):
        self.path = path

class BlogEntry(Page):
    def __init__(self, out_path, template_path_on_disk, template):
        super().__init__(out_path)
        self._template = template
        self._template_path_on_disk = template_path_on_disk
    @property
    def title(self):
        return self._template.render(title_only=True).strip()

    @property
    def authors(self):
        authors = get_authors_of_file(self._template_path_on_disk)
        # For now, we only have one author
        assert len(authors) == 1 and all(a.name == "Colin Wallace" for a in authors)
        return authors

    @property
    def template_path_on_disk(self):
        return self._template_path_on_disk

    @property
    def pub_date(self):
        return get_edit_dates_of_file(self._template_path_on_disk)[0]

    @property
    def last_edit_date(self):
        return get_edit_dates_of_file(self._template_path_on_disk)[-1]

class Author(object):
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return self.name == other.name
    def __hash__(self):
        return hash(self.name)

def get_blog_objects(env):
    blogs = [BlogEntry(out_path=os.path.join(BLOG_ENTRY_DIR, path, "index.html"), template_path_on_disk=\
            os.path.join(BLOG_ENTRY_DIR, path, "index.html"), template=env.from_string( \
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
    blog_entries = get_blog_objects(env)
    env.globals["blog_entries"] = blog_entries
    env.globals["pages"] = {
        "index": Page("index.html"),
        "about": Page("pages/about/index.html"),
        "global_css": Page("res/css/global.css"),
    }
    env.filters["into_tag"] = filter_into_tag
    env.filters["friendly_date"] = filter_friendly_date
    env.filters["to_rel_path"] = to_rel_path

    for entry in blog_entries:
        if entry.template_path_on_disk == in_path:
            env.globals["blog_entry"] = entry

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
