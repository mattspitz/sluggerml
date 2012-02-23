#!/usr/bin/python

# input: beginning and ending year (e.g. 1996 2011), label to predict, feature type, algorithm
# output: p-independence for all features

import json
import os
import multiprocessing
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
        return numpy.array(lst)

    def get_feature_name(self, idx):
        return self.indices2features[idx]

def print_significant_features(p_values, feature_mapper, start_year, end_year):
    best_indices = sorted(range(len(p_values)),
                          key=(lambda x: p_values[x]))
    lines = []
    for idx in best_indices:
        lines.append( [feature_mapper.get_feature_name(idx), str(p_values[idx])] )

    max_width_by_col = [ max( len(lines[i][c]) for i in xrange(len(lines)) ) for c in xrange(len(lines[0])) ]
    for fname, val in lines:
        print fname.ljust(max_width_by_col[0]), "\t", val.ljust(max_width_by_col[1])

def _read_file(args):
    fn, params, functions = args[0], args[1], args[2:]
    results = []
    for line in open(fn):
        results.append([ f(line.strip(), **params) for f in functions ])
    return results

def _get_label(line, **kwargs):
    return 1 if json.loads(line)["label"] == kwargs["predicted_label"] else 0

def _make_arr(line, **kwargs):
    return kwargs["feature_mapper"].make_feature_array(json.loads(line))

def _noop(line, **kwargs):
    pass

def get_feature_array(start_year, end_year, feature_mapper, predicted_label):
    pool = multiprocessing.Pool(processes=(multiprocessing.cpu_count()-1))

    try:
        def send_to_pool(args):
            return itertools.chain(*pool.imap(_read_file, args, chunksize=1))

        filenames = [ os.path.join("data", "training", "%d.tdata" % year) for year in range(start_year, end_year + 1) ]
        args = [ (fn, {}, _noop) for fn in filenames ]

        num_lines = sum( 1 for _ in enumerate(send_to_pool(args)) )

        value_array = numpy.zeros( (num_lines, feature_mapper.get_num_features()) )
        labels = numpy.zeros(num_lines)

        kwargs = {"feature_mapper": feature_mapper, "predicted_label": predicted_label}
        args = [ (fn, kwargs, _make_arr, _get_label) for fn in filenames ]

        # rip through all data points again, this time populating the array
        for i, (val_arr, label) in enumerate(send_to_pool(args)):
            for j in xrange(len(val_arr)):
                value_array[i][j] = val_arr[j]
            labels[i] = label

        return value_array, labels
    finally:
        pool.close()

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
    start_year, end_year, predicted_label, feature_type, selection_type = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]

    feature_mapper_clss = {"name": Features2IndicesByFeature, "nameval": Features2IndicesByValue}[feature_type]
    selection_fn = {"chi2": univariate_selection.chi2, "anova": univariate_selection.f_classif}[selection_type]

    feature_mapper = get_feature_mapper(start_year, end_year, feature_mapper_clss)
    value_array, labels = get_feature_array(start_year, end_year, feature_mapper, predicted_label)

    _, p_values = selection_fn(value_array, labels)
    print_significant_features(p_values, feature_mapper, start_year, end_year)

if __name__ == "__main__":
    main()
