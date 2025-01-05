
from functions import *


def main() -> None:
    # print_largest_changes()

    # debug_at_move(game, board, engine, 53)
    player_name = "MagnusCarlsen"
    year = "2023"
    month = "10"
    # get_games_of_player(player_name, year, month, output_file=f"{player_name}_games_{year}_{month}.pgn")
    # generate_event_log(f"Games/{player_name}_games_{year}_{month}.pgn", player_name, "event_log_MagnusCarlsen_games_2024_10.xes")
    # generate_event_log("Games/mygame.pgn", "carljchess", None, True)
    # add_move_to_activities("event_log_Hikaru_games_2024_11.xes")
    # extract_sample_from_csv()
    # start = time.time()
    # generate_fine_grained_event_log(None, "Games/1400_italian_game_two_knights_defense_knight_attack.pgn")
    # end = time.time()
    # print(f"Elapsed time: {end - start}")

    # input_file = "Games/2014-March.pgn"
    # output_file = "filtered_games.pgn"
    # moves_prefix = ["e4", "e5", "Bc4", "Nc6", "Qh5"]
    # filter_pgn(input_file, output_file, moves_prefix)
    # heuristic_mine_log("data/event_log_italian_1400.csv")

    # generate_coarse_event_log_xes(None, "Games/2014-March-0-1400.pgn")
    # inductive_mine_log()

    # generate_puzzle_log("sample_puzzles.csv", None, True)
    # split_csv_in_rating("sample_puzzles_2.csv")

    # generate_theme_log("sample_puzzles_2_0_1400.csv")
    # extract_sample_from_csv()

    # generate_puzzle_move_log("sample_puzzles_1000_after_5000.csv", None, True)
    generate_puzzle_move_log_extra_traces("Puzzles/sample_puzzles_1000_after_5000.csv", None, True)

if __name__ == '__main__':
    main()
