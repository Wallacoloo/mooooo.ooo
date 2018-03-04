#!/usr/bin/env python3
# Requires the following pip packages:
# python-dateutil, jinja2

import json, os, subprocess, jsonpickle
import re

import dateutil.parser, jinja2, joblib, PIL.Image, pygments
import xml.etree.ElementTree as ElementTree
import jinja2.ext
from jinja2 import Environment, PackageLoader, ChoiceLoader, FileSystemLoader, StrictUndefined
from jinja2.utils import Namespace
from urllib.parse import urlsplit
from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter


CONFIG_PATH = "../build/config.json"
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

persistent = joblib.Memory(cachedir="../build/joblib", verbose=0)

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

def highlight_code(self, code, filetype=None):
    if filetype:
        lexer = get_lexer_by_name(filetype)
    else:
        lexer = guess_lexer(code)
    return pygments.highlight(code, lexer, HtmlFormatter())
def get_highlight_css(self):
    """Return the CSS needed to perform syntax highlighting"""
    return HtmlFormatter().get_style_defs('.highlight')

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
    """Takes a datetime.datetime object, returns a detailed version of the date, e.g. 'Jan 22, 2015 at 8:09 PM PST'"""
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

@persistent.cache
def filter_tex_to_svg(tex):
    """Convert LaTeX into an inline svg.
    e.g. "e=mc^2"|tex
    """
    # TODO: don't render if do_render == False
    # Note: we prepend a space to fix bug in tex2svg when input is a number or starts with '-'
    tex = subprocess.Popen(["tex2svg", "--inline", " " + tex], stdout=subprocess.PIPE)
    res = subprocess.check_output(["scour", "-q", "-p" "10",
            "--strip-xml-prolog",
            "--enable-comment-stripping",
            "--enable-id-stripping",
            "--create-groups",
        ], stdin=tex.stdout)
    res = res.decode().strip()
    if not "<svg" in res.lower():
        print("ERROR IN filter_tex_to_svg: %r", res)
        print("Is tex2svg installed? Install via 'npm install -g tex-equation-to-svg'")
    return res
    
def filter_unique(it):
    """Skip items if they've been seen before in the sequence.
    """
    seen = set()
    for i in it:
        if i not in seen:
            seen.add(i)
            yield i



class Page(object):
    def __init__(self, src_filename):
        assert os.path.exists(src_filename)
        self.src_filename = src_filename
        self.src_pageinfo_file = src_filename + ".pageinfo"

    def __repr__(self):
        return "<Page %s>" %self.src_filename

    def get_jinja_env(self, do_render=False):
        global config
        intermediate_path = self.src_filename.replace(".html.jinja.html", ".html")
        build_path = intermediate_path.replace(config["build"]["intermediate"], config["build"]["output"])

        # If there's info associated with the source, provide that to jinja, too.
        try:
            src_pageinfo = jsonpickle.decode(open(self.src_pageinfo_file).read())
        except FileNotFoundError:
            src_pageinfo = {}

        page_info = Namespace(
            intermediate_path = intermediate_path,
            build_path = build_path,
            title = "",
            desc = "",
            comments = dict(),
            rtdeps = set(),
            srcdeps = set(),
            anchors = set(),
            **src_pageinfo,
        )

        #def to_build_path(abs_path):
        #    return abs_path.replace(config['build']['intermediate'],
        #            config['build']['output'])

        def to_rel_path(abs_path):
            #build_root = config["build"]["output"] + "/"
            #if abs_path.startswith(build_root):
            #    abs_path = abs_path[len(build_root):]
            # Separate the anchor, if it was provided
            if "#" in abs_path:
                abs_path, anchor = abs_path.split("#")
            else:
                anchor = ""
            # Remove any stem that is common to (abs_path, build_path).
            parts_out, parts_abs = intermediate_path.split("/"), abs_path.split("/")
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

        def get_resource(pg):
            nonlocal page_info
            basedir = os.path.dirname(self.src_filename)
            full_path = os.path.join(basedir, pg) + ".pageinfo"
            page_info.srcdeps.add(full_path)
            page_info.rtdeps.add(full_path)
            if do_render:
                # load the page info
                info = jsonpickle.decode(open(full_path).read())
                return info


        env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined,
            extensions=[jinja2.ext.do],
            loader=ChoiceLoader([
                PackageLoader("__main__", TEMPLATE_DIR),
                FileSystemLoader("/")
            ]))

        # Populate template global variables & filters
        env.globals.update(config)
        env.globals["do_render"] = do_render
        env.globals["config"] = config
        env.globals["get_page"] = get_resource
        env.globals["get_image"] = get_resource
        #env.globals["resources"] = Pages("res/", [".css", ".scss"])
        env.filters["into_tag"] = filter_into_tag
        env.filters["friendly_date"] = filter_friendly_date
        env.filters["detailed_date"] = filter_detailed_date
        env.filters["drop_null_values"] = filter_drop_null_values
        env.filters["url_with_args"] = filter_url_with_args
        env.filters["unique"] = filter_unique
        env.filters["tex"] = filter_tex_to_svg
        env.filters["to_rel_path"] = to_rel_path
        # Expose these types for passing to the `page.set_type` macro
        env.globals["BlogEntry"] = BlogEntry
        env.globals["HomePage"] = HomePage
        env.globals["AboutPage"] = AboutPage
        env.globals["Page"] = Page
        env.globals['page_info'] = page_info

        return env, page_info._Namespace__attrs

    def render(self):
        """ Render a .jinja.html page to html. """
        env, page_info = self.get_jinja_env(do_render=True)

        template = env.get_template(self.src_filename)
        return template.render().strip()

    def get_page_info(self):
        # TODO: what to do if this is an image!
        env, page_info = self.get_jinja_env(do_render=False)
        if self.src_filename.endswith(".jinja.html"):
            template = env.get_template(self.src_filename)
            template.render()
        return page_info



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
            cmd = "ffprobe -show_entries stream=height,width -v error -of flat=s=_ %s" %self._path_on_disk
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = p.communicate()
            video_vars = {}
            for line in output:
                exec(line, video_vars)
            return video_vars["streams_stream_0_width"], video_vars["streams_stream_0_height"]
        else:
            if self._path_on_disk.endswith(".svg"):
                # PIL doesn't support SVG.
                # Instead, parse as XML.
                # Width and Height are stored as attributes on the root SVG element.
                tree = ElementTree.parse(self._path_on_disk)
                root = tree.getroot()
                width = int(root.attrib["width"].replace("pt", ""))
                height = int(root.attrib["height"].replace("pt", ""))
                return (width, height)
            else:
                im = PIL.Image.open(self._path_on_disk)
                return im.size
    @property
    def rasterized(self):
        """Return an Image object for a rasterized version of this image.
        For non-vector graphics, this is a noop.
        """
        if self.path_on_disk.endswith(".svg"):
            return Image(path_on_disk=self.path_in_build_tree[:-4] + ".png", need_exist=False)
        else:
            return self

class Audio(Page):
    do_render_with_jinja = False

class Font(Page):
    do_render_with_jinja = False

class Css(Page):
    do_render_with_jinja = True

class Other(Page):
    do_render_with_jinja = False

class BlogEntry(Page):
    do_render_with_jinja = True

class HomePage(Page):
    do_render_with_jinja = True

class AboutPage(Page):
    do_render_with_jinja = True

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
                    pg = Page(path_on_disk=os.path.join(self._basedir, fname))
                    self._all[pg.path] = pg
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

