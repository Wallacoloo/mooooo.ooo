#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import json, os, subprocess
import re

import dateutil.parser, jinja2, PIL.Image
from jinja2 import Environment, PackageLoader
from urllib.parse import urlsplit


CONFIG_PATH = "../build/config.json"
# Directory in which blog entries are stored
BLOG_ENTRY_DIR="blog_entries"
# Directory in which Jinja2 templates are stored
TEMPLATE_DIR="templates"

IMG_EXTENSIONS = ".gif", ".jpg", ".jpeg", ".png", ".svg"
VID_EXTENSIONS = ".webm",
SND_EXTENSIONS = ".ogg",
# Anything visual
GFX_EXTENSIONS = IMG_EXTENSIONS + VID_EXTENSIONS
FONT_EXTENSIONS = ".eot", ".ttf", ".woff", ".woff2"
CSS_EXTENSIONS = ".css",

# Config file read from .json on disk
config = json.loads(open(CONFIG_PATH, "r").read())


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

def filter_detailed_date(date):
    """Takes a datetime.datetime object, returns a detaile version of the date, e.g. 'Jan 22, 2015 at 8:09 PM PST'"""
    return date.strftime("%b %d, %Y at %I:%M %p PST")

def filter_drop_null_values(dict):
    """Returns a new dict that contains only the items for which bool(item.value) == True
    Example:
    >>> filter_drop_null_values(dict(x=2, y=None, z="", k="yes", j="False"))
    dict(x=2, k="yes", j="False")
    """

    filt = {}
    for k, v in dict.items():
        if v:
            filt[k] = v
    return filt

def filter_url_with_args(path, **kwargs):
    """Returns `path` + "?" + urlencode(kwargs),
    or just `path` if there are no kwargs
    """
    urlargs = "?" + jinja2.filters.do_urlencode(kwargs) if kwargs else ""
    return path + urlargs

