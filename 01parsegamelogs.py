#!/usr/bin/python

# input: filename(s) in EVA/EVN format
# output: training set representing labelled situations

from common import FeatureSet, GameState, PlayerState, Label
import json
import logging
import re
import sys

def parse_header(header):
    game_state = GameState()
    base_featureset = FeatureSet()

    for line in header.split("\n"):
        line = line.strip()
        if line.startswith("info,"):
            _, key, value = line.split(",")

            if key in ["visteam", "hometeam"]:
                setattr(GameState, key, value)

            fs_key = "game_%s" % key
            if fs_key in FeatureSet.__slots__:
                setattr(FeatureSet, fs_key, value)

    return game_state, base_featureset

def add_player_state(line, game_state, state_by_id):
    # note, this doesn't keep track of who gets subbed out, just the latest state for each player
    _, retrosheetid, name, team, batpos, fieldpos = line.split(",")

    player_state = PlayerState()
    player_state.retrosheetid = retrosheetid
    player_state.name = name
    player_state.visorhome = "visteam" if team == "0" else "hometeam"
    player_state.team = getattr(game_state, player_state.visorhome)
    player_state.batpos = batpos
    player_state.fieldpos = fieldpos

    state_by_id[retrosheetid] = player_state

def parse_players(players, game_state):
    state_by_id = {}

    for line in players.split("\n"):
        line = line.strip()
        if line.startswith("start,"):
            add_player_state(line, game_state, state_by_id)

    return state_by_id

def get_feature_sets(playbyplay, game_state, base_featureset, player_state_by_id):
    for line in playbyplay.split("\n"):
        line = line.strip()

        if line.startswith("sub"):
            add_player_state(line, game_state, player_state_by_id)

        elif line.startswith("play"):
            _, inning, visorhome, retrosheetid, count, pitches, play = line.split(",")

            if any( play.startswith(ignore) for ignore in ["NP"] ):
                continue

            try:
                featureset = base_featureset.copy()

                # player
                featureset.add_player_info(player_state_by_id[retrosheetid])

                # at-bat stats
                featureset.ab_inning = inning
                numballs, numstrikes = count
                featureset.ab_numballs = numballs
                featureset.ab_numstrikes = numstrikes

                # TODO: keep track of outs, runners on?

                # label
                if play.startswith("HR"):
                    featureset.label = Label.HR
                elif play.startswith("K"):
                    featureset.label = Label.K
                else:
                    featureset.label = Label.OTHER

                yield featureset
            except Exception:
                logging.exception("Choked on line: %s" % line)
                raise

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
    player_state_by_id = parse_players(sections.group("players"), game_state)

    for feature_set in get_feature_sets(sections.group("playbyplay"), game_state, base_featureset, player_state_by_id):
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
