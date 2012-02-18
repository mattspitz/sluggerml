import json
import re

class Label(object):
    HR = "HR"
    K = "K"
    OTHER = "OTHER"

class GameState(object):
    __slots__ = [
        "visteam",
        "hometeam",
        "visteam_pitcherid",
        "hometeam_pitcherid"
        ]

    def __str__(self):
        return "<GameState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in self.__slots__ ])

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
        return "<PlayerState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in self.__slots__ ])

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
            if hasattr(self, slot):
                d[slot] = getattr(self, slot)
        return json.dumps(d)

    def from_json(self):
        # TODO
        pass

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
        for field in ["fieldpos", "batpos", "team", "visorhome", "retrosheetid"]:
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
            setattr(self, "%s_%s" % (prefix, lahman_field), getattr(player_state, "lahman_%s" % lahman_field))

line_regex = re.compile(r'((?:".*?")|.*?)(?:,|$)')
def csv_split(line):
    # there's gotta be a better way to do this
    values = line_regex.findall(line)
    if not line.endswith(","):
        return values[:-1]
    return values
