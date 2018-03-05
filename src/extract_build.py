#!/usr/bin/env python3
from page_info import config

import jsonpickle, sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input .build> <output>" %sys.argv[0])
        sys.exit(1)
    in_path, out_path = sys.argv[1:]

    build = jsonpickle.decode(open(in_path).read())
    output = build['output']
    if isinstance(output, str):
        out_file = open(out_path, 'w+')
    else:
        out_file = open(out_path, 'wb+')
    out_file.write(output)

