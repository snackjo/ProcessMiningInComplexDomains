from Evaluation.global_functions import board, all_squares, colorflip
from Evaluation.pawns import backward


def rank(pos, square=None):
    if square is None:
        return sum(rank(pos, sq) for sq in all_squares(pos))  # Assuming all_squares returns all squares
    return 8 - square.y


def file(pos, square=None):
    if square is None:
        return sum(file(pos, sq) for sq in all_squares(pos))
    return 1 + square.x


def bishop_count(pos, square=None):
    if square is None:
        return sum(bishop_count(pos, sq) for sq in all_squares(pos))
    return 1 if board(pos, square.x, square.y) == "B" else 0


def queen_count(pos, square=None):
    if square is None:
        return sum(queen_count(pos, sq) for sq in all_squares(pos))
    return 1 if board(pos, square.x, square.y) == "Q" else 0


def pawn_count(pos, square=None):
    if square is None:
        return sum(pawn_count(pos, sq) for sq in all_squares(pos))
    return 1 if board(pos, square.x, square.y) == "P" else 0


def knight_count(pos, square=None):
    if square is None:
        return sum(knight_count(pos, sq) for sq in all_squares(pos))
    return 1 if board(pos, square.x, square.y) == "N" else 0


def rook_count(pos, square=None):
    if square is None:
        return sum(rook_count(pos, sq) for sq in all_squares(pos))
    return 1 if board(pos, square.x, square.y) == "R" else 0


def opposite_bishops(pos):
    if bishop_count(pos) != 1 or bishop_count(colorflip(pos)) != 1:
        return 0

    color = [0, 0]
    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "B":
                color[0] = (x + y) % 2
            if board(pos, x, y) == "b":
                color[1] = (x + y) % 2

    return 0 if color[0] == color[1] else 1


def king_distance(pos, square=None):
    if square is None:
        return sum(king_distance(pos, sq) for sq in all_squares(pos))

    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "K":
                return max(abs(x - square.x), abs(y - square.y))
    return 0


def king_ring(pos, square=None, full=True):
    if square is None:
        return sum(king_ring(pos, sq) for sq in all_squares(pos))

    if not full and board(pos, square.x + 1, square.y - 1) == "p" and board(pos, square.x - 1, square.y - 1) == "p":
        return 0

    for ix in range(-2, 3):
        for iy in range(-2, 3):
            if board(pos, square.x + ix, square.y + iy) == "k" and (
                    (-1 <= ix <= 1 or square.x + ix in [0, 7]) and (-1 <= iy <= 1 or square.y + iy in [0, 7])):
                return 1
    return 0


def piece_count(pos, square=None):
    if square is None:
        return sum(piece_count(pos, sq) for sq in all_squares(pos))

    i = "PNBRQK".find(board(pos, square.x, square.y))
    return 1 if i >= 0 else 0


def pawn_attacks_span(pos, square=None):
    if square is None:
        return sum(pawn_attacks_span(pos, sq) for sq in all_squares(pos))

    pos2 = colorflip(pos)
    for y in range(square.y):
        if (board(pos, square.x - 1, y) == "p" and (y == square.y - 1 or (
                board(pos, square.x - 1, y + 1) != "P" and not backward(pos2, {'x': square.x - 1, 'y': 7 - y})))) or \
                (board(pos, square.x + 1, y) == "p" and (y == square.y - 1 or (
                        board(pos, square.x + 1, y + 1) != "P" and not backward(pos2,
                                                                                {'x': square.x + 1, 'y': 7 - y})))):
            return 1
    return 0
