from Evaluation.attack import attack, knight_attack, queen_attack_diagonal, bishop_xray_attack, rook_xray_attack, \
    queen_attack, king_attack, pawn_attack
from Evaluation.global_functions import board, colorflip, sum_function
from Evaluation.helpers import queen_count
from Evaluation.mobility import mobility_area


def safe_pawn(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, safe_pawn)

    if board(pos, square['x'], square['y']) != "P":
        return 0

    if attack(pos, square):
        return 1

    if not attack(colorflip(pos), {'x': square['x'], 'y': 7 - square['y']}):
        return 1

    return 0


def threat_safe_pawn(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, threat_safe_pawn)

    if "nbrq".find(board(pos, square['x'], square['y'])) < 0:
        return 0

    if not pawn_attack(pos, square):
        return 0

    if safe_pawn(pos, {'x': square['x'] - 1, 'y': square['y'] + 1}) or safe_pawn(pos, {'x': square['x'] + 1,
                                                                                       'y': square['y'] + 1}):
        return 1

    return 0


def weak_enemies(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, weak_enemies)

    if "pnbrqk".find(board(pos, square['x'], square['y'])) < 0:
        return 0

    if board(pos, square['x'] - 1, square['y'] - 1) == "p" or board(pos, square['x'] + 1, square['y'] - 1) == "p":
        return 0

    if not attack(pos, square):
        return 0

    if attack(pos, square) <= 1 and attack(colorflip(pos), {'x': square['x'], 'y': 7 - square['y']}) > 1:
        return 0

    return 1


def minor_threat(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, minor_threat)

    piece_type = "pnbrqk".find(board(pos, square['x'], square['y']))

    if piece_type < 0:
        return 0

    if not knight_attack(pos, square) and not bishop_xray_attack(pos, square):
        return 0

    if (board(pos, square['x'], square['y']) == "p" or not (board(pos, square['x'] - 1, square['y'] - 1) == "p" or
                                                            board(pos, square['x'] + 1, square['y'] - 1) == "p" or
                                                            (attack(pos, square) <= 1 and attack(colorflip(pos),
                                                                                                 {'x': square['x'],
                                                                                                  'y': 7 - square[
                                                                                                      'y']}) > 1))) \
            and not weak_enemies(pos, square):
        return 0

    return piece_type + 1


def rook_threat(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, rook_threat)

    piece_type = "pnbrqk".find(board(pos, square['x'], square['y']))

    if piece_type < 0 or not weak_enemies(pos, square) or not rook_xray_attack(pos, square):
        return 0

    return piece_type + 1


def hanging(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, hanging)

    if not weak_enemies(pos, square):
        return 0

    if board(pos, square['x'], square['y']) != "p" and attack(pos, square) > 1:
        return 1

    if not attack(colorflip(pos), {'x': square['x'], 'y': 7 - square['y']}):
        return 1

    return 0


def king_threat(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, king_threat)

    if "pnbrq".find(board(pos, square['x'], square['y'])) < 0 or not weak_enemies(pos, square) or not king_attack(pos,
                                                                                                                  square):
        return 0

    return 1


def pawn_push_threat(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pawn_push_threat)

    if "pnbrqk".find(board(pos, square['x'], square['y'])) < 0:
        return 0

    for ix in [-1, 1]:
        if (board(pos, square['x'] + ix, square['y'] + 2) == "P" and board(pos, square['x'] + ix,
                                                                           square['y'] + 1) == "-" and
                board(pos, square['x'] + ix - 1, square['y']) != "p" and board(pos, square['x'] + ix + 1,
                                                                               square['y']) != "p" and
                (attack(pos, {'x': square['x'] + ix, 'y': square['y'] + 1}) or
                 not attack(colorflip(pos), {'x': square['x'] + ix, 'y': 6 - square['y']}))):
            return 1

        if (square['y'] == 3 and board(pos, square['x'] + ix, square['y'] + 3) == "P" and
                board(pos, square['x'] + ix, square['y'] + 2) == "-" and board(pos, square['x'] + ix,
                                                                               square['y'] + 1) == "-" and
                board(pos, square['x'] + ix - 1, square['y']) != "p" and board(pos, square['x'] + ix + 1,
                                                                               square['y']) != "p" and
                (attack(pos, {'x': square['x'] + ix, 'y': square['y'] + 1}) or
                 not attack(colorflip(pos), {'x': square['x'] + ix, 'y': 6 - square['y']}))):
            return 1

    return 0


