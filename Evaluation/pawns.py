from Evaluation.global_functions import board, rank, sum_function, colorflip


def isolated(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, isolated)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    for y in range(8):
        if board(pos, square['x'] - 1, y) == "P" or board(pos, square['x'] + 1, y) == "P":
            return 0

    return 1


def opposed(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, opposed)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    for y in range(square['y']):
        if board(pos, square['x'], y) == "p":
            return 1

    return 0


def phalanx(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, phalanx)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    if board(pos, square['x'] - 1, square['y']) == "P" or board(pos, square['x'] + 1, square['y']) == "P":
        return 1

    return 0


def supported(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, supported)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    return (board(pos, square['x'] - 1, square['y'] + 1) == "P") + (board(pos, square['x'] + 1, square['y'] + 1) == "P")


def backward(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, backward)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    for y in range(square['y'], 8):
        if board(pos, square['x'] - 1, y) == "P" or board(pos, square['x'] + 1, y) == "P":
            return 0

    if board(pos, square['x'] - 1, square['y'] - 2) == "p" or board(pos, square['x'] + 1,
                                                                    square['y'] - 2) == "p" or board(pos,
                                                                                                     square['x'],
                                                                                                     square[
                                                                                                         'y'] - 1) == "p":
        return 1

    return 0


def doubled(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, doubled)

    if board(pos, square['x'], square['y']) != "P":
        return 0
    if board(pos, square['x'], square['y'] + 1) != "P":
        return 0
    if board(pos, square['x'] - 1, square['y'] + 1) == "P" or board(pos, square['x'] + 1, square['y'] + 1) == "P":
        return 0

    return 1


def connected(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, connected)

    return 1 if supported(pos, square) or phalanx(pos, square) else 0


def connected_bonus(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, connected_bonus)

    if not connected(pos, square):
        return 0

    seed = [0, 7, 8, 12, 29, 48, 86]
    op = opposed(pos, square)
    ph = phalanx(pos, square)
    su = supported(pos, square)
    bl = 1 if board(pos, square['x'], square['y'] - 1) == "p" else 0
    r = rank(pos, square)

    if r < 2 or r > 7:
        return 0

    return seed[r - 1] * (2 + ph - op) + 21 * su


def weak_unopposed_pawn(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, weak_unopposed_pawn)

    if opposed(pos, square):
        return 0

    return 1 if isolated(pos, square) or backward(pos, square) else 0


def weak_lever(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, weak_lever)

    if board(pos, square['x'], square['y']) != "P":
        return 0
    if board(pos, square['x'] - 1, square['y'] - 1) != "p" or board(pos, square['x'] + 1, square['y'] - 1) != "p":
        return 0
    if board(pos, square['x'] - 1, square['y'] + 1) == "P" or board(pos, square['x'] + 1, square['y'] + 1) == "P":
        return 0

    return 1


def blocked(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, blocked)

    if board(pos, square['x'], square['y']) != "P" or square['y'] not in [2, 3]:
        return 0
    if board(pos, square['x'], square['y'] - 1) != "p":
        return 0

    return 4 - square['y']


def doubled_isolated(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, doubled_isolated)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    if isolated(pos, square):
        obe, eop, ene = 0, 0, 0

        for y in range(8):
            if y > square['y'] and board(pos, square['x'], y) == "P":
                obe += 1
            if y < square['y'] and board(pos, square['x'], y) == "p":
                eop += 1
            if board(pos, square['x'] - 1, y) == "p" or board(pos, square['x'] + 1, y) == "p":
                ene += 1

        if obe > 0 and ene == 0 and eop > 0:
            return 1

    return 0


def pawns_mg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pawns_mg)

    v = 0
    if doubled_isolated(pos, square):
        v -= 11
    elif isolated(pos, square):
        v -= 5
    elif backward(pos, square):
        v -= 9

    v -= doubled(pos, square) * 11
    v += connected(pos, square) * connected_bonus(pos, square)
    v -= 13 * weak_unopposed_pawn(pos, square)
    v += [0, -11, -3][blocked(pos, square)]

    return v


def pawns_eg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pawns_eg)

    v = 0
    if doubled_isolated(pos, square):
        v -= 56
    elif isolated(pos, square):
        v -= 15
    elif backward(pos, square):
        v -= 24

    v -= doubled(pos, square) * 56
    if connected(pos, square):
        v += int(connected_bonus(pos, square) * (rank(pos, square) - 3) / 4)
    v -= 27 * weak_unopposed_pawn(pos, square)
    v -= 56 * weak_lever(pos, square)
    v += [0, -4, 4][blocked(pos, square)]

    return v
