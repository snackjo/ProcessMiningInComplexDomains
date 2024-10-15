from Evaluation.attack import knight_attack, bishop_xray_attack, rook_xray_attack, queen_attack
from Evaluation.global_functions import board, all_squares, colorflip
from Evaluation.helpers import rank
from Evaluation.king import blockers_for_king


def mobility(pos, square=None):
    if square is None:
        return sum(mobility(pos, sq) for sq in all_squares(pos))

    v = 0
    b = board(pos, square.x, square.y)

    if "NBRQ".find(b) < 0:
        return 0

    for x in range(8):
        for y in range(8):
            s2 = {'x': x, 'y': y}
            if not mobility_area(pos, s2):
                continue
            if b == "N" and knight_attack(pos, s2, square) and board(pos, x, y) != 'Q':
                v += 1
            if b == "B" and bishop_xray_attack(pos, s2, square) and board(pos, x, y) != 'Q':
                v += 1
            if b == "R" and rook_xray_attack(pos, s2, square):
                v += 1
            if b == "Q" and queen_attack(pos, s2, square):
                v += 1

    return v


def mobility_area(pos, square=None):
    if square is None:
        return sum(mobility_area(pos, sq) for sq in all_squares(pos))

    if board(pos, square.x, square.y) == "K":
        return 0
    if board(pos, square.x, square.y) == "Q":
        return 0
    if board(pos, square.x - 1, square.y - 1) == "p":
        return 0
    if board(pos, square.x + 1, square.y - 1) == "p":
        return 0
    if (board(pos, square.x, square.y) == "P" and
            (rank(pos, square) < 4 or board(pos, square.x, square.y - 1) != "-")):
        return 0
    if blockers_for_king(colorflip(pos), {'x': square.x, 'y': 7 - square.y}):
        return 0

    return 1


def mobility_bonus(pos, square=None, mg=True):
    if square is None:
        return sum(mobility_bonus(pos, sq, mg) for sq in all_squares(pos))

    bonus = [
        [-62, -53, -12, -4, 3, 13, 22, 28, 33],
        [-48, -20, 16, 26, 38, 51, 55, 63, 63, 68, 81, 81, 91, 98],
        [-60, -20, 2, 3, 3, 11, 22, 31, 40, 40, 41, 48, 57, 57, 62],
        [-30, -12, -8, -9, 20, 23, 23, 35, 38, 53, 64, 65, 65, 66, 67, 67, 72, 72, 77, 79, 93, 108, 108, 108, 110, 114,
         114, 116]
    ] if mg else [
        [-81, -56, -31, -16, 5, 11, 17, 20, 25],
        [-59, -23, -3, 13, 24, 42, 54, 57, 65, 73, 78, 86, 88, 97],
        [-78, -17, 23, 39, 70, 99, 103, 121, 134, 139, 158, 164, 168, 169, 172],
        [-48, -30, -7, 19, 40, 55, 59, 75, 78, 96, 96, 100, 121, 127, 131, 133, 136, 141, 147, 150, 151, 168, 168, 171,
         182, 182, 192, 219]
    ]

    i = "NBRQ".find(board(pos, square.x, square.y))
    if i < 0:
        return 0

    return bonus[i][mobility(pos, square)]


def mobility_mg(pos, square=None):
    if square is None:
        return sum(mobility_mg(pos, sq) for sq in all_squares(pos))
    return mobility_bonus(pos, square, True)


def mobility_eg(pos, square=None):
    if square is None:
        return sum(mobility_eg(pos, sq) for sq in all_squares(pos))
    return mobility_bonus(pos, square, False)
