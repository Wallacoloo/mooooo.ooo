#!/usr/bin/env python3

import sys, jsonpickle

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input .pageinfo> <.deps>" %sys.argv[0])
        sys.exit(1)
    in_path, out_path = sys.argv[1:]

    page_info = jsonpickle.decode(open(in_path).read())
    make_deps = "\n".join("$(shell make {}.deps)".format(d) for d in page_info['rtdeps'])
    include_deps = "\n".join("-include {}.deps".format(d) for d in page_info['rtdeps'])
    src_deps = "\\\n    ".join(page_info['srcdeps'])
    rt_deps = "\\\n    ".join("$(RTDEPS{})".format(d) for d in page_info['rtdeps'])
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
{make_deps}
{include_deps}
""".format(**globals(), **page_info)
    out_file = open(out_path, 'w+')
    out_file.write(output)

