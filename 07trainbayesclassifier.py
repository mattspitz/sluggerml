#!/usr/bin/python

# input: beginning and ending year (e.g. 1996 2011), output filename
# output: per feature, per value, per value histogram

import json
import os
import sys

import nltk

from common import dump_bayes_to_file

def tset_gen(start_year, end_year):
    for fn in ( os.path.join("data", "training", "%d.tdata" % year) for year in range(start_year, end_year + 1) ):
        print fn
        for line in open(fn):
            td = json.loads(line.strip())
            label = td.pop("label")
            yield (td, label)

def main():
    start_year, end_year, out_fn = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]

    dump_bayes_to_file(nltk.NaiveBayesClassifier.train(tset_gen(start_year, end_year)),
                       out_fn)

if __name__ == "__main__":
    main()
