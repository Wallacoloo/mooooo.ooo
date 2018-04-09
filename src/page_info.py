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

def get_ext(path):
    """Return the extension of a filename.
    Example:
    >>> get_ext("my/name/is/pinkie.pie")
    ".pie"
    """
    return os.path.splitext(path)[1]

def highlight_code(code, filetype=None):
    if filetype:
        lexer = get_lexer_by_name(filetype)
    else:
        lexer = guess_lexer(code)
    return pygments.highlight(code, lexer, HtmlFormatter())
def get_highlight_css():
    """Return the CSS needed to perform syntax highlighting"""
    return HtmlFormatter().get_style_defs('.highlight')

def filter_into_tag(value):
    """Given some text, this returns a human-readable tag that closely
    corresponds to the text but is safe to use in a URL.
    Example:
    >>> filter_into_tag("Hello, This is Arnold")
    "hello-this-is-arnold"
    """
    valid = 'abcdefghijklmnopqrstuvwxyz0123456789'
    # Make lowercase and replace illegal chars with hyphens
    value = "".join([c if c in valid else '-' for c in value.lower()])
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
    @staticmethod
    def from_unknown_type(src_filename, **kwargs):
        """ Auto-deduce the type of a page, and return an instance of that. """
        if src_filename.endswith(".html.jinja.html") or src_filename.endswith(".css.jinja.css"):
            Cls = JinjaPage
        elif get_ext(src_filename.replace(".src.bin", "")) in GFX_EXTENSIONS:
            Cls = Image
        else:
            Cls = BinaryBlob
        return Cls(src_filename=src_filename, **kwargs)

    def __init__(self, src_filename):
        assert os.path.exists(src_filename)
        self.src_filename = src_filename
        self.src_srcinfo_file = src_filename + ".srcinfo"

    def __repr__(self):
        return "<Page %s>" %self.src_filename
    
    @property
    def intermediate_path(self):
        # TODO: this should be passed via CLI
        return self.src_filename \
            .replace(".html.jinja.html", ".html") \
            .replace(".css.jinja.css", ".css") \
            .replace(".src.bin", "")

    @property
    def intermediate_dir(self):
        return os.path.dirname(self.intermediate_path)

    @property
    def build_path(self):
        return self.intermediate_path \
            .replace(config["build"]["intermediate"], config["build"]["output"])

    @property
    def base_src_info(self):
        """ Return the src_info common to all pages,
        sometimes unpopulated. """
        # If there's info associated with the source, provide that, too.
        try:
            src_srcinfo = jsonpickle.decode(open(self.src_srcinfo_file).read())
        except FileNotFoundError:
            src_srcinfo = {}

        return dict(
            intermediate_src_path = self.src_filename,
            intermediate_path = self.intermediate_path,
            build_path = self.build_path,
            rtdeps = set(),
            srcdeps = set(),
            **src_srcinfo,
        )
    @property
    def base_build_info(self):
        """ Return the build common to all pages
        """
        return dict(
            intermediate_path = self.intermediate_path,
            build_path = self.build_path,
            anchors = set(),
        )

    def get_build(self):
        """ Default build rule for POD files """
        build = self.base_build_info
        build['rtdeps'] = set()
        build['content'] = \
            open(self.src_filename, 'rb').read()
        return build

