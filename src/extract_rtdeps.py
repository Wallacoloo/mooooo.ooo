#!/usr/bin/env python3
from page_info import config

import jsonpickle, sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input .build> <.rtdeps>" %sys.argv[0])
        sys.exit(1)
    in_path, out_path = sys.argv[1:]

    build = jsonpickle.decode(open(in_path).read())
    srcdep = out_path.replace(".rtdeps", ".srcdeps")
    include_rtdeps = "\n".join(
        "include {}.rtdeps".format(
            d.replace(".srcinfo","")
            .replace(config['build']['output'], config['build']['intermediate'])
        )
        for d in build['rtdeps'] )
    include_srcdeps = include_rtdeps.replace(".rtdeps", ".srcdeps")
    builddir_deps = [d.replace(".srcinfo", "")
        .replace(config['build']['intermediate'], config['build']['output'])
        for d in build['rtdeps'] ]
    rt_deps = "\\\n    ".join("$(RT_DEPS{})".format(d) for d in builddir_deps)
    output = """
include {srcdep}
# But we don't know how to compute the above variables (the runtime dependencies
# of our runtime dependencies).
# Accomplish that by building and including any .rtdeps files for our runtime
# dependencies, below:
{include_srcdeps}
{include_rtdeps}
# _Runtime_ dependencies for this file
RT_DEPS{build_path} = {build_path} \
    {rt_deps}
""".format(**globals(), **build)
    out_file = open(out_path, 'w+')
    out_file.write(output)

