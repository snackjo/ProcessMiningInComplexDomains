from Evaluation.attack import attack
from Evaluation.global_functions import colorflip, board, rank, sum_function
from Evaluation.helpers import file
from Evaluation.pawns import supported


def candidate_passed(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, candidate_passed)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    ty1, ty2, oy = 8, 8, 8
    for y in range(square['y'] - 1, -1, -1):
        if board(pos, square['x'], y) == "P":
            return 0
        if board(pos, square['x'], y) == "p":
            ty1 = y
        if board(pos, square['x'] - 1, y) == "p" or board(pos, square['x'] + 1, y) == "p":
            ty2 = y

    if ty1 == 8 and ty2 >= square['y'] - 1:
        return 1
    if ty2 < square['y'] - 2 or ty1 < square['y'] - 1:
        return 0
    if ty2 >= square['y'] and ty1 == square['y'] - 1 and square['y'] < 4:
        if (board(pos, square['x'] - 1, square['y'] + 1) == "P" and board(pos, square['x'] - 1, square['y']) != "p"
                and board(pos, square['x'] - 2, square['y'] - 1) != "p"):
            return 1
        if (board(pos, square['x'] + 1, square['y'] + 1) == "P" and board(pos, square['x'] + 1, square['y']) != "p"
                and board(pos, square['x'] + 2, square['y'] - 1) != "p"):
            return 1

    if board(pos, square['x'], square['y'] - 1) == "p":
        return 0

    lever = (board(pos, square['x'] - 1, square['y'] - 1) == "p") + (
                board(pos, square['x'] + 1, square['y'] - 1) == "p")
    leverpush = (board(pos, square['x'] - 1, square['y'] - 2) == "p") + (
                board(pos, square['x'] + 1, square['y'] - 2) == "p")
    phalanx = (board(pos, square['x'] - 1, square['y']) == "P") + (board(pos, square['x'] + 1, square['y']) == "P")

    if lever - supported(pos, square) > 1:
        return 0
    if leverpush - phalanx > 0:
        return 0
    if lever > 0 and leverpush > 0:
        return 0

    return 1


def king_proximity(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, king_proximity)

    if not passed_leverable(pos, square):
        return 0

    r = rank(pos, square) - 1
    w = 5 * r - 13 if r > 2 else 0
    v = 0

    if w <= 0:
        return 0

    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "k":
                v += ((min(max(abs(y - square['y'] + 1), abs(x - square['x'])), 5) * 19 // 4)) * w
            if board(pos, x, y) == "K":
                v -= min(max(abs(y - square['y'] + 1), abs(x - square['x'])), 5) * 2 * w
                if square['y'] > 1:
                    v -= min(max(abs(y - square['y'] + 2), abs(x - square['x'])), 5) * w

    return v


def passed_block(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, passed_block)

    if not passed_leverable(pos, square):
        return 0
    if rank(pos, square) < 4:
        return 0
    if board(pos, square['x'], square['y'] - 1) != "-":
        return 0

    r = rank(pos, square) - 1
    w = 5 * r - 13 if r > 2 else 0
    pos2 = colorflip(pos)

    defended = 0
    unsafe = 0
    wunsafe = 0
    defended1 = 0
    unsafe1 = 0

    for y in range(square['y'] - 1, -1, -1):
        if attack(pos, {'x': square['x'], 'y': y}):
            defended += 1
        if attack(pos2, {'x': square['x'], 'y': 7 - y}):
            unsafe += 1
        if attack(pos2, {'x': square['x'] - 1, 'y': 7 - y}) or attack(pos2, {'x': square['x'] + 1, 'y': 7 - y}):
            wunsafe += 1
        if y == square['y'] - 1:
            defended1 = defended
            unsafe1 = unsafe

    for y in range(square['y'] + 1, 8):
        if board(pos, square['x'], y) in ["R", "Q"]:
            defended1 = defended = square['y']
        if board(pos, square['x'], y) in ["r", "q"]:
            unsafe1 = unsafe = square['y']

    k = (35 if unsafe == 0 and wunsafe == 0 else 20 if unsafe == 0 else 9 if unsafe1 == 0 else 0) + (
        5 if defended1 != 0 else 0)

    return k * w


def passed_file(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, passed_file)

    if not passed_leverable(pos, square):
        return 0

    file_val = file(pos, square)
    return min(file_val - 1, 8 - file_val)


def passed_rank(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, passed_rank)

    if not passed_leverable(pos, square):
        return 0

    return rank(pos, square) - 1


def passed_leverable(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, passed_leverable)
    if not candidate_passed(pos, square):
        return 0
    if board(pos, square['x'], square['y'] - 1) != "p":
        return 1
    pos2 = colorflip(pos)
    for i in [-1, 1]:
        s1 = {'x': square['x'] + i, 'y': square['y']}
        s2 = {'x': square['x'] + i, 'y': 7 - square['y']}
        if (board(pos, square['x'] + i, square['y'] + 1) == "P" and "pnbrqk".find(
                board(pos, square['x'] + i, square['y'])) < 0
                and (attack(pos, s1) > 0 or attack(pos2, s2) <= 1)):
            return 1
    return 0


def passed_mg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, passed_mg)

    if not passed_leverable(pos, square):
        return 0

    v = 0
    v += [0, 10, 17, 15, 62, 168, 276, None][passed_rank(pos, square)]
    v += passed_block(pos, square)
    v -= 11 * passed_file(pos, square)

    return v


def passed_eg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, passed_eg)

    if not passed_leverable(pos, square):
        return 0

    v = 0
    v += king_proximity(pos, square)
    v += [0, 28, 33, 41, 72, 177, 260, None][passed_rank(pos, square)]
    v += passed_block(pos, square)
    v -= 8 * passed_file(pos, square)

    return v
