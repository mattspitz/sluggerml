import json

class FeatureSet:
    __slots__ = [
        # general, per-game
        "daynight",
        "date",
        "number", # 0 is the first game of the day, 1 is the second of a doubleheader
        "site", # ballpark
        "temp",
        "winddir"
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
            setattr(obj, s, getattr(self, s))
        return obj
