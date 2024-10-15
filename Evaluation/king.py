from Evaluation.attack import rook_xray_attack, queen_attack, bishop_xray_attack, knight_attack, attack, king_attack, \
    pinned_direction
from Evaluation.global_functions import board, all_squares, colorflip
from Evaluation.helpers import king_ring, queen_count
from Evaluation.mobility import mobility_mg


def pawnless_flank(pos):
    pawns = [0] * 8
    kx = 0
    for x in range(8):
        for y in range(8):
            if board(pos, x, y).upper() == "P":
                pawns[x] += 1
            if board(pos, x, y) == "k":
                kx = x

    if kx == 0:
        sum_pawns = pawns[0] + pawns[1] + pawns[2]
    elif kx < 3:
        sum_pawns = pawns[0] + pawns[1] + pawns[2] + pawns[3]
    elif kx < 5:
        sum_pawns = pawns[2] + pawns[3] + pawns[4] + pawns[5]
    elif kx < 7:
        sum_pawns = pawns[4] + pawns[5] + pawns[6] + pawns[7]
    else:
        sum_pawns = pawns[5] + pawns[6] + pawns[7]

    return 1 if sum_pawns == 0 else 0


def strength_square(pos, square=None):
    if square is None:
        return sum(strength_square(pos, sq) for sq in all_squares(pos))

    v = 5
    kx = min(6, max(1, square.x))
    weakness = [
        [-6, 81, 93, 58, 39, 18, 25],
        [-43, 61, 35, -49, -29, -11, -63],
        [-10, 75, 23, -2, 32, 3, -45],
        [-39, -13, -29, -52, -48, -67, -166]
    ]

    for x in range(kx - 1, kx + 2):
        us = 0
        for y in range(7, square.y - 1, -1):
            if board(pos, x, y) == "p" and board(pos, x - 1, y + 1) != "P" and board(pos, x + 1, y + 1) != "P":
                us = y
        f = min(x, 7 - x)
        v += weakness[f][us] if us in weakness[f] else 0

    return v


def storm_square(pos, square, eg=False):
    if square is None:
        return sum(storm_square(pos, sq) for sq in all_squares(pos))

    v = 0
    ev = 5
    kx = min(6, max(1, square.x))
    unblockedstorm = [
        [85, -289, -166, 97, 50, 45, 50],
        [46, -25, 122, 45, 37, -10, 20],
        [-6, 51, 168, 34, -2, -22, -14],
        [-15, -11, 101, 4, 11, -15, -29]
    ]
    blockedstorm = [
        [0, 0, 76, -10, -7, -4, -1],
        [0, 0, 78, 15, 10, 6, 2]
    ]

    for x in range(kx - 1, kx + 2):
        us = 0
        them = 0
        for y in range(7, square.y - 1, -1):
            if board(pos, x, y) == "p" and board(pos, x - 1, y + 1) != "P" and board(pos, x + 1, y + 1) != "P":
                us = y
            if board(pos, x, y) == "P":
                them = y
        f = min(x, 7 - x)
        if us > 0 and them == us + 1:
            v += blockedstorm[0][them]
            ev += blockedstorm[1][them]
        else:
            v += unblockedstorm[f][them]

    return ev if eg else v


def shelter_strength(pos, square=None):
    w = 0
    s = 1024
    tx = None
    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "k" or (pos.c[2] and x == 6 and y == 0) or (pos.c[3] and x == 2 and y == 0):
                w1 = strength_square(pos, {'x': x, 'y': y})
                s1 = storm_square(pos, {'x': x, 'y': y})
                if s1 - w1 < s - w:
                    w = w1
                    s = s1
                    tx = max(1, min(6, x))

    if square is None:
        return w

    if tx is not None and board(pos, square.x, square.y) == "p" and tx - 1 <= square.x <= tx + 1:
        for y in range(square.y - 1, -1, -1):
            if board(pos, square.x, y) == "p":
                return 0
        return 1

    return 0


def shelter_storm(pos, square=None):
    w = 0
    s = 1024
    tx = None
    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "k" or (pos.c[2] and x == 6 and y == 0) or (pos.c[3] and x == 2 and y == 0):
                w1 = strength_square(pos, {'x': x, 'y': y})
                s1 = storm_square(pos, {'x': x, 'y': y})
                if s1 - w1 < s - w:
                    w = w1
                    s = s1
                    tx = max(1, min(6, x))

    if square is None:
        return s

    if tx is not None and board(pos, square.x, square.y).upper() == "P" and tx - 1 <= square.x <= tx + 1:
        for y in range(square.y - 1, -1, -1):
            if board(pos, square.x, y) == board(pos, square.x, square.y):
                return 0
        return 1

    return 0


def king_pawn_distance(pos, square=None):
    v = 6
    kx, ky = 0, 0
    px, py = 0, 0

    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "K":
                kx = x
                ky = y

    for x in range(8):
        for y in range(8):
            dist = max(abs(x - kx), abs(y - ky))
            if board(pos, x, y) == "P" and dist < v:
                px = x
                py = y
                v = dist

    if square is None or (square.x == px and square.y == py):
        return v

    return 0


