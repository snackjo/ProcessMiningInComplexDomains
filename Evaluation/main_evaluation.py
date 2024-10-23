"""
https://hxim.github.io/Stockfish-Evaluation-Guide/
"""
from Evaluation.global_functions import colorflip, board
from Evaluation.helpers import pawn_count, queen_count, bishop_count, knight_count, opposite_bishops, piece_count
from Evaluation.imbalance import imbalance_total
from Evaluation.king import king_mg, king_eg
from Evaluation.material import piece_value_mg, psqt_mg, piece_value_eg, psqt_eg, non_pawn_material
from Evaluation.mobility import mobility_mg, mobility_eg
from Evaluation.passed_pawns import passed_mg, passed_eg, candidate_passed
from Evaluation.pawns import pawns_mg, pawns_eg
from Evaluation.pieces import pieces_mg, pieces_eg
from Evaluation.space import space
from Evaluation.threats import threats_mg, threats_eg


def main_evaluation(pos, *args):
    mg = middle_game_evaluation(pos)
    eg = end_game_evaluation(pos)
    p = phase(pos)
    rule50 = rule_50(pos)

    # Apply scaling factor to endgame evaluation
    eg = eg * scale_factor(pos, eg) / 64

    # Calculate combined evaluation
    v = int((mg * p + int(eg * (128 - p))) / 128)

    if len(args) == 0 or args[0] is None:
        v = int(v / 16) * 16

    # Add tempo adjustment
    v += tempo(pos)

    # Apply rule50 modification
    v = int(v * (100 - rule50) / 100)

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
    return int(((npm - endgame_limit) * 128) / (midgame_limit - endgame_limit))


def tempo(pos, square=None):
    if square is not None:
        return 0
    return 28 * (1 if pos['w'] else -1)


def rule_50(pos, square=None):
    if square is not None:
        return 0
    return pos['m'][0]


'''Winnable'''


def winnable(pos, square=None):
    if square is not None:
        return 0

    pawns = 0
    kx = [0, 0]
    ky = [0, 0]
    flanks = [0, 0]

    for x in range(8):
        open_files = [0, 0]
        for y in range(8):
            piece = board(pos, x, y).upper()

            if piece == "P":
                open_files[0 if board(pos, x, y) == "P" else 1] = 1
                pawns += 1

            if piece == "K":
                king_index = 0 if board(pos, x, y) == "K" else 1
                kx[king_index] = x
                ky[king_index] = y

        if open_files[0] + open_files[1] > 0:
            flanks[0 if x < 4 else 1] = 1

    pos2 = colorflip(pos)
    passed_count = candidate_passed(pos) + candidate_passed(pos2)
    both_flanks = 1 if flanks[0] and flanks[1] else 0
    outflanking = abs(kx[0] - kx[1]) - abs(ky[0] - ky[1])
    pure_pawn = 1 if (non_pawn_material(pos) + non_pawn_material(pos2)) == 0 else 0
    almost_unwinnable = 1 if outflanking < 0 and both_flanks == 0 else 0
    infiltration = 1 if ky[0] < 4 or ky[1] > 3 else 0

    return (9 * passed_count
            + 12 * pawns
            + 9 * outflanking
            + 21 * both_flanks
            + 24 * infiltration
            + 51 * pure_pawn
            - 43 * almost_unwinnable
            - 110)


def winnable_total_mg(pos, v=None):
    if v is None:
        v = middle_game_evaluation(pos, nowinnable=True)

    return (1 if v > 0 else -1 if v < 0 else 0) * max(min(winnable(pos) + 50, 0), -abs(v))


def winnable_total_eg(pos, v=None):
    if v is None:
        v = end_game_evaluation(pos, nowinnable=True)

    return (1 if v > 0 else -1 if v < 0 else 0) * max(winnable(pos), -abs(v))