def get_unparsed_commits(filename):
    """Returns an array of commit dicts, where each entry looks like:
    { 'author': '<name>', 'date': '<date>', 'message': '<message>' }
    """
    proc = subprocess.Popen(["git", "log", '--pretty=format:{%n  "author": "%aN",%n  "date": "%cD",%n  "message": "%s"%n},', "--", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if stderr:
        raise RuntimeError("git log error:", stderr)

    raw = stdout.decode('utf-8')
    return json.loads("[%s []]" %raw)[:-1]

def get_commits(filename):
    """Returns an array of commit dicts, where each entry looks like:
    { 'author': <Author object>, 'date': <Datetime object>, 'message': '<message>' }
    """
    commits = get_unparsed_commits(filename)
    for c in commits:
        c["author"] = Author(c["author"])
        c["date"] = dateutil.parser.parse(c["date"])

    return commits

def get_authors_of_file(filename):
    """Return a set of Author objects that have commits associated with the
    file"""
    commits = get_commits(filename)

    authors = set()
    for commit in commits:
        authors.add(commit['author'])
    return list(authors)

def get_pub_date_of_file(filename):
    """Returns the date at which this file was committed with the message "PUBLISH", indicating it is ready to be made public"""
    commits = get_commits(filename)

    for c in commits:
        if c["message"] == "PUBLISH":
            return c["date"]


class Page(object):
    comments = {}
    def __init__(self, path_on_disk=None, title=None, need_exist=True):
        if need_exist: assert os.path.exists(path_on_disk)

        self._path_on_disk = path_on_disk
        self._title = title
        self._desc = None
        self._srcdeps = None # Haven't calculated the dependencies
        self._rtdeps = None # Haven't calculated the dependencies
        self._anchors = None # Haven't enumerated the page's anchors
        if path_on_disk and path_on_disk.startswith("pages/"):
            self._path = path_on_disk[len("pages/"):]
        else:
            self._path = path_on_disk

        if get_ext(self._path) in GFX_EXTENSIONS:
            # If this resource is an image, cast it as such for the extra data
            self.set_type(Image)
        elif get_ext(self._path) in FONT_EXTENSIONS:
            self.set_type(Font)
        elif get_ext(self._path) == ".css":
            self.set_type(Css)
        elif get_ext(self._path) in SND_EXTENSIONS:
            self.set_type(Audio)
        else:
            assert get_ext(self._path) == ".html"
            self.do_render_with_jinja = True
            # By rendering the page, we can determine our type
            self.render(query_type=True)

    def __repr__(self):
        return "<Page.%s %r>" %(self.__class__.__name__, self.path_on_disk)

    @property
    def path(self):
        """Path relative to the build directory (i.e. the URL of the resource, minus the domain name"""
        assert self._path is not None
        return self._path
    @property
    def friendly_path(self):
        """Returns the (unique) identifier/path for this page, but in the most friendly manner, i.e. no trailing 'index.html' or slash"""
        p = self.path
        if p.endswith("index.html"):
            p = p[:-len("index.html")]
        if p.endswith("/"):
            p = p[:-1]
        if p == "":
            p = "/"
        return p.lower()
    @property
    def repo_page(self):
        """Path where the user can view the source/revision history of a file & submit pull requests."""
        return "https://github.com/Wallacoloo/mooooo.ooo/tree/master/src/pages/%s" %self.path

    def anchor_path(self, anchor, validate=True):
        """Assert that the anchor is found on this page, and return the full page + anchor path.
        e.g. mypage.html#myheading
        """
        if not anchor:
            return self.path
        else:
            if anchor.startswith("#"):
                anchor = anchor[1:0]
            if not validate or anchor == "" or anchor in self.anchors:
                return self.path + "#" + anchor
            else:
                raise KeyError("anchor not found on page: #%s" %anchor)

    @property
    def path_in_build_tree(self):
        """Path that this page will occupy on the disk after being built.
        This is always just the URL relative to base of the website, prefixed
        with the build directory path on disk"""
        return os.path.join(config["build"]["dir"], self.path)

    @property
    def build_dep_path(self):
        """Path in which dependency information for this file should be stored"""
        return os.path.join(config["build"]["root"], "deps", self.path + ".deps")

    @property
    def path_on_disk(self):
        assert self._path_on_disk is not None
        return self._path_on_disk

    @property
    def dir_on_disk(self):
        """Returns the directory containing the source file for this resource"""
        return os.path.split(self._path_on_disk)[0]

    def set_type(self, type):
        self.__class__ = type
        return ""

    def offsite_comments(self, url):
        domain_name = urlsplit(url).netloc
        nick = domain_name.lstrip("www.").rstrip(".com")
        comments = self.comments or {}
        comments[nick] = url
        self.comments = comments
        return ""


    @property
    def title(self):
        assert self._title is not None
        return self._title
    def set_title(self, title):
        # Only makes sense to set the title once
        assert self._title == None or title == self._title
        self._title = title
        return ""

    @property
    def desc(self):
        return self._desc
    def set_desc(self, desc):
        # Only makes sense to set the description once
        assert self._desc == None or desc == self._desc
        self._desc = desc
        return ""

    @property
    def authors(self):
        authors = get_authors_of_file(self._path_on_disk)
        # For now, we only have one author
        #assert len(authors) == 1 and all(a.name == "Colin Wallace" for a in authors)
        return authors

    @property
    def _pub_date(self):
        """Returns the date the article was made public, or None if it's still in draft form"""
        return get_pub_date_of_file(self._path_on_disk)

    @property
    def pub_date(self):
        pub_date = self._pub_date
        assert pub_date is not None
        return pub_date

    @property
    def is_published(self):
        return self._pub_date is not None

    @property
    def last_edit_date(self):
        return sorted(get_commits(self._path_on_disk), key=lambda c: c["date"])[-1]["date"]

    @property
    def anchors(self):
        """Return a set of all html anchors on the page that can be linked to"""
        if self._anchors is None:
            self.render(query_anchors=True)
        return self._anchors

    def _get_images(self, names=None, **kwargs):
        """Returns all the images in the same source directory as the object,
        or the images in the files indicated by names, regardless of if they exist"""
        if not names:
            names = os.listdir(self.dir_on_disk)

        images = {}
        for page in names:
            if get_ext(page) in IMG_EXTENSIONS:
                images[page] = Image(path_on_disk=os.path.join(self.dir_on_disk, page), **kwargs)
            if get_ext(page) in VID_EXTENSIONS:
                images[page] = Image(path_on_disk=os.path.join(self.dir_on_disk, page), is_video=True, **kwargs)
        return images


    @property
    def images(self):
        """Retrives the images in the same directory as this page"""
        return self._get_images()

    def _get_audio(self, names=None, **kwargs):
        """Returns all audio files in the same source directory as the object,
        or the audio in the files indicated by names, regardless of if they exist"""
        if not names:
            names = os.listdir(self.dir_on_disk)

        audio = {}
        for page in names:
            if get_ext(page) in SND_EXTENSIONS:
                audio[page] = Audio(path_on_disk=os.path.join(self.dir_on_disk, page), **kwargs)
        return audio


    @property
    def audio(self):
        """Retrives the audio in the same directory as this page"""
        return self._get_audio()

    # Commented out because unused.
    #def _get_css(self, names=None, **kwargs):
    #    """Returns all the css in the same source directory as the object,
    #    or the css in the directory indicated by names, regardless of if they exist"""
    #    if not names:
    #        names = os.listdir(self.dir_on_disk)

    #    css = {}
    #    for page in names:
    #        if get_ext(page) in CSS_EXTENSIONS:
    #            images[page] = Page(path_on_disk=os.path.join(self.dir_on_disk, page), **kwargs)
    #    return css

    #@property
    #def css(self):
    #    """Retrieves the css files in the same directory as this page"""
    #    return self._get_css()

    @property
    def srcdeps(self):
        """Query all the resources this file *immediately* depends on,
        and return them as a list of Page objects"""
        if self._srcdeps is None:
            r = self.render(query_deps=True)
        return self._srcdeps
    @property
    def rtdeps(self):
        """All resources that this file depends on at runtime (e.g. links, etc)"""
        # trigger building of deps    
        self.srcdeps
        return self._rtdeps

    @property
    def contents(self):
        return self.render()

    def render(self, query_type=False, query_anchors=False, query_deps=False):
        global config
        in_path = self._path_on_disk
        out_path = self.path
        srcdeps = set()
        rtdeps = set()
        anchors = set() # html anchors, e.g. mypage.html#heading1 - "heading1" is an anchor
        def to_rel_path(abs_path):
            # Separate the anchor, if it was provided
            if "#" in abs_path:
                abs_path, anchor = abs_path.split("#")
            else:
                anchor = ""
            # Remove any stem that is common to (abs_path, out_path).
            parts_out, parts_abs = out_path.split("/"), abs_path.split("/")
            while parts_out and parts_abs and parts_out[0] == parts_abs[0]:
                del parts_out[0]
                del parts_abs[0]
            
            # add necessary ../ parents
            prefix = "../"*(len(parts_out)-1)
            # Add the leaf
            base = os.path.join(prefix, "/".join(parts_abs))
            # Remove index.html from the path if configured to.
            if base.endswith("index.html") and config["omit_index_from_url"]:
                base = base[:-len("index.html")]
            # Re-add the anchor, if there was one
            retstr = "#".join((base, anchor)) if anchor else base
            if retstr == "":
                # old web browsers misinterpret empty href. See http://stackoverflow.com/questions/5637969/is-an-empty-href-valid
                retstr = "#"
            return retstr
        def add_srcdep(dep):
            srcdeps.add(dep)
            # Return empty string so this expression won't write to the output stream
            return ""
        def add_rtdep(dep):
            rtdeps.add(dep)
            return ""
        def add_anchor(anch):
            anchors.add(anch)
            return ""

        def get_image(name):
            if isinstance(name, Image):
                return name # we already found the image

            try:
                return self.images[name]
            except KeyError:
                if not query_deps:
                    raise
                else:
                    # If we aren't rendering, we can pretend the image already exists (we assume it will be generated later)
                    return self._get_images([name], need_exist=False)[name]

        # We are either (a) rendering the page,
        # (b) querying its type
        # (c) querying its anchors
        # (d) querying its dependencies
        # Both (a), (c), (d) require rendering the page
        do_render = not query_type and not query_anchors and not query_deps

        env = Environment(loader=PackageLoader("__main__", TEMPLATE_DIR), trim_blocks=True, lstrip_blocks=True)

        # Populate template global variables & filters
        env.globals.update(config)
        env.globals["add_srcdep"] = add_srcdep
        env.globals["add_rtdep"] = add_rtdep
        env.globals["add_anchor"] = add_anchor
        env.globals["get_image"] = get_image
        env.globals["query_type"] = query_type
        env.globals["query_anchors"] = query_anchors
        env.globals["query_deps"] = query_deps
        env.globals["do_render"] = do_render
        env.globals["validate_anchors"] = not query_anchors # Avoid circular dependencies.
        env.globals["config"] = config
        env.globals["pages"] = get_pages()
        #env.globals["resources"] = Pages("res/", [".css", ".scss"])
        env.filters["into_tag"] = filter_into_tag
        env.filters["friendly_date"] = filter_friendly_date
        env.filters["detailed_date"] = filter_detailed_date
        env.filters["drop_null_values"] = filter_drop_null_values
        env.filters["url_with_args"] = filter_url_with_args
        env.filters["to_rel_path"] = to_rel_path
        env.globals["page"] = self
        # Expose these types for passing to the `set_page_type` macro
        env.globals["BlogEntry"] = BlogEntry
        env.globals["HomePage"] = HomePage
        env.globals["AboutPage"] = AboutPage
        env.globals["Page"] = Page

        if self.do_render_with_jinja:
            template = env.from_string(open(in_path).read())
            r = template.render().strip()
        elif do_render:
            # This is a binary file
            r = open(in_path, "rb").read()

        if query_deps:
            if self._srcdeps:
                srcdeps.update(self._srcdeps)
            self._srcdeps = srcdeps
            if self._rtdeps:
                rtdeps.update(self._rtdeps)
            self._rtdeps = rtdeps

        if query_anchors:
            if self._anchors:
                anchors.update(self._anchors)
            self._anchors = anchors

        if do_render:
            return r

class Author(object):
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return self.name == other.name
    def __hash__(self):
        return hash(self.name)

class Image(Page):
    do_render_with_jinja = False
    def __init__(self, **kwargs):
        self._is_video = kwargs.pop("is_video", False)
        super().__init__(**kwargs)
    @property
    def is_video(self):
        return self._is_video
    @property
    def size(self):
        """Returns the size of the image in pixels (width, height)"""
        if self.is_video:
            cmd = "avconv -i %s" % self._path_on_disk
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            di = p.communicate()
            for line in di:
                if str(line).rfind("Video") > 0:
                    resolution = re.findall("(\d+x\d+)", str(line))[0]
            return [int(dim) for dim in resolution.split("x")]
        else:
            im = PIL.Image.open(self._path_on_disk)
            return im.size

class Audio(Page):
    do_render_with_jinja = False

class Font(Page):
    do_render_with_jinja = False

class Css(Page):
    do_render_with_jinja = True

class BlogEntry(Page):
    do_render_with_jinja = True
    @property
    def comment_email(self):
        """The email address that should be used to send comments to this blog entry"""
        return config["social"]["comment_email"]

    @property
    def comment_email_subject(self):
        """The subject tagline that should be used to identify a comment to this article"""
        return "[%s]" %self.friendly_path
    

class HomePage(Page):
    do_render_with_jinja = True

class AboutPage(Page):
    do_render_with_jinja = True

class Comment(Page):
    def __init__(self, page, body):
        """page = the Page object to which this comment belongs to."""
        self._page = page
        self._body = body
    def save(self):
        """Save the comment to disk.
        Note: this will not implicitly regenerate any affected content
        """
        print("[FIXME] Comment.save() not implemented")

class Pages(object):
    def __init__(self, basedir, extensions):
        self._basedir = basedir
        self._extensions = extensions
        self._all = None

    @property
    def all(self):
        if self._all is None:
            self._all = {}
            for fname in recursive_listdir(self._basedir):
                if get_ext(fname) in self._extensions:
                    self._all[fname] = Page(path_on_disk=os.path.join(self._basedir, fname))
        return self._all

    def __hasitem__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def __getitem__(self, key):
        """Returns a page by its path.
        Note: index.html is implicit (if the path doesn't exist)
        """
        if not isinstance(key, str):
            raise KeyError(key)

        if key.startswith("/"):
            # Leading slash is optional, but useful for requesting the index page
            key = key[1:]
        if key in self.all:
            return self.all[key]
        elif os.path.join(key, "index.html") in self.all:
            return self.all[os.path.join(key, "index.html")]
        else:
            raise KeyError(key)

    @property
    def blog_entries(self):
        """Return all pages which are blog entries"""
        entries = {}
        for key, item in self.all.items():
            if isinstance(item, BlogEntry):
                entries[key] = item
        return entries

def get_pages():
    ext = [".html", ".css"]
    ext.extend(GFX_EXTENSIONS)
    ext.extend(FONT_EXTENSIONS)
    return Pages("pages/", ext)

