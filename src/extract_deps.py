#!/usr/bin/env python3
from page_info import config

import jsonpickle, sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input .srcinfo> <.deps>" %sys.argv[0])
        sys.exit(1)
    in_path, out_path = sys.argv[1:]

    page_info = jsonpickle.decode(open(in_path).read())
    include_deps = "\n".join("include {}.deps".format(d.replace(".srcinfo","")) for d in page_info['rtdeps'])
    src_deps = "\\\n    ".join(page_info['srcdeps'])
    builddir_deps = [d.replace(".srcinfo", "")
        .replace(config['build']['intermediate'], config['build']['output'])
        for d in page_info['rtdeps'] ]
    rt_deps = "\\\n    ".join("$(RT_DEPS{})".format(d) for d in builddir_deps)
    output = """
# _Buildtime_ dependencies for this file
{intermediate_path}: {src_deps}
# _Runtime_ dependencies for this file
RT_DEPS{build_path} = {build_path} \
    {rt_deps}
# But we don't know how to compute the above variables (the runtime dependencies
# of our runtime dependencies).
# Accomplish that by building and including any .deps files for our runtime
# dependencies, below:
{include_deps}
""".format(**globals(), **page_info)
    out_file = open(out_path, 'w+')
    out_file.write(output)

