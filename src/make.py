#!/usr/bin/env python
"""Dependency management from python.
Exposes methods to build specific resources & publish to IPFS, etc"""

import os

import page_info

def create_dirs_and_open(fname, mode):
    """Creates any directories not existing in the file path
    and then opens the file name with the given mode and returns a handle"""
    os.makedirs(os.path.split(fname)[0], exist_ok=True)
    return open(fname, mode)


def new_dependency(page):
    """page should be an instance of page_info.Page.
    This function will re-compute the dependencies of page"""
    print("[FIXME] make.new_dependency() not implemented")

def make(page=None):
    """If page is None: rebuild any targets that have changed.
    This will result in an up-to-date website in the build directory,
    but it will not be implicitly published.
    If page is an instance of page_info.Page, build just that page"""
    if page is None:
        for page in page_info.get_pages():
            make(page)
    else:
        print("[make %r]" %page)

def make_deps(page=None, outfile=None):
    """Determine the dependencies for building the given page,
    and create the proper Makefile rules for that,
    inserting them into <page>.deps.
    If page is None, this will create ALL dependencies,
    otherwise, page should be a page_info.Page object."""
    if page is None:
        f = create_dirs_and_open(outfile, "w+")
        for page in page_info.get_pages().all.values():
            make_deps(page)
            f.write("-include %s.deps\n" %page.path_in_build_tree)
            #f.write("all: %s\n" %page.path_in_build_tree)
    else:
        rule_name = page.path_in_build_tree

        if outfile is None:
            outfile = rule_name + ".deps"

        f = create_dirs_and_open(outfile, "w+")

        f.write("%s: %s\n" %(rule_name, page.path_on_disk))
        for dep in page.deps:
            f.write("%s: %s\n" %(rule_name, dep.path_in_build_tree))
        for dep in page.rtdeps:
            f.write("all: %s\n" %dep.path_in_build_tree)

def publish():
    """Publish the website to IPFS and update any necessary host records"""
    if page is None:
        import page_info
        for page in page_info.get_pages():
            make_deps(page)
    else:
        print("[make_deps %r]" %page)
        print("[FIXME] make.publish() not implemented")


if __name__ == "__main__":
    # Build all the targets given on the command line
    import sys
    import page_info
    targets = sys.argv[1:]

    for target in targets:
        if target.endswith("all.depincludes"):
            make_deps(outfile=target)
        elif target.endswith(".deps"):
            page = page_info.get_pages()[target[:-len(".deps")]]
            make_deps(page)
        else:
            page = page_info.get_pages()[target]
            make(page)

