from Evaluation.global_functions import board, pinned_direction, sum_function


def knight_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, knight_attack, s2)

    v = 0

    for i in range(8):
        ix = ((i > 3) + 1) * (((i % 4) > 1) * 2 - 1)
        iy = (2 - (i > 3)) * (1 if i % 2 == 0 else -1)
        b = board(pos, square['x'] + ix, square['y'] + iy)

        if (b == "N"
                and (s2 is None or (s2['x'] == square['x'] + ix and s2['y'] == square['y'] + iy))
                and not pinned(pos, {'x': square['x'] + ix, 'y': square['y'] + iy})):
            v += 1
    return v


def bishop_xray_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, bishop_xray_attack)

    v = 0

    for i in range(4):
        ix = (2 if i > 1 else -2) // 2
        iy = (2 if i % 2 == 0 else -2) // 2

        for d in range(1, 8):
            b = board(pos, square['x'] + d * ix, square['y'] + d * iy)

            if b == "B" and (s2 is None or (s2['x'] == square['x'] + d * ix and s2['y'] == square['y'] + d * iy)):
                dir = pinned_direction(pos, {'x': square['x'] + d * ix, 'y': square['y'] + d * iy})
                if dir == 0 or abs(ix + iy * 3) == dir:
                    v += 1

            if b != "-" and b != "Q" and b != "q":
                break

    return v


def rook_xray_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, rook_xray_attack)

    v = 0

    for i in range(4):
        ix = -1 if i == 0 else (1 if i == 1 else 0)
        iy = -1 if i == 2 else (1 if i == 3 else 0)

        for d in range(1, 8):
            b = board(pos, square['x'] + d * ix, square['y'] + d * iy)

            if b == "R" and (s2 is None or (s2['x'] == square['x'] + d * ix and s2['y'] == square['y'] + d * iy)):
                dir = pinned_direction(pos, {'x': square['x'] + d * ix, 'y': square['y'] + d * iy})
                if dir == 0 or abs(ix + iy * 3) == dir:
                    v += 1
            if b != "-" and b != "R" and b != "Q" and b != "q":
                break
    return v


def queen_attack(pos, square=None, s2=None):
    if square is None:
        return sum_function(pos, queen_attack)

    v = 0

    for i in range(8):
        ix = (i + (i > 3)) % 3 - 1
        iy = int((i + (i > 3)) / 3) - 1

        for d in range(1, 8):
            b = board(pos, square['x'] + d * ix, square['y'] + d * iy)

            if b == "Q" and (s2 is None or (s2['x'] == square['x'] + d * ix and s2['y'] == square['y'] + d * iy)):
                dir = pinned_direction(pos, {'x': square['x'] + d * ix, 'y': square['y'] + d * iy})
                if dir == 0 or abs(ix + iy * 3) == dir:
                    v += 1
            if b != "-":
                break
    return v


def pawn_attack(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pawn_attack)

    v = 0
    if board(pos, square['x'] - 1, square['y'] + 1) == "P":
        v += 1
    if board(pos, square['x'] + 1, square['y'] + 1) == "P":
        v += 1
    return v


def king_attack(pos, square=None):
    if square is None:
        return sum_function(pos, king_attack)

    for i in range(8):
        ix = (i + (i > 3)) % 3 - 1
        iy = int((i + (i > 3)) / 3) - 1

        if board(pos, square['x'] + ix, square['y'] + iy) == "K":
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

    # Iterate through 8 possible diagonal directions
    for i in range(8):
        ix = (i + (i > 3)) % 3 - 1
        iy = int((i + (i > 3)) / 3) - 1

        # Skip non-diagonal directions (ix or iy being zero)
        if ix == 0 or iy == 0:
            continue

        # Check each direction for up to 7 squares (queen's range diagonally)
        for d in range(1, 8):
            b = board(pos, square['x'] + d * ix, square['y'] + d * iy)

            # If we find a queen and either no second square (s2) is specified or it's the correct target square
            if (b == "Q"
                    and (s2 is None or (s2['x'] == square['x'] + d * ix and s2['y'] == square['y'] + d * iy))):
                direction = pinned_direction(pos, {'x': square['x'] + d * ix, 'y': square['y'] + d * iy})

                # Check if the direction is not pinned or the pin allows movement in this direction
                if direction == 0 or abs(ix + iy * 3) == direction:
                    v += 1
            if b != "-":
                break
    return v


def pinned(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, pinned)

    if "PNBRQK".find(board(pos, square['x'], square['y'])) < 0:
        return 0
    return 1 if pinned_direction(pos, square) > 0 else 0
