#!/usr/bin/python

# input: beginning and ending year (e.g. 1996 2011)
# output: ?

import json
import os
import sys
import time

import itertools
import numpy
from sklearn.feature_selection import univariate_selection

class Features2Indices(object):
    def __init__(self, featuresets):
        raise NotImplemented

class Features2IndicesByFeature(Features2Indices):
    """ Just uses the feature name itself, not particular values. """
    def __init__(self, featuresets):
        self.features2indices = {}
        self.indices2features = []
        for i, (key, all_values) in enumerate(sorted(featuresets.items())):
            self.features2indices[key] = {"index": i,
                                          "values": dict([ (j, v) for v, j in enumerate(sorted(all_values)) ])}
            self.indices2features.append({"key": key,
                                          "values": sorted(all_values)})

    def get_num_features(self):
        return len(self.features2indices)

    def make_feature_array(self, dct):
        lst = [ -1 ] * self.get_num_features()
        for k, v in dct.iteritems():
            if k == "label":
                continue
            idx = self.features2indices[k]["index"]
            val = self.features2indices[k]["values"][v]
            lst[idx] = val
        return lst

    def get_feature_name(self, idx):
        return self.indices2features[idx]["key"]

class Features2IndicesByValue(Features2Indices):
    """ Uses feature name+value as the feature name. """
    @classmethod
    def get_fname(cls, key, value):
        return "%s::%s" % (key, value)

    def __init__(self, featuresets):
        self.features2indices = {}
        self.indices2features = []
        curpos = 0
        for key, all_values in sorted(featuresets.items()):
            for value in sorted(all_values):
                fname = self.get_fname(key, value)
                self.features2indices[fname] = curpos
                self.indices2features.append(fname)
                curpos += 1

    def get_num_features(self):
        return len(self.features2indices)

    def make_feature_array(self, dct):
        lst = [ -1 ] * self.get_num_features()
        for k, v in dct.iteritems():
            if k == "label":
                continue
            fname = self.get_fname(k, v)
            idx = self.features2indices[fname]
            lst[idx] = 1
        return lst

    def get_feature_name(self, idx):
        return self.indices2features[idx]

def print_significant_features(p_values, feature_mapper):
    print
    print "=== significant features ==="
    best_indices = sorted(range(len(p_values)),
                          key=(lambda x: p_values[x]))
    lines = []
    for idx in best_indices:
        lines.append( [feature_mapper.get_feature_name(idx), str(p_values[idx])] )

    max_width_by_col = [ max( len(lines[i][c]) for i in xrange(len(lines)) ) for c in xrange(len(lines[0])) ]
    for fname, val in lines:
        print fname.ljust(max_width_by_col[0]), "\t", val.ljust(max_width_by_col[1])

def get_feature_array(start_year, end_year, feature_mapper, predicted_label):
    def tdata_gen(functions, print_progress=False):
        for year in range(start_year, end_year + 1):
            fn = os.path.join("data", "training", "%d.tdata" % year)

            if print_progress:
                start = time.time()
                print fn, "...",

            for line in open(fn):
                yield ( f(line.strip()) for f in functions )

            if print_progress:
                print "done (%0.4f seconds)" % (time.time()-start)

    def make_arr(line):
        return feature_mapper.make_feature_array(json.loads(line))

    num_lines = 0
    # rip through all data points once to build up the array (prevents keeping all objects in memory)
    for _, in tdata_gen( (lambda x: 1,) ):
        num_lines += 1

    value_array = numpy.zeros( (num_lines, feature_mapper.get_num_features()) )
    labels = numpy.zeros(num_lines)

    # rip through all data points again, this time populating the array
    for i, (val_arr, label) in enumerate(tdata_gen([make_arr, lambda ln: 1 if json.loads(ln)["label"] == predicted_label else 0], print_progress=True)):
        for j in xrange(len(val_arr)):
            value_array[i][j] = val_arr[j]
        labels[i] = label

    return value_array, labels

def get_feature_mapper(start_year, end_year, feature_mapper_clss):
    # grabs all possible features for a given start/end year and maps all keys and values to integers for arrays

    featuresets = {}
    for year in range(start_year, end_year + 1):
        fn = os.path.join("data", "featuresets", "%d.json" % year)
        d = json.load(open(fn))
        for k, values in d.iteritems():
            featuresets.setdefault(k, set()).update(set(values))

    return feature_mapper_clss(featuresets)

def main():
    start_year, end_year, predicted_label, feature_type = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]

    feature_mapper_clss = {"name": Features2IndicesByFeature, "nameval": Features2IndicesByValue}[feature_type]

    feature_mapper = get_feature_mapper(start_year, end_year, feature_mapper_clss)
    value_array, labels = get_feature_array(start_year, end_year, feature_mapper, predicted_label)

    _, p_values = univariate_selection.chi2(value_array, labels)
    print_significant_features(p_values, feature_mapper)

if __name__ == "__main__":
    main()
