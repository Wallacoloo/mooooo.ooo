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
    print("[FIXME] make.make() not implemented")

def publish():
    """Publish the website to IPFS and update any necessary host records"""
    print("[FIXME] make.publish() not implemented")


if __name__ == "__main__":
    # Build all the targets given on the command line
    import sys
    import page_info
    targets = sys.argv[1:]

    for target in targets:
        if target == "all":
            make()
        elif target == "publish":
            publish()
        else:
            page = page_info.get_pages()[target]
            make(page)

