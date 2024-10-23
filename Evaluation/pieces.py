from Evaluation.attack import pawn_attack, knight_attack, bishop_xray_attack
from Evaluation.global_functions import board, sum_function, rank
from Evaluation.helpers import king_distance, pawn_attacks_span, king_ring
from Evaluation.king import king_attackers_count
from Evaluation.mobility import mobility


def outpost(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, outpost)

    if board(pos, square['x'], square['y']) not in ["N", "B"]:
        return 0

    if not outpost_square(pos, square):
        return 0

    return 1


def outpost_square(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, outpost_square)

    if rank(pos, square) < 4 or rank(pos, square) > 6:
        return 0

    if board(pos, square['x'] - 1, square['y'] + 1) != "P" and board(pos, square['x'] + 1, square['y'] + 1) != "P":
        return 0

    if pawn_attacks_span(pos, square):
        return 0

    return 1


def reachable_outpost(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, reachable_outpost)

    if board(pos, square['x'], square['y']) not in ["N", "B"]:
        return 0

    v = 0
    for x in range(8):
        for y in range(2, 5):
            if (board(pos, square['x'], square['y']) == "N"
                and "PNBRQK".find(board(pos, x, y)) < 0
                and knight_attack(pos, {'x': x, 'y': y}, square)
                and outpost_square(pos, {'x': x, 'y': y})) \
                    or (board(pos, square['x'], square['y']) == "B"
                        and "PNBRQK".find(board(pos, x, y)) < 0
                        and bishop_xray_attack(pos, {'x': x, 'y': y}, square)
                        and outpost_square(pos, {'x': x, 'y': y})):
                support = 2 if board(pos, x - 1, y + 1) == "P" or board(pos, x + 1, y + 1) == "P" else 1
                v = max(v, support)

    return v


def minor_behind_pawn(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, minor_behind_pawn)

    if board(pos, square['x'], square['y']) not in ["B", "N"]:
        return 0

    if board(pos, square['x'], square['y'] - 1).upper() != "P":
        return 0

    return 1


def bishop_pawns(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, bishop_pawns)

    if board(pos, square['x'], square['y']) != "B":
        return 0

    c = (square['x'] + square['y']) % 2
    v = 0
    blocked = 0

    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "P" and c == (x + y) % 2:
                v += 1
            if (board(pos, x, y) == "P"
                    and 1 < x < 6
                    and board(pos, x, y - 1) != "-"):
                blocked += 1

    return v * (blocked + (0 if pawn_attack(pos, square) > 0 else 1))


def rook_on_file(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, rook_on_file)

    if board(pos, square['x'], square['y']) != "R":
        return 0

    open_file = 1
    for y in range(8):
        if board(pos, square['x'], y) == "P":
            return 0
        if board(pos, square['x'], y) == "p":
            open_file = 0

    return open_file + 1


def trapped_rook(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, trapped_rook)

    if board(pos, square['x'], square['y']) != "R":
        return 0

    if rook_on_file(pos, square) or mobility(pos, square) > 3:
        return 0

    kx, ky = 0, 0
    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "K":
                kx, ky = x, y

    if (kx < 4) != (square['x'] < kx):
        return 0

    return 1


def weak_queen(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, weak_queen)

    if board(pos, square['x'], square['y']) != "Q":
        return 0

    for i in range(8):
        ix = (i + (i > 3)) % 3 - 1
        iy = int((i + (i > 3)) / 3) - 1
        count = 0

        for d in range(1, 8):
            b = board(pos, square['x'] + d * ix, square['y'] + d * iy)

            if b == "r" and (ix == 0 or iy == 0) and count == 1:
                return 1
            if b == "b" and (ix != 0 and iy != 0) and count == 1:
                return 1
            if b != "-":
                count += 1

    return 0


def king_protector(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, king_protector)

    if board(pos, square['x'], square['y']) not in ["N", "B"]:
        return 0

    return king_distance(pos, square)


def long_diagonal_bishop(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, long_diagonal_bishop)

    if board(pos, square['x'], square['y']) != "B":
        return 0

    if square['x'] - square['y'] != 0 and square['x'] - (7 - square['y']) != 0:
        return 0

    x1, y1 = square['x'], square['y']

    if min(x1, 7 - x1) > 2:
        return 0

    for i in range(min(x1, 7 - x1), 4):
        if board(pos, x1, y1) in ["p", "P"]:
            return 0
        if x1 < 4:
            x1 += 1
        else:
            x1 -= 1
        if y1 < 4:
            y1 += 1
        else:
            y1 -= 1

    return 1


