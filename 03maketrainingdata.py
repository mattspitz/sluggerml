#!/usr/bin/python

# input: parsed game logs filename, training set output filename
# output: parsed and cleaned training set

from common import TrainingDatum
import sys

def main():
    input_fn, output_fn = sys.argv[1:]

    out_f = open(output_fn, 'w')
    for line in open(input_fn):
        td = TrainingDatum.from_featureset_json(line.strip())
        out_f.write("%s\n" % td.to_json())

if __name__ == "__main__":
    main()
