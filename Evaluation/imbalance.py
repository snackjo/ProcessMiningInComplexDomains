from Evaluation.global_functions import board, colorflip, sum_function
from Evaluation.helpers import bishop_count


def imbalance(pos, square=None, param=None):
    if square is None:
        return sum_function(pos, imbalance)

    qo = [[0], [40, 38], [32, 255, -62], [0, 104, 4, 0], [-26, -2, 47, 105, -208], [-189, 24, 117, 133, -134, -6]]
    qt = [[0], [36, 0], [9, 63, 0], [59, 65, 42, 0], [46, 39, 24, -24, 0], [97, 100, -42, 137, 268, 0]]

    j = "XPNBRQxpnbrq".find(board(pos, square['x'], square['y']))
    if j < 0 or j > 5:
        return 0

    bishop = [0, 0]
    v = 0

    for x in range(8):
        for y in range(8):
            i = "XPNBRQxpnbrq".find(board(pos, x, y))
            if i < 0:
                continue
            if i == 9:
                bishop[0] += 1
            if i == 3:
                bishop[1] += 1
            if i % 6 > j:
                continue
            if i > 5:
                v += qt[j][i - 6]
            else:
                v += qo[j][i]

    if bishop[0] > 1:
        v += qt[j][0]
    if bishop[1] > 1:
        v += qo[j][0]

    return v


def bishop_pair(pos, square=None):
    if bishop_count(pos) < 2:
        return 0
    if square is None:
        return 1438
    return 1 if board(pos, square['x'], square['y']) == "B" else 0


def imbalance_total(pos, square=None):
    v = 0
    v += imbalance(pos) - imbalance(colorflip(pos))
    v += bishop_pair(pos) - bishop_pair(colorflip(pos))
    return int(v / 16)
