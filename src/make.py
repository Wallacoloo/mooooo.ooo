"""Dependency management from python.
Exposes methods to build specific resources & publish to IPFS, etc"""

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
        import page_info
        for page in page_info.get_pages():
            make(page)
    else:
        print("[make %r]" %page)
        print("[FIXME] make.make() not implemented")

def make_deps(page=None):
    """Determine the dependencies for building the given page,
    and create the proper Makefile rules for that,
    inserting them into <page>.deps.
    If page is None, this will create ALL dependencies,
    otherwise, page should be a page_info.Page object."""
    print("[FIXME] make.make_deps() not implemented")

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
        if target == "dependencies.includes":
            make_deps()
        elif target.endswith(".deps"):
            page = page_info.get_pages()[target[:-len(".deps")]]
            make_deps(page)
        else:
            page = page_info.get_pages()[target]
            make(page)

