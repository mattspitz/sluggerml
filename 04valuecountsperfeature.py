#!/usr/bin/python

# input: output filename, training set filename(s)
# output: all possible feature / value pairs

import json
import sys

from common import TrainingDatum

def main():
    output_fn, tdata_fns = sys.argv[1], sys.argv[2:]
    all_features = {}
    for fn in tdata_fns:
        print "processing", fn
        for line in open(fn):
            td = json.loads(line.strip())
            for fname, fval in td.iteritems():
                all_features.setdefault(fname, set()).add(fval)

    for k in td:
        all_features[k] = sorted(all_features[k])

    json.dump(all_features, open(output_fn, 'w'))

if __name__ == "__main__":
    main()
