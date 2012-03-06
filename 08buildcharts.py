#!/usr/bin/python

# input: histogram fn and an output directory
# output: per-feature significance charts for home runs and strikeouts

import csv
import json
import os.path
import re
import sys

from common import UNK

def build_chart(feature_name, data, category_names, output_dir):
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.legends import Legend
    from reportlab.graphics.charts.textlabels import Label
    from reportlab.lib import colors
    from reportlab.lib.validators import Auto

    # build chart and save it
    d = Drawing(800, 600)
    d.add(String(200,180,feature_name), name='title')

    chart = VerticalBarChart()
    chart.width = d.width-100
    chart.height = d.height-75
    chart.x = 40
    chart.y = 40

    chart.data = data
    chart.categoryAxis.categoryNames = category_names
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 2

    chart.bars[0].fillColor = colors.red
    chart.bars[1].fillColor = colors.blue

    d.add(chart)

    d.title.x = d.width/2
    d.title.y = d.height - 30
    d.title.textAnchor ='middle'
    d.title.fontSize = 24

    d.add(Legend(),name='Legend')
    d.Legend.colorNamePairs  = [(chart.bars[i].fillColor, name) for i, name in enumerate(["Home Run", "Strikeout"])]
    d.Legend.fontName = 'Times-Roman'
    d.Legend.fontSize = 16
    d.Legend.x = d.width-80
    d.Legend.y = d.height-25
    d.Legend.dxTextSpace = 5
    d.Legend.dy = 5
    d.Legend.dx = 5
    d.Legend.deltay = 5
    d.Legend.alignment ='right'

    d.add(Label(),name='XLabel')
    d.XLabel.fontName = 'Times-Roman'
    d.XLabel.fontSize = 12
    d.XLabel.x = chart.x + chart.width/2
    d.XLabel.y = 15
    d.XLabel.textAnchor ='middle'
    d.XLabel._text = "Value"

    d.add(Label(),name='YLabel')
    d.YLabel.fontName = 'Times-Roman'
    d.YLabel.fontSize = 12
    d.YLabel.x = 10
    d.YLabel.y = chart.y + chart.height/2
    d.YLabel.angle = 90
    d.YLabel.textAnchor ='middle'
    d.YLabel._text = "Likelihood Index"

    d.save(fnRoot=os.path.join(output_dir, feature_name), formats=['png'])

def build_csv(feature_name, data, category_names, output_dir):
    out_csv = csv.writer(open(os.path.join(output_dir, feature_name + ".csv"), "w"))

    out_csv.writerow([""] + category_names)
    out_csv.writerow(["HR"] + data[0])
    out_csv.writerow(["K"] + data[1])

def dump_feature(feature_name, value_dict, output_dir):
    # drop insignificant features
    value_dict.pop(UNK, None)
    # HACK: apparently game_temp = 0 is the same as <UNK>
    if feature_name == "game_temp":
        value_dict.pop("[0-5)", None)

    # first pass, sum up the labels
    label_counts = {}
    for fval, counts_by_label in value_dict.iteritems():
        for label, count in counts_by_label.iteritems():
            label_counts[label] = label_counts.get(label, 0) + count

    num_samples = sum(label_counts.itervalues())

    predictor_labels = ["HR", "K"]
    data = [ [] for l in predictor_labels ]
    category_names = []

    baseline_likelihood = dict( (k, float(label_counts[k])/num_samples) for k in predictor_labels )

    def keyfn(x):
        # gah, pesky numeric values
        try:
            return int(x)
        except Exception:
            pass
        if x.startswith("[") and x.endswith(")"): return int(re.match("\[(-?\d+)-\d+\)", x).group(1))
        if x.endswith("+"): return int(x[:-1])
        return x

    # (HR-index, K-index) for each significant value
    for fval in sorted(value_dict.keys(), key=keyfn):
        counts_by_label = value_dict[fval]

        # "significant" features have > 0.05% of the total number of samples
        if sum(counts_by_label.values()) > 0.0005 * num_samples:
            category_names.append(fval)
            for i, label in enumerate(predictor_labels):
                likelihood = float(counts_by_label[label])/sum(counts_by_label.values())
                data[i].append(likelihood / baseline_likelihood[label])

    build_chart(feature_name, data, category_names, output_dir)
    build_csv(feature_name, data, category_names, output_dir)

def main():
    histogram_fn, output_dir = sys.argv[1:]

    histogram = json.load(open(histogram_fn))
    for feature, value_dict in histogram.iteritems():
        dump_feature(feature, value_dict, output_dir)

if __name__ == "__main__":
    main()
