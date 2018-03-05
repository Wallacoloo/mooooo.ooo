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
    # all runtime intermediates we need
    rtdeps = [
            d.replace(".srcinfo","")
            .replace(config['build']['output'], config['build']['intermediate'])
            for d in build['rtdeps'] ]
    # actual Make code to include the .alldeps
    include_alldeps = "\n".join(
        "include {}.alldeps".format(d)
        for d in rtdeps)
    builddir_deps = [d
        .replace(config['build']['intermediate'], config['build']['output'])
        for d in rtdeps]
    rt_deps_vars = "\\\n    ".join("$(RT_DEPS{})".format(d) for d in builddir_deps)
    output = """
# Trigger calculation of the runtime dependencies for each of our dependencies
{include_alldeps}
# _Runtime_ dependencies for this file
RT_DEPS{build_path} = {build_path} \
    {rt_deps_vars}
""".format(build_path=build['build_path'], **globals())
    out_file = open(out_path, 'w+')
    out_file.write(output)

