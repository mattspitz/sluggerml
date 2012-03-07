
from cgi import FieldStorage, parse_qs
import json
import re

from common import load_bayes_from_file, UNK

PREDICTOR_LABELS = ["HR", "K", "OTHER"]
HISTOGRAM_FN = "output/histogram_1980-2011.json"
ALL_FEATURES = None
def get_all_features(args, post_data):
    global ALL_FEATURES

    if ALL_FEATURES is None:
        # pedantic note: I could do this in one line, but that would be wrong.
        ALL_FEATURES = []
        for fname, valdict in json.load(open(HISTOGRAM_FN)).iteritems():

            if fname != "label":
                def keyfn(x):
                    try:
                        return int(x)
                    except Exception:
                        pass
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

def predict_bundle(args, post_data):
    # this is a silly hack because qs args are coming through to the post data and I'm too lazy to figure out why
    d = dict( (k, post_data[k].value) for k in post_data if k != "type" )

    for k in d.keys():
        try:
            # gah, this is so gross; stupid post args not being ints and I'm running out of time.  PyCon is Friday!
            d[k] = int(d[k])
        except ValueError:
            pass

    response = {"bundle": {},
                "baseline": {}}
    probdist = CLASSIFIER.prob_classify(d)
    baseline_probdist = CLASSIFIER.prob_classify({})
    for label in PREDICTOR_LABELS:
        response["bundle"][label] = probdist.prob(label)
        response["baseline"][label] = baseline_probdist.prob(label)

    return response

BAYES_FN = "output/bayes_1980-2011.json"
CLASSIFIER = load_bayes_from_file(BAYES_FN)
def get_response(args, post_data):
    response_map = {"features": get_all_features,
                    "predict": predict_bundle}
    unspecified = (lambda x,y: {"error": "specify 'type'"})

    fn = response_map.get(args.pop("type", None), unspecified)
    return fn(args, post_data)

# WSGI funtimes
def get_args(environ):
    # just use the first argument for each key provided
    return dict(( (k, v[0]) for k,v in parse_qs(environ["QUERY_STRING"]).iteritems() ))

def get_post_data(environ):
    post_data = environ.copy()
    return FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_data,
        keep_blank_values=True)

def application(environ, start_response):
    args = get_args(environ)
    post_data = get_post_data(environ)
    response = json.dumps(get_response(args, post_data))

    headers = [ ("Content-Type", "application/json"),
                ("Content-Length", len(response)) ]

    start_response("200 OK", headers)
    return iter([response])
