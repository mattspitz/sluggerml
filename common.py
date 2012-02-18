import json

class Label:
    HR = "HR"
    K = "K"
    OTHER = "OTHER"

class GameState:
    __slots__ = [
        "visteam",
        "hometeam"
        ]

    def __str__(self):
        return "<GameState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in self.__slots__ ])

class PlayerState:
    __slots__ = [
        "retrosheetid",
        "visorhome",
        "team",
        "name",
        "fieldpos",
        "batpos"
        ]

    def __str__(self):
        return "<PlayerState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in self.__slots__ ])

    def __repr__(self):
        return self.__str__()

class FeatureSet:
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

        # player stats
        "player_fieldpos",
        "player_batpos",
        "player_team",
        "player_visorhome",
        "player_retrosheetid",

        # label
        "label"
        ]

    def __str__(self):
        d = {}
        for slot in self.__slots__:
            if hasattr(self, slot):
                d[slot] = getattr(self, slot)
        return json.dumps(d)

    def copy(self):
        obj = FeatureSet()
        for s in self.__slots__:
            if hasattr(self, s):
                setattr(obj, s, getattr(self, s))
        return obj

    def add_player_info(self, player_state):
        for field in ["fieldpos", "batpos", "team", "visorhome", "retrosheetid"]:
            setattr(self, "player_%s" % field, getattr(player_state, field))
