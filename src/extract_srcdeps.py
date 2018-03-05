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
    output = """
# _Buildtime_ dependencies for this file
{src_deps}
""".format(**globals(), **page_info)
    out_file = open(out_path, 'w+')
    out_file.write(output)

