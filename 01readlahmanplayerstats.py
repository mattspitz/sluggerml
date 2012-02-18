#!/usr/bin/python

# Converts Master.csv into a python shelf object
# input: Master.csv filename from the Lahman data set (http://seanlahman.com/files/database/readme59.txt), python shelf filename for data
# output: (none)

import re
import shelve
import sys

def process_master_file(shelf_fn, master_fn):
    lahman_shelf = shelve.open(shelf_fn, flag='n')

    for i, line in enumerate(open(master_fn)):
        line = line.strip()
        if i == 0:
            schema = line.split(",")
        else:
            # there's gotta be a better way to do this
            values = []
            line_regex = re.compile(r'((?:".*?")|.*?)(?:,|$)')
            values = line_regex.findall(line)[:-1]

            if len(values) != len(schema):
                raise Exception("Line mismatch: expected %d values, got %d.  Schema:\n%s\nLine:\n%s" % (len(schema), len(values), ",".join(schema), line))
            stats = dict( zip(schema, values) )
            lahman_shelf[stats["retroID"]] = stats

    lahman_shelf.close()

def main():
    shelf_fn = sys.argv[1]
    master_fn = sys.argv[2]

    process_master_file(shelf_fn, master_fn)

if __name__ == "__main__":
    main()
