
from cgi import parse_qs
import json
import re

from common import load_bayes_from_file, UNK

PREDICTOR_LABELS = ["HR", "K"]
HISTOGRAM_FN = "output/histogram_1980-2011.json"
ALL_FEATURES = None
def get_all_features(args):
    global ALL_FEATURES

    if ALL_FEATURES is None:
        # pedantic note: I could do this in one line, but that would be wrong.
        ALL_FEATURES = []
        for fname, valdict in json.load(open(HISTOGRAM_FN)).iteritems():

            if fname != "label":
                def keyfn(x):
                    # gah, pesky numeric values
                    if x.startswith("[") and x.endswith(")"): return int(re.match("\[(-?\d+)-\d+\)", x).group(1))
                    if x.endswith("+"): return int(x[:-1])
                    return x

                tpl = (fname,
                       sorted([ k for k in valdict.keys() if k != UNK ],
                              key=keyfn))
                ALL_FEATURES.append(tpl)

        ALL_FEATURES.sort()

    return {"features": ALL_FEATURES}

BAYES_FN = "output/bayes_1980-2011.json"
CLASSIFIER = load_bayes_from_file(BAYES_FN)
def get_response(args):
    response_map = {"features": get_all_features}
    unspecified = (lambda x: {"error": "specify 'type'"})

    fn = response_map.get(args.pop("t", None), unspecified)
    return fn(args)

# WSGI funtimes
def get_args(environ):
    # just use the first argument for each key provided
    return dict(( (k, v[0]) for k,v in parse_qs(environ["QUERY_STRING"]).iteritems() ))

def application(environ, start_response):
    args = get_args(environ)
    response = json.dumps(get_response(args))

    headers = [ ("Content-Type", "application/json"),
                ("Content-Length", len(response)) ]

    start_response("200 OK", headers)
    return iter([response])
