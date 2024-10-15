from Evaluation.global_functions import colorflip, board
from Evaluation.main_evaluation import middle_game_evaluation, end_game_evaluation
from Evaluation.material import non_pawn_material
from Evaluation.passed_pawns import candidate_passed


def winnable(pos, square=None):
    if square is not None:
        return 0

    pawns = 0
    kx = [0, 0]
    ky = [0, 0]
    flanks = [0, 0]

    for x in range(8):
        open_files = [0, 0]
        for y in range(8):
            piece = board(pos, x, y).upper()

            if piece == "P":
                open_files[0 if board(pos, x, y) == "P" else 1] = 1
                pawns += 1

            if piece == "K":
                king_index = 0 if board(pos, x, y) == "K" else 1
                kx[king_index] = x
                ky[king_index] = y

        if open_files[0] + open_files[1] > 0:
            flanks[0 if x < 4 else 1] = 1

    pos2 = colorflip(pos)
    passed_count = candidate_passed(pos) + candidate_passed(pos2)
    both_flanks = 1 if flanks[0] and flanks[1] else 0
    outflanking = abs(kx[0] - kx[1]) - abs(ky[0] - ky[1])
    pure_pawn = 1 if (non_pawn_material(pos) + non_pawn_material(pos2)) == 0 else 0
    almost_unwinnable = 1 if outflanking < 0 and both_flanks == 0 else 0
    infiltration = 1 if ky[0] < 4 or ky[1] > 3 else 0

    return (9 * passed_count
            + 12 * pawns
            + 9 * outflanking
            + 21 * both_flanks
            + 24 * infiltration
            + 51 * pure_pawn
            - 43 * almost_unwinnable
            - 110)


def winnable_total_mg(pos, v=None):
    if v is None:
        v = middle_game_evaluation(pos, nowinnable=True)

    return (1 if v > 0 else -1 if v < 0 else 0) * max(min(winnable(pos) + 50, 0), -abs(v))


def winnable_total_eg(pos, v=None):
    if v is None:
        v = end_game_evaluation(pos, nowinnable=True)

    return (1 if v > 0 else -1 if v < 0 else 0) * max(winnable(pos), -abs(v))
