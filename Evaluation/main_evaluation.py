from Evaluation.global_functions import *
from Evaluation.helpers import *
from Evaluation.imbalance import *
from Evaluation.king import *
from Evaluation.material import *
from Evaluation.mobility import *
from Evaluation.passed_pawns import *
from Evaluation.pawns import *
from Evaluation.pieces import *
from Evaluation.space import *
from Evaluation.threats import *
from Evaluation.winnable import *

"""
https://hxim.github.io/Stockfish-Evaluation-Guide/
"""


def main_evaluation(pos, *args):
    mg = middle_game_evaluation(pos)
    eg = end_game_evaluation(pos)
    p = phase(pos)
    rule50 = rule_50(pos)

    # Apply scaling factor to endgame evaluation
    eg = eg * scale_factor(pos, eg) / 64

    # Calculate combined evaluation
    v = ((mg * p + (eg * (128 - p))) // 128)

    # Adjust v if there's only one argument (as in original code)
    if len(args) == 0:
        v = (v // 16) * 16

    # Add tempo adjustment
    v += tempo(pos)

    # Apply rule50 modification
    v = (v * (100 - rule50) // 100)

    return v


def middle_game_evaluation(pos, nowinnable=False):
    v = 0
    v += piece_value_mg(pos) - piece_value_mg(colorflip(pos))
    v += psqt_mg(pos) - psqt_mg(colorflip(pos))
    v += imbalance_total(pos)
    v += pawns_mg(pos) - pawns_mg(colorflip(pos))
    v += pieces_mg(pos) - pieces_mg(colorflip(pos))
    v += mobility_mg(pos) - mobility_mg(colorflip(pos))
    v += threats_mg(pos) - threats_mg(colorflip(pos))
    v += passed_mg(pos) - passed_mg(colorflip(pos))
    v += space(pos) - space(colorflip(pos))
    v += king_mg(pos) - king_mg(colorflip(pos))
    if not nowinnable:
        v += winnable_total_mg(pos, v)
    return v


def end_game_evaluation(pos, nowinnable=False):
    v = 0
    v += piece_value_eg(pos) - piece_value_eg(colorflip(pos))
    v += psqt_eg(pos) - psqt_eg(colorflip(pos))
    v += imbalance_total(pos)
    v += pawns_eg(pos) - pawns_eg(colorflip(pos))
    v += pieces_eg(pos) - pieces_eg(colorflip(pos))
    v += mobility_eg(pos) - mobility_eg(colorflip(pos))
    v += threats_eg(pos) - threats_eg(colorflip(pos))
    v += passed_eg(pos) - passed_eg(colorflip(pos))
    v += king_eg(pos) - king_eg(colorflip(pos))
    if not nowinnable:
        v += winnable_total_eg(pos, v)
    return v


def scale_factor(pos, eg=None):
    if eg is None:
        eg = end_game_evaluation(pos)

    pos2 = colorflip(pos)
    pos_w = pos if eg > 0 else pos2
    pos_b = pos2 if eg > 0 else pos

    sf = 64
    pc_w = pawn_count(pos_w)
    pc_b = pawn_count(pos_b)
    qc_w = queen_count(pos_w)
    qc_b = queen_count(pos_b)
    bc_w = bishop_count(pos_w)
    bc_b = bishop_count(pos_b)
    nc_w = knight_count(pos_w)
    nc_b = knight_count(pos_b)
    npm_w = non_pawn_material(pos_w)
    npm_b = non_pawn_material(pos_b)

    bishop_value_mg = 825
    bishop_value_eg = 915
    rook_value_mg = 1276

    if pc_w == 0 and npm_w - npm_b <= bishop_value_mg:
        sf = 0 if npm_w < rook_value_mg else 4 if npm_b <= bishop_value_mg else 14

    if sf == 64:
        ob = opposite_bishops(pos)
        if ob and npm_w == bishop_value_mg and npm_b == bishop_value_mg:
            sf = 22 + 4 * candidate_passed(pos_w)
        elif ob:
            sf = 22 + 3 * piece_count(pos_w)
        else:
            if npm_w == rook_value_mg and npm_b == rook_value_mg and pc_w - pc_b <= 1:
                pawnking_b = 0
                pcw_flank = [0, 0]
                for x in range(8):
                    for y in range(8):
                        if board(pos_w, x, y) == "P":
                            pcw_flank[0 if x < 4 else 1] = 1
                        if board(pos_b, x, y) == "K":
                            for ix in range(-1, 2):
                                for iy in range(-1, 2):
                                    if board(pos_b, x + ix, y + iy) == "P":
                                        pawnking_b = 1
                if pcw_flank[0] != pcw_flank[1] and pawnking_b:
                    return 36

            if qc_w + qc_b == 1:
                sf = 37 + 3 * (bc_b + nc_b if qc_w == 1 else bc_w + nc_w)
            else:
                sf = min(sf, 36 + 7 * pc_w)

    return sf


def phase(pos):
    midgame_limit = 15258
    endgame_limit = 3915
    npm = non_pawn_material(pos) + non_pawn_material(colorflip(pos))
    npm = max(endgame_limit, min(npm, midgame_limit))
    return ((npm - endgame_limit) * 128) // (midgame_limit - endgame_limit)


def tempo(pos, square=None):
    if square is not None:
        return 0
    return 28 * (1 if pos.w else -1)


def rule_50(pos, square=None):
    if square is not None:
        return 0
    return pos.m[0]
