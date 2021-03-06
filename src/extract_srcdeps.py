#!/usr/bin/env python3
from page_info import config

import jsonpickle, sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input .srcinfo> <.srcdeps>" %sys.argv[0])
        sys.exit(1)
    in_path, out_path = sys.argv[1:]

    page_info = jsonpickle.decode(open(in_path).read())
    src_deps = "\n".join(
            "{intermediate_path}.build: {d}".format(d=d, **page_info)
            for d in page_info['srcdeps'])
    incl_src_deps = "\n".join(
            "include {d}.srcdeps".format(d= \
                d.replace(".srcinfo", "")
                .replace(".build", "")
            ) for d in page_info['srcdeps'])
    output = """
ifndef INCL_{out_path}
# include guard
INCL_{out_path}=y

# _Buildtime_ dependencies for this file
{incl_src_deps}
{src_deps}

# How to build this file
{intermediate_path}.build: {intermediate_src_path}
	./build_page.py $< $@
endif
""".format(intermediate_path=page_info['intermediate_path'],
        intermediate_src_path=page_info['intermediate_src_path'],
        **globals())
    out_file = open(out_path, 'w+')
    out_file.write(output)

