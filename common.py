import datetime
import json
import logging
import pickle
import re

import nltk

UNK = "<UNK>"

class Label(object):
    HR = "HR"
    K = "K"
    OTHER = "OTHER"

    @classmethod
    def get_all(cls):
        return [ k for k in dir(cls) if not k.startswith("_") and k != "get_all" ]

class GameState(object):
    __slots__ = [
        "visteam",
        "hometeam",
        "visteam_pitcherid",
        "hometeam_pitcherid"
        ]

    def __str__(self):
        return "<GameState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in sorted(self.__slots__) ])

class PlayerState(object):
    lahman_stats = ["birthYear",
                    "birthMonth",
                    "birthDay",
                    "birthCountry",
                    "birthState",
                    "birthCity",
                    "weight",
                    "height",
                    "bats",
                    "throws",
                    "debut",
                    "finalGame",
                    "college"]

    player_stats = ["retrosheetid",
                    "visorhome",
                    "team",
                    "name",
                    "fieldpos",
                    "batpos"]
    __slots__ = player_stats \
        + [ "lahman_%s" % stat for stat in lahman_stats ]

    def __str__(self):
        return "<PlayerState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in sorted(self.__slots__) ])

    def __repr__(self):
        return self.__str__()

class FeatureSet(object):
    __slots__ = [
        # general, per-game
        "game_daynight",
        "game_date",
        "game_number", # 0 is the first game of the day, 1 is the second of a doubleheader
        "game_site", # ballpark
        "game_temp",
        "game_winddir",

        # at-bat
        "ab_inning",
        "ab_numballs",
        "ab_numstrikes",

        # label
        "label" ] \
        + [ "batter_%s" % stat for stat in (PlayerState.player_stats + PlayerState.lahman_stats) ] \
        + [ "pitcher_%s" % stat for stat in (PlayerState.player_stats + PlayerState.lahman_stats) ]

    def __str__(self):
        return self.to_json()

    def to_json(self):
        d = {}
        for slot in self.__slots__:
            # all values are strings!
            d[slot] = getattr(self, slot, "").strip() or UNK
        return json.dumps(d)

    @classmethod
    def get_parse_map(cls):
        if not hasattr(cls, "parse_map"):
            player_ints = ["birthYear",
                           "birthMonth",
                           "birthDay",
                           "weight",
                           "height",
                           "batpos",
                           "fieldpos"]
            int_fields = ["game_number",
                          "game_temp",
                          "ab_inning",
                          "ab_numballs",
                          "ab_numstrikes",
                          "birthYear"] + \
                          [ "batter_%s" % k for k in player_ints ] + \
                          [ "pitcher_%s" % k for k in player_ints ]
            parse_map = {"game_date": (lambda x: datetime.datetime.strptime(x, "%Y/%m/%d")),
                         "batter_debut": (lambda x: datetime.datetime.strptime(x, "%m/%d/%Y")),
                         "pitcher_debut": (lambda x: datetime.datetime.strptime(x, "%m/%d/%Y"))}

            for field in int_fields:
                parse_map[field] = int
            cls.parse_map = parse_map
        return cls.parse_map

    def copy(self):
        # this is very puzzling; why does a new object created in the context of a given object have all the fields of the object in which the new object is created...?
        new_obj = FeatureSet()
        assert(new_obj.to_json() == self.to_json())
        return new_obj

    def add_batter_info(self, batter_state):
        self.add_player_info(batter_state, "batter")

    def add_pitcher_info(self, pitcher_state):
        self.add_player_info(pitcher_state, "pitcher")

    def add_player_info(self, player_state, prefix):
        for field in ["fieldpos", "batpos", "team", "visorhome", "name", "retrosheetid"]:
            setattr(self, "%s_%s" % (prefix, field), getattr(player_state, field))

        for lahman_field in ["birthYear",
                             "birthMonth",
                             "birthDay",
                             "birthCountry",
                             "birthState",
                             "birthCity",
                             "weight",
                             "height",
                             "bats",
                             "throws",
                             "debut",
                             "college"]:
            if hasattr(player_state, "lahman_%s" % lahman_field):
                setattr(self, "%s_%s" % (prefix, lahman_field), getattr(player_state, "lahman_%s" % lahman_field))