class JinjaPage(Page):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _get_jinja_env(self, do_render=False):
        global config

        src_info = Namespace(
            title = "",
            desc = "",
            comments = dict(),
            page_type = Page,
            anchors = set(),
            **self.base_src_info
        )

        def to_build_path(abs_path):
            return abs_path.replace(config['build']['intermediate'],
                    config['build']['output'])
        def path_from_root(path):
            """ Treat `path' as a path relative to the intermediate root.
            """
            return os.path.join(config['build']['intermediate'], path)
        def path_from_here(path):
            """ Treat `path' as a path relative to the current folder
            """
            return os.path.join(self.intermediate_dir, path)

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
            parts_out, parts_abs = src_info.intermediate_path.split("/"), abs_path.split("/")
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

        def get_srcinfo(pg):
            nonlocal src_info
            basedir = os.path.dirname(self.src_filename)
            full_path = os.path.join(basedir, pg) + ".srcinfo"
            src_info.srcdeps.add(full_path)
            if do_render:
                # load the page info
                info = jsonpickle.decode(open(full_path).read())
                return info

        def get_resource(pg):
            nonlocal src_info
            basedir = os.path.dirname(self.src_filename)
            full_path = os.path.join(basedir, pg) + ".build"
            src_info.srcdeps.add(full_path)
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
        env.globals["get_srcinfo"] = get_srcinfo
        # TODO: replace with get_resource
        env.globals["get_page"] = get_resource
        env.globals["get_image"] = get_srcinfo
        env.globals["get_audio"] = get_srcinfo
        env.filters["into_tag"] = filter_into_tag
        env.filters["friendly_date"] = filter_friendly_date
        env.filters["highlight_code"] = highlight_code
        env.filters["detailed_date"] = filter_detailed_date
        env.filters["drop_null_values"] = filter_drop_null_values
        env.filters["url_with_args"] = filter_url_with_args
        env.filters["unique"] = filter_unique
        env.filters["tex"] = filter_tex_to_svg
        env.filters["to_rel_path"] = to_rel_path
        env.filters["to_build_path"] = to_build_path
        env.filters["path_from_root"] = path_from_root
        env.filters["path_from_here"] = path_from_here
        env.globals["get_highlight_css"] = get_highlight_css
        # Expose these types for passing to the `page.set_type` macro
        env.globals["BlogEntry"] = BlogEntry
        env.globals["HomePage"] = HomePage
        env.globals["AboutPage"] = AboutPage
        env.globals["Page"] = Page
        env.globals['page_info'] = src_info

        return env, src_info._Namespace__attrs

    def get_rendered_jinja(self, do_render):
        env, jinja_info = self._get_jinja_env(do_render=do_render)

        template = env.get_template(self.src_filename)
        rendered = template.render().strip()
        # Don't rely on self!
        jinja_info['srcdeps'].discard(self.intermediate_path)
        jinja_info['rtdeps'].discard(self.intermediate_path)
        jinja_info['rtdeps'].discard(self.build_path)
        
        return jinja_info, rendered


    def get_build(self):
        """ Render a .jinja.html page to html. """
        jinja_info, rendered = self.get_rendered_jinja(do_render=True)

        build = self.base_build_info
        build['content'] = rendered
        build['rtdeps'] = jinja_info['rtdeps']
        build['anchors'] = jinja_info['anchors']

        return build

    def get_src_info(self):
        src_info, _rendered = self.get_rendered_jinja(do_render=False)
        return src_info



class Image(Page):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    @property
    def size(self):
        """Returns the size of the image in pixels (width, height)"""
        if get_ext(self.intermediate_path) == ".svg":
            # PIL doesn't support SVG.
            # Instead, parse as XML.
            # Width and Height are stored as attributes on the root SVG element.
            tree = ElementTree.parse(self.src_filename)
            root = tree.getroot()
            width = int(float(root.attrib["width"].replace("pt", "").replace("mm", "")))
            height = int(float(root.attrib["height"].replace("pt", "").replace("mm", "")))
            return (width, height)
        elif get_ext(self.intermediate_path) in VID_EXTENSIONS:
            cmd = "ffprobe -show_entries stream=height,width -v error -of flat=s=_ %s" %self.src_filename
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = p.communicate()
            video_vars = {}
            for line in output:
                exec(line, video_vars)
            return int(video_vars["streams_stream_0_width"]), int(video_vars["streams_stream_0_height"])
        else:
            im = PIL.Image.open(self.src_filename)
            return im.size

    def get_src_info(self):
        src_info = self.base_src_info
        src_info['size'] = self.size
        return src_info


    #@property
    #def rasterized(self):
    #    """Return an Image object for a rasterized version of this image.
    #    For non-vector graphics, this is a noop.
    #    """
    #    if self.path_on_disk.endswith(".svg"):
    #        return Image(path_on_disk=self.path_in_build_tree[:-4] + ".png", need_exist=False)
    #    else:
    #        return self

class BinaryBlob(Page):
    def get_src_info(self):
        return self.base_src_info

class Author(object):
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return self.name == other.name
    def __hash__(self):
        return hash(self.name)

class BlogEntry(Page):
    do_render_with_jinja = True

class HomePage(Page):
    do_render_with_jinja = True

class AboutPage(Page):
    do_render_with_jinja = True

