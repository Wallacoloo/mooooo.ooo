#!/usr/bin/env python3
""" Extract git info from a file,
i.e. authors and commit dates.
"""
from page_info import Author
import dateutil, json, jsonpickle, subprocess, sys

def get_unparsed_commits(filename):
    """Returns an array of commit dicts, where each entry looks like:
    { 'author': '<name>', 'date': '<date>', 'message': '<message>' }
    """
    proc = subprocess.Popen([
            'git',
            'log',
            '--follow',
            '--pretty=format:{%n  "author": "%aN",%n  "date": "%cD",%n  "message": "%s"%n},',
            "--",
            filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if stderr:
        raise RuntimeError("git log error:", stderr)

    raw = stdout.decode('utf-8')
    return json.loads("[%s []]" %raw)[:-1]

def get_commits(filename):
    """Returns an array of commit dicts, where each entry looks like:
    { 'author': <Author object>, 'date': <Datetime object>, 'message': '<message>' }
    """
    commits = get_unparsed_commits(filename)
    for c in commits:
        c["author"] = Author(c["author"])
        c["date"] = dateutil.parser.parse(c["date"])

    return commits

def get_authors_of_file(filename):
    """Return a set of Author objects that have commits associated with the
    file"""
    commits = get_commits(filename)

    authors = set()
    for commit in commits:
        authors.add(commit['author'])
    return list(authors)

def get_pub_date_of_file(filename):
    """Returns the date at which this file was committed with the message "PUBLISH", indicating it is ready to be made public"""
    commits = get_commits(filename)

    for c in commits:
        if c["message"] == "PUBLISH":
            return c["date"]

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input filename> <output .srcinfo>" %sys.argv[0])
        sys.exit(1)
    git_filename, out_path = sys.argv[1:]

    authors = get_authors_of_file(git_filename)
    pub_date = get_pub_date_of_file(git_filename)
    commits = sorted(get_commits(git_filename), key=lambda c: c["date"])
    last_edit_date = commits[-1]["date"] if commits else None

    page_info = dict(
        authors = authors,
        pub_date = pub_date,
        last_edit_date = last_edit_date,
    )

    output = jsonpickle.encode(page_info)
    out_file = open(out_path, "w+")
    out_file.write(output)

