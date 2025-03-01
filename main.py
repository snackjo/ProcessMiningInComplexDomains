from functions import *


def main() -> None:
    # USE CASE 1
    # generate_fine_grained_event_log(pgn_path="Data/2017_May_italian_game_filtered_high_elo.pgn")

    # USE CASE 2
    # generate_coarse_event_log_xes(pgn_path="Data/2014_March_filtered_high_elo.pgn")

    # USE CASE 3
    extract_sample_from_csv(start=0, end=10000)
    generate_puzzle_move_log(file_path="Data/0_10000_puzzles.csv", existing_xes_path=None, elo_limit=2400)

if __name__ == '__main__':
    main()