def outpost_total(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, outpost_total)

    if board(pos, square['x'], square['y']) not in ["N", "B"]:
        return 0

    knight = board(pos, square['x'], square['y']) == "N"
    reachable = 0

    if not outpost(pos, square):
        if not knight:
            return 0
        reachable = reachable_outpost(pos, square)
        if not reachable:
            return 0
        return 1

    if knight and (square['x'] < 2 or square['x'] > 5):
        ea = 0
        cnt = 0
        for x in range(8):
            for y in range(8):
                if ((abs(square['x'] - x) == 2 and abs(square['y'] - y) == 1) or
                    (abs(square['x'] - x) == 1 and abs(square['y'] - y) == 2)) and \
                        board(pos, x, y) in "nbrqk":
                    ea = 1
                if (x < 4 and square['x'] < 4) or (x >= 4 and square['x'] >= 4):
                    if board(pos, x, y) in "nbrqk":
                        cnt += 1
        if not ea and cnt <= 1:
            return 2

    return 4 if knight else 3


def rook_on_queen_file(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, rook_on_queen_file)

    if board(pos, square['x'], square['y']) != "R":
        return 0

    for y in range(8):
        if board(pos, square['x'], y).upper() == "Q":
            return 1

    return 0


def bishop_xray_pawns(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, bishop_xray_pawns)

    if board(pos, square['x'], square['y']) != "B":
        return 0

    count = 0
    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "p" and abs(square['x'] - x) == abs(square['y'] - y):
                count += 1

    return count


def rook_on_king_ring(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, rook_on_king_ring)

    if board(pos, square['x'], square['y']) != "R":
        return 0

    if king_attackers_count(pos, square) > 0:
        return 0

    for y in range(8):
        if king_ring(pos, {'x': square['x'], 'y': y}):
            return 1

    return 0


def bishop_on_king_ring(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, bishop_on_king_ring)

    if board(pos, square['x'], square['y']) != "B":
        return 0

    if king_attackers_count(pos, square) > 0:
        return 0

    for i in range(4):
        ix = 2 * (i > 1) - 1
        iy = 2 * (i % 2 == 0) - 1
        for d in range(1, 8):
            x = square['x'] + d * ix
            y = square['y'] + d * iy
            if board(pos, x, y) == "x":
                break
            if king_ring(pos, {'x': x, 'y': y}):
                return 1
            if board(pos, x, y).upper() == "P":
                break

    return 0


def queen_infiltration(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, queen_infiltration)

    if board(pos, square['x'], square['y']) != "Q":
        return 0

    if square['y'] > 3:
        return 0

    if board(pos, square['x'] + 1, square['y'] - 1) == "p":
        return 0

    if board(pos, square['x'] - 1, square['y'] - 1) == "p":
        return 0

    if pawn_attacks_span(pos, square):
        return 0

    return 1


def pieces_mg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pieces_mg, param)

    if "NBRQ".find(board(pos, square['x'], square['y'])) < 0:
        return 0

    v = 0
    v += [0, 31, -7, 30, 56][outpost_total(pos, square)]
    v += 18 * minor_behind_pawn(pos, square)
    v -= 3 * bishop_pawns(pos, square)
    v -= 4 * bishop_xray_pawns(pos, square)
    v += 6 * rook_on_queen_file(pos, square)
    v += 16 * rook_on_king_ring(pos, square)
    v += 24 * bishop_on_king_ring(pos, square)
    v += [0, 19, 48][rook_on_file(pos, square)]
    v -= trapped_rook(pos, square) * 55 * (1 if pos['c'][0] or pos['c'][1] else 2)
    v -= 56 * weak_queen(pos, square)
    v -= 2 * queen_infiltration(pos, square)
    v -= (8 if board(pos, square['x'], square['y']) == "N" else 6) * king_protector(pos, square)
    v += 45 * long_diagonal_bishop(pos, square)

    return v


def pieces_eg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pieces_eg, param)

    if "NBRQ".find(board(pos, square['x'], square['y'])) < 0:
        return 0

    v = 0
    v += [0, 22, 36, 23, 36][outpost_total(pos, square)]
    v += 3 * minor_behind_pawn(pos, square)
    v -= 7 * bishop_pawns(pos, square)
    v -= 5 * bishop_xray_pawns(pos, square)
    v += 11 * rook_on_queen_file(pos, square)
    v += [0, 7, 29][rook_on_file(pos, square)]
    v -= trapped_rook(pos, square) * 13 * (1 if pos['c'][0] or pos['c'][1] else 2)
    v -= 15 * weak_queen(pos, square)
    v += 14 * queen_infiltration(pos, square)
    v -= 9 * king_protector(pos, square)

    return v
