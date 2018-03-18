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
    build_path=build['build_path']
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
    call_rt_deps = " ".join("$(call GET_RT_DEPS_{dep},{build_path} $(1))"
            .format(dep=d, build_path=build_path) for d in builddir_deps)
    output = """
ifndef INCL_{out_path}
#include guard
INCL_{out_path}=y
# Trigger calculation of the runtime dependencies for each of our dependencies
{include_alldeps}
# _Runtime_ dependencies for this file
define GET_RT_DEPS_{build_path}
$(if $(filter {build_path},$(1)), \\
    $(1), \\
    {build_path} {call_rt_deps} \\
)
endef
endif # include guard
""".format(**globals())
    out_file = open(out_path, 'w+')
    out_file.write(output)

