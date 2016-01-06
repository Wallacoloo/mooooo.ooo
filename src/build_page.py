#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import json, os, subprocess, sys

import dateutil.parser
from jinja2 import Environment, PackageLoader
import PIL.Image;


# Directory in which blog entries are stored
BLOG_ENTRY_DIR="blog_entries"
# Directory in which Jinja2 templates are stored
TEMPLATE_DIR="templates"

IMG_EXTENSIONS = ".jpg", ".jpeg", ".png", ".svg"

# Config file read from .json on disk
config = None

def recursive_listdir(path):
    """Same as os.listdir, but recurses into subdirectories.
    Original code by John La Rooy. Source: http://stackoverflow.com/a/19309964
    Slight modification from original to remove the base dir from the returned paths
        (thus mimicking os.listdir)
    """
    return [os.path.join(dp, f)[len(path):] for dp, dn, fn in os.walk(path) for f in fn]

def get_ext(path):
    """Return the extension of a filename.
    Example:
    >>> get_ext("my/name/is/pinkie.pie")
    ".pie"
    """
    return os.path.splitext(path)[1]

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
            line = line[len("Date:"):]
            date = dateutil.parser.parse(line.strip())
            edit_dates.append(date)
    edit_dates.sort()
    return edit_dates

class Page(object):
    def __init__(self, path_on_disk=None, title=None):
        assert os.path.exists(path_on_disk)

        self._path_on_disk = path_on_disk
        self._title = title
        if path_on_disk and path_on_disk.startswith("pages/"):
            self._path = path_on_disk[len("pages/"):]
        elif path_on_disk and get_ext(path_on_disk) == ".scss":
            # SASS files are compiled to CSS in the build directory
            self._path = path_on_disk[:-len(".scss")] + ".css"
        else:
            self._path = path_on_disk

        if get_ext(self._path) in IMG_EXTENSIONS:
            # If this resource is an image, cast it as such for the extra data
            self.set_type(Image)
        elif get_ext(self._path) == ".css":
            self.set_type(Css)
        else:
            assert get_ext(self._path) == ".html"
            self.set_type(UnknownHtml)

    @property
    def path(self):
        """Path relative to the build directory (i.e. the URL of the resource, minus the domain name"""
        assert self._path is not None
        return self._path
    def set_type(self, type):
        self.__class__ = type
        return ""

    def resolve_type(self):
        """Used by derivative classes (e.g. UnknownHtml) to determine in more
        detail what type of resource this is.
        This can be an expensive operation, and could potentially cause infinite
        recursion if it was done upon instantiation, hence why it's done on-demand
        """
        assert self.__class__ != Page
        return self.__class__

    @property
    def title(self):
        assert self._title is not None
        return self._title
    def set_title(self, title):
        # Only makes sense to set the title once
        assert self._title == None
        self._title = title
        return ""

    @property
    def authors(self):
        authors = get_authors_of_file(self._path_on_disk)
        # For now, we only have one author
        assert len(authors) == 1 and all(a.name == "Colin Wallace" for a in authors)
        return authors

    @property
    def pub_date(self):
        return get_edit_dates_of_file(self._path_on_disk)[0]

    @property
    def last_edit_date(self):
        return get_edit_dates_of_file(self._path_on_disk)[-1]

    @property
    def images(self):
        """Retrives the images in the same directory as this page"""
        basedir = os.path.split(self._path_on_disk)[0]

        images = {}
        for page in os.listdir(basedir):
            if get_ext(page) in IMG_EXTENSIONS:
                images[page] = Image(path_on_disk=os.path.join(basedir, page))
        return images

    def render(self, query_type=False):
        global config
        in_path = self._path_on_disk
        out_path = self.path
        def to_rel_path(abs_path):
            prefix = "../"*out_path.count("/")
            rel = os.path.join(prefix, abs_path)
            if rel.endswith("index.html") and config["omit_index_from_url"]:
                rel = rel[:-len("index.html")]
            return rel

        env = Environment(loader=PackageLoader("__main__", TEMPLATE_DIR), trim_blocks=True, lstrip_blocks=True)

        # Populate template global variables & filters
        env.globals.update(config)
        env.globals["query_type"] = query_type
        env.globals["pages"] = Pages("pages/", [".html"])
        env.globals["resources"] = Pages("res/", [".css", ".scss"])
        env.filters["into_tag"] = filter_into_tag
        env.filters["friendly_date"] = filter_friendly_date
        env.filters["to_rel_path"] = to_rel_path
        env.globals["page"] = self
        # Expose these types for passing to the `set_page_type` macro
        env.globals["BlogEntry"] = BlogEntry
        env.globals["HomePage"] = HomePage
        env.globals["AboutPage"] = AboutPage

        template = env.from_string(open(in_path).read())
        r = template.render()
        return r

class Author(object):
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return self.name == other.name
    def __hash__(self):
        return hash(self.name)

class Image(Page):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    @property
    def size(self):
        """Returns the size of the image in pixels (width, height)"""
        im = PIL.Image.open(self._path_on_disk)
        return im.size

class Css(Page):
    pass

class BlogEntry(Page):
    pass 

class UnknownHtml(Page):
    """
    Type for a Page where we know it's some html resource,
    but haven't identified yet if it's a BlogEntry or something else.
    """
    def resolve_type(self):
        """Try rendering the template to determine its type"""
        self.render(query_type=True)
        return self.__class__


class HomePage(Page):
    pass

class AboutPage(Page):
    pass

class Pages(object):
    def __init__(self, basedir, extensions):
        self.all = {}
        for fname in recursive_listdir(basedir):
            if get_ext(fname) in extensions:
                self.all[fname] = Page(path_on_disk=os.path.join(basedir, fname))
    def __getitem__(self, key):
        """Returns a page by its path.
        Note: index.html is implicit (if the path doesn't exist)
        """
        if key.startswith("/"):
            # Leading slash is optional, but useful for requesting the index page
            key = key[1:]
        if key in self.all:
            return self.all[key]
        elif os.path.join(key, "index.html") in self.all:
            return self.all[os.path.join(key, "index.html")]
        else:
            if os.path.splitext(key)[1] == ".css":
                # SASS files are compiled into normal CSS
                return self[key[:-len(".css")] + ".scss"]
            return KeyError(key)

    @property
    def blog_entries(self):
        """Return all pages which are blog entries"""
        entries = {}
        for key, item in self.all.items():
            t = item.resolve_type()
            if t == BlogEntry:
                entries[key] = item
        return entries




if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: %s <input html template> <config file path> <root build dir> <output path>" %(sys.argv[0] if len(sys.argv) else "build_page.py"))
        sys.exit(1)

    in_path, config_path, build_dir, out_path = sys.argv[1:]

    config = json.loads(open(config_path, "r").read())

    page = Page(in_path).render() #_page(config, in_path, out_path)
    f = open(os.path.join(build_dir, out_path), "w")
    f.write(page)