def check(pos, square=None, type=None):
    if square is None:
        return sum(check(pos, sq, type) for sq in all_squares(pos))

    if (rook_xray_attack(pos, square) and (type is None or type in [2, 4])) or \
            (queen_attack(pos, square) and (type is None or type == 3)):
        for i in range(4):
            ix = -1 if i == 0 else 1 if i == 1 else 0
            iy = -1 if i == 2 else 1 if i == 3 else 0
            for d in range(1, 8):
                b = board(pos, square.x + d * ix, square.y + d * iy)
                if b == "k":
                    return 1
                if b != "-" and b != "q":
                    break

    if (bishop_xray_attack(pos, square) and (type is None or type in [1, 4])) or \
            (queen_attack(pos, square) and (type is None or type == 3)):
        for i in range(4):
            ix = (i > 1) * 2 - 1
            iy = (i % 2 == 0) * 2 - 1
            for d in range(1, 8):
                b = board(pos, square.x + d * ix, square.y + d * iy)
                if b == "k":
                    return 1
                if b != "-" and b != "q":
                    break

    if knight_attack(pos, square) and (type is None or type in [0, 4]):
        if board(pos, square.x + 2, square.y + 1) == "k" or \
                board(pos, square.x + 2, square.y - 1) == "k" or \
                board(pos, square.x + 1, square.y + 2) == "k" or \
                board(pos, square.x + 1, square.y - 2) == "k" or \
                board(pos, square.x - 2, square.y + 1) == "k" or \
                board(pos, square.x - 2, square.y - 1) == "k" or \
                board(pos, square.x - 1, square.y + 2) == "k" or \
                board(pos, square.x - 1, square.y - 2) == "k":
            return 1

    return 0


def safe_check(pos, square=None, type=None):
    if square is None:
        return sum(safe_check(pos, sq, type) for sq in all_squares(pos))

    if "PNBRQK".find(board(pos, square.x, square.y)) >= 0:
        return 0
    if not check(pos, square, type):
        return 0

    pos2 = colorflip(pos)
    if type == 3 and safe_check(pos, square, 2):
        return 0
    if type == 1 and safe_check(pos, square, 3):
        return 0

    if (not attack(pos2, {'x': square.x, 'y': 7 - square.y}) or
        (weak_squares(pos, square) and attack(pos, square) > 1)) and \
            (type != 3 or not queen_attack(pos2, {'x': square.x, 'y': 7 - square.y})):
        return 1

    return 0


def king_attackers_count(pos, square=None):
    if square is None:
        return sum(king_attackers_count(pos, sq) for sq in all_squares(pos))

    if "PNBRQ".find(board(pos, square.x, square.y)) < 0:
        return 0

    if board(pos, square.x, square.y) == "P":
        v = 0
        for dir in [-1, 1]:
            fr = board(pos, square.x + dir * 2, square.y) == "P"
            if 0 <= square.x + dir <= 7 and king_ring(pos, {'x': square.x + dir, 'y': square.y - 1}, True):
                v += 0.5 if fr else 1
        return v

    for x in range(8):
        for y in range(8):
            s2 = {'x': x, 'y': y}
            if king_ring(pos, s2):
                if knight_attack(pos, s2, square) or \
                        bishop_xray_attack(pos, s2, square) or \
                        rook_xray_attack(pos, s2, square) or \
                        queen_attack(pos, s2, square):
                    return 1
    return 0


def king_attackers_weight(pos, square=None):
    if square is None:
        return sum(king_attackers_weight(pos, sq) for sq in all_squares(pos))

    if king_attackers_count(pos, square):
        return [0, 81, 52, 44, 10]["PNBRQ".find(board(pos, square.x, square.y))]

    return 0


def king_attacks(pos, square=None):
    if square is None:
        return sum(king_attacks(pos, sq) for sq in all_squares(pos))

    if "NBRQ".find(board(pos, square.x, square.y)) < 0:
        return 0
    if king_attackers_count(pos, square) == 0:
        return 0

    kx, ky = 0, 0
    v = 0
    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "k":
                kx = x
                ky = y

    for x in range(kx - 1, kx + 2):
        for y in range(ky - 1, ky + 2):
            if 0 <= x <= 7 and 0 <= y <= 7 and (x != kx or y != ky):
                s2 = {'x': x, 'y': y}
                v += knight_attack(pos, s2, square)
                v += bishop_xray_attack(pos, s2, square)
                v += rook_xray_attack(pos, s2, square)
                v += queen_attack(pos, s2, square)

    return v


def weak_bonus(pos, square=None):
    if square is None:
        return sum(weak_bonus(pos, sq) for sq in all_squares(pos))

    if not weak_squares(pos, square):
        return 0
    if not king_ring(pos, square):
        return 0

    return 1


