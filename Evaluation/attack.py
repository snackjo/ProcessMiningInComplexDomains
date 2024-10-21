from Evaluation.global_functions import board, pinned_direction, sum_function


def knight_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, knight_attack)

    v = 0
    knight_moves = [
        (-2, -1), (-2, 1), (2, -1), (2, 1),
        (-1, -2), (-1, 2), (1, -2), (1, 2)
    ]

    for move in knight_moves:
        dx, dy = move
        b = board(pos, square['y'] + dy, square['x'] + dx)
        if b == "N" and (s2 is None or (s2['y'] == square['y'] + dy and s2['x'] == square['x'] + dx)) and not pinned(
                pos, {
                    'y': square['y'] + dy, 'x': square['x'] + dx}):
            v += 1
    return v


def bishop_xray_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, bishop_xray_attack)

    v = 0
    diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for direction in diagonal_directions:
        dx, dy = direction
        for d in range(1, 8):
            b = board(pos, square['y'] + d * dy, square['x'] + d * dx)
            if b == "B" and (s2 is None or (s2['y'] == square['y'] + d * dy and s2['x'] == square['x'] + d * dx)):
                dir = pinned_direction(pos, {'y': square['y'] + d * dy, 'x': square['x'] + d * dx})
                if dir == 0 or abs(dx + dy * 3) == dir:
                    v += 1
            if b != "-" and b != "Q" and b != "q":
                break
    return v


def rook_xray_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, rook_xray_attack)

    v = 0
    straight_directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    for direction in straight_directions:
        dx, dy = direction
        for d in range(1, 8):
            b = board(pos, square['y'] + d * dy, square['x'] + d * dx)
            if b == "R" and (s2 is None or (s2['y'] == square['y'] + d * dy and s2['x'] == square['x'] + d * dx)):
                dir = pinned_direction(pos, {'y': square['y'] + d * dy, 'x': square['x'] + d * dx})
                if dir == 0 or abs(dx + dy * 3) == dir:
                    v += 1
            if b != "-" and b != "R" and b != "Q" and b != "q":
                break
    return v


def queen_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, queen_attack)

    v = 0
    all_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, 1), (1, 0), (0, -1), (-1, 0)]

    for direction in all_directions:
        dx, dy = direction
        for d in range(1, 8):
            b = board(pos, square['y'] + d * dy, square['x'] + d * dx)
            if b == "Q" and (s2 is None or (s2['y'] == square['y'] + d * dy and s2['x'] == square['x'] + d * dx)):
                dir = pinned_direction(pos, {'y': square['y'] + d * dy, 'x': square['x'] + d * dx})
                if dir == 0 or abs(dx + dy * 3) == dir:
                    v += 1
            if b != "-":
                break
    return v


def pawn_attack(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pawn_attack)

    v = 0
    if board(pos, square['y'] + 1, square['x'] - 1) == "P":
        v += 1
    if board(pos, square['y'] + 1, square['x'] + 1) == "P":
        v += 1
    return v


def king_attack(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, king_attack)

    king_moves = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]

    for move in king_moves:
        dx, dy = move
        if board(pos, square['y'] + dy, square['x'] + dx) == "K":
            return 1
    return 0


def attack(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, attack)

    v = 0
    v += pawn_attack(pos, square)
    v += king_attack(pos, square)
    v += knight_attack(pos, square)
    v += bishop_xray_attack(pos, square)
    v += rook_xray_attack(pos, square)
    v += queen_attack(pos, square)
    return v


def queen_attack_diagonal(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, queen_attack_diagonal)

    v = 0
    diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for direction in diagonal_directions:
        dx, dy = direction
        for d in range(1, 8):
            b = board(pos, square['y'] + d * dy, square['x'] + d * dx)
            if b == "Q" and (s2 is None or (s2['y'] == square['y'] + d * dy and s2['x'] == square['x'] + d * dx)):
                dir = pinned_direction(pos, {'y': square['y'] + d * dy, 'x': square['x'] + d * dx})
                if dir == 0 or abs(dx + dy * 3) == dir:
                    v += 1
            if b != "-":
                break
    return v


def pinned(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pinned)

    if "PNBRQK".find(board(pos, square['y'], square['x'])) < 0:
        return 0
    return 1 if pinned_direction(pos, square) > 0 else 0
