#!/usr/bin/python

# input: filename(s) in EVA/EVN format
# output: training set representing labelled situations

from common import FeatureSet
import json
import re
import sys

class GameState:
    __slots__ = [
        "visteam",
        "hometeam"
        ]

    def __str__(self):
        return "<GameState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in self.__slots__ ])

class PlayerState:
    __slots__ = [
        "retrosheet_id",
        "team",
        "name",
        "field_pos",
        "bat_pos"
        ]

    def __str__(self):
        return "<PlayerState: %s>" % ", ".join([ "%s=%s" % (slot, getattr(self, slot, None)) for slot in self.__slots__ ])

    def __repr__(self):
        return self.__str__()

def parse_header(header):
    game_state = GameState()
    base_featureset = FeatureSet()

    for line in header.split("\n"):
        if line.startswith("info,"):
            _, key, value = line.strip().split(",")

            if key in ["visteam", "hometeam"]:
                setattr(GameState, key, value)

            if key in FeatureSet.__slots__:
                setattr(FeatureSet, key, value)

    return game_state, base_featureset

def parse_players(players):
    state_by_id = {}

    for line in players.split("\n"):
        if line.startswith("start,"):
            _, retrosheet_id, name, team, bat_pos, field_pos = line.strip().split(",")
            if retrosheet_id in state_by_id:
                raise Exception("Tried to add %s, which had been previously recorded.  Old: %s, new: %s" % (retrosheet_id, state_by_id[retrosheet_id], line.strip()))

            player_state = PlayerState()
            player_state.retrosheet_id = retrosheet_id
            player_state.name = name
            player_state.team = "visteam" if team == "1" else "hometeam"
            player_state.bat_pos = bat_pos
            player_state.field_pos = field_pos

            state_by_id[retrosheet_id] = player_state

    return state_by_id

def get_game_sections(game):
    sections_regex = re.compile(r"(?P<header>^id,.*?)"
                                r"(?P<players>^start,.*?)"
                                r"(?P<playbyplay>^play,.*?)"
                                r"(?P<data>^data,.*)$",
                                re.DOTALL | re.MULTILINE)
    return sections_regex.match(game)

def parse_game(game):
    sections = get_game_sections(game)

    game_state, base_featureset = parse_header(sections.group("header"))
    player_state_by_id = parse_players(sections.group("players"))

    for feature_set in get_feature_sets(base_featureset, player_state_by_id):
        print feature_set

def parse_ev(ev_fn):
    game_regex = re.compile(r"(\s|^)id,(.*?)(?=((\s|^)id,|$))", re.DOTALL)

    num = 1
    for i, match in enumerate(game_regex.finditer(open(ev_fn).read())):
        if i < num:
            parse_game(match.group(0))

def main():
    for fn in sys.argv[1:]:
        parse_ev(fn)

if __name__ == "__main__":
    main()
