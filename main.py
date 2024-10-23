"""from HttpRequests.chess_api import ChessAPI
chess_api_hikaru = ChessAPI("hikaru", "2018", "01")
games_pgn = chess_api_hikaru.get_games()
print(games_pgn)
"""
import time
import chess.engine
import chess.pgn
from chess import Board
from chess.pgn import GameNode

from Evaluation.global_functions import board_to_position
from Evaluation.main_evaluation import main_evaluation


def get_sliced_moves(game: GameNode, param: int) -> list[chess.Move]:
    moves = []
    for move in game.mainline():
        moves.append(move.move)

    sliced_moves = moves[0:param]

    return sliced_moves


def get_move_num_and_color(board: Board) -> tuple[int, bool]:
    return board.fullmove_number, board.turn

def debug_at_move(game, board, engine, move_num) -> None:
    sliced_moves = get_sliced_moves(game, move_num)
    for move in sliced_moves:
        board.push(move)

    calc_score = main_evaluation(board_to_position(board), None)
    print(f"Calculated score: {calc_score}")
    info = engine.analyse(board, chess.engine.Limit(depth=20))
    print(f"Engine score: {info['score'].white()}")


def run_and_evaluate_game(game, board):
    for move in game.mainline_moves():
        move_num, color = get_move_num_and_color(board)
        board.push(move)
        start = time.time()
        calc_score = main_evaluation(board_to_position(board), None)
        end = time.time()

        print(f"Move: {move_num}{' W' if color else ' B'} {move} Score: {calc_score}")
        # print(f"Elapsed time: {end - start}")


def main() -> None:
    engine = chess.engine.SimpleEngine.popen_uci(
        r"C:\Users\carlj\Documents\stockfish\stockfish\stockfish-windows-x86-64-avx2.exe")

    # pgn = open("Games/ruy_lopez_chigorin_variation_adams_vs_kasimdzhanov.pgn")
    pgn = open("Games/game_2.pgn")

    game = chess.pgn.read_game(pgn)
    board = game.board()

    largest_changes = []
    prev_score = None

    """for move in game.mainline_moves():
        move_num, color = get_move_num_and_color(board)
        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(depth=20))
        overall_score = info['score'].white()

        if prev_score is not None:
            change = abs(overall_score.score() - prev_score.score())
            largest_changes.append((move_num, move, change, prev_score, overall_score, color))
            largest_changes = sorted(largest_changes, key=lambda x: x[2], reverse=True)[:10]

        prev_score = overall_score
        print(f"Move: {move_num}{'W' if color else 'B'} {move} Score: {overall_score}")


    print("\n")
    for move_num, move, change, prev_score, overall_score, color in largest_changes:
        print(f"Move: {move_num}{' W' if color else ' B'} {move}, Change: {change}, From: {prev_score} -> {overall_score}")
    """



    #calc_score = main_evaluation(board_to_position(board), None)
    #print(f"Calculated score: {calc_score}")
    #print(f"Elapsed time: {end - start}")

    run_and_evaluate_game(game, board)

    #debug_at_move(game, board, engine, 38)


    engine.quit()


if __name__ == '__main__':
    main()
