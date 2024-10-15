"""from HttpRequests.chess_api import ChessAPI
chess_api_hikaru = ChessAPI("hikaru", "2018", "01")
games_pgn = chess_api_hikaru.get_games()
print(games_pgn)
"""
import chess.pgn
import chess.engine
from Evaluation.main_evaluation import main_evaluation
from Evaluation.global_functions import board_to_position


def main() -> None:
    engine = chess.engine.SimpleEngine.popen_uci(
        r"C:\Users\carlj\Documents\stockfish\stockfish\stockfish-windows-x86-64-avx2.exe")

    #pgn = open("Games/ruy_lopez_chigorin_variation_adams_vs_kasimdzhanov.pgn")
    pgn = open("Games/game_2.pgn")

    game = chess.pgn.read_game(pgn)
    board = game.board()

    largest_changes = []
    prev_score = None

    for move in game.mainline_moves():
        move_num = board.fullmove_number
        color = board.turn
        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(depth=20))
        overall_score = info['score'].white()

        if prev_score is not None:
            change = abs(overall_score.score() - prev_score.score())
            largest_changes.append((move_num, move, change, prev_score, overall_score, color))
            largest_changes = sorted(largest_changes, key=lambda x: x[2], reverse=True)[:10]

        prev_score = overall_score
        print(f"Move: {move_num}{'.' if board.turn == chess.WHITE else '...'} {move} Score: {overall_score}")


    print("\n")
    for move_num, move, change, prev_score, overall_score, color in largest_changes:
        print(f"Move: {move_num}{' W' if color else ' B'} {move}, Change: {change}, From: {prev_score} -> {overall_score}")
    engine.quit()


if __name__ == '__main__':
    main()
