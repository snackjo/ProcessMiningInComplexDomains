"""from HttpRequests.chess_api import ChessAPI
chess_api_hikaru = ChessAPI("hikaru", "2018", "01")
games_pgn = chess_api_hikaru.get_games()
print(games_pgn)
"""

from functions import *


def main() -> None:
    # print_largest_changes()

    # debug_at_move(game, board, engine, 53)

    generate_event_log()
    # start = time.time()
    # generate_fine_grained_event_log(None, "Games/4000_italian_game_two_knights_defense_knight_attack.pgn")
    # end = time.time()
    # print(f"Elapsed time: {end - start}")

    # input_file = "Games/2014-March.pgn"
    # output_file = "filtered_games.pgn"
    # moves_prefix = ["e4", "e5", "Bc4", "Nc6", "Qh5"]
    # filter_pgn(input_file, output_file, moves_prefix)
    # heuristic_mine_log("data/event_log_italian_1400.csv")

    # generate_coarse_event_log_xes(None, "Games/2014-March-0-1400.pgn")
    # inductive_mine_log()

if __name__ == '__main__':
    main()
