from Evaluation.global_functions import board, sum_function


def non_pawn_material(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, non_pawn_material)
    i = "NBRQ".find(board(pos, square['x'], square['y']))
    if i >= 0:
        return piece_value_bonus(pos, square, True)
    return 0


def piece_value_bonus(pos, square=None, mg=True):
    if square is None:
        return sum_function(pos, piece_value_bonus)

    a = [124, 781, 825, 1276, 2538] if mg else [206, 854, 915, 1380, 2682]
    i = "PNBRQ".find(board(pos, square['x'], square['y']))
    if i >= 0:
        return a[i]
    return 0


def psqt_bonus(pos, square=None, mg=True):
    if square is None:
        return sum_function(pos, psqt_bonus, mg)

    bonus = [
        [
            [-175, -92, -74, -73], [-77, -41, -27, -15], [-61, -17, 6, 12], [-35, 8, 40, 49],
            [-34, 13, 44, 51], [-9, 22, 58, 53], [-67, -27, 4, 37], [-201, -83, -56, -26]
        ],
        [
            [-53, -5, -8, -23], [-15, 8, 19, 4], [-7, 21, -5, 17], [-5, 11, 25, 39],
            [-12, 29, 22, 31], [-16, 6, 1, 11], [-17, -14, 5, 0], [-48, 1, -14, -23]
        ],
        [
            [-31, -20, -14, -5], [-21, -13, -8, 6], [-25, -11, -1, 3], [-13, -5, -4, -6],
            [-27, -15, -4, 3], [-22, -2, 6, 12], [-2, 12, 16, 18], [-17, -19, -1, 9]
        ],
        [
            [3, -5, -5, 4], [-3, 5, 8, 12], [-3, 6, 13, 7], [4, 5, 9, 8],
            [0, 14, 12, 5], [-4, 10, 6, 8], [-5, 6, 10, 8], [-2, -2, 1, -2]
        ],
        [
            [271, 327, 271, 198], [278, 303, 234, 179], [195, 258, 169, 120], [164, 190, 138, 98],
            [154, 179, 105, 70], [123, 145, 81, 31], [88, 120, 65, 33], [59, 89, 45, -1]
        ]
    ] if mg else [
        [
            [-96, -65, -49, -21], [-67, -54, -18, 8], [-40, -27, -8, 29], [-35, -2, 13, 28],
            [-45, -16, 9, 39], [-51, -44, -16, 17], [-69, -50, -51, 12], [-100, -88, -56, -17]
        ],
        [
            [-57, -30, -37, -12], [-37, -13, -17, 1], [-16, -1, -2, 10], [-20, -6, 0, 17],
            [-17, -1, -14, 15], [-30, 6, 4, 6], [-31, -20, -1, 1], [-46, -42, -37, -24]
        ],
        [
            [-9, -13, -10, -9], [-12, -9, -1, -2], [6, -8, -2, -6], [-6, 1, -9, 7],
            [-5, 8, 7, -6], [6, 1, -7, 10], [4, 5, 20, -5], [18, 0, 19, 13]
        ],
        [
            [-69, -57, -47, -26], [-55, -31, -22, -4], [-39, -18, -9, 3], [-23, -3, 13, 24],
            [-29, -6, 9, 21], [-38, -18, -12, 1], [-50, -27, -24, -8], [-75, -52, -43, -36]
        ],
        [
            [1, 45, 85, 76], [53, 100, 133, 135], [88, 130, 169, 175], [103, 156, 172, 172],
            [96, 166, 199, 199], [92, 172, 184, 191], [47, 121, 116, 131], [11, 59, 73, 78]
        ]
    ]

    pbonus = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [3, 3, 10, 19, 16, 19, 7, -5],
        [-9, -15, 11, 15, 32, 22, 5, -22],
        [-4, -23, 6, 20, 40, 17, 4, -8],
        [13, 0, -13, 1, 11, -2, -13, 5],
        [5, -12, -7, 22, -8, -5, -15, -8],
        [-7, 7, -3, -13, 5, -16, 10, -8],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ] if mg else [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [-10, -6, 10, 0, 14, 7, -5, -19],
        [-10, -10, -10, 4, 4, 3, -6, -4],
        [6, -2, -8, -4, -13, -12, -10, -9],
        [10, 5, 4, -5, -5, -5, 14, 9],
        [28, 20, 21, 28, 30, 7, 6, 13],
        [0, -11, 12, 21, 25, 19, 4, 7],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]

    i = "PNBRQK".find(board(pos, square['x'], square['y']))
    if i < 0:
        return 0
    if i == 0:
        return pbonus[7 - square['y']][square['x']]
    else:
        return bonus[i - 1][7 - square['y']][min(square['x'], 7 - square['x'])]


def piece_value_mg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, piece_value_mg, param)
    return piece_value_bonus(pos, square, True)


def piece_value_eg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, piece_value_eg, param)
    return piece_value_bonus(pos, square, False)


def psqt_mg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, psqt_mg, param)
    return psqt_bonus(pos, square, True)


def psqt_eg(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, psqt_eg, param)
    return psqt_bonus(pos, square, False)
