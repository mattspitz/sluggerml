#!/usr/bin/python

# input: output filename, training set filename
# output: all possible feature / value pairs in that training set

import json
import sys

from common import TrainingDatum

def main():
    output_fn, tdata_fn = sys.argv[1], sys.argv[2]
    all_features = {}
    for line in open(tdata_fn):
        td = json.loads(line.strip())
        for fname, fval in td.iteritems():
            if fname != "label":
                all_features.setdefault(fname, set()).add(fval)

    for k in all_features:
        all_features[k] = sorted(all_features[k])

    json.dump(all_features, open(output_fn, 'w'))

if __name__ == "__main__":
    main()