class TrainingDatum(object):
    player_stats = ["age", # bucketized by 3
                    "weight", # bucketized by 10
                    "height", # bucketized by 3
                    "team",
                    "experience", # game date - debut, bucketized by 3
                    "birthCountry",
                    "throws"]

    batter_stats = ["fieldpos",
                    "batpos", # bucketized 1-2,3-5,6-7,8-9,10,11 (10 is DH, 11 is PH)
                    "bats",
                    "visorhome" ]

    __slots__ = ["game_daynight",
                 "game_month", # bucketized by 2
                 "game_year", # bucketized by 5
                 "game_number", # 0 or 1+
                 "game_site",
                 "game_temp", # bucketized by 5
                 "game_winddir", # in or out

                 "ab_inning", # bucketized: 1-3, 4-6, 7-9, 9+
                 "ab_numballs",
                 "ab_numstrikes",
                 "ab_lrmatchup", # "same" for L vs. R, "opposite" for R vs. R

                 "label"] \
                 + [ "batter_%s" % stat for stat in (player_stats + batter_stats) ] \
                 + [ "pitcher_%s" % stat for stat in player_stats ]

    @classmethod
    def bucketized(cls, val, buckets=None, granularity=None):
        if granularity:
            lower = (val / granularity) * granularity
            upper = ((val / granularity) + 1) * granularity
            return "[%d-%d)" % (lower, upper)
        if buckets:
            for i in reversed(xrange(len(buckets))):
                bkt = buckets[i]
                if val >= bkt:
                    if i == (len(buckets) - 1):
                        # this is the last bucket
                        return "%d+" % bkt
                    else:
                        return "[%d-%d)" % (bkt, buckets[i+1])
            raise Exception, "Bucket value %s doesn't fit into buckets: %s" % (val, buckets)

    @classmethod
    def get_winddir(cls, d):
        if d["game_winddir"].startswith("from"):
            return "in"
        elif d["game_winddir"].startswith("to"):
            return "out"
        return UNK

    @classmethod
    def get_lrmatchup(cls, d):
        if d["batter_bats"] is UNK:
            return UNK

        if d["batter_bats"] in "B":
            return "same"

        if d["pitcher_throws"] is UNK:
            return None

        return "same" if d["batter_bats"] == d["pitcher_throws"] else "opposite"

    @classmethod
    def from_featureset_json(cls, json_str):
        d = json.loads(json_str)
        parse_map = FeatureSet.get_parse_map()

        for k in d:
            # all keys are strings in the .features format
            if d[k] != UNK and k in parse_map:
                try:
                    d[k] = parse_map[k](d[k])
                except ValueError:
                    d[k] = UNK

        obj = cls()

        def unk_check(obj_key, keys=None):
            """ If all specified keys are known, return True.  Otherwise,
            set UNK on the specified object key. """
            if keys is None:
                keys = [ obj_key ]

            if all( (d[k] != UNK) for k in keys):
                # proceed with calculation
                return True
            else:
                setattr(obj, obj_key, UNK)
                return False

        obj.game_daynight = d["game_daynight"]
        if unk_check("game_date"):
            obj.game_month = cls.bucketized(d["game_date"].month, granularity=2)

        if unk_check("game_date"):
            obj.game_year = cls.bucketized(d["game_date"].year, granularity=5)

        if unk_check("game_number"):
            obj.game_number = cls.bucketized(d["game_number"], buckets=[0,1])

        if unk_check("game_temp"):
            obj.game_temp = cls.bucketized(d["game_temp"], granularity=5)

        obj.game_site = d["game_site"]

        obj.game_winddir = cls.get_winddir(d)

        if unk_check("ab_inning"):
            obj.ab_inning = cls.bucketized(d["ab_inning"], buckets=[1,4,7,10])

        obj.ab_numballs = d["ab_numballs"]
        obj.ab_numstrikes = d["ab_numstrikes"]

        obj.ab_lrmatchup = cls.get_lrmatchup(d)

        obj.batter_bats = d["batter_bats"]
        obj.batter_fieldpos = d["batter_fieldpos"]
        obj.batter_visorhome = d["batter_visorhome"]

        if unk_check("batter_batpos"):
            obj.batter_batpos = cls.bucketized(d["batter_batpos"], buckets=[1,3,5,8,10,11,12])

        obj.label = d["label"]

        for prefix in ["batter_", "pitcher_"]:
            def key(k):
                return prefix + k

            def year_from_td(td):
                return td.days / 365

            if unk_check(key("age"), keys=[key("birthYear"), key("birthMonth"), key("birthDay"), "game_date"]):
                birthday = datetime.datetime(d[key("birthYear")], d[key("birthMonth")], d[key("birthDay")])
                setattr(obj, key("age"), cls.bucketized(year_from_td(d["game_date"] - birthday), granularity=3))

            if unk_check(key("weight")):
                setattr(obj, key("weight"), cls.bucketized(d[key("weight")], granularity=10))
            if unk_check(key("height")):
                setattr(obj, key("height"), cls.bucketized(d[key("height")], granularity=3))

            setattr(obj, key("team"), d[key("team")])
            setattr(obj, key("throws"), d[key("throws")])
            setattr(obj, key("birthCountry"), d[key("birthCountry")])

            if unk_check(key("experience"), keys=[key("debut"), "game_date"]):
                setattr(obj, key("experience"), cls.bucketized(year_from_td(d["game_date"] - d[key("debut")]), granularity=3))

        return obj

    def __str__(self):
        return "<TrainingDatum: %s>" % ", ".join([ "%s=%s" % (k, getattr(self, k)) for k in sorted(self.__slots__) if hasattr(self, k)])

    def to_json(self):
        return json.dumps(dict([ (slot, getattr(self,slot)) for slot in self.__slots__ ]))

line_regex = re.compile(r'((?:".*?")|.*?)(?:,|$)')
def csv_split(line):
    # there's gotta be a better way to do this
    values = line_regex.findall(line)
    if not line.endswith(","):
        return values[:-1]
    return values

def dump_bayes_to_file(bayes_classifier, filename):
    pickle.dump({"_label_probdist": bayes_classifier._label_probdist,
                 "_feature_probdist": bayes_classifier._feature_probdist},
                open(filename, "w"))

def load_bayes_from_file(filename):
    d = pickle.load(open(filename))
    return nltk.NaiveBayesClassifier(d["_label_probdist"], d["_feature_probdist"])
