from Evaluation.attack import attack
from Evaluation.global_functions import board, colorflip, all_squares
from Evaluation.helpers import rank, file
from Evaluation.material import non_pawn_material


def space_area(pos, square=None):
    if square is None:
        return sum(space_area(pos, sq) for sq in all_squares(pos))

    v = 0
    rank_value = rank(pos, square)
    file_value = file(pos, square)

    if (2 <= rank_value <= 4 and 3 <= file_value <= 6
            and board(pos, square.x, square.y) != "P"
            and board(pos, square.x - 1, square.y - 1) != "p"
            and board(pos, square.x + 1, square.y - 1) != "p"):

        v += 1
        if (board(pos, square.x, square.y - 1) == "P"
            or board(pos, square.x, square.y - 2) == "P"
            or board(pos, square.x, square.y - 3) == "P") \
                and not attack(colorflip(pos), {'x': square.x, 'y': 7 - square.y}):
            v += 1

    return v


def space(pos, square=None):
    if non_pawn_material(pos) + non_pawn_material(colorflip(pos)) < 12222:
        return 0

    piece_count = 0
    blocked_count = 0

    for x in range(8):
        for y in range(8):
            piece = board(pos, x, y)
            if "PNBRQK".find(piece) >= 0:
                piece_count += 1
            if piece == "P" and (board(pos, x, y - 1) == "p" or (
                    board(pos, x - 1, y - 2) == "p" and board(pos, x + 1, y - 2) == "p")):
                blocked_count += 1
            if piece == "p" and (board(pos, x, y + 1) == "P" or (
                    board(pos, x - 1, y + 2) == "P" and board(pos, x + 1, y + 2) == "P")):
                blocked_count += 1

    weight = piece_count - 3 + min(blocked_count, 9)
    return (space_area(pos, square) * weight * weight // 16)