def slider_on_queen(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, slider_on_queen)

    pos2 = colorflip(pos)

    if queen_count(pos2) != 1 or board(pos, square['x'], square['y']) == "P" or \
            board(pos, square['x'] - 1, square['y'] - 1) == "p" or board(pos, square['x'] + 1, square['y'] - 1) == "p":
        return 0

    if attack(pos, square) <= 1 or not mobility_area(pos, square):
        return 0

    diagonal = queen_attack_diagonal(pos2, {'x': square['x'], 'y': 7 - square['y']})
    v = 2 if queen_count(pos) == 0 else 1

    if diagonal and bishop_xray_attack(pos, square):
        return v
    if not diagonal and rook_xray_attack(pos, square) and queen_attack(pos2, {'x': square['x'], 'y': 7 - square['y']}):
        return v

    return 0


def knight_on_queen(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, knight_on_queen)

    pos2 = colorflip(pos)
    qx, qy = -1, -1

    for x in range(8):
        for y in range(8):
            if board(pos, x, y) == "q":
                if qx >= 0 or qy >= 0:
                    return 0
                qx, qy = x, y

    if queen_count(pos2) != 1 or board(pos, square['x'], square['y']) == "P" or \
            board(pos, square['x'] - 1, square['y'] - 1) == "p" or board(pos, square['x'] + 1,
                                                                         square['y'] - 1) == "p" or \
            (attack(pos, square) <= 1 and attack(pos2, {'x': square['x'], 'y': 7 - square['y']}) > 1) or \
            not mobility_area(pos, square) or not knight_attack(pos, square):
        return 0

    v = 2 if queen_count(pos) == 0 else 1

    if abs(qx - square['x']) == 2 and abs(qy - square['y']) == 1:
        return v
    if abs(qx - square['x']) == 1 and abs(qy - square['y']) == 2:
        return v

    return 0


def restricted(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, restricted)

    if attack(pos, square) == 0:
        return 0

    pos2 = colorflip(pos)

    if not attack(pos2, {'x': square['x'], 'y': 7 - square['y']}):
        return 0

    if pawn_attack(pos2, {'x': square['x'], 'y': 7 - square['y']}) > 0:
        return 0

    if attack(pos2, {'x': square['x'], 'y': 7 - square['y']}) > 1 and attack(pos, square) == 1:
        return 0

    return 1


def weak_queen_protection(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, weak_queen_protection)

    if not weak_enemies(pos, square) or not queen_attack(colorflip(pos), {'x': square['x'], 'y': 7 - square['y']}):
        return 0

    return 1


def threats_mg(pos):
    v = 0
    v += 69 * hanging(pos)
    v += 24 if king_threat(pos) > 0 else 0
    v += 48 * pawn_push_threat(pos)
    v += 173 * threat_safe_pawn(pos)
    v += 60 * slider_on_queen(pos)
    v += 16 * knight_on_queen(pos)
    v += 7 * restricted(pos)
    v += 14 * weak_queen_protection(pos)

    for x in range(8):
        for y in range(8):
            s = {'x': x, 'y': y}
            v += [0, 5, 57, 77, 88, 79, 0][minor_threat(pos, s)]
            v += [0, 3, 37, 42, 0, 58, 0][rook_threat(pos, s)]

    return v


def threats_eg(pos):
    v = 0
    v += 36 * hanging(pos)
    v += 89 if king_threat(pos) > 0 else 0
    v += 39 * pawn_push_threat(pos)
    v += 94 * threat_safe_pawn(pos)
    v += 18 * slider_on_queen(pos)
    v += 11 * knight_on_queen(pos)
    v += 7 * restricted(pos)

    for x in range(8):
        for y in range(8):
            s = {'x': x, 'y': y}
            v += [0, 32, 41, 56, 119, 161, 0][minor_threat(pos, s)]
            v += [0, 46, 68, 60, 38, 41, 0][rook_threat(pos, s)]

    return v