def weak_squares(pos, square=None):
    if square is None:
        return sum(weak_squares(pos, sq) for sq in all_squares(pos))

    if attack(pos, square):
        pos2 = colorflip(pos)
        attack_val = attack(pos2, {'x': square.x, 'y': 7 - square.y})
        if attack_val >= 2:
            return 0
        if attack_val == 0:
            return 1
        if king_attack(pos2, {'x': square.x, 'y': 7 - square.y}) or \
                queen_attack(pos2, {'x': square.x, 'y': 7 - square.y}):
            return 1

    return 0


def unsafe_checks(pos, square=None):
    if square is None:
        return sum(unsafe_checks(pos, sq) for sq in all_squares(pos))

    if check(pos, square, 0) and safe_check(pos, None, 0) == 0:
        return 1
    if check(pos, square, 1) and safe_check(pos, None, 1) == 0:
        return 1
    if check(pos, square, 2) and safe_check(pos, None, 2) == 0:
        return 1

    return 0


def knight_defender(pos, square=None):
    if square is None:
        return sum(knight_defender(pos, sq) for sq in all_squares(pos))

    if knight_attack(pos, square) and king_attack(pos, square):
        return 1

    return 0


def endgame_shelter(pos, square=None):
    w = 0
    s = 1024
    e = None
    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "k" or (pos.c[2] and x == 6 and y == 0) or (pos.c[3] and x == 2 and y == 0):
                w1 = strength_square(pos, {'x': x, 'y': y})
                s1 = storm_square(pos, {'x': x, 'y': y})
                e1 = storm_square(pos, {'x': x, 'y': y}, True)
                if s1 - w1 < s - w:
                    w = w1
                    s = s1
                    e = e1

    if square is None:
        return e

    return 0


def blockers_for_king(pos, square=None):
    if square is None:
        return sum(blockers_for_king(pos, sq) for sq in all_squares(pos))

    if pinned_direction(colorflip(pos), {'x': square.x, 'y': 7 - square.y}):
        return 1

    return 0


def flank_attack(pos, square=None):
    if square is None:
        return sum(flank_attack(pos, sq) for sq in all_squares(pos))

    if square.y > 4:
        return 0

    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "k":
                if x == 0 and square.x > 2:
                    return 0
                if x < 3 and square.x > 3:
                    return 0
                if 3 <= x < 5 and (square.x < 2 or square.x > 5):
                    return 0
                if x >= 5 and square.x < 4:
                    return 0
                if x == 7 and square.x < 5:
                    return 0

    a = attack(pos, square)
    if not a:
        return 0
    return 2 if a > 1 else 1


def flank_defense(pos, square=None):
    if square is None:
        return sum(flank_defense(pos, sq) for sq in all_squares(pos))

    if square.y > 4:
        return 0

    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "k":
                if x == 0 and square.x > 2:
                    return 0
                if x < 3 and square.x > 3:
                    return 0
                if 3 <= x < 5 and (square.x < 2 or square.x > 5):
                    return 0
                if x >= 5 and square.x < 4:
                    return 0
                if x == 7 and square.x < 5:
                    return 0

    return 1 if attack(colorflip(pos), {'x': square.x, 'y': 7 - square.y}) > 0 else 0


def king_danger(pos):
    count = king_attackers_count(pos)
    weight = king_attackers_weight(pos)
    king_attacks_val = king_attacks(pos)
    weak = weak_bonus(pos)
    unsafe_checks_val = unsafe_checks(pos)
    blockers_for_king_val = blockers_for_king(pos)
    king_flank_attack = flank_attack(pos)
    king_flank_defense = flank_defense(pos)
    no_queen = 0 if queen_count(pos) > 0 else 1

    v = (count * weight
         + 69 * king_attacks_val
         + 185 * weak
         - 100 * (knight_defender(colorflip(pos)) > 0)
         + 148 * unsafe_checks_val
         + 98 * blockers_for_king_val
         - 4 * king_flank_defense
         + ((3 * king_flank_attack * king_flank_attack / 8) << 0)
         - 873 * no_queen
         - ((6 * (shelter_strength(pos) - shelter_storm(pos)) / 8) << 0)
         + mobility_mg(pos) - mobility_mg(colorflip(pos))
         + 37
         + ((772 * min(safe_check(pos, None, 3), 1.45)) << 0)
         + ((1084 * min(safe_check(pos, None, 2), 1.75)) << 0)
         + ((645 * min(safe_check(pos, None, 1), 1.50)) << 0)
         + ((792 * min(safe_check(pos, None, 0), 1.62)) << 0))

    return v if v > 100 else 0


def king_mg(pos):
    v = 0
    kd = king_danger(pos)
    v -= shelter_strength(pos)
    v += shelter_storm(pos)
    v += (kd * kd / 4096) << 0
    v += 8 * flank_attack(pos)
    v += 17 * pawnless_flank(pos)
    return v


def king_eg(pos):
    v = 0
    v -= 16 * king_pawn_distance(pos)
    v += endgame_shelter(pos)
    v += 95 * pawnless_flank(pos)
    v += (king_danger(pos) / 16) << 0
    return v
